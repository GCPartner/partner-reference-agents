import os
import vertexai
from vertexai.preview.reasoning_engines import A2aAgent
from a2a.types import AgentSkill
from vertexai.preview.reasoning_engines.templates.a2a import create_agent_card
from google.genai import types
from agent_executor import AdkAgentToA2AExecutor
from google.protobuf import json_format

# Monkey-patch json_format.MessageToJson and MessageToDict to handle Pydantic models (like AgentCard) correctly
original_message_to_json = json_format.MessageToJson
def patched_message_to_json(message, *args, **kwargs):
    if hasattr(message, "model_dump_json"):
        return message.model_dump_json()
    elif hasattr(message, "json"):
        return message.json()
    elif isinstance(message, dict):
        import json
        return json.dumps(message)
    return original_message_to_json(message, *args, **kwargs)
json_format.MessageToJson = patched_message_to_json

original_message_to_dict = json_format.MessageToDict
def patched_message_to_dict(message, *args, **kwargs):
    if hasattr(message, "model_dump"):
        return message.model_dump()
    elif hasattr(message, "dict"):
        return message.dict()
    elif isinstance(message, dict):
        return message
    return original_message_to_dict(message, *args, **kwargs)
json_format.MessageToDict = patched_message_to_dict

# Resolve active GCP project dynamically from Application Default Credentials
import google.auth
import json

active_project = None
try:
    _, active_project = google.auth.default()
except Exception as e:
    print(f"Warning: Failed to automatically resolve active project from ADC: {e}")

# Load deployments.json history config if exists
deployments_config = {}
deployments_path = os.path.join(os.path.dirname(__file__), "deployments.json")
if os.path.exists(deployments_path):
    try:
        with open(deployments_path, "r") as f:
            deployments_config = json.load(f)
    except Exception as e:
        print(f"Warning: Failed to parse deployments.json: {e}")

# Apply configuration dynamically based on active project
env_config = {}
if active_project and active_project in deployments_config:
    env_config = deployments_config[active_project]
    print(f"Applying dynamic configuration for project '{active_project}' from deployments.json")
    for k, v in env_config.items():
        os.environ[k] = v
else:
    # Fallback to local .env file
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        from dotenv import load_dotenv
        load_dotenv(env_path)

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", active_project or "YOUR_PROJECT_ID")
BUCKET = os.environ.get("GOOGLE_CLOUD_STAGING_BUCKET", "gs://YOUR_STAGING_BUCKET")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")

# Sync the active config back to local .env so local runners are always in sync
try:
    with open(os.path.join(os.path.dirname(__file__), ".env"), "w") as f:
        f.write(f"GOOGLE_GENAI_USE_VERTEXAI=True\n")
        f.write(f"GOOGLE_CLOUD_PROJECT={PROJECT_ID}\n")
        f.write(f"GOOGLE_CLOUD_LOCATION={LOCATION}\n")
        f.write(f"GOOGLE_CLOUD_STAGING_BUCKET={BUCKET}\n")
        f.write(f"EXISTING_ENGINE_ID={os.environ.get('EXISTING_ENGINE_ID', '')}\n\n")
        f.write(f"# Added by Agent Engine Deployer Skill\n")
        f.write(f"GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true\n")
        f.write(f"OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true\n\n")
        f.write(f"# Maps API Key for Frontend Embeds\n")
        f.write(f"GOOGLE_MAPS_API_KEY={MAPS_API_KEY}\n")
    print(f"Successfully synchronized local .env configuration.")
except Exception as e:
    print(f"Warning: Failed to synchronize .env file: {e}")

print(f"Deploying to Project ID: {PROJECT_ID}")
print(f"Staging Bucket: {BUCKET}")

# STABLE VERSIONS FOR PYTHON 3.13 / A2UI
VERSIONS = [
    "google-adk==1.34.1", "a2a-sdk==0.3.25", "pydantic==2.12.5", 
    "cloudpickle==3.1.2", "protobuf==6.33.6",
    "a2ui-agent-sdk @ git+https://github.com/google/A2UI.git#subdirectory=agent_sdks/python"
]

def main():
    vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=BUCKET)
    
    # Initialize genai Client
    client = vertexai.Client(project=PROJECT_ID, location=LOCATION)

    # Build agent card
    agent_skill = AgentSkill(
        id="route_planner",
        name="Route Planner Agent",
        description="Optimizes customer visit schedules for a field representative workday.",
        tags=["Route-Planner"],
        examples=["Plan route for today"],
    )

    my_card = create_agent_card(
        agent_name="Route Planner A2Ui agent",
        description="Optimizes customer visit schedules for a field representative workday.",
        skills=[agent_skill],
    )

    # Create A2A agent wrapper
    a2a_agent = A2aAgent(agent_card=my_card, agent_executor_builder=AdkAgentToA2AExecutor)
    
    config = {
        "staging_bucket": BUCKET,
        "requirements": VERSIONS,
        "extra_packages": ["agent_executor.py", "agent.py", "tools.py"],
        "display_name": "Route Planner A2Ui agent",
        "env_vars": {
            "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true",
            "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "true",
            "GOOGLE_MAPS_API_KEY": os.environ.get("GOOGLE_MAPS_API_KEY", ""),
            "GOOGLE_GENAI_USE_VERTEXAI": "True"
        }
    }

    print("Deploying Reasoning Engine...")
    existing_id = os.environ.get("EXISTING_ENGINE_ID")
    if existing_id:
        name = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{existing_id}"
        print(f"Applying inplace update to: {existing_id}")
        remote = client.agent_engines.update(name=name, agent=a2a_agent, config=config)
    else:
        print("Spinning up fresh create instance...")
        remote = client.agent_engines.create(agent=a2a_agent, config=config)
    print(f"Deploy complete: {remote.api_resource.name}")

if __name__ == "__main__":
    main()
