import os
import requests
import json
from google.auth import default
from google.auth.transport.requests import Request
from dotenv import load_dotenv

load_dotenv()

def get_bearer_token():
    credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(Request())
    return credentials.token

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("PROJECT_ID")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION") or "us-central1"
    engine_id = os.environ.get("REASONING_ENGINE_ID")
    
    if not engine_id:
        print("Error: REASONING_ENGINE_ID is not set in environment or .env.")
        return
        
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
        card_path = os.path.join(current_dir, "agent_card.json")
        with open(card_path, "w") as f:
            json.dump(card, f, indent=2)
        print(f"Saved card to {card_path}")
    else:
        print(res.text)

if __name__ == "__main__":
    main()
