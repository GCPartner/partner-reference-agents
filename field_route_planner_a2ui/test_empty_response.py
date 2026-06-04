import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv("field_route_planner_a2ui/.env")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from field_route_planner_a2ui.agent import root_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

async def main():
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name="field_route_planner_a2ui", user_id="test_user", session_id="test_session"
    )
    # Inject state
    session = await session_service.get_session(
        app_name="field_route_planner_a2ui", user_id="test_user", session_id="test_session"
    )
    session.state["start_time"] = "07:58"
    session.state["end_location"] = ""
    session.state["start_location"] = "1380 Woodvine Way ALpharetta GA 30005"
    
    runner = Runner(
        agent=root_agent, app_name="field_route_planner_a2ui", session_service=session_service
    )
    
    query = "Plan my route [State: start_time=07:58] [State: end_location=] [State: start_location=1380 Woodvine Way ALpharetta GA 30005]"
    print(f"Sending query: {query}")
    
    async for event in runner.run_async(
        user_id="test_user",
        session_id="test_session",
        new_message=genai_types.Content(
            role="user",
            parts=[genai_types.Part.from_text(text=query)]
        ),
    ):
        if event.is_final_response():
            print(f"Final response content: {event.content}")
        elif event.content and event.content.parts:
            for part in event.content.parts:
                print(f"Part text chunk: '{part.text}'")

if __name__ == "__main__":
    asyncio.run(main())
