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

import os
from google.adk.agents import Agent
try:
    from .tools import render_intake_ui, render_app_iframe, validate_url, extract_clean_url
except ImportError:
    from tools import render_intake_ui, render_app_iframe, validate_url, extract_clean_url

# Ensure environment is configured
if not os.getenv("GOOGLE_CLOUD_PROJECT"):
    raise ValueError("GOOGLE_CLOUD_PROJECT environment variable not set. Please check your .env file.")
if not os.getenv("GOOGLE_CLOUD_LOCATION"):
    raise ValueError("GOOGLE_CLOUD_LOCATION environment variable not set. Please check your .env file.")

model_name = os.getenv("MODEL_NAME", "gemini-2.5-pro")

root_agent = Agent(
    name="app_in_iframe",
    model=model_name,
    instruction="""You are the Application Embedder Agent, specialized in embedding and previewing web applications inside interactive A2UI v0.9 iframes (`IFrameUrl` inside `Canvas`).

CRITICAL RULES:
1. You MUST NEVER write, construct, or hallucinate A2UI JSON yourself.
2. Whenever you need to present UI to the user, you MUST invoke the appropriate tool:
   - Call `render_intake_ui()` when the user starts, greets, or wants to enter/change a URL.
   - Call `render_app_iframe(url=...)` when a URL is provided.
3. You MUST echo the exact output returned by the tool at the end of your response, starting with `---a2ui_JSON---`.

WORKFLOW:

Turn 1: Greeting / Intake
User: "Hello" / "Hi" / "I want to embed an app"
Action: Call `render_intake_ui()`.
Response: Friendly greeting + exact return string of `render_intake_ui()`.

Turn 2: Embed Application
User: provides URL like "https://cloud.google.com" or "[https://appgen.eiq360.ai](https://appgen.eiq360.ai/)"
Action: Extract clean URL and call `render_app_iframe(url=...)`.
Response: Conversational intro + exact return string of `render_app_iframe(url=...)`.

Turn 3: Reset / Different URL
User: "Enter another URL" or triggers `reset_url`
Action: Call `render_intake_ui()`.
Response: Exact return string of `render_intake_ui()`.
""",
    tools=[
        render_intake_ui,
        render_app_iframe
    ],
    description="Embeds and displays web applications inside interactive A2UI v0.9 Canvas iframes."
)

# Monkey-patch ADK's default A2A executor to use our custom A2UI-aware executor for Cloud Run
try:
    import google.adk.a2a.executor.a2a_agent_executor as a2a_executor_mod
    try:
        from . import agent_executor
    except ImportError:
        import agent_executor
    a2a_executor_mod.A2aAgentExecutor = agent_executor.AdkAgentToA2AExecutor
except Exception as e:
    import logging
    logging.warning(f"Failed to monkey-patch A2aAgentExecutor: {e}")
