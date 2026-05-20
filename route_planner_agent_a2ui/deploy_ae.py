import os
import json
import vertexai
from vertexai.preview.reasoning_engines import A2aAgent
from vertexai.preview.reasoning_engines.templates.a2a import create_agent_card
from a2a.types import AgentSkill
from dotenv import load_dotenv
from google.genai import types

import agent_executor

def deploy():
    load_dotenv()
    
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or "<YOUR_PROJECT_ID>"
    location = os.environ.get("GOOGLE_CLOUD_LOCATION") or "us-central1"
    storage = os.environ.get("STORAGE_BUCKET") or "gs://your-staging-bucket"
    

        
    vertexai.init(
        project=project_id,
        location=location,
        staging_bucket=storage,
    )

    # 1. Define Skills & Agent Card
    agent_skill = AgentSkill(
        id="route_planner_agent",
        name="Route Planner Agent",
        description="Helps field service reps plan their routes efficiently using A2UI.",
        tags=["Route-Planning", "A2UI"],
        examples=[
            "Plan my route for today",
            "Show me the route plan",
        ],
    )

    pp_agent_card = create_agent_card(
        agent_name="Route Planner Agent",
        description="Helps field service reps plan their routes efficiently using A2UI.",
        skills=[agent_skill],
    )
    
    # 2. Instantiate local A2aAgent
    a2a_agent = A2aAgent(
        agent_card=pp_agent_card,
        agent_executor_builder=agent_executor.AdkAgentToA2AExecutor,
    )

    client = vertexai.Client(
        project=project_id,
        location=location,
        http_options=types.HttpOptions(api_version="v1beta1"),
    )

    # 3. Create Config with working dependencies for A2UI
    config = {
        "display_name": "Route Planner Agent",
        "description": "Helps field service reps plan their routes efficiently using A2UI.",
        "agent_framework": "google-adk",
        "staging_bucket": storage,
        "requirements": [
            "google-adk==1.28.1",
            "google-cloud-aiplatform[agent_engines,adk]==1.143.0",
            "a2a-sdk==0.3.25",
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
            "agent.py",
            "tools.py",
        ],
        "env_vars": {
            "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true",
            "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "true",
            "GOOGLE_MAPS_API_KEY": os.environ.get("GOOGLE_MAPS_API_KEY", ""),
        },
    }

    existing_engine_id = os.environ.get("EXISTING_ENGINE_ID")
    
    if existing_engine_id:
        engine_name = f"projects/{project_id}/locations/{location}/reasoningEngines/{existing_engine_id}"
        print(f"Applying inplace update to: {existing_engine_id}")
        remote_agent = client.agent_engines.update(name=engine_name, agent=a2a_agent, config=config)
    else:
        print("Spinning up fresh create instance...")
        remote_agent = client.agent_engines.create(agent=a2a_agent, config=config)
    print(f"✓ Agent created: {remote_agent.api_resource.name}")

if __name__ == "__main__":
    deploy()
