import os
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import logging
import requests
import time
from google.auth import default
from google.auth.transport.requests import Request as AuthRequest

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

# Configure these for your deployed agent
PROJECT_ID = "agentspace-demo-1145-b"
LOCATION = "us-central1"
ENGINE_ID = "1229817499562803200"

def get_bearer_token():
    credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(AuthRequest())
    return credentials.token

@app.get("/.well-known/agent-card.json")
async def get_agent_card():
    token = get_bearer_token()
    url = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{ENGINE_ID}/a2a/v1/card"
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(url, headers=headers)
    return res.json()

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
        
        token = get_bearer_token()
        url = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{ENGINE_ID}/a2a/v1/message:send"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        payload = {"message": message}
        
        logger.info(f"Forwarding to remote agent: {url}")
        res = requests.post(url, headers=headers, json=payload)
        
        if res.status_code != 200:
            return {"jsonrpc": "2.0", "error": {"code": res.status_code, "message": res.text}, "id": request_id}
            
        remote_response = res.json()
        task_id = remote_response.get("task", {}).get("id")
        
        if task_id:
            logger.info(f"Polling Task {task_id}...")
            task_url = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{ENGINE_ID}/a2a/v1/tasks/{task_id}"
            
            for _ in range(30):
                time.sleep(2)
                task_res = requests.get(task_url, headers=headers)
                if task_res.status_code == 200:
                    task_data = task_res.json()
                    state = task_data.get("status", {}).get("state")
                    
                    if state == "TASK_STATE_SUCCEEDED" or state == "TASK_STATE_COMPLETED":
                        artifacts = task_data.get("artifacts", [])
                        parts = []
                        if artifacts:
                            parts = artifacts[0].get("parts", [])
                            # Clean nested data fields in A2UI parts if needed
                            for part in parts:
                                if "data" in part and part.get("metadata", {}).get("mimeType") == "application/json+a2ui":
                                    data_field = part["data"]
                                    if isinstance(data_field, dict) and "data" in data_field:
                                        part["data"] = data_field["data"]
                            
                        return {
                            "jsonrpc": "2.0",
                            "result": {
                                "message": {
                                    "parts": parts
                                }
                            },
                            "id": request_id
                        }
                    elif state == "TASK_STATE_FAILED":
                        return {"jsonrpc": "2.0", "error": {"code": 500, "message": "Task failed on remote agent"}, "id": request_id}
                
            return {"jsonrpc": "2.0", "error": {"code": 504, "message": "Task timeout on remote agent"}, "id": request_id}
        else:
            return {"jsonrpc": "2.0", "error": {"code": 500, "message": "No task ID returned from remote agent"}, "id": request_id}
        
    return {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": request_id}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
