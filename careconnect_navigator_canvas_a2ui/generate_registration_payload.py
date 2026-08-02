import json
import os
import subprocess

def main():
    agent_dir = os.path.dirname(os.path.abspath(__file__))
    project_id = subprocess.check_output(
        ["gcloud", "config", "get-value", "project"],
        text=True
    ).strip()
    # Fetch engine ID from terraform output dynamically
    try:
        tf_output_raw = subprocess.check_output(
            ["terraform", "output", "-json", "deployment_info"],
            cwd=os.path.join(agent_dir, "deploy"),
            text=True
        )
        tf_output = json.loads(tf_output_raw)
        engine_id = tf_output["engine_id"].split("/")[-1]
    except Exception as e:
        print(f"Warning: Failed to fetch engine_id from terraform, using fallback. Error: {e}")
        engine_id = "381488203640602624"
    
    # Fetch project number dynamically
    project_number = subprocess.check_output(
        ["gcloud", "projects", "describe", project_id, "--format=value(projectNumber)"],
        text=True
    ).strip()
    
    # Load agent card
    card_path = os.path.join(agent_dir, "agent_card.json")
    with open(card_path, "r") as f:
        agent_card = json.load(f)
        
    # Update url with the active engine ID
    agent_card["url"] = f"https://us-central1-aiplatform.googleapis.com/v1beta1/projects/{project_id}/locations/us-central1/reasoningEngines/{engine_id}/a2a"
    
    # Save back updated agent card
    with open(card_path, "w") as f:
        json.dump(agent_card, f, indent=2)
    print("Updated agent_card.json with correct engine ID.")
        
    # Construct payload
    auth_resource = f"projects/{project_number}/locations/global/authorizations/careconnect-navigator-canvas-auth"
    payload = {
        "name": "careconnect_navigator_canvas_a2ui",
        "displayName": "CareConnect Navigator Canvas A2UI",
        "description": "Helpful assistant for finding doctors and booking appointments in Atlanta using canvas-based A2UI v0.9.",
        "a2aAgentDefinition": {
            "jsonAgentCard": json.dumps(agent_card)
        },
        "authorizationConfig": {
            "agentAuthorization": auth_resource
        },
        "sharingConfig": {
            "scope": "ALL_USERS"
        }
    }
    
    # Write to registration_payload.json
    payload_path = os.path.join(agent_dir, "registration_payload.json")
    with open(payload_path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"Generated registration_payload.json at {payload_path}")

if __name__ == "__main__":
    main()
