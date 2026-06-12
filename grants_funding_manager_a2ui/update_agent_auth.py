import json
import os
import requests
from dotenv import load_dotenv
from google.auth import default
from google.auth.transport.requests import Request

def _get_bearer_token():
    try:
        credentials, _ = default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        request = Request()
        credentials.refresh(request)
        return credentials.token
    except Exception as e:
        print(f"Error getting credentials: {e}")
        return None

def main():
    load_dotenv()

    project_id = os.environ.get("PROJECT_ID", "agentspace-demo-1145-b")
    app_id = os.environ.get("GEMINI_ENTERPRISE_APP_ID", "neuravibeapp_1738849257936")
    
    # Target existing agent ID
    agent_id = "12946228157836919269"
    project_number = "121968733869" # Verified from previous outputs
    auth_id = "grants-manager-auth"

    api_endpoint = (
        f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/"
        f"locations/global/collections/default_collection/engines/{app_id}/"
        f"assistants/default_assistant/agents/{agent_id}"
    )

    # Use updateMask to target only the authorizationConfig field
    url_with_mask = f"{api_endpoint}?updateMask=authorizationConfig"

    bearer_token = _get_bearer_token()
    if not bearer_token:
        print("Failed to get bearer token.")
        return

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": project_id,
    }

    payload = {
        "authorizationConfig": {
            "agentAuthorization": f"projects/{project_number}/locations/global/authorizations/{auth_id}"
        }
    }

    print(f"Attaching authorizationConfig to agent {agent_id}...")
    print(f"Endpoint: {url_with_mask}")
    
    response = requests.patch(url_with_mask, headers=headers, json=payload)

    if response.status_code in [200, 201]:
         print("✓ Agent authorization configuration attached successfully!")
         print(json.dumps(response.json(), indent=2))
    else:
         print(f"✗ Update failed with status code: {response.status_code}")
         print(response.text)

if __name__ == "__main__":
    main()
