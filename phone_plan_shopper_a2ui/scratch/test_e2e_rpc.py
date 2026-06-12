import requests
import json
import time

url = "http://localhost:8000/jsonrpc"
session_id = "e2e_test_session_v9"

def send_message(text, user_action=None):
    payload = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "text": text
            },
            "session_id": session_id
        },
        "id": 1
    }
    
    if user_action:
        payload["params"]["message"]["parts"] = [
            {
                "data": { "userAction": user_action },
                "metadata": { "mimeType": "application/json+a2ui" }
            }
        ]
        
    response = requests.post(url, json=payload)
    print(f"\n--- Turn: {text} ---")
    print(f"Status Code: {response.status_code}")
    try:
        res_json = response.json()
        print("Response JSON:")
        parts = res_json.get("result", {}).get("message", {}).get("parts", [])
        for part in parts:
            if "text" in part:
                print(f"Text: {part['text']}")
            if "data" in part:
                print(f"UI Data: {json.dumps(part['data'], indent=2)}") 
    except Exception as e:
        print(f"Error parsing response: {e}")
        print(f"Raw Response: {response.text}")

# # Turn 1: Search Plans
# send_message("I need a plan with unlimited data and international calling.")
# time.sleep(5)
# 
# # Turn 2: Select Plan
# send_message("I have selected the plan.", user_action={"name": "submit", "context": {"selected_plan_id": "p3", "message": "I select the Global Traveler plan."}})
# time.sleep(5)

# # Turn 3: Ask for devices
# send_message("Show me compatible devices.")
# time.sleep(5)
# 
# # Turn 4: Select Device
# send_message("I select the Google Pixel 9.", user_action={"name": "submit", "context": {"selected_device_id": "d1", "message": "I select the Google Pixel 9."}})
# time.sleep(5)

# Turn 5: Complain about price
send_message("This is too expensive.")
time.sleep(5)

# Turn 6: Agree to discount request
send_message("Yes, please request a discount.")
time.sleep(5)

# Turn 7: Place Order
send_message("Place my order.", user_action={"name": "submit", "context": {"action": "place_order", "message": "Place my order."}})
