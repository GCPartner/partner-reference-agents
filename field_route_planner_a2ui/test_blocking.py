import os
import requests
from google.auth import default
from google.auth.transport.requests import Request as AuthRequest

if os.path.exists(".env"):
    from dotenv import load_dotenv
    load_dotenv()

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "YOUR_PROJECT_ID")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
ENGINE_ID = os.environ.get("EXISTING_ENGINE_ID", "YOUR_ENGINE_ID")

def get_bearer_token():
    credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(AuthRequest())
    return credentials.token

def main():
    token = get_bearer_token()
    url = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{ENGINE_ID}/a2a/v1/message:send"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Construct blocking payload
    payload = {
        "message": {
            "role": "ROLE_USER",
            "content": [
                {
                    "text": "Plan my route"
                },
                {
                    "data": {
                        "data": {
                            "userAction": {
                                "name": "submit_trip_details",
                                "context": {
                                    "start_time": "07:58",
                                    "message": "Plan my route",
                                    "end_location": "",
                                    "same_as_start": True,
                                    "start_location": "1380 Woodvine Way ALpharetta GA 30005"
                                }
                            }
                        }
                    }
                }
            ]
        },
        "configuration": {
            "blocking": True
        }
    }
    
    print(f"Sending POST to {url}...")
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=180)
        print(f"Response Status Code: {res.status_code}")
        print(f"Response Headers: {res.headers}")
        print(f"Response Body: {res.text}")
    except Exception as e:
        print(f"Request failed: {str(e)}")

if __name__ == "__main__":
    main()
