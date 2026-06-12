import json
import urllib.request

URL = "http://127.0.0.1:8000/jsonrpc"
SESSION_ID = "test_script_session"

def send_message(text, parts=None, session_id=SESSION_ID):
    payload = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "session_id": session_id,
            "message": {
                "text": text,
                "parts": parts or []
            }
        },
        "id": 1
    }
    
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(URL, data=json.dumps(payload).encode('utf-8'), headers=headers)
    
    try:
        with urllib.request.urlopen(req) as res:
            response_data = json.loads(res.read().decode('utf-8'))
            if "error" in response_data:
                print(f"Error: {response_data['error']}")
                return None
            return response_data["result"]["message"]
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

def get_response_text(res):
    if not res:
        return "None"
    if "text" in res:
        return res["text"]
    parts = res.get("parts", [])
    text_parts = [p["text"] for p in parts if "text" in p]
    if text_parts:
        return "\n".join(text_parts)
    return str(res)

def test_flow():
    print("=== Step 1: Send CSV Upload ===")
    csv_path = "/usr/local/google/home/veermuchandi/code/agents/rad-workshop/company_performance_analyzer/test_performance.csv"
    res1 = send_message(f"Analyze this spreadsheet: {csv_path}")
    if not res1:
        return
    print(f"Response:\n{get_response_text(res1)}\n")
    
    print("=== Step 2: Confirm Schema Mapping ===")
    confirm_action = {
        "metadata": {"mimeType": "application/json+a2ui"},
        "data": {
            "userAction": {
                "name": "submit",
                "context": {
                    "message": "Schema Mapping Confirmed!",
                    "action": "confirmSchema",
                    "state_col": "State Name",
                    "revenue_col": "Revenue (USD)",
                    "offering_col": "Product/Service Line"
                }
            }
        }
    }
    res2 = send_message("Schema Mapping Confirmed!", parts=[confirm_action])
    if not res2:
        return
    print(f"Response:\n{get_response_text(res2)}\n")
    
    print("=== Step 3: Choose Pie Chart ===")
    pie_action = {
        "metadata": {"mimeType": "application/json+a2ui"},
        "data": {
            "userAction": {
                "name": "submit",
                "context": {
                    "message": "Show the Pie Chart.",
                    "action": "changeChartType",
                    "chart_type": "pie"
                }
            }
        }
    }
    res3 = send_message("Show the Pie Chart.", parts=[pie_action])
    if not res3:
        return
    print(f"Response:\n{get_response_text(res3)}\n")
    # Check parts
    parts = res3.get("parts", [])
    print(f"Found {len(parts)} response parts.")
    for i, part in enumerate(parts):
        print(f"Part {i} mimeType: {part.get('metadata', {}).get('mimeType', 'text/plain')}")
        if part.get('metadata', {}).get('mimeType') == 'application/json+a2ui':
            print("Successfully received A2UI JSON payload!")
            print(json.dumps(part.get("data"), indent=2)[:500] + "...\n")
            
    print("=== Step 4: Toggle to Bar Chart ===")
    # Simulate clicking the Bar Chart button
    action_part = {
        "metadata": {"mimeType": "application/json+a2ui"},
        "data": {
            "userAction": {
                "name": "submit",
                "context": {
                    "message": "Display the data as a bar.",
                    "action": "changeChartType",
                    "chart_type": "bar"
                }
            }
        }
    }
    res4 = send_message("Display the data as a bar.", parts=[action_part])
    if not res4:
        return
    print(f"Response:\n{get_response_text(res4)}\n")
    parts = res4.get("parts", [])
    for i, part in enumerate(parts):
        if part.get('metadata', {}).get('mimeType') == 'application/json+a2ui':
            print("Successfully received updated A2UI JSON payload for Bar Chart!")
            print(json.dumps(part.get("data"), indent=2)[:500] + "...\n")

    print("=== Step 5: Drill down into California ===")
    # Simulate clicking the California slice/bar
    drill_part = {
        "metadata": {"mimeType": "application/json+a2ui"},
        "data": {
            "userAction": {
                "name": "submit",
                "context": {
                    "message": "Show performance breakdown by service offerings in California",
                    "action": "drillDown",
                    "state": "California"
                }
            }
        }
    }
    res5 = send_message("Show performance breakdown by service offerings in California", parts=[drill_part])
    if not res5:
        return
    print(f"Response:\n{get_response_text(res5)}\n")
    parts = res5.get("parts", [])
    for i, part in enumerate(parts):
        if part.get('metadata', {}).get('mimeType') == 'application/json+a2ui':
            print("Successfully received updated A2UI JSON payload for Drill Down!")
            print(json.dumps(part.get("data"), indent=2)[:500] + "...\n")

if __name__ == "__main__":
    test_flow()
