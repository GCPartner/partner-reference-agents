import json
import logging
from a2a import types
from a2a import utils
from a2a.server import agent_execution
from a2a.server import events
from a2a.server import tasks
from a2a.utils import errors as a2a_errors

from . import agent
from google.adk import runners
from google.adk.artifacts import in_memory_artifact_service
from google.adk.memory import in_memory_memory_service
from google.adk.sessions import in_memory_session_service
from google.genai import types as genai_types

logger = logging.getLogger(__name__)

class AdkAgentToA2AExecutor(agent_execution.AgentExecutor):
  """An agent executor bridging the ADK Sales Data Error Handler Agent with the A2A platform."""

  _runner: runners.Runner

  def __init__(self):
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

    # Get or create the session
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

    # 1. SESSION RECOVERY: Extract state from client-side A2UI action context
    try:
        if hasattr(context, 'message') and context.message:
            for part in context.message.parts:
                if hasattr(part, 'root') and hasattr(part.root, 'data'):
                    data = part.root.data
                    if isinstance(data, dict) and 'userAction' in data:
                        action_ctx = data['userAction'].get('context', {})
                        query = action_ctx.get('message', query)
                        
                        # Save all context fields to session state
                        for k, v in action_ctx.items():
                            if k != 'message':
                                session.state[k] = v
                                
        # Deepcopy Workaround: Overwrite the session object directly in the underlying memory dictionary
        app_name = self._agent.name
        user_id = self._user_id
        if hasattr(self._runner.session_service, 'sessions'):
            if app_name in self._runner.session_service.sessions:
                if user_id in self._runner.session_service.sessions[app_name]:
                    self._runner.session_service.sessions[app_name][user_id][session.id] = session
                    logger.info("[DEBUG] Successfully persisted session state directly to the runner database.")
    except Exception as e:
        logger.warning("Session recovery failed: %s", e)

    # 2. STATE INJECTION: Append state variables to the query string to assist the LLM
    state_vars = [f"{k}={v}" for k, v in session.state.items() if k not in ['message']]
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
      logger.info("[DEBUG] Attempt: %s", attempt)

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
              logger.info("[DEBUG] Final response content: %s", final_response_content)
      except Exception as e:
        await updater.failed(
            message=utils.new_agent_text_message(f"Task failed with error: {str(e)}")
        )
        return

      if final_response_content is None:
        if attempt <= max_retries:
          current_query_text = "I received no response. Please try again."
          continue
        else:
          await updater.failed(message=utils.new_agent_text_message("No response generated."))
          return

      # Parse A2UI JSON payload
      is_valid = False
      error_message = ""
      json_string_cleaned = "[]"
      text_part = final_response_content

      if "---a2ui_JSON---" not in final_response_content:
        error_message = "Delimiter '---a2ui_JSON---' not found in final response."
      else:
        try:
          text_part, json_string = final_response_content.split("---a2ui_JSON---", 1)
          json_string_cleaned = (
              json_string.strip().lstrip("```json").rstrip("```").strip().replace('\\\n', '\n')
          )
          if not json_string_cleaned:
            json_string_cleaned = "[]"
          parsed_json = json.loads(json_string_cleaned)
          logger.info("[DEBUG] Parsed UI JSON: %s", parsed_json)
          is_valid = True
        except Exception as e:
          error_message = f"Failed to parse A2UI JSON: {str(e)}"

      if is_valid:
        parts = []
        if text_part.strip():
          parts.append(types.Part(root=types.TextPart(text=text_part.strip())))

        json_data = json.loads(json_string_cleaned)
        messages = []
        if isinstance(json_data, list):
          messages = json_data
        elif isinstance(json_data, dict) and "a2ui_messages" in json_data:
          messages = json_data["a2ui_messages"]
        else:
          messages = [json_data]

        for message in messages:
          # Dynamically rewrite "main" to a unique, turn-specific surface ID to prevent card overwriting
          unique_surface_id = f"surface_{task.id.replace('/', '_').replace('-', '_')}"
          if isinstance(message, dict):
            for inst in ["beginRendering", "surfaceUpdate", "dataModelUpdate"]:
              if inst in message and isinstance(message[inst], dict) and "surfaceId" in message[inst]:
                message[inst]["surfaceId"] = unique_surface_id

          ui_data_part = types.Part(
              root=types.DataPart(
                  data=message,
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
              f" generate a valid response containing the ---a2ui_JSON--- delimiter. Please retry: '{query}'"
          )
          logger.warning("[DEBUG] Retrying due to validation error: %s", error_message)
          continue
        else:
          await updater.add_artifact(
              [
                  types.Part(
                      root=types.TextPart(
                          text=f"I encountered an error generating the UI: {error_message}. Raw response: {final_response_content}"
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
