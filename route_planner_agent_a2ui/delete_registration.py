import os
import json
import requests
from google.auth import default
from google.auth.transport.requests import Request

def get_bearer_token():
    credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(Request())
    return credentials.token

def delete():
    project_id = "agentspace-demo-1145-b"
    app_id = "neuravibeapp_1738849257936"
    agent_id = "route_planner_agent"
    
    token = get_bearer_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Goog-User-Project": project_id
    }
    
    delete_url = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/collections/default_collection/engines/{app_id}/assistants/default_assistant/agents/{agent_id}"
    print(f"Deleting agent at: {delete_url}")
    response = requests.delete(delete_url, headers=headers)
    print(f"Delete response: {response.status_code} - {response.text}")

if __name__ == "__main__":
    delete()
