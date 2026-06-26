"""Agent executor for ADK agents with A2UI validation (adapted for phone_plan_shopper_a2ui)."""

import json
import logging
import re
import zlib
import base64
import tools
from a2a import types
from a2a import utils
from a2a.server import agent_execution
from a2a.server import events
from a2a.server import tasks
from a2a.utils import errors as a2a_errors
# We need to ensure we can load schema locally if needed, but let's just use what's in the folder
try:
    import a2ui_schema
except ImportError:
    # If not found, we can try to load from json file directly
    a2ui_schema = None

import agent # Using our phone plan shopper agent
from google.adk import runners
from google.adk.artifacts import in_memory_artifact_service
from google.adk.memory import in_memory_memory_service
from google.adk.sessions import in_memory_session_service
from google.genai import types as genai_types
import jsonschema

logger = logging.getLogger(__name__)


class AdkAgentToA2AExecutor(agent_execution.AgentExecutor):
  """An agent executor for ADK agents."""

  _runner: runners.Runner

  def __init__(
      self,
  ):
    # Prepare A2UI schema validator
    self.a2ui_schema_object = None
    if a2ui_schema and hasattr(a2ui_schema, 'A2UI_SCHEMA'):
        try:
          single_message_schema = json.loads(a2ui_schema.A2UI_SCHEMA)
          self.a2ui_schema_object = {
              "type": "array",
              "items": single_message_schema,
          }
          logger.info("[DEBUG] A2UI_SCHEMA successfully loaded from a2ui_schema.py.")
        except Exception as e:  # pylint: disable=broad-except
          logger.error("[DEBUG] Failed to parse A2UI_SCHEMA from py: %s", e)
    
    if not self.a2ui_schema_object:
        # Try loading from JSON file
        try:
            with open("a2ui_schema.json", "r") as f:
                single_message_schema = json.load(f)
                self.a2ui_schema_object = {
                    "type": "array",
                    "items": single_message_schema,
                }
                logger.info("[DEBUG] A2UI_SCHEMA successfully loaded from a2ui_schema.json.")
        except Exception as e:
             logger.error("[DEBUG] Failed to load schema from json file: %s", e)

    self._agent = agent.root_agent
    self._runner = runners.Runner(
        app_name=self._agent.name,
        agent=self._agent,
        session_service=in_memory_session_service.InMemorySessionService(),
        artifact_service=in_memory_artifact_service.InMemoryArtifactService(),
        memory_service=in_memory_memory_service.InMemoryMemoryService(),
    )
    self._user_id = "remote_agent"

  async def execute(
      self,
      context: agent_execution.RequestContext,
      event_queue: events.EventQueue,
  ) -> None:
    query = context.get_user_input()
    task = context.current_task
    logger.info("[DEBUG] Query: %s", query)

    if not task:
      if not context.message:
        return

      task = utils.new_task(context.message)
      await event_queue.enqueue_event(task)

    updater = tasks.TaskUpdater(event_queue, task.id, task.context_id)
    session_id = task.context_id

    session = await self._runner.session_service.get_session(
        app_name=self._agent.name,
        user_id=self._user_id,
        session_id=session_id,
    )
    if session is None:
      session = await self._runner.session_service.create_session(
          app_name=self._agent.name,
          user_id=self._user_id,
          state={},
          session_id=session_id,
      )

    # 1. SESSION RECOVERY: Extract state from A2UI payload
    try:
        if hasattr(context, 'message') and context.message:
            for part in context.message.parts:
                if hasattr(part, 'root') and hasattr(part.root, 'data'):
                    data = part.root.data
                    if isinstance(data, dict) and 'userAction' in data:
                        action_ctx = data['userAction'].get('context', {})
                        query = action_ctx.get('message', query)
                        # Save context to session state
                        for k, v in action_ctx.items():
                            if k != 'message':
                                session.state[k] = v
    except Exception as e:
        logger.warning("Recovery failed: %s", e)

    # 2. STATE INJECTION: Persist state via prompt (Transcript Echoing)
    state_vars = [f"{k}={v}" for k, v in session.state.items()]
    if state_vars:
        query = f"{query} [State: {', '.join(state_vars)}]"
        logger.info("[DEBUG] Appended state to query: %s", query)

    current_query_text = query
    max_retries = 1
    attempt = 0

    await updater.start_work()

    while attempt <= max_retries:
      attempt += 1
      content = genai_types.Content(
          role="user", parts=[{"text": current_query_text}]
      )

      final_response_content = None
      intercepted_payloads = []

      logger.info("[DEBUG] attempt: %s", attempt)

      try:
        async for event in self._runner.run_async(
            user_id=self._user_id, session_id=session.id, new_message=content
        ):
          # Intercept tool response events to capture A2UI payloads directly from the source!
          if event.content and event.content.parts:
            for part in event.content.parts:
              if part.function_response:
                func_resp = part.function_response
                logger.info("[DEBUG] Intercepted tool response: %s", func_resp.name)
                if isinstance(func_resp.response, dict) and "result" in func_resp.response:
                  result_str = func_resp.response["result"]
                  if isinstance(result_str, str) and "---a2ui_B64---" in result_str:
                    try:
                      _, b64_part = result_str.split("---a2ui_B64---", 1)
                      b64_str = b64_part.strip().replace(' ', '').replace('\n', '')
                      compressed_data = base64.b64decode(b64_str)
                      json_str = zlib.decompress(compressed_data).decode('utf-8')
                      parsed_json = json.loads(json_str)
                      
                      # Validate against A2UI schema
                      messages_to_validate = []
                      if isinstance(parsed_json, list):
                        messages_to_validate = parsed_json
                      elif isinstance(parsed_json, dict) and "a2ui_messages" in parsed_json:
                        messages_to_validate = parsed_json["a2ui_messages"]
                      else:
                        messages_to_validate = [parsed_json]

                      for msg in messages_to_validate:
                        if not isinstance(msg, dict):
                          raise ValueError("Each A2UI message must be a JSON object.")
                        if not any(k in msg for k in ["beginRendering", "surfaceUpdate", "dataModelUpdate", "deleteSurface"]):
                          raise ValueError("Each A2UI message must contain at least one of: 'beginRendering', 'surfaceUpdate', 'dataModelUpdate', 'deleteSurface'.")

                      if self.a2ui_schema_object:
                        jsonschema.validate(
                            instance=messages_to_validate, schema=self.a2ui_schema_object
                        )
                      
                      logger.info("[DEBUG] Successfully validated intercepted A2UI payload.")
                      intercepted_payloads.append(parsed_json)
                    except Exception as ex:
                      logger.error("[ERROR] Failed to decode/validate intercepted tool payload: %s", ex)

          if event.is_final_response():
            if (
                event.content
                and event.content.parts
                and event.content.parts[0].text
            ):
              final_response_content = "\n".join(
                  [p.text for p in event.content.parts if p.text]
              )
              logger.info(
                  "[DEBUG] Final response content: %s", final_response_content
              )

      except Exception as e:
        await updater.failed(
            message=utils.new_agent_text_message(
                f"Task failed with error: {str(e)}"
            )
        )
        return

      if final_response_content is None:
        if attempt <= max_retries:
          current_query_text = "I received no response. Please try again."
          continue
        else:
          await updater.failed(
              message=utils.new_agent_text_message("No response generated.")
          )
          return

      # Clean up final response text: strip out any base64 blocks or tokens
      text_part = final_response_content
      if text_part and "---a2ui_B64---" in text_part:
        text_part, _ = text_part.split("---a2ui_B64---", 1)
      if text_part:
        text_part = text_part.strip()

      parts = []
      if text_part:
        parts.append(types.Part(root=types.TextPart(text=text_part)))

      # Package each intercepted and validated A2UI payload
      for payload in intercepted_payloads:
        messages = []
        if isinstance(payload, list):
          messages = payload
        elif isinstance(payload, dict) and "a2ui_messages" in payload:
          messages = payload["a2ui_messages"]
        else:
          messages = [payload]

        for message in messages:
          ui_data_part = types.Part(
              root=types.DataPart(
                  data=message,
                  metadata={"mimeType": "application/json+a2ui"},
              )
          )
          parts.append(ui_data_part)

      logger.info("[DEBUG] Parts successfully packaged: %s", parts)
      await updater.add_artifact(parts, name="response")
      await updater.complete()
      return


  async def cancel(
      self,
      context: agent_execution.RequestContext,
      event_queue: events.EventQueue,
  ) -> None:
    raise a2a_errors.ServerError(error=types.UnsupportedOperationError())
