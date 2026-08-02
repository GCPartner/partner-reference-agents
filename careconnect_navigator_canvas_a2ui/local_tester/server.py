import os
import sys
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
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

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

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
            "extensions": [{"uri": "https://a2ui.org/a2a-extension/a2ui/v0.9", "required": False}]
        },
        "name": "careconnect-navigator-a2ui",
        "url": "http://localhost:8000/jsonrpc",
        "version": "1.0.0"
    }

@app.get("/")
async def get_index():
    # index.html is in the same directory as server.py
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
        
        user_action = None
        for part in parts:
            if part.get("metadata", {}).get("mimeType") == "application/json+a2ui":
                data = part.get("data")
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except:
                        pass
                if isinstance(data, dict):
                    action_data = None
                    if 'action' in data:
                        action_data = data['action']
                    elif 'userAction' in data:
                        action_data = data['userAction']
                    if action_data:
                        user_action = action_data
                        break
        
        # Run agent
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
        
        if user_action:
            action_context = user_action.get('context', {})
            for key, value in action_context.items():
                state[key] = value
                if key == 'message':
                    query = value
            # Update session state (in-memory object is modified directly)
            session.state = state
            
        # Append state to query to maintain context across replicas
        state_str = " ".join([f"[State: {k}={v}]" for k, v in state.items() if k not in ['message']])
        if state_str:
            query = f"{query} {state_str}"
            logger.info(f"Injected state into query: {query}")
            
        content = genai_types.Content(role="user", parts=[{"text": query}])
        
        response_parts = []
        async for event in runner.run_async(
            user_id="local_user", session_id=session.id, new_message=content
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    response_parts = event.content.parts
                    
        if not response_parts:
            return {"jsonrpc": "2.0", "result": {"message": {"text": "No response from agent"}}, "id": request_id}
            
        parts = []
        for p in response_parts:
            # Handle text part (e.g. greeting or delimiter-based fallback)
            if p.text:
                text_part = p.text
                if "---a2ui_JSON---" in text_part:
                    text_part, json_string = text_part.split("---a2ui_JSON---", 1)
                    json_string_cleaned = json_string.strip().lstrip("```json").rstrip("```").strip()
                    try:
                        ui_data = json.loads(json_string_cleaned)
                        messages = []
                        if isinstance(ui_data, dict):
                            if "messages" in ui_data:
                                messages = ui_data["messages"]
                            elif "a2ui_messages" in ui_data:
                                messages = ui_data["a2ui_messages"]
                            else:
                                messages = [ui_data]
                        elif isinstance(ui_data, list):
                            messages = ui_data
                        else:
                            messages = [ui_data]
                        for msg in messages:
                            parts.append({"data": msg, "metadata": {"mimeType": "application/json+a2ui"}})
                    except Exception as e:
                        logger.error(f"Failed to parse UI JSON: {e}")
                if text_part.strip():
                    parts.append({"text": text_part.strip()})
            # Handle binary blob part (wrapped by callback)
            elif p.inline_data:
                blob_bytes = p.inline_data.data
                try:
                    blob_str = blob_bytes.decode("utf-8")
                except Exception as e:
                    logger.error(f"Failed to decode blob bytes: {e}")
                    continue
                if "<a2a_datapart_json>" in blob_str:
                    json_str = blob_str.replace("<a2a_datapart_json>", "").replace("</a2a_datapart_json>", "").strip()
                    try:
                        part_data = json.loads(json_str)
                        if isinstance(part_data, dict) and part_data.get("kind") == "data":
                            a2ui_msg = part_data.get("data")
                            parts.append({
                                "data": a2ui_msg,
                                "metadata": {"mimeType": "application/json+a2ui"}
                            })
                    except Exception as e:
                        logger.error(f"Failed to parse inline datapart json: {e}")
            
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
    uvicorn.run(app, host="0.0.0.0", port=8001)

