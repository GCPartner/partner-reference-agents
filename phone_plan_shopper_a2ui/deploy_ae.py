import os
import vertexai
from vertexai.preview.reasoning_engines import A2aAgent
from vertexai.preview.reasoning_engines.templates.a2a import create_agent_card
from a2a.types import AgentSkill
from dotenv import load_dotenv
from google.genai import types # Added for HttpOptions

# We need to import our custom executor
import agent_executor

def deploy():
    # Load .env vars
    load_dotenv()
    
    project_id = os.environ.get("PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("LOCATION") or os.environ.get("GOOGLE_CLOUD_LOCATION") or "us-central1"
    
    # Use the discovered staging bucket as default if not in env
    storage = os.environ.get("STORAGE_BUCKET") or "gs://your-staging-bucket"
    
    print(f"Using staging bucket: {storage}")
    

    print(f"Initializing Vertex AI (Project: {project_id}, Location: {location}, Bucket: {storage})")
    vertexai.init(
        project=project_id,
        location=location,
        staging_bucket=storage,
    )

    # 1. Define Skills & Agent Card
    agent_skill = AgentSkill(
        id="phone_plan_shopper",
        name="Phone Plan Shopper",
        description="A helpful assistant for shopping phone plans and devices using A2UI.",
        tags=["Phone-Plans", "A2UI"],
        examples=[
            "I want to shop for phone plans.",
            "Show me available devices.",
        ],
    )

    pp_agent_card = create_agent_card(
        agent_name="Phone Plan Shopper Agent",
        description="A helpful assistant that uses A2UI to shop for phone plans.",
        skills=[agent_skill],
    )
    import json
    # Use standard json.dumps to print it as a JSON string
    print(f"JSON_AGENT_CARD_START{json.dumps(pp_agent_card, default=lambda o: o.__dict__)}JSON_AGENT_CARD_END")
    print("✓ Agent card created.")
    
    # 2. Instantiate local A2aAgent
    a2a_agent = A2aAgent(
        agent_card=pp_agent_card,
        agent_executor_builder=agent_executor.AdkAgentToA2AExecutor,
    )
    print("✓ Local A2aAgent created.")

    # Instantiate Client for Creation (Option B style)
    client = vertexai.Client(
        project=project_id,
        location=location,
        http_options=types.HttpOptions(
            api_version="v1beta1",
        ),
    )
    print("✓ Vertex AI client created.")

    # 3. Create or Update (Option B style)
    
    config = {
        "display_name": "Phone Plan Shopper A2A (New A2A)",
        "description": "Phone Plan Shopper with A2UI and A2A Golden Template.",
        "agent_framework": "google-adk",
        "staging_bucket": storage,
        "requirements": [
            "google-adk==1.28.1",
            "google-cloud-aiplatform[agent_engines,adk]==1.143.0",
            "a2a-sdk==0.3.22",
            "pydantic==2.12.5",
            "cloudpickle==3.1.2",
            "protobuf==6.33.6",
            "jsonschema==4.26.0",
            "a2ui-agent-sdk @ git+https://github.com/google/A2UI.git#subdirectory=agent_sdks/python",
        ],
        "http_options": {
            "api_version": "v1beta1",
        },
        "max_instances": 1,
        "extra_packages": [
            "agent_executor.py",
            "a2ui_examples.py",
            "a2ui_schema.py",
            "a2ui_schema.json",
            "agent.py",
            "tools.py",
            "a2ui_tools.py",
        ],
        "env_vars": {
            "NUM_WORKERS": "1",
        },
    }

    existing_engine_id = "2067680544300204032"
    engine_name = f"projects/{project_id}/locations/{location}/reasoningEngines/{existing_engine_id}"
    print(f"Updating existing Agent Engine instance: {engine_name}...")
    remote_agent = client.agent_engines.update(name=engine_name, agent=a2a_agent, config=config)
    print(f"✓ Agent update call completed! {remote_agent.api_resource.name if hasattr(remote_agent, 'api_resource') else remote_agent}")



if __name__ == "__main__":
    deploy()
