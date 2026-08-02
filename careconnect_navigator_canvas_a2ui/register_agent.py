import os
import requests
import json
from google.auth import default
from google.auth.transport.requests import Request

from dotenv import load_dotenv

load_dotenv()

import subprocess

def get_bearer_token():
    credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(Request())
    return credentials.token

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    app_id = os.environ.get("GEMINI_ENTERPRISE_APP_ID")
    
    # Fetch project number dynamically
    project_number = subprocess.check_output(
        ["gcloud", "projects", "describe", project_id, "--format=value(projectNumber)"],
        text=True
    ).strip()
    
    token = get_bearer_token()
    
    # Read agent card from file
    agent_card_path = os.path.join(current_dir, "agent_card.json")
    try:
        with open(agent_card_path, "r") as f:
            agent_card = json.load(f)
    except FileNotFoundError:
        print(f"agent_card.json not found at {agent_card_path}. Run fetch_card.py first.")
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
    
    # Construct authorization resource dynamically using existing careconnect-navigator-canvas-auth-v2
    auth_resource = f"projects/{project_number}/locations/global/authorizations/careconnect-navigator-canvas-auth-v2"
    
    payload = {
        "name": "careconnect_navigator_canvas_a2ui",
        "displayName": "CareConnect Navigator Canvas A2UI",
        "description": "Helpful assistant for finding doctors and booking appointments in Atlanta using canvas-based A2UI.",
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
