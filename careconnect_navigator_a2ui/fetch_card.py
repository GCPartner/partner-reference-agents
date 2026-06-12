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
    location = "us-central1"
    engine_id = "9045887220631732224"
    
    token = get_bearer_token()
    
    url = f"https://{location}-aiplatform.googleapis.com/v1beta1/projects/{project_id}/locations/{location}/reasoningEngines/{engine_id}/a2a/v1/card"
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"Fetching Agent Card from {url}...")
    res = requests.get(url, headers=headers)
    print(f"Status: {res.status_code}")
    
    if res.status_code == 200:
        card = res.json()
        print(json.dumps(card, indent=2))
        
        # Save card to file
        with open("agent_card.json", "w") as f:
            json.dump(card, f, indent=2)
        print("Saved card to agent_card.json")
    else:
        print(res.text)

if __name__ == "__main__":
    main()
