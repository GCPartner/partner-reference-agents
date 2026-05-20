import requests
import json

url = "http://localhost:8002/jsonrpc"
payload = {
    "jsonrpc": "2.0",
    "method": "message/send",
    "params": {
        "message": {
            "text": "I need a plan with unlimited data and international calling."
        },
        "session_id": "test_session"
    },
    "id": 1
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    try:
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2))
    except:
        print("Raw Response Content:")
        print(response.text)
except Exception as e:
    print(f"Error: {e}")
