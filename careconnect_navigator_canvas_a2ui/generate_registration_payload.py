import json
import os
import subprocess
from dotenv import load_dotenv

load_dotenv()

def main():
    agent_dir = os.path.dirname(os.path.abspath(__file__))
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("PROJECT_ID") or "agentspace-demo-1145-b"
    location = os.environ.get("GOOGLE_CLOUD_LOCATION") or "us-central1"
    
    # Engine ID from env or fallback
    engine_id = os.environ.get("REASONING_ENGINE_ID")
    if not engine_id:
        try:
            tf_output_raw = subprocess.check_output(
                ["terraform", "output", "-json", "deployment_info"],
                cwd=os.path.join(agent_dir, "deploy"),
                text=True
            )
            tf_output = json.loads(tf_output_raw)
            engine_id = tf_output["engine_id"].split("/")[-1]
        except Exception as e:
            print(f"Warning: Failed to fetch engine_id from terraform, using default. Error: {e}")
            engine_id = "2102989161202974720"
    
    # Project Number from env or gcloud
    project_number = os.environ.get("PROJECT_NUMBER")
    if not project_number:
        try:
            project_number = subprocess.check_output(
                ["gcloud", "projects", "describe", project_id, "--format=value(projectNumber)"],
                text=True
            ).strip()
        except Exception:
            project_number = "121968733869"
            
    auth_profile_id = os.environ.get("AUTH_PROFILE_ID") or "careconnect-navigator-canvas-auth-v2"
    
    # Load agent card
    card_path = os.path.join(agent_dir, "agent_card.json")
    try:
        with open(card_path, "r") as f:
            agent_card = json.load(f)
    except FileNotFoundError:
        print(f"Warning: {card_path} not found, generating minimal card.")
        agent_card = {
            "name": "CareConnect Navigator Canvas A2UI",
            "description": "Helpful assistant for finding doctors and booking appointments in Atlanta using canvas-based A2UI."
        }
        
    # Update url with active reasoning engine
    agent_card["url"] = f"https://{location}-aiplatform.googleapis.com/v1beta1/projects/{project_id}/locations/{location}/reasoningEngines/{engine_id}/a2a"
    
    # Save back updated agent card
    with open(card_path, "w") as f:
        json.dump(agent_card, f, indent=2)
    print(f"Updated agent_card.json with Reasoning Engine ID: {engine_id}")
        
    # Construct payload
    auth_resource = f"projects/{project_number}/locations/global/authorizations/{auth_profile_id}"
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
