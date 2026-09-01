"""Agent executor for ADK agents with A2UI v0.8 validation for app_in_iframe."""

import asyncio
import inspect
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

from a2a import types
from a2a import utils
from a2a.server import agent_execution
from a2a.server import events
from a2a.server import tasks
from a2a.utils import errors as a2a_errors

# Apply Protobuf & Pydantic compatibility patches
try:
    from google.protobuf.message import Message
    _orig_setstate = Message.__setstate__

    def _patched_setstate(self, state):
        if isinstance(state, dict) and "serialized" not in state:
            state["serialized"] = b""
        return _orig_setstate(self, state)

    Message.__setstate__ = _patched_setstate
except Exception:
    pass

from google.adk import runners
from google.adk.artifacts import in_memory_artifact_service
from google.adk.memory import in_memory_memory_service
from google.adk.sessions import in_memory_session_service
from google.genai import types as genai_types

try:
    from . import tools
except (ImportError, ValueError):
    import tools

logger = logging.getLogger("app_in_iframe_executor")


async def a2ui_execute(
    self,
    context: agent_execution.RequestContext,
    event_queue: events.EventQueue,
) -> None:
    """Universal execute method translating ADK output to A2UI v0.8 DataParts."""
    runner: runners.Runner
    if hasattr(self, "_resolve_runner") and callable(self._resolve_runner):
        runner = await self._resolve_runner()
    elif hasattr(self, "_runner"):
        if callable(self._runner):
            res = self._runner()
            if inspect.iscoroutine(res):
                runner = await res
            else:
                runner = res
        else:
            runner = self._runner
    else:
        try:
            from . import agent as agent_mod
        except (ImportError, ValueError):
            import agent as agent_mod
        root_agent = agent_mod.root_agent
        runner = runners.Runner(
            app_name=root_agent.name,
            agent=root_agent,
            session_service=in_memory_session_service.InMemorySessionService(),
            artifact_service=in_memory_artifact_service.InMemoryArtifactService(),
            memory_service=in_memory_memory_service.InMemoryMemoryService(),
        )

    app_name = getattr(runner, "app_name", "app_in_iframe_a2ui")
    user_id = getattr(self, "_user_id", "remote_agent")

    query = context.get_user_input()
    task = context.current_task
    logger.info("[A2UI-DEBUG] Raw User Query: %s", query)

    if not task:
        if not context.message:
            return
        task = utils.new_task(context.message)
        await event_queue.enqueue_event(task)

    task_id = context.task_id or (task.id if task else "default_task")
    context_id = context.context_id or (task.context_id if task else "default_ctx")
    session_id = context_id or "default_session"

    updater = tasks.TaskUpdater(event_queue, task_id, context_id)

    session = await runner.session_service.get_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )
    if session is None:
        session = await runner.session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            state={},
            session_id=session_id,
        )

    def find_action_context(obj: Any) -> Optional[dict]:
        """Recursively searches an arbitrary object/dict for an action context dictionary."""
        if not isinstance(obj, dict):
            return None
        if "context" in obj and isinstance(obj["context"], dict):
            return obj["context"]
        if "context" in obj and isinstance(obj["context"], list):
            # Convert context list of {key, value} to dict
            ctx_dict = {}
            for item in obj["context"]:
                if isinstance(item, dict) and "key" in item:
                    val = item.get("value")
                    if isinstance(val, dict):
                        val = val.get("literalString") or val.get("path") or list(val.values())[0] if val else ""
                    ctx_dict[item["key"]] = val
            return ctx_dict
        if "message" in obj and isinstance(obj["message"], str):
            return {"message": obj["message"]}
        for k in ("userAction", "action", "event", "data", "params", "payload"):
            if k in obj and isinstance(obj[k], dict):
                found = find_action_context(obj[k])
                if found:
                    return found
        return None

    # 1. Extract action context from DataPart if present
    try:
        if hasattr(context, "message") and context.message:
            for part in context.message.parts:
                part_root = getattr(part, "root", part)
                if hasattr(part_root, "text") and part_root.text:
                    query = part_root.text
                    logger.info("[A2UI-DEBUG] Found TextPart query: %s", query)
                elif hasattr(part_root, "data"):
                    data = part_root.data
                    logger.info("[A2UI-DEBUG] Inspecting DataPart: %s", data)
                    action_ctx = find_action_context(data)
                    if action_ctx:
                        logger.info("[A2UI-DEBUG] Extracted action context: %s", action_ctx)
                        app_url_val = action_ctx.get("app_url") or action_ctx.get("url")
                        if app_url_val and isinstance(app_url_val, str) and app_url_val.strip():
                            clean_app_url = tools.extract_clean_url(app_url_val)
                            session.state["app_url"] = clean_app_url
                            query = f"Embed URL: {clean_app_url}"
                        elif "message" in action_ctx and action_ctx["message"]:
                            query = str(action_ctx["message"]).strip()
                            logger.info("[A2UI-DEBUG] Overriding query with action message: %s", query)

                        for k, v in action_ctx.items():
                            if k != "message":
                                session.state[k] = v
    except Exception as e:
        logger.warning("[A2UI-DEBUG] Context extraction failed: %s", e)

    if not query or not str(query).strip():
        query = "Hello"

    await updater.start_work()

    clean_q = re.sub(r"\[State:.*?\]", "", str(query)).strip()
    clean_q_lower = clean_q.lower()
    final_response_content = None

    # Deterministic Fast-Path for Greetings & Reset Actions
    if clean_q_lower in (
        "hi", "hello", "hey", "start", "help", "embed an application",
        "enter another url", "change url", "reset", "reset url",
        "load different url", "load a different application url"
    ):
        logger.info("[A2UI-DEBUG] Executing deterministic intake form fast-path for: %s", clean_q)
        final_response_content = tools.render_intake_ui()

    # If URL is detected in user query (handles plain URLs, markdown links, bracketed links)
    if not final_response_content:
        extracted_url = tools.extract_clean_url(clean_q)
        if extracted_url and tools.validate_url(extracted_url):
            logger.info("[A2UI-DEBUG] Executing direct iframe render for detected URL: %s", extracted_url)
            final_response_content = tools.render_app_iframe(url=extracted_url)

    if not final_response_content:
        state_vars = [f"{k}={v}" for k, v in session.state.items()]
        if state_vars:
            query = f"{query} [State: {', '.join(state_vars)}]"
            logger.info("[A2UI-DEBUG] Appended state to query: %s", query)

        content = genai_types.Content(
            role="user", parts=[{"text": str(query)}]
        )

        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                async for event in runner.run_async(
                    user_id=user_id, session_id=session.id, new_message=content
                ):
                    for resp in event.get_function_responses():
                        val = None
                        if resp.response is not None and isinstance(resp.response, dict):
                            if "result" in resp.response:
                                val = resp.response["result"]
                            elif "response" in resp.response:
                                val = resp.response["response"]
                            elif len(resp.response) == 1:
                                val = list(resp.response.values())[0]
                        elif isinstance(resp.response, str):
                            val = resp.response

                        if isinstance(val, str) and "---a2ui_JSON---" in val:
                            logger.info("[A2UI-DEBUG] Intercepted A2UI tool output: %s", val)
                            final_response_content = val

                    if event.is_final_response():
                        if (
                            not final_response_content
                            and getattr(event, "content", None)
                            and getattr(event.content, "parts", None)
                        ):
                            text_parts = [p.text for p in event.content.parts if getattr(p, "text", None)]
                            if text_parts:
                                final_response_content = "\n".join(text_parts)

                break

            except Exception as e:
                err_str = str(e)
                if ("429" in err_str or "RESOURCE_EXHAUSTED" in err_str) and attempt < max_retries:
                    logger.warning(f"[A2UI-DEBUG] 429 Rate Limit on attempt {attempt+1}, retrying in {attempt+1}s...")
                    await asyncio.sleep(1.5 * (attempt + 1))
                    continue
                else:
                    logger.error("[A2UI-DEBUG] Error running agent: %s", e)
                    await updater.failed(
                        message=utils.new_agent_text_message(
                            f"Task failed with error: {str(e)}"
                        )
                    )
                    return

    if not final_response_content:
        final_response_content = tools.render_intake_ui()

    # 3. OUTPUT PARSING: Regex-based extraction matching field_route_planner_a2ui
    text_part = ""
    json_obj = None

    if "---a2ui_JSON---" in final_response_content:
        del_parts = final_response_content.split("---a2ui_JSON---")
        text_part = del_parts[0].strip()
        for chunk in reversed(del_parts[1:]):
            cleaned = chunk.strip().lstrip("```json").rstrip("```").strip().replace("\\\n", "\n")
            try:
                json_obj = json.loads(cleaned)
                break
            except Exception:
                m = re.search(r"(\{.*\})", cleaned, re.DOTALL)
                if m:
                    try:
                        json_obj = json.loads(m.group(1))
                        break
                    except Exception:
                        pass
    else:
        text_part = final_response_content.strip()

    # Clean text_part: Never leak delimiters or raw JSON to user chat
    text_part = re.sub(r"---a2ui_JSON---.*", "", text_part, flags=re.DOTALL).strip()

    parts = []
    if text_part:
        parts.append(types.Part(root=types.TextPart(text=text_part)))

    if json_obj:
        messages = []
        if isinstance(json_obj, list):
            messages = json_obj
        elif isinstance(json_obj, dict):
            if "a2ui_messages" in json_obj:
                messages = json_obj["a2ui_messages"]
            elif "messages" in json_obj:
                messages = json_obj["messages"]
            else:
                messages = [json_obj]
        else:
            messages = [json_obj]

        for message in messages:
            ui_data_part = types.Part(
                root=types.DataPart(
                    data=message,
                    metadata={"mimeType": "application/json+a2ui"},
                )
            )
            parts.append(ui_data_part)

    await updater.add_artifact(parts, name="response")
    await updater.complete()


class AdkAgentToA2AExecutor(agent_execution.AgentExecutor):
    """An agent executor translating ADK output to A2UI v0.8 DataParts."""

    def __init__(self, *args, **kwargs):
        self._runner = kwargs.get("runner")
        self._user_id = "remote_agent"

    async def execute(
        self,
        context: agent_execution.RequestContext,
        event_queue: events.EventQueue,
    ) -> None:
        await a2ui_execute(self, context, event_queue)

    async def cancel(
        self,
        context: agent_execution.RequestContext,
        event_queue: events.EventQueue,
    ) -> None:
        pass
