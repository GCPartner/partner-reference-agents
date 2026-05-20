import os
import json
import requests
from google.auth import default
from google.auth.transport.requests import Request

def get_bearer_token():
    credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(Request())
    return credentials.token

def register():
    project_id = "<YOUR_PROJECT_ID>"
    location = "us-central1"
    engine_resource = "projects/<YOUR_PROJECT_NUMBER>/locations/us-central1/reasoningEngines/<YOUR_REASONING_ENGINE_ID>"
    app_id = "<YOUR_APP_ID>"
    agent_id = "route_planner_agent"
    
    token = get_bearer_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": project_id
    }
    
    # 1. Fetch Agent Card
    card_url = f"https://{location}-aiplatform.googleapis.com/v1beta1/{engine_resource}/a2a/v1/card"
    print(f"Fetching card from: {card_url}")
    response = requests.get(card_url, headers={"Authorization": f"Bearer {token}"})
    
    if response.status_code != 200:
        print(f"ERROR fetching card: {response.status_code} - {response.text}")
        return
        
    a2ui_agent_card = response.json()
    print("Successfully fetched agent card.")
    
    # Delete existing agent if it exists
    delete_url = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/collections/default_collection/engines/{app_id}/assistants/default_assistant/agents/{agent_id}"
    print(f"Deleting existing agent at: {delete_url}")
    response = requests.delete(delete_url, headers=headers)
    print(f"Delete response: {response.status_code}")

    # 2. Register via Discovery Engine
    register_url = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/collections/default_collection/engines/{app_id}/assistants/default_assistant/agents?agentId={agent_id}"
    
    payload = {
        "name": f"projects/{project_id}/locations/global/collections/default_collection/engines/{app_id}/assistants/default_assistant/agents/{agent_id}",
        "displayName": "Route Planner Agent",
        "description": "Helps field service reps plan their routes efficiently using A2UI.",
        "a2aAgentDefinition": {"jsonAgentCard": json.dumps(a2ui_agent_card)},
    }
    
    print(f"Registering agent at: {register_url}")
    response = requests.post(register_url, headers=headers, json=payload)
    
    if response.status_code in [200, 201]:
        print(f"✓ Agent registered successfully: {response.json().get('name')}")
    else:
        print(f"ERROR registering agent: {response.status_code} - {response.text}")

if __name__ == "__main__":
    register()
