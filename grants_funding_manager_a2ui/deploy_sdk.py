import os
from a2a.types import AgentSkill
import agent_executor # Package import
from dotenv import load_dotenv
from google.auth import default
from google.auth.transport.requests import Request
from google.genai import types
import vertexai
from vertexai.preview.reasoning_engines import A2aAgent
from vertexai.preview.reasoning_engines.templates.a2a import create_agent_card

def _get_bearer_token():
    """Gets a bearer token for authenticating with Google Cloud."""
    try:
        credentials, _ = default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        request = Request()
        credentials.refresh(request)
        return credentials.token
    except Exception as e:
        print(f"Error getting credentials: {e}")
        return None

def main():
    # Load environment variables
    load_dotenv()

    project_id = os.environ.get("PROJECT_ID", "agentspace-demo-1145-b")
    location = os.environ.get("LOCATION", "us-central1")
    storage = os.environ.get("STORAGE_BUCKET", "gs://careconnect-navigator-a2ui")
    api_endpoint = f"{location}-aiplatform.googleapis.com"

    vertexai.init(
        project=project_id,
        location=location,
        api_endpoint=api_endpoint,
        staging_bucket=storage,
    )
    print("✓ Vertex AI initialized.")

    client = vertexai.Client(
        project=project_id,
        location=location,
        http_options=types.HttpOptions(
            api_version="v1beta1",
        ),
    )

    agent_skill = AgentSkill(
        id="grants_funding_manager",
        name="Grants Funding Manager",
        description="A helpful assistant for orchestrating the grant lifecycle from intake to review using A2UI.",
        tags=["Grants", "A2UI"],
        examples=[
            "I want to submit a new project proposal for funding.",
        ],
    )

    grants_agent_card = create_agent_card(
        agent_name="Grants Funding Manager A2UI",
        description="Grants Lifecycle orchestrator with A2UI interface.",
        skills=[agent_skill],
    )

    a2a_agent = A2aAgent(
        agent_card=grants_agent_card,
        agent_executor_builder=agent_executor.AdkAgentToA2AExecutor,
    )

    # Read requirements from file
    requirements_path = "requirements.txt"
    try:
        with open(requirements_path, "r") as f:
            requirements = [
                line.strip()
                for line in f
                if line.strip() and not line.startswith("#")
            ]
        print(f"✓ Loaded {len(requirements)} requirements from {requirements_path}")
    except FileNotFoundError:
        print(f"Warning: {requirements_path} not found. Using defaults.")
        requirements = [
            "google-cloud-aiplatform[agent_engines,adk]>=1.143.0",
            "a2a-sdk>=0.3.4",
            "pydantic==2.12.5",
            "cloudpickle==3.1.2",
            "jsonschema"
        ]

    config = {
        "display_name": "Grants Funding Manager A2UI",
        "description": "Grants Lifecycle orchestrator with A2UI interface.",
        "agent_framework": "google-adk",
        "staging_bucket": storage,
        "requirements": requirements,
        "http_options": {
            "api_version": "v1beta1",
        },
        "max_instances": 1,
        "env_vars": {
            "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true",
            "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "true",
        },
        "extra_packages": [
            "agent_executor.py",
            "tools.py",
            "agent.py",
            "a2ui_examples.py",
            "a2ui_schema.py",
            "data/strategic_plan.txt" # Vendor data dependency
        ],
    }

    # To update an existing engine, set EXISTING_ENGINE_ID in env
    existing_engine_id = os.environ.get("EXISTING_ENGINE_ID")

    if existing_engine_id:
        engine_name = f"projects/{project_id}/locations/{location}/reasoningEngines/{existing_engine_id}"
        print(f"Applying inplace update to: {existing_engine_id}")
        remote_agent = client.agent_engines.update(
            name=engine_name,
            agent=a2a_agent,
            config=config
        )
    else:
        print("Spinning up fresh create instance... This might take a few minutes.")
        remote_agent = client.agent_engines.create(
            agent=a2a_agent,
            config=config
        )
        
    print("✓ Agent process settlement success!")

    if hasattr(remote_agent, "api_resource"):
        print(f"Engine Resource Name: {remote_agent.api_resource.name}")
    elif hasattr(remote_agent, "gca_resource"):
        print(f"Engine Resource Name: {remote_agent.gca_resource.name}")
    else:
        print(f"Engine Name: {remote_agent.name}")

if __name__ == "__main__":
    main()
