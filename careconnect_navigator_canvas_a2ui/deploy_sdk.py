import os
import vertexai
from vertexai.preview.reasoning_engines import A2aAgent
from a2a.types import AgentSkill
from vertexai.preview.reasoning_engines.templates.a2a import create_agent_card
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

import agent_executor

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION") or "us-central1"
    storage = os.environ.get("STORAGE_BUCKET") or "gs://your-staging-bucket"
    
    print(f"Initializing Vertex AI with project={project_id}, location={location}, bucket={storage}")
    vertexai.init(project=project_id, location=location, staging_bucket=storage)
    
    # Use the correct Client initialization as per skill
    # Wait, the skill says: client = vertexai.Client(project=..., location=...)
    # Let's check if vertexai has Client. Yes, it should if the skill says so.
    client = vertexai.Client(project=project_id, location=location)
    
    # Define Agent Skill and Card
    agent_skill = AgentSkill(
        id="careconnect_navigator_a2ui",
        name="CareConnect Navigator A2UI",
        description="Helpful assistant for finding doctors and booking appointments in Atlanta.",
        tags=["Healthcare", "Booking"],
        examples=["Find a physical therapist near 30303"],
    )

    agent_card = create_agent_card(
        agent_name="CareConnect Navigator A2UI",
        description="Helpful assistant for finding doctors and booking appointments in Atlanta.",
        skills=[agent_skill],
    )

    # Instantiate A2aAgent with Custom Executor
    print("Instantiating A2aAgent with custom executor...")
    a2a_agent = A2aAgent(
        agent_card=agent_card,
        agent_executor_builder=agent_executor.AdkAgentToA2AExecutor,
    )

    # Configuration for deployment
    config = {
        "display_name": "CareConnect Navigator A2UI",
        "agent_framework": "google-adk",
        "requirements": [
            "google-adk==1.28.1",
            "google-cloud-aiplatform[agent_engines,adk]==1.143.0",
            "a2a-sdk==0.3.25",
            "pydantic==2.12.5",
            "cloudpickle==3.1.2",
            "protobuf==6.33.6",
            "jsonschema==4.26.0",
            "a2ui-agent-sdk"
        ],
        "env_vars": {
            "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true",
            "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "true"
        },
        "extra_packages": [
            os.path.join(current_dir, "agent_executor.py"),
            os.path.join(current_dir, "tools.py"),
            os.path.join(current_dir, "agent.py"),
            os.path.join(current_dir, "ui_renderer.py"),
            os.path.join(current_dir, "composite_catalog_v0_9.json"),
            os.path.join(current_dir, "common_types_v0_9.json"),
            os.path.join(current_dir, "server_to_client_v0_9.json")
        ],
        "staging_bucket": storage
    }

    existing_engine_id = os.environ.get("EXISTING_ENGINE_ID") or os.environ.get("REASONING_ENGINE_ID")
    
    if existing_engine_id:
        engine_name = f"projects/{project_id}/locations/{location}/reasoningEngines/{existing_engine_id}"
        print(f"Applying inplace update to: {existing_engine_id}")
        remote_agent = client.agent_engines.update(name=engine_name, agent=a2a_agent, config=config)
    else:
        print("Spinning up fresh create instance...")
        remote_agent = client.agent_engines.create(agent=a2a_agent, config=config)
    
    print(f"✓ Process settlement: {remote_agent.name}")

if __name__ == "__main__":
    main()
