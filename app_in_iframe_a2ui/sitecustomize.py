"""sitecustomize module to automatically patch ADK's A2aAgentExecutor on startup."""

import logging
import sys

logger = logging.getLogger(__name__)

try:
    import google.adk.a2a.executor.a2a_agent_executor as a2a_executor_mod
    try:
        from . import agent_executor
    except (ImportError, ValueError):
        import agent_executor

    a2a_executor_mod.A2aAgentExecutor.execute = agent_executor.a2ui_execute
    print("[A2UI-STARTUP] Successfully patched A2aAgentExecutor.execute on startup in sitecustomize.py", file=sys.stderr)
except Exception as e:
    print(f"[A2UI-STARTUP] Failed to patch A2aAgentExecutor in sitecustomize.py: {e}", file=sys.stderr)
