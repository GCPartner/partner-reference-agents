"""Agent executor for ADK agents adapted for A2A compatibility with A2UI support."""

import logging
import json
from a2a import types
from a2a import utils
from a2a.server import agent_execution
from a2a.server import events
from a2a.server import tasks
from a2a.utils import errors as a2a_errors

import agent # Import your ADK agent
from google.adk import runners
from google.adk.artifacts import in_memory_artifact_service
from google.adk.memory import in_memory_memory_service
from google.adk.sessions import in_memory_session_service
from google.genai import types as genai_types

logger = logging.getLogger(__name__)

# Monkey-patch for Protobuf KeyError 'serialized' on Python 3.13
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

class AdkAgentToA2AExecutor(agent_execution.AgentExecutor):
  """An agent executor for ADK agents to make them A2A compatible."""

  _runner: runners.Runner

  def __init__(self):
    self._agent = agent.route_planner_agent # Use the specific agent
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

    # State Injection Pattern for Multi-Replica Continuity
    # Extract context from A2UI DataPart if present
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
                                if 'message' in action_context:
                                    query = action_context['message'] # Override query
                                    
                                # Save other context to session state
                                for k, v in action_context.items():
                                    if k != 'message':
                                        session.state[k] = v
    except Exception as e:
        logger.warning("Failed to extract action context: %s", e)

    # Inject session state into query to maintain context across replicas
    state_vars = [f"{k}={v}" for k, v in session.state.items()]
    if state_vars:
        query = f"{query} [State: {' '.join(state_vars)}]"
        logger.info("[DEBUG] Appended state to query: %s", query)

    await updater.start_work()

    content = genai_types.Content(
        role="user", parts=[{"text": query}]
    )

    final_response_content = ""

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
            final_response_content += event.content.parts[0].text

    except Exception as e:
      await updater.failed(
          message=utils.new_agent_text_message(
              f"Task failed with error: {str(e)}"
          )
      )
      return

    if not final_response_content:
        await updater.failed(
            message=utils.new_agent_text_message("No response generated.")
        )
        return

    # Extract A2UI JSON and deliver as separate DataParts (matching phone_plan_shopper)
    parts = []
    import re
    
    # Search for any JSON containing a2ui_messages
    json_match = re.search(r"(\{.*\"a2ui_messages\".*\})", final_response_content, re.DOTALL)
    
    if json_match:
        json_string = json_match.group(1)
        # Remove JSON string and delimiter from text response
        text_part = final_response_content.replace(json_string, "").strip()
        text_part = text_part.replace("---a2ui_JSON---", "").strip()
        
        if text_part:
            parts.append(types.Part(root=types.TextPart(text=text_part)))
            
        try:
            json_data = json.loads(json_string)
            messages = []
            if isinstance(json_data, dict) and "a2ui_messages" in json_data:
                messages = json_data["a2ui_messages"]
            else:
                messages = [json_data]
                
            for message in messages:
                parts.append(types.Part(root=types.DataPart(
                    data=message,
                    metadata={"mimeType": "application/json+a2ui"}
                )))
            logger.info(f"Successfully extracted and added {len(messages)} A2UI messages.")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse extracted JSON: {e}")
            parts.append(types.Part(root=types.TextPart(text=final_response_content)))
    else:
        # No JSON found, return as text
        parts.append(types.Part(root=types.TextPart(text=final_response_content)))

    await updater.add_artifact(parts, name="response")
    await updater.complete()

  async def cancel(
      self,
      context: agent_execution.RequestContext,
      event_queue: events.EventQueue,
  ) -> None:
    raise a2a_errors.ServerError(error=types.UnsupportedOperationError())
