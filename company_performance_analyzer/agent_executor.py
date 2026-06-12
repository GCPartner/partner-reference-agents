"""Agent executor for ADK agents with A2UI validation for company_performance_analyzer."""

import sys
from typing import Any

# Protobuf unpickling patch
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

# Starlette request type alignment patch
try:
    import vertexai.preview.reasoning_engines.templates.a2a as a2a_module
    import starlette.requests
    import a2a.server.apps.rest.rest_adapter as adapter_module
    
    if "Request" not in a2a_module.__dict__:
        a2a_module.__dict__["Request"] = starlette.requests.Request
    if "ServerCallContext" not in a2a_module.__dict__:
        a2a_module.__dict__["ServerCallContext"] = adapter_module.ServerCallContext
except Exception:
    pass

import base64
import json
import logging
import os
from a2a import types
from a2a import utils
from a2a.server import agent_execution
from a2a.server import events
from a2a.server import tasks
from a2a.utils import errors as a2a_errors

try:
    import a2ui_schema
except ImportError:
    a2ui_schema = None

import agent
from google.adk import runners
from google.adk.artifacts import in_memory_artifact_service
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.memory.vertex_ai_memory_bank_service import VertexAiMemoryBankService
from google.genai import types as genai_types

logger = logging.getLogger(__name__)


def extract_json_block(s: str) -> str:
    s = s.strip()
    start_idx = s.find('{')
    if start_idx == -1:
        start_idx = s.find('[')
    
    if start_idx == -1:
        return s
        
    end_idx = s.rfind('}')
    if end_idx == -1:
        end_idx = s.rfind(']')
        
    if end_idx == -1:
        return s[start_idx:]
        
    return s[start_idx:end_idx+1]


import fsspec

def save_state_to_gcs(session_id: str, state: dict):
    bucket = "partner-engg-agents-adk-staging"
    gcs_path = f"gs://{bucket}/sessions/{session_id}.json"
    try:
        clean_state = {k: v for k, v in state.items() if k != "a2ui_json"}
        with fsspec.open(gcs_path, "w") as f:
            json.dump(clean_state, f)
        logger.info("[DEBUG] Persisted session state to %s: %s", gcs_path, clean_state)
    except Exception as e:
        logger.error("[DEBUG] Failed to persist session state to GCS: %s", e)

def load_state_from_gcs(session_id: str) -> dict:
    bucket = "partner-engg-agents-adk-staging"
    gcs_path = f"gs://{bucket}/sessions/{session_id}.json"
    try:
        with fsspec.open(gcs_path, "r") as f:
            state = json.load(f)
            logger.info("[DEBUG] Restored session state from GCS: %s", state)
            return state
    except Exception as e:
        logger.info("[DEBUG] No session state found in GCS for %s or error: %s", session_id, e)
        return {}


class AdkAgentToA2AExecutor(agent_execution.AgentExecutor):
  """An agent executor for the PerformanceAnalyzer agent."""

  _runner: runners.Runner

  def __init__(self):
    self.a2ui_schema_object = None
    if a2ui_schema and hasattr(a2ui_schema, 'A2UI_SCHEMA'):
        try:
          single_message_schema = json.loads(a2ui_schema.A2UI_SCHEMA)
          self.a2ui_schema_object = {
              "type": "array",
              "items": single_message_schema,
          }
          logger.info("[DEBUG] A2UI_SCHEMA successfully loaded from a2ui_schema.py.")
        except Exception as e:
          logger.error("[DEBUG] Failed to parse A2UI_SCHEMA from py: %s", e)

    project_id = getattr(sys.modules[__name__], 'PROJECT_ID', None) or os.environ.get("PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = getattr(sys.modules[__name__], 'LOCATION', None) or os.environ.get("LOCATION") or "us-central1"
    agent_engine_id = os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_ID") or os.environ.get("GOOGLE_CLOUD_REASONING_ENGINE_ID") or "test-agent-engine"

    self._agent = agent.root_agent
    self._runner = runners.Runner(
        app_name=self._agent.name,
        agent=self._agent,
        session_service=InMemorySessionService(),
        artifact_service=in_memory_artifact_service.InMemoryArtifactService(),
        memory_service=VertexAiMemoryBankService(
            project=project_id, location=location, agent_engine_id=agent_engine_id
        ),
    )
    self._user_id = "remote_agent"

  async def execute(
      self,
      context: agent_execution.RequestContext,
      event_queue: events.EventQueue,
  ) -> None:
    query = context.get_user_input()
    task = context.current_task
    logger.info("[DEBUG] Query received: %s", query)
    try:
        if context.message:
            logger.info("[DEBUG] Full Request Message: %s", context.message.model_dump_json(exclude_none=True))
    except Exception as e:
        logger.warning("[DEBUG] Failed to serialize request message: %s", e)


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
      gcs_state = load_state_from_gcs(session_id)
      session = await self._runner.session_service.create_session(
          app_name=self._agent.name,
          user_id=self._user_id,
          state=gcs_state,
          session_id=session_id,
      )
    else:
      gcs_state = load_state_from_gcs(session_id)
      if gcs_state:
          session.state.update(gcs_state)

    # 1. SESSION RECOVERY: Extract state from A2UI payload (Drill Down or Toggles)
    try:
        if hasattr(context, 'message') and context.message:
            for part in context.message.parts:
                if hasattr(part, 'root') and hasattr(part.root, 'data'):
                    data = part.root.data
                    while isinstance(data, dict) and 'data' in data:
                        data = data['data']
                    if isinstance(data, dict) and 'userAction' in data:
                        action_ctx = data['userAction'].get('context', {})
                        query = action_ctx.get('message', query)
                        # Save action parameters into session state
                        for k, v in action_ctx.items():
                            if k != 'message':
                                session.state[k] = v
    except Exception as e:
        logger.warning("Recovery failed: %s", e)

    # 1.1 FILE EXTRACTION: Extract uploaded files (FilePart)
    try:
        if hasattr(context, 'message') and context.message:
            for part in context.message.parts:
                if hasattr(part, 'root') and hasattr(part.root, 'file'):
                    file_obj = part.root.file
                    if hasattr(file_obj, 'uri') and file_obj.uri:
                        session.state["csv_file_path"] = file_obj.uri
                        logger.info("[DEBUG] Extracted CSV file path from GCS URI: %s", file_obj.uri)
                    elif hasattr(file_obj, 'bytes') and file_obj.bytes:
                        os.makedirs("./tmp", exist_ok=True)
                        local_path = os.path.abspath(os.path.join("./tmp", file_obj.name))
                        with open(local_path, "wb") as f:
                            f.write(base64.b64decode(file_obj.bytes))
                        session.state["csv_file_path"] = local_path
                        logger.info("[DEBUG] Extracted CSV file path from decoded bytes: %s", local_path)
    except Exception as e:
        logger.warning("File extraction failed: %s", e)

    # 2. STATE INJECTION: Append state to query for model context tracking
    state_vars = [f"{k}={v}" for k, v in session.state.items() if k != "a2ui_json"]
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
      logger.info("[DEBUG] Execution attempt: %s", attempt)

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
        try:
          s = await self._runner.session_service.get_session(
              app_name=self._agent.name, user_id=self._user_id, session_id=session_id
          )
          if s:
              save_state_to_gcs(session_id, s.state)
        except Exception:
          pass
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

      is_valid = False
      error_message = ""
      json_string_cleaned = "[]"
      text_part = final_response_content
      
      # Re-fetch session to retrieve any state properties saved by tool calls
      updated_session = await self._runner.session_service.get_session(
          app_name=self._agent.name,
          user_id=self._user_id,
          session_id=session_id,
      )
      cached_a2ui = None
      if updated_session:
          cached_a2ui = updated_session.state.pop("a2ui_json", None)

      if "---a2ui_JSON---" not in final_response_content:
        # Graceful text-only fallback (e.g. for greeting or clarifying turns)
        parts = [types.Part(root=types.TextPart(text=final_response_content.strip()))]
        if updated_session:
            save_state_to_gcs(session_id, updated_session.state)
        await updater.add_artifact(parts, name="response")
        await updater.complete()
        return
      else:
        try:
          text_part, json_string = final_response_content.split(
              "---a2ui_JSON---", 1
          )
          json_string_cleaned = extract_json_block(
              json_string.strip().lstrip("```json").rstrip("```").strip().replace('\\\n', '\n')
          )

          if not json_string_cleaned:
            json_string_cleaned = "[]"

          parsed_json = json.loads(json_string_cleaned)
          logger.info("[DEBUG] Parsed JSON from response text: %s", parsed_json)
          is_valid = True
        except Exception as e:
          error_message = f"Validation failed: {str(e)}"
          
      if not is_valid and cached_a2ui:
          logger.info("[DEBUG] Text parsing failed. Attempting fallback to session-cached a2ui_json...")
          try:
              parsed_json = json.loads(cached_a2ui)
              json_string_cleaned = cached_a2ui
              is_valid = True
              logger.info("[DEBUG] Fallback to cached JSON successful!")
          except Exception as fallback_err:
              logger.error("[DEBUG] Fallback parsing failed: %s", fallback_err)

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
          ui_data_part = types.Part(
              root=types.DataPart(
                  data=message,
                  metadata={"mimeType": "application/json+a2ui"},
              )
          )
          parts.append(ui_data_part)

        logger.info("[DEBUG] Stream parts constructed: %s", parts)
        if updated_session:
            save_state_to_gcs(session_id, updated_session.state)
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
          logger.warning("[DEBUG] Retrying due to validation error: %s", error_message)
          continue
        else:
          if updated_session:
              save_state_to_gcs(session_id, updated_session.state)
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
