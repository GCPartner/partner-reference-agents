"""Agent executor for Grants Funding Manager with A2UI validation."""

import json

# Monkey-patch missing template types to fix Pydantic schema warnings on server
import sys
from typing import Any
try:
    import vertexai.preview.reasoning_engines.templates.a2a as a2a_module
    import starlette.requests
    import a2a.server.apps.rest.rest_adapter as adapter_module
    
    if "Request" not in a2a_module.__dict__:
        a2a_module.__dict__["Request"] = starlette.requests.Request
    if "ServerCallContext" not in a2a_module.__dict__:
        a2a_module.__dict__["ServerCallContext"] = adapter_module.ServerCallContext
except ImportError:
    pass
import logging
from a2a import types
from a2a import utils
from a2a.server import agent_execution
from a2a.server import events
from a2a.server import tasks
from a2a.utils import errors as a2a_errors
import a2ui_schema
from agent import root_agent
from google.adk import runners
from google.adk.artifacts import in_memory_artifact_service
from google.adk.memory import in_memory_memory_service
from google.adk.sessions import in_memory_session_service
from google.genai import types as genai_types
import jsonschema

logger = logging.getLogger(__name__)


class AdkAgentToA2AExecutor(agent_execution.AgentExecutor):
  """An agent executor for ADK agents with A2UI extraction."""

  _runner: runners.Runner

  def __init__(
      self,
  ):
    # Prepare A2UI schema validator
    try:
      single_message_schema = json.loads(a2ui_schema.A2UI_SCHEMA)
      self.a2ui_schema_object = {
          "type": "array",
          "items": single_message_schema,
      }
      logger.info("[DEBUG]A2UI_SCHEMA successfully loaded.")
    except Exception as e:  # pylint: disable=broad-except
      logger.error("[DEBUG] Failed to parse A2UI_SCHEMA: %s", e)
      self.a2ui_schema_object = None

    self._agent = root_agent
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
    logger.info(">>> EXECUTE CALLED! Query: %s", context.get_user_input())
    query = context.get_user_input()
    task = context.current_task
    print(f"[DEBUG] Query: {query}", flush=True)
    print(f"[DEBUG] RequestContext attributes: {dir(context)}", flush=True)
    if hasattr(context, "_params"):
        print(f"[DEBUG] context._params type: {type(context._params)}", flush=True)
        if isinstance(context._params, dict):
             print(f"[DEBUG] context._params keys: {context._params.keys()}", flush=True)
        else:
             print(f"[DEBUG] context._params value str: {str(context._params)[:200]}", flush=True)
    if hasattr(context, "metadata"):
        print(f"[DEBUG] context.metadata type: {type(context.metadata)}", flush=True)
        if hasattr(context.metadata, "keys"):
             print(f"[DEBUG] context.metadata keys: {context.metadata.keys()}", flush=True)
        else:
             print(f"[DEBUG] context.metadata value str: {str(context.metadata)[:200]}", flush=True)
    if task:
        print(f"[DEBUG] Task attributes: {dir(task)}", flush=True)
    if hasattr(context, 'message') and context.message:
        print(f"[DEBUG] context.message: {context.message}", flush=True)

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

    # Extract A2UI context variables from message parts
    extracted_context = {}
    if hasattr(context, 'message') and context.message and hasattr(context.message, 'parts'):
        for part in context.message.parts:
            if hasattr(part, 'data') and isinstance(part.data, dict):
                 user_action = part.data.get('userAction')
                 if isinstance(user_action, dict):
                      action_ctx = user_action.get('context')
                      if isinstance(action_ctx, dict):
                           # Safely extract description and budget
                           desc = action_ctx.get('description')
                           budget = action_ctx.get('budget')
                           if desc:
                               extracted_context['Description'] = desc
                           if budget:
                               extracted_context['Budget'] = budget

    if extracted_context:
         extracted_str = "\n".join([f"{k}: {v}" for k, v in extracted_context.items()])
         current_query_text = f"{query}\n[Extracted A2UI Context Variables]:\n{extracted_str}"
         print(f"[DEBUG] Injected Context: {extracted_str}", flush=True)
    else:
         current_query_text = query
    max_retries = 1
    attempt = 0

    # Working status
    await updater.start_work()

    while attempt <= max_retries:
      attempt += 1
      content = genai_types.Content(
          role="user", parts=[{"text": current_query_text}]
      )

      final_response_content = None

      logger.info("[DEBUG] attempt: %s", attempt)

      try:
        async for event in self._runner.run_async(
            user_id=self._user_id, session_id=session.id, new_message=content
        ):
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

      except Exception as e:  # pylint: disable=broad-except
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

      logger.info("[DEBUG]Final response content: %s", final_response_content)
      is_valid = False
      error_message = ""
      json_string_cleaned = "[]"
      text_part = final_response_content

      if "---a2ui_JSON---" not in final_response_content:
        error_message = "Delimiter '---a2ui_JSON---' not found."
      else:
        try:
          text_part, json_string = final_response_content.split(
              "---a2ui_JSON---", 1
          )
          json_string_cleaned = (
              json_string.strip().lstrip("```json").rstrip("```").strip()
          )

          if not json_string_cleaned:
            json_string_cleaned = "[]"

          parsed_json = json.loads(json_string_cleaned)
          logger.info("[DEBUG] Parsed JSON: %s", parsed_json)
          
          validation_target = parsed_json
          if isinstance(parsed_json, dict) and "a2ui_messages" in parsed_json:
              validation_target = parsed_json["a2ui_messages"]

          if self.a2ui_schema_object:
            jsonschema.validate(
                instance=validation_target, schema=self.a2ui_schema_object
            )
          is_valid = True
        except Exception as e:  # pylint: disable=broad-except
          error_message = f"Validation failed: {str(e)}"

      if is_valid:
        parts = []
        if text_part.strip():
          parts.append(types.Part(root=types.TextPart(text=text_part.strip())))

        json_data = json.loads(json_string_cleaned)

        if isinstance(json_data, list):
          for message in json_data:
            ui_data_part = types.Part(
                root=types.DataPart(
                    data=message,
                    metadata={"mimeType": "application/json+a2ui"},
                )
            )
            parts.append(ui_data_part)
        else:
          ui_data_part = types.Part(
              root=types.DataPart(
                  data=json_data,
                  metadata={"mimeType": "application/json+a2ui"},
              )
          )
          parts.append(ui_data_part)

        await updater.add_artifact(parts, name="response")
        await updater.complete()
        return

      else:
        if attempt <= max_retries:
          current_query_text = (
              f"Your previous response was invalid. {error_message} You MUST"
              " generate a valid response that strictly follows the A2UI JSON"
              f" SCHEMA. Please retry the original request: '{query}'"
          )
          continue
        else:
          await updater.add_artifact(
              [
                  types.Part(
                      root=types.TextPart(
                          text=(
                              "I encountered an error generating the UI:"
                              f" {error_message}. Here is the raw response:"
                              f" {final_response_content}"
                          )
                      )
                  )
              ],
              name="error_response",
          )
          await updater.complete()
          return

  async def cancel(
      self,
      context: agent_execution.RequestContext,
      event_queue: events.EventQueue,
  ) -> None:
    raise a2a_errors.ServerError(error=types.UnsupportedOperationError())
