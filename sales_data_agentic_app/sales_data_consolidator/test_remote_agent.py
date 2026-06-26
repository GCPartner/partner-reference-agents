import os
import sys
import requests
import json
from google.auth import default
from google.auth.transport.requests import Request

PROJECT_ID = "agentspace-demo-1145-b"
LOCATION = "us-central1"
ENGINE_ID = "4685210910732582912"

def get_bearer_token():
    credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(Request())
    return credentials.token

def test_remote():
    token = get_bearer_token()
    url = f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{ENGINE_ID}:streamQuery"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "class_method": "stream_query",
        "input": {
            "message": "Process daily sales data",
            "user_id": "test_user"
        }
    }
    
    print(f"Sending streamQuery request to: {url}...")
    try:
        response = requests.post(url, headers=headers, json=payload, stream=True)
        print("Status Code:", response.status_code)
        
        if response.status_code != 200:
            print("Error response:", response.text)
            return
            
        print("\n=== REMOTE AGENT STREAM RESPONSE ===")
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode("utf-8")
                # Clean up SSE formatting if present
                if decoded_line.startswith("data:"):
                    decoded_line = decoded_line[5:].strip()
                try:
                    data = json.loads(decoded_line)
                    # Print actual content if present
                    if "content" in data:
                        print(data["content"])
                    else:
                        print(json.dumps(data, indent=2))
                except json.JSONDecodeError:
                    print(decoded_line)
        print("====================================\n")
    except Exception as e:
        print(f"Request failed: {e}", file=sys.stderr)

if __name__ == "__main__":
    test_remote()
