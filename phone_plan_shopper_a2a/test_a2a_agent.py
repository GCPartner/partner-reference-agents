import os
import requests
import json
import sys
from google.auth import default
from google.auth.transport.requests import Request

def get_bearer_token():
    credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(Request())
    return credentials.token

def test_agent(project_id, location, engine_id, query):
    # We need to use project number in the resource name for API calls usually if project ID fails,
    # but the card fetch worked with project number 121968733869.
    # Let's use the project number we found in logs to be safe.
    project_number = "121968733869"
    resource_name = f"projects/{project_number}/locations/{location}/reasoningEngines/{engine_id}"
    
    # Test Card Fetch
    card_url = f"https://{location}-aiplatform.googleapis.com/v1beta1/{resource_name}/a2a/v1/card"
    headers = {
        "Authorization": f"Bearer {get_bearer_token()}",
        "Content-Type": "application/json"
    }
    
    print(f"1. Fetching Agent Card from: {card_url}")
    try:
        response = requests.get(card_url, headers=headers)
        print("Status Code:", response.status_code)
        if response.status_code == 200:
            print("Success! Card fetched.")
            print(json.dumps(response.json(), indent=2))
        else:
            print("Failed to fetch card.")
            print(response.text)
    except Exception as e:
        print(f"Error fetching card: {e}")
        
    print("\n" + "="*40 + "\n")
    
    # Test Message Send
    message_url = f"https://{location}-aiplatform.googleapis.com/v1beta1/{resource_name}/a2a/v1/message:send"
    
    payload = {
      "request": {
        "message_id": "test-msg-id-002",
        "role": "ROLE_USER",
        "content": [
          {
            "text": query
          }
        ]
      },
      "configuration": {
        "blocking": True
      }
    }
    
    print(f"2. Sending Message to: {message_url}")
    print("Payload:", json.dumps(payload, indent=2))
    try:
        response = requests.post(message_url, headers=headers, json=payload)
        print("Status Code:", response.status_code)
        print("Response:", response.text)
    except Exception as e:
        print(f"Error sending message: {e}")

if __name__ == "__main__":
    # Defaults for the current deployed agent
    PROJECT_ID = "agentspace-demo-1145-b"
    LOCATION = "us-central1"
    ENGINE_ID = "3099774517107490816"
    QUERY = "Hello, I want to shop for phone plans."
    
    if len(sys.argv) > 1:
        QUERY = sys.argv[1]
        
    test_agent(PROJECT_ID, LOCATION, ENGINE_ID, QUERY)
