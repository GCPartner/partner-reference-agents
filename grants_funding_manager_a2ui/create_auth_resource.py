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
    location = "global" # Authorizations are global or multi-region? Skill says global or us.
    # But Skill Phase 2.3 says locations/${ENDPOINT_LOCATION} where endpoint location is e.g. global, us, eu.
    # The registration script used 'global' for the agents list URL: .../locations/global/collections/default_collection/engines/...
    # Let's check the skill example:
    # "https://${ENDPOINT_LOCATION}-discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/${ENDPOINT_LOCATION}/authorizations?authorizationId=${AUTH_ID}"
    # If ENDPOINT_LOCATION is global, it's discoveryengine.googleapis.com.
    # Let's use 'global' as it's the standard for tenant suite registration.

    auth_id = "grants-manager-auth"
    client_id = os.environ.get("OAUTH_CLIENT_ID", "")
    client_secret = os.environ.get("OAUTH_CLIENT_SECRET", "")

    # Construct authorizationUri with the cloud-platform scope
    authorization_uri = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={client_id}"
        f"&redirect_uri=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fstatic%2Foauth%2Foauth.html"
        f"&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcloud-platform"
        f"&include_granted_scopes=true"
        f"&response_type=code"
        f"&access_type=offline"
        f"&prompt=consent"
    )
    token_uri = "https://oauth2.googleapis.com/token"

    # We use global endpoint for authorizations
    api_endpoint = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/authorizations?authorizationId={auth_id}"

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
        "name": f"projects/{project_id}/locations/global/authorizations/{auth_id}",
        "serverSideOauth2": {
            "clientId": client_id,
            "clientSecret": client_secret,
            "authorizationUri": authorization_uri,
            "tokenUri": token_uri
        }
    }

    print(f"Creating authorization resource: {auth_id}...")
    print(f"Endpoint: {api_endpoint}")
    
    response = requests.post(api_endpoint, headers=headers, json=payload)

    if response.status_code in [200, 201]:
         print("✓ Authorization resource created successfully!")
         print(json.dumps(response.json(), indent=2))
    else:
         print(f"✗ Creation failed with status code: {response.status_code}")
         print(response.text)

if __name__ == "__main__":
    main()
