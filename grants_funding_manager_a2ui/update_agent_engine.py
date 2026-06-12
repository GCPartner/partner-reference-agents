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
    location = os.environ.get("LOCATION", "us-central1")
    app_id = os.environ.get("GEMINI_ENTERPRISE_APP_ID", "neuravibeapp_1738849257936")
    
    # Target existing agent ID
    agent_id = "12946228157836919269"
    
    # New Engine ID
    engine_id = "1229817499562803200"

    reasoning_engine_name = f"projects/{project_id}/locations/{location}/reasoningEngines/{engine_id}"
    a2a_card_endpoint = f"https://{location}-aiplatform.googleapis.com/v1beta1/{reasoning_engine_name}/a2a/v1/card"
    
    bearer_token = _get_bearer_token()
    if not bearer_token:
        print("Failed to get bearer token.")
        return

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
    }

    print(f"Fetching card from: {a2a_card_endpoint}")
    response = requests.get(a2a_card_endpoint, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch card: {response.status_code}")
        print(response.text)
        return

    agent_card_json = response.json()
    print("✓ Card fetched successfully.")

    # 1. Modify the URL to point to the correct base endpoint
    base_url = f"https://{location}-aiplatform.googleapis.com/v1beta1/{reasoning_engine_name}/a2a"
    agent_card_json["url"] = base_url
    print(f"✓ Overrode URL to: {base_url}")

    # 2. Add A2UI capabilities
    agent_card_json["capabilities"] = {
        "streaming": False,
        "extensions": [{
            "uri": "https://a2ui.org/a2a-extension/a2ui/v0.8",
            "description": "Ability to render A2UI",
            "required": False,
            "params": {
                "supportedCatalogIds": [
                    "https://a2ui.org/specification/v0_8/standard_catalog_definition.json"
                ]
            },
        }],
    }
    print("✓ Added A2UI capabilities.")

    agent_card_str = json.dumps(agent_card_json)

    # 3. PATCH existing agent in Gemini Enterprise
    api_endpoint = (
        f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/"
        f"locations/global/collections/default_collection/engines/{app_id}/"
        f"assistants/default_assistant/agents/{agent_id}"
    )

    url_with_mask = f"{api_endpoint}?updateMask=a2aAgentDefinition"

    payload = {
        "a2aAgentDefinition": {"jsonAgentCard": agent_card_str}
    }

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": project_id,
    }

    print(f"Updating engine for agent {agent_id}...")
    print(f"Endpoint: {url_with_mask}")
    
    response = requests.patch(url_with_mask, headers=headers, json=payload)

    if response.status_code in [200, 201]:
         print("✓ Agent engine configuration updated successfully!")
         print(json.dumps(response.json(), indent=2))
    else:
         print(f"✗ Update failed with status code: {response.status_code}")
         print(response.text)

if __name__ == "__main__":
    main()
