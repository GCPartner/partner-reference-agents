import asyncio
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

# Set env vars if not set
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", os.getenv("GOOGLE_CLOUD_PROJECT", ""))
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"))
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")

from agent import root_agent
from google.adk import runners
from google.adk.sessions import in_memory_session_service
from google.genai import types

logging.basicConfig(level=logging.INFO)

async def test_flow():
    print("\n--- Initializing Runner for app_in_iframe ---")
    session_service = in_memory_session_service.InMemorySessionService()
    runner = runners.Runner(
        app_name=root_agent.name,
        agent=root_agent,
        session_service=session_service,
        auto_create_session=True,
    )
    
    session_id = "test-session-v08-001"
    user_id = "test-user"
    
    print("\n[Turn 1: User says Hello (Intake Form Card)]")
    turn1_msg = types.Content(role="user", parts=[{"text": "Hello, I want to embed an application."}])
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=turn1_msg):
        if event.is_final_response() and event.content:
            for p in event.content.parts:
                print(f"Agent Response:\n{p.text}")
                assert "---a2ui_JSON---" in p.text, "A2UI delimiter missing in Turn 1"
                assert "createSurface" in p.text, "createSurface missing in Turn 1"
                assert "Canvas" in p.text, "Canvas root missing in Turn 1"
                assert "app_embedder" in p.text, "Surface ID app_embedder missing in Turn 1"
                print(">>> Turn 1 Verified: Successfully rendered A2UI v0.9 Intake Form Card!")

    print("\n[Turn 2: User provides markdown formatted URL from Gemini Enterprise]")
    turn2_msg = types.Content(role="user", parts=[{"text": "[https://appgen.eiq360.ai](https://appgen.eiq360.ai/)"}])
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=turn2_msg):
        if event.is_final_response() and event.content:
            for p in event.content.parts:
                print(f"Agent Response:\n{p.text}")
                assert "---a2ui_JSON---" in p.text, "A2UI delimiter missing in Turn 2"
                assert "createSurface" in p.text, "createSurface missing in Turn 2"
                assert "IFrameUrl" in p.text, "IFrameUrl missing in Turn 2"
                assert "Canvas" in p.text, "Canvas missing in Turn 2"
                assert "https://appgen.eiq360.ai" in p.text, "Target URL missing in Turn 2"
                print(">>> Turn 2 Verified: Successfully extracted clean URL and rendered IFrameUrl in Canvas!")

if __name__ == "__main__":
    asyncio.run(test_flow())
