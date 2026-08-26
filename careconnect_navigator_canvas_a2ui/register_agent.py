import os
import requests
import json
from google.auth import default
from google.auth.transport.requests import Request
from dotenv import load_dotenv
import subprocess

load_dotenv()

def get_bearer_token():
    credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(Request())
    return credentials.token

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("PROJECT_ID") or "agentspace-demo-1145-b"
    app_id = os.environ.get("GEMINI_ENTERPRISE_APP_ID") or "neuravibeapp_1738849257936"
    project_number = os.environ.get("PROJECT_NUMBER")
    auth_profile_id = os.environ.get("AUTH_PROFILE_ID") or "careconnect-navigator-canvas-auth-v2"
    
    if not project_number:
        try:
            project_number = subprocess.check_output(
                ["gcloud", "projects", "describe", project_id, "--format=value(projectNumber)"],
                text=True
            ).strip()
        except Exception:
            project_number = "121968733869"
            
    print(f"Registering CareConnect Navigator for Project: {project_id} (Number: {project_number}), App ID: {app_id}")
    
    # Read agent card from file
    agent_card_path = os.path.join(current_dir, "agent_card.json")
    try:
        with open(agent_card_path, "r") as f:
            agent_card = json.load(f)
    except FileNotFoundError:
        print(f"agent_card.json not found at {agent_card_path}. Run generate_registration_payload.py or fetch_card.py first.")
        return
        
    api_endpoint = (
        f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/"
        f"locations/global/collections/default_collection/engines/{app_id}/"
        "assistants/default_assistant/agents"
    )
    
    auth_resource = f"projects/{project_number}/locations/global/authorizations/{auth_profile_id}"
    agent_name = "careconnect_navigator_canvas_a2ui"
    
    # Load registration payload if exists, or construct it
    reg_payload_path = os.path.join(current_dir, "registration_payload.json")
    if os.path.exists(reg_payload_path):
        try:
            with open(reg_payload_path, "r") as f:
                payload = json.load(f)
        except Exception:
            payload = None
    else:
        payload = None

    if not payload:
        payload = {
            "name": agent_name,
            "displayName": "CareConnect Navigator Canvas A2UI",
            "description": "Helpful assistant for finding doctors and booking appointments in Atlanta using canvas-based A2UI v0.9.",
            "a2aAgentDefinition": {"jsonAgentCard": json.dumps(agent_card)},
            "authorizationConfig": {
                "agentAuthorization": auth_resource
            },
            "sharingConfig": {
                "scope": "ALL_USERS"
            }
        }
    
    token = get_bearer_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": project_id
    }

    # First check if an agent with this display name or authorization profile already exists
    print("Checking for existing agent registration in Gemini Enterprise...")
    existing_agent_res_name = None
    page_token = None
    while True:
        list_url = api_endpoint + (f"?pageToken={page_token}" if page_token else "")
        list_res = requests.get(list_url, headers=headers)
        if list_res.status_code == 200:
            agents_data = list_res.json()
            for a in agents_data.get("agents", []):
                a_disp = a.get("displayName", "")
                a_name = a.get("name", "")
                a_auth = a.get("authorizationConfig", {}).get("agentAuthorization", "")
                if a_disp == payload.get("displayName") or a_auth == auth_resource or agent_name in a_name:
                    existing_agent_res_name = a_name
                    break
            page_token = agents_data.get("nextPageToken")
            if existing_agent_res_name or not page_token:
                break
        else:
            print(f"Warning: Failed to list agents ({list_res.status_code}): {list_res.text}")
            break

    if existing_agent_res_name:
        print(f"ℹ Existing agent found: {existing_agent_res_name}")
        print("Updating existing agent via PATCH...")
        payload["name"] = existing_agent_res_name
        patch_url = f"https://discoveryengine.googleapis.com/v1alpha/{existing_agent_res_name}"
        patch_res = requests.patch(patch_url, headers=headers, json=payload)
        if patch_res.status_code in [200, 201]:
            print("✓ Agent updated successfully in Gemini Enterprise!")
            print(json.dumps(patch_res.json(), indent=2))
        else:
            print(f"Update Status: {patch_res.status_code}")
            try:
                print(json.dumps(patch_res.json(), indent=2))
            except Exception:
                print(patch_res.text)
    else:
        print(f"Submitting new registration request to Discovery Engine: {api_endpoint}...")
        res = requests.post(api_endpoint, headers=headers, json=payload)
        
        if res.status_code in [200, 201]:
            print("✓ Agent registered successfully with Gemini Enterprise!")
            print(json.dumps(res.json(), indent=2))
        else:
            print(f"Status: {res.status_code}")
            try:
                print(json.dumps(res.json(), indent=2))
            except Exception:
                print(res.text)

if __name__ == "__main__":
    main()
