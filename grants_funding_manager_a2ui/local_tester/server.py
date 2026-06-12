import os
import sys
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import logging
from dotenv import load_dotenv

# Add parent directory to path to import agent and tools
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Load environment variables from .env file in parent directory
load_dotenv(os.path.join(parent_dir, '.env'))

import agent
from google.adk import runners
from google.adk.sessions import in_memory_session_service
from google.adk.artifacts import in_memory_artifact_service
from google.adk.memory import in_memory_memory_service
from google.genai import types as genai_types

app = FastAPI()

# Enable CORS for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Initialize ADK Runner
adk_agent = agent.root_agent
runner = runners.Runner(
    app_name=adk_agent.name,
    agent=adk_agent,
    session_service=in_memory_session_service.InMemorySessionService(),
    artifact_service=in_memory_artifact_service.InMemoryArtifactService(),
    memory_service=in_memory_memory_service.InMemoryMemoryService(),
)

@app.get("/.well-known/agent-card.json")
async def get_agent_card():
    return {
        "capabilities": {
            "streaming": False,
            "extensions": [{"uri": "https://a2ui.org/a2a-extension/a2ui/v0.8", "required": False}]
        },
        "name": adk_agent.name,
        "url": "/jsonrpc",
        "version": "1.0.0"
    }

@app.get("/")
async def get_index():
    return FileResponse(os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html"))

@app.post("/jsonrpc")
async def handle_jsonrpc(request: Request):
    body = await request.json()
    logger.info(f"Received JSON-RPC request: {body}")
    
    if body.get("jsonrpc") != "2.0":
        return {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}, "id": body.get("id")}
        
    method = body.get("method")
    params = body.get("params", {})
    request_id = body.get("id")
    
    if method == "message/send":
        message = params.get("message", {})
        query = message.get("text", "")
        parts = message.get("parts", [])
        session_id = params.get("session_id", "local_session")
        
        # Extract userAction from DataPart
        user_action = None
        for part in parts:
            if part.get("metadata", {}).get("mimeType") == "application/json+a2ui":
                data = part.get("data")
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except:
                        pass
                if isinstance(data, dict) and 'userAction' in data:
                    user_action = data['userAction']
                    break
        
        # Get session
        session = await runner.session_service.get_session(
            app_name=adk_agent.name,
            user_id="local_user",
            session_id=session_id,
        )
        if not session:
            session = await runner.session_service.create_session(
                app_name=adk_agent.name,
                user_id="local_user",
                state={},
                session_id=session_id,
            )
            
        state = session.state if session.state else {}
        
        # Inject userAction context into session state
        if user_action:
            action_context = user_action.get('context', {})
            for key, value in action_context.items():
                state[key] = value
            session.state = state # Update in-memory object
            
        # Append state to query to maintain context
        state_str = " ".join([f"[State: {k}={v}]" for k, v in state.items() if k not in ['message']])
        if state_str:
            query = f"{query} {state_str}"
            logger.info(f"Injected state into query: {query}")
            
        content = genai_types.Content(role="user", parts=[{"text": query}])
        
        final_response_content = None
        async for event in runner.run_async(
            user_id="local_user", session_id=session.id, new_message=content
        ):
            logger.info(f"Received event: {event}")
            if event.is_final_response():
                if event.content and event.content.parts:
                    logger.info(f"Final response content parts: {event.content.parts}")
                    if event.content.parts[0].text:
                        final_response_content = "\n".join([p.text for p in event.content.parts if p.text])
                    
        logger.info(f"Final response content: {final_response_content}")
        
        if not final_response_content:
            return {"jsonrpc": "2.0", "result": {"message": {"parts": [{"text": "No response from agent"}]}}, "id": request_id}
            
        # Reload session to get state updates from tools
        session = await runner.session_service.get_session(
            app_name=adk_agent.name,
            user_id="local_user",
            session_id=session_id,
        )
        state = session.state if session.state else {}
        a2ui_json = state.get("a2ui_json")
        ui_data = []
        text_part = final_response_content
        
        if a2ui_json:
            try:
                ui_data = json.loads(a2ui_json)
                logger.info("Loaded A2UI JSON from state.")
                # Clear it so we don't send it again
                del state["a2ui_json"]
                session.state = state
            except Exception as e:
                logger.error(f"Failed to parse UI JSON from state: {e}")
        
        # Also check if there is JSON in text (fallback or additional)
        if "---a2ui_JSON---" in final_response_content:
            text_part, json_string = final_response_content.split("---a2ui_JSON---", 1)
            json_string_cleaned = json_string.strip().lstrip("```json").rstrip("```").strip()
            if not json_string_cleaned:
                json_string_cleaned = "[]"
                
            try:
                text_ui_data = json.loads(json_string_cleaned)
                if not ui_data:
                    ui_data = text_ui_data
                    logger.info("Loaded A2UI JSON from text.")
            except Exception as e:
                logger.error(f"Failed to parse UI JSON from text: {e}")
            
        parts = []
        if text_part.strip():
            parts.append({"text": text_part.strip()})
            
        # Wrap A2UI messages in DataPart
        if isinstance(ui_data, list):
            messages = ui_data
        elif isinstance(ui_data, dict) and "a2ui_messages" in ui_data:
            messages = ui_data["a2ui_messages"]
        else:
            messages = [ui_data] if ui_data else []
            
        for msg in messages:
            parts.append({
                "data": msg,
                "metadata": {"mimeType": "application/json+a2ui"}
            })
            
        return {
            "jsonrpc": "2.0",
            "result": {
                "message": {
                    "parts": parts
                }
            },
            "id": request_id
        }
        
    return {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": request_id}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
