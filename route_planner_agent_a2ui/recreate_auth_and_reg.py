import os
import json
import requests
from google.auth import default
from google.auth.transport.requests import Request

def get_bearer_token():
    credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(Request())
    return credentials.token

def run():
    project_id = "<YOUR_PROJECT_ID>"
    app_id = "<YOUR_APP_ID>"
    agent_id = "route_planner_agent"
    old_auth_id = "route_planner_auth"
    new_auth_id = "route_planner_auth_v2"
    
    client_id = "<YOUR_CLIENT_ID>"
    client_secret = "<YOUR_CLIENT_SECRET>"
    
    token = get_bearer_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": project_id
    }
    
    # 1. Delete OLD Auth Resource (just in case)
    delete_auth_url = f"https://global-discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/authorizations/{old_auth_id}"
    print(f"Deleting old auth resource at: {delete_auth_url}")
    response = requests.delete(delete_auth_url, headers=headers)
    print(f"Delete old auth response: {response.status_code}")
    
    # 2. Create NEW Auth Resource
    create_auth_url = f"https://global-discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/authorizations?authorizationId={new_auth_id}"
    auth_payload = {
        "name": f"projects/{project_id}/locations/global/authorizations/{new_auth_id}",
        "serverSideOauth2": {
            "clientId": client_id,
            "clientSecret": client_secret,
            "authorizationUri": f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&redirect_uri=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fstatic%2Foauth%2Foauth.html&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcloud-platform&include_granted_scopes=true&response_type=code&access_type=offline&prompt=consent",
            "tokenUri": "https://oauth2.googleapis.com/token"
        }
    }
    print(f"Creating new auth resource at: {create_auth_url}")
    response = requests.post(create_auth_url, headers=headers, json=auth_payload)
    print(f"Create new auth response: {response.status_code} - {response.text}")
    
    # 3. Delete existing agent registration (so we can recreate it with new auth)
    delete_reg_url = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/collections/default_collection/engines/{app_id}/assistants/default_assistant/agents/{agent_id}"
    print(f"Deleting agent registration at: {delete_reg_url}")
    response = requests.delete(delete_reg_url, headers=headers)
    print(f"Delete registration response: {response.status_code}")

    # 4. Fetch Agent Card
    engine_resource = "projects/<YOUR_PROJECT_NUMBER>/locations/us-central1/reasoningEngines/<YOUR_REASONING_ENGINE_ID>"
    card_url = f"https://us-central1-aiplatform.googleapis.com/v1beta1/{engine_resource}/a2a/v1/card"
    print(f"Fetching card from: {card_url}")
    response = requests.get(card_url, headers={"Authorization": f"Bearer {token}"})
    if response.status_code != 200:
        print(f"ERROR fetching card: {response.status_code} - {response.text}")
        return
    a2ui_agent_card = response.json()
    
    # 5. Register Agent with NEW Auth
    register_url = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/collections/default_collection/engines/{app_id}/assistants/default_assistant/agents?agentId={agent_id}"
    reg_payload = {
        "name": f"projects/{project_id}/locations/global/collections/default_collection/engines/{app_id}/assistants/default_assistant/agents/{agent_id}",
        "displayName": "Route Planner Agent",
        "description": "Helps field service reps plan their routes efficiently using A2UI.",
        "a2aAgentDefinition": {"jsonAgentCard": json.dumps(a2ui_agent_card)},
        "authorizationConfig": {
            "agentAuthorization": f"projects/<YOUR_PROJECT_NUMBER>/locations/global/authorizations/{new_auth_id}"
        }
    }
    print(f"Registering agent at: {register_url}")
    response = requests.post(register_url, headers=headers, json=reg_payload)
    print(f"Register response: {response.status_code} - {response.text}")

if __name__ == "__main__":
    run()
