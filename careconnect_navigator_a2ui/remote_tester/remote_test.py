import os
import requests
import json
import time
from google.auth import default
from google.auth.transport.requests import Request

def get_bearer_token():
    credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(Request())
    return credentials.token

def main():
    project_id = "agentspace-demo-1145-b"
    location = "us-central1"
    engine_id = "6431936864059392000"
    
    token = get_bearer_token()
    
    # Verify Agent Card
    card_url = f"https://{location}-aiplatform.googleapis.com/v1beta1/projects/{project_id}/locations/{location}/reasoningEngines/{engine_id}/a2a/v1/card"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    print("Fetching Agent Card...")
    res = requests.get(card_url, headers=headers)
    print(f"Status: {res.status_code}")
    print(res.json())
    
    # Send Message
    msg_url = f"https://{location}-aiplatform.googleapis.com/v1beta1/projects/{project_id}/locations/{location}/reasoningEngines/{engine_id}/a2a/v1/message:send"
    
    payload = {
        "message": {
            "content": [
                {
                    "text": "Find a doctor in Atlanta"
                }
            ]
        }
    }
    
    print("\nSending Message...")
    res = requests.post(msg_url, headers=headers, json=payload)
    print(f"Status: {res.status_code}")
    
    response_data = res.json()
    print(json.dumps(response_data, indent=2))
    
    context_id = response_data.get("task", {}).get("contextId")
    
    if context_id:
        print(f"\nFetching Context {context_id}...")
        context_url = f"https://{location}-aiplatform.googleapis.com/v1beta1/projects/{project_id}/locations/{location}/reasoningEngines/{engine_id}/a2a/v1/contexts/{context_id}"
        
        time.sleep(5) # Wait for agent to work
        res = requests.get(context_url, headers=headers)
        print(f"Status: {res.status_code}")
        context_data = res.json()
        print(json.dumps(context_data, indent=2))
    else:
        print("No context ID returned.")

if __name__ == "__main__":
    main()
