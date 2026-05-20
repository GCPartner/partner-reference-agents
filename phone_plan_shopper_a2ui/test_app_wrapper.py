import asyncio
from app import agent as app
import json

async def test():
    print("Testing custom A2A AdkAppWrapper...")
    try:
        query_text = "I need a phone plan for 2 lines with unlimited data. I have an iPhone 13."
        events = app.async_stream_query(
            message=query_text,
            user_id="test_user"
        )
        
        async for event in events:
            print("EVENT:", json.dumps(event, indent=2))
    except Exception as e:
        print(f"Error during test: {e}")

if __name__ == "__main__":
    asyncio.run(test())
