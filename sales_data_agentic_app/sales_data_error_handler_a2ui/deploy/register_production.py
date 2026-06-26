import os
import sys
import json
import requests
from google.auth import default
from google.auth.transport.requests import Request

def get_bearer_token():
    """Gets a bearer token for authenticating with Google Cloud APIs."""
    credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(Request())
    return credentials.token

def main():
    project_id = "agentspace-demo-1145-b"
    project_number = "121968733869"
    app_id = "neuravibeapp_1738849257936"
    engine_id = "4951556607445041152"
    auth_id = "sales-data-error-handler-auth"

    # Get OAuth credentials from environment or prompt
    client_id = os.environ.get("OAUTH_CLIENT_ID")
    client_secret = os.environ.get("OAUTH_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("Error: OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET environment variables must be set.")
        print("Please run the script as: OAUTH_CLIENT_ID='...' OAUTH_CLIENT_SECRET='...' python3 register_production.py")
        return

    token = get_bearer_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": project_id
    }

    # 1. Construct the authorizationUri
    encoded_redirect = "https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fstatic%2Foauth%2Foauth.html"
    auth_uri = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={encoded_redirect}&"
        f"scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcloud-platform&"
        f"include_granted_scopes=true&"
        f"response_type=code&"
        f"access_type=offline&"
        f"prompt=consent"
    )

    # 2. Create the Authorization Resource in Gemini Enterprise using project_number
    auth_endpoint = f"https://global-discoveryengine.googleapis.com/v1alpha/projects/{project_number}/locations/global/authorizations?authorizationId={auth_id}"
    auth_payload = {
        "name": f"projects/{project_number}/locations/global/authorizations/{auth_id}",
        "serverSideOauth2": {
            "clientId": client_id,
            "clientSecret": client_secret,
            "authorizationUri": auth_uri,
            "tokenUri": "https://oauth2.googleapis.com/token"
        }
    }

    print(f"Creating global Authorization Resource '{auth_id}'...")
    res = requests.post(auth_endpoint, headers=headers, json=auth_payload)
    if res.status_code in [200, 201]:
        print("✔ Authorization Resource created successfully.")
    elif res.status_code == 409:
        print("ℹ Authorization Resource already exists. Proceeding...")
    else:
        print(f"❌ Failed to create Authorization Resource: {res.status_code}")
        print(res.text)
        return

    # 3. Fetch the Agent Card from the running Reasoning Engine
    location = "us-central1"
    reasoning_engine_name = f"projects/{project_id}/locations/{location}/reasoningEngines/{engine_id}"
    card_endpoint = f"https://{location}-aiplatform.googleapis.com/v1beta1/{reasoning_engine_name}/a2a/v1/card"
    
    print(f"Fetching card from Reasoning Engine endpoint: {card_endpoint}...")
    card_res = requests.get(card_endpoint, headers={"Authorization": f"Bearer {token}"})
    if card_res.status_code != 200:
        print(f"❌ Failed to fetch card from Reasoning Engine: {card_res.status_code}")
        print(card_res.text)
        return

    agent_card = card_res.json()
    
    # 4. Resolve the URL placeholder in the card with our real Reasoning Engine ID
    expected_url = f"https://{location}-aiplatform.googleapis.com/v1beta1/{reasoning_engine_name}/a2a"
    agent_card["url"] = expected_url
    print(f"✔ Resolved Agent Card URL: {expected_url}")

    # 5. Register the Agent with the Gemini Enterprise App
    register_endpoint = (
        f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/"
        f"locations/global/collections/default_collection/engines/{app_id}/"
        f"assistants/default_assistant/agents"
    )

    register_payload = {
        "name": "sales_data_error_handler_a2ui",
        "displayName": "Sales Data Error Handler",
        "description": "Helps you inspect, repair, and resubmit quarantined sales CSV files using an interactive A2UI dashboard.",
        "a2aAgentDefinition": {
            "jsonAgentCard": json.dumps(agent_card)
        },
        "authorizationConfig": {
            "agentAuthorization": f"projects/{project_number}/locations/global/authorizations/{auth_id}"
        }
    }

    print(f"Registering Agent with Gemini Enterprise App '{app_id}'...")
    reg_res = requests.post(register_endpoint, headers=headers, json=register_payload)
    if reg_res.status_code in [200, 201]:
        print("✔ Agent registered successfully with Gemini Enterprise!")
        print(json.dumps(reg_res.json(), indent=2))
    else:
        print(f"❌ Failed to register Agent with Gemini Enterprise: {reg_res.status_code}")
        print(reg_res.text)

if __name__ == "__main__":
    main()
