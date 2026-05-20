"""Agent executor for ADK agents with A2UI validation."""

try:
    from google.protobuf.message import Message
    original_setstate = Message.__setstate__
    def patched_setstate(self, state):
        if 'serialized' not in state:
             state['serialized'] = b''
        return original_setstate(self, state)
    Message.__setstate__ = patched_setstate
except Exception as e:
    pass

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

import json
import logging
import os
from a2a import types
from a2a import utils
from a2a.server import agent_execution
from a2a.server import events
from a2a.server import tasks
from a2a.utils import errors as a2a_errors
from agent import root_agent
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

  def __init__(self):
    # Prepare A2UI schema validator by reading the JSON file
    try:
      schema_path = os.path.join(os.path.dirname(__file__), "a2ui_schema.json")
      with open(schema_path, "r") as f:
        single_message_schema = json.load(f)
      
      # The schema validates a single message, but the agent might return an array of messages
      # or a wrapped object. The example executor handled arrays.
      # Let's support both single message and array of messages in validation.
      self.a2ui_schema_object = {
          "anyOf": [
              single_message_schema,
              {
                  "type": "array",
                  "items": single_message_schema
              },
              {
                  "type": "object",
                  "properties": {
                      "a2ui_messages": {
                          "type": "array",
                          "items": single_message_schema
                      }
                  },
                  "required": ["a2ui_messages"]
              }
          ]
      }
      logger.info("[DEBUG] A2UI_SCHEMA successfully loaded from file.")
    except Exception as e:  # pylint: disable=broad-except
      logger.error("[DEBUG] Failed to load A2UI_SCHEMA from file: %s", e)
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
    query = context.get_user_input()
    extracted_context = {}
    
    # Extract action context from DataPart if available
    try:
        if hasattr(context, 'message') and context.message and hasattr(context.message, 'parts'):
            for part in context.message.parts:
                if hasattr(part, 'root') and hasattr(part.root, 'data'):
                    data_part = part.root
                    if hasattr(data_part, 'metadata') and data_part.metadata and data_part.metadata.get('mimeType') == 'application/json+a2ui':
                        data = data_part.data
                        if 'userAction' in data:
                            user_action = data['userAction']
                            if 'context' in user_action:
                                action_context = user_action['context']
                                logger.warning("[DEBUG] Extracted action context: %s", action_context)
                                extracted_context = action_context
                                if 'message' in action_context:
                                    query = action_context['message']
                                    logger.warning("[DEBUG] Overriding query with action message: %s", query)
    except Exception as e:
        logger.warning("[DEBUG] Failed to extract action context: %s", e)

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

    # Save extracted context to session state
    if extracted_context:
        for k, v in extracted_context.items():
            if k != 'message':
                session.state[k] = v
        logger.warning("[DEBUG] Updated session state: %s", session.state)
    
    # Inject session state into query
    state_vars = [f"{k}={v}" for k, v in session.state.items()]
    if state_vars:
        query = f"{query} [State: {', '.join(state_vars)}]"
        logger.warning("[DEBUG] Appended state to query: %s", query)

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
          if self.a2ui_schema_object:
            jsonschema.validate(
                instance=parsed_json, schema=self.a2ui_schema_object
            )

          is_valid = True
        except Exception as e:  # pylint: disable=broad-except
          error_message = f"Validation failed: {str(e)}"

      if is_valid:
        parts = []
        if text_part.strip():
          parts.append(types.Part(root=types.TextPart(text=text_part.strip())))

        logger.info("[DEBUG]UI JSON: %s", json_string_cleaned)

        json_data = json.loads(json_string_cleaned)
        
        # Handle wrapped object or array
        messages_to_send = []
        if isinstance(json_data, dict) and "a2ui_messages" in json_data:
            messages_to_send = json_data["a2ui_messages"]
        elif isinstance(json_data, list):
            messages_to_send = json_data
        else:
            messages_to_send = [json_data]

        for message in messages_to_send:
            ui_data_part = types.Part(
                root=types.DataPart(
                    data=message,
                    metadata={"mimeType": "application/json+a2ui"},
                )
            )
            parts.append(ui_data_part)
            
        logger.info("[DEBUG] Parts: %s", parts)

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
          logger.warning(
              "[DEBUG] Retrying due to validation error: %s", error_message
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
