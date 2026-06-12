import os
import vertexai
from vertexai.preview.reasoning_engines import A2aAgent
from vertexai.preview.reasoning_engines.templates.a2a import create_agent_card
from a2a.types import AgentSkill
from dotenv import load_dotenv
from google.genai import types

import agent_executor

def deploy():
    load_dotenv()
    
    project_id = os.environ.get("PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("LOCATION") or os.environ.get("GOOGLE_CLOUD_LOCATION") or "us-central1"
    storage = os.environ.get("STORAGE_BUCKET") or "gs://your-staging-bucket"
    
    print(f"Using staging bucket: {storage}")
    
    vertexai.init(
        project=project_id,
        location=location,
        staging_bucket=storage,
    )

    # 1. Define Skills & Agent Card
    agent_skill = AgentSkill(
        id="phone_plan_shopper_a2a",
        name="Phone Plan Shopper A2A",
        description="A helpful assistant for shopping phone plans and devices (A2A compatible).",
        tags=["Phone-Plans", "A2A"],
        examples=[
            "I want to shop for phone plans.",
            "Show me available devices.",
        ],
    )

    pp_agent_card = create_agent_card(
        agent_name="Phone Plan Shopper A2A Agent",
        description="A helpful assistant that uses A2A to shop for phone plans.",
        skills=[agent_skill],
    )
    
    print("✓ Agent card created.")
    
    # 2. Instantiate local A2aAgent
    a2a_agent = A2aAgent(
        agent_card=pp_agent_card,
        agent_executor_builder=agent_executor.AdkAgentToA2AExecutor,
    )
    print("✓ Local A2aAgent created.")

    client = vertexai.Client(
        project=project_id,
        location=location,
        http_options=types.HttpOptions(
            api_version="v1beta1",
        ),
    )
    print("✓ Vertex AI client created.")

    # 3. Create Config
    config = {
        "display_name": "Phone Plan Shopper A2A",
        "description": "Phone Plan Shopper with A2A compatibility (non-A2UI).",
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
        ],
        "http_options": {
            "api_version": "v1beta1",
        },
        "max_instances": 1,
        "extra_packages": [
            "agent_executor.py",
            "agent.py",
            "tools.py",
        ],
        "env_vars": {
            "NUM_WORKERS": "1",
        },
    }

    print("Spinning up fresh create instance...")
    remote_agent = client.agent_engines.create(agent=a2a_agent, config=config)
    print(f"✓ Agent created: {remote_agent.api_resource.name if hasattr(remote_agent, 'api_resource') else remote_agent}")

if __name__ == "__main__":
    deploy()
