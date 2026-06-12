import os
import requests
import json
from google.auth import default
from google.auth.transport.requests import Request

def get_bearer_token():
    credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(Request())
    return credentials.token

def main():
    project_id = "anusheelp-test1"
    app_id = "gemini-enterprise-anusheel_1768518209986"
    
    token = get_bearer_token()
    
    # Read agent card from file
    try:
        with open("agent_card.json", "r") as f:
            agent_card = json.load(f)
    except FileNotFoundError:
        print("agent_card.json not found. Run fetch_card.py first.")
        return
        
    api_endpoint = (
        f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/"
        f"locations/global/collections/default_collection/engines/{app_id}/"
        "assistants/default_assistant/agents"
    )
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Using the authorization resource from the previous deployment history as fallback
    # projects/121968733869/locations/global/authorizations/careconnect-navigator-auth
    auth_resource = "projects/382717586960/locations/global/authorizations/careconnect-navigator-auth"
    
    payload = {
        "name": "careconnect_navigator_a2ui",
        "displayName": "CareConnect Navigator A2UI",
        "description": "Helpful assistant for finding doctors and booking appointments in Atlanta.",
        "a2aAgentDefinition": {"jsonAgentCard": json.dumps(agent_card)},
        "authorizationConfig": {
            "agentAuthorization": auth_resource
        }
    }
    
    print(f"Registering agent with Discovery Engine at {api_endpoint}...")
    res = requests.post(api_endpoint, headers=headers, json=payload)
    print(f"Status: {res.status_code}")
    print(json.dumps(res.json(), indent=2))

if __name__ == "__main__":
    main()
