---
name: A2UI Remote Tester
description: Generates test code and renderer clients for remote testing of A2UI agents deployed on Agent Engine.
---

# A2UI Remote Tester Skill

This skill provides instructions and templates for generating test code to verify A2UI agents deployed on Vertex AI Agent Engine using the A2A protocol.

## Core Capabilities
1. **Agent Card Verification**: Verify the agent's capabilities and endpoints by fetching its card.
2. **Remote Communication**: Send requests to the remote agent endpoint.
3. **Task Polling**: Handle asynchronous task execution by polling for results.
4. **A2UI Parsing**: Extract and validate A2UI payloads from the response.
5. **Renderer Client Generation**: Create a mock client or script to visualize interactions.

## Workflow

### 1. Verify Agent Card
Before testing, fetch the agent card to verify it supports A2UI and get the correct endpoint URL.
- Endpoint: `https://<location>-aiplatform.googleapis.com/v1beta1/projects/<project>/locations/<location>/reasoningEngines/<id>/a2a/v1/card`

### 2. Generate Remote Test Script
Generate a Python script that sends messages to the agent and polls for results.
See the template in `remote_test.py` below.

### 3. Generate Renderer Client
Create an HTML client and a proxy server to visualize the A2UI components.
- **Proxy Server**: A FastAPI server that serves the HTML client and proxies JSON-RPC requests to the remote Agent Engine endpoint, handling authentication and task polling.
- **HTML Client**: A chat interface that renders A2UI components and handles user actions.

## Component Support
The generated HTML client includes specific renderers for the following A2UI components:
- `Text` (with usage hints for headings)
- `Card`
- `Column`
- `Row`
- `Button` (triggers actions)
- `MultipleChoice` (dropdowns)
- `DateTimeInput`
- `CheckBox`
- `Slider`
- `TextField`

For any other component or unsupported types, the client falls back gracefully by rendering a placeholder box with the component type and ID, allowing you to see that it was returned.

## Examples
Working examples of the proxy server and client are available in the skill's directory:
- `examples/proxy_server.py`: Handles polling and response mapping.
- `examples/index.html`: The interactive renderer client.

## Operational Lessons
- **Authentication**: Always use standard Google ADC to get the token.
- **URL Mapping**: Ensure the endpoint is `/a2a/v1/message:send` for sending messages and `/a2a/v1/tasks/{taskId}` for polling.
- **Payload Structure**: The `message` payload expects a `content` array with `parts` or `text` directly in the part object. For `userAction` in `DataPart`, wrap the action object inside a `data` field to match the `a2a.v1.DataPart` schema: `data: { data: { userAction: ... } }`.

#### Python Template (`remote_test.py`):
```python
import os
import requests
import json
import time
from google.auth import default
from google.auth.transport.requests import Request

def get_bearer_token():
    credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(Request())
    return credentials.token

def main():
    project_id = "your-project-id"
    location = "us-central1"
    engine_id = "your-engine-id"
    
    token = get_bearer_token()
    
    # Verify Agent Card
    card_url = f"https://{location}-aiplatform.googleapis.com/v1beta1/projects/{project_id}/locations/{location}/reasoningEngines/{engine_id}/a2a/v1/card"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    print("Fetching Agent Card...")
    res = requests.get(card_url, headers=headers)
    print(f"Status: {res.status_code}")
    print(res.json())
    
    # Send Message
    msg_url = f"https://{location}-aiplatform.googleapis.com/v1beta1/projects/{project_id}/locations/{location}/reasoningEngines/{engine_id}/a2a/v1/message:send"
    
    payload = {
        "message": {
            "content": [
                {
                    "text": "Find a doctor in Atlanta"
                }
            ]
        }
    }
    
    print("\nSending Message...")
    res = requests.post(msg_url, headers=headers, json=payload)
    print(f"Status: {res.status_code}")
    
    response_data = res.json()
    print(json.dumps(response_data, indent=2))
    
    task_id = response_data.get("task", {}).get("id")
    
    if task_id:
        print(f"\nPolling Task {task_id}...")
        task_url = f"https://{location}-aiplatform.googleapis.com/v1beta1/projects/{project_id}/locations/{location}/reasoningEngines/{engine_id}/a2a/v1/tasks/{task_id}"
        
        for _ in range(30): # 60 seconds timeout
            time.sleep(2)
            res = requests.get(task_url, headers=headers)
            print(f"Status: {res.status_code}")
            task_data = res.json()
            
            state = task_data.get("status", {}).get("state")
            if state == "TASK_STATE_SUCCEEDED" or state == "TASK_STATE_COMPLETED":
                print("Task Completed!")
                print(json.dumps(task_data, indent=2))
                break
            elif state == "TASK_STATE_FAILED":
                print("Task Failed!")
                print(json.dumps(task_data, indent=2))
                break
    else:
        print("No task ID returned.")

if __name__ == "__main__":
    main()
```
