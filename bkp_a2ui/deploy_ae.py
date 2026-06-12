import os
import vertexai
from vertexai.preview.reasoning_engines import A2aAgent
from vertexai.preview.reasoning_engines.templates.a2a import create_agent_card
from a2a.types import AgentSkill
from dotenv import load_dotenv
from google.genai import types
from importlib.metadata import version, PackageNotFoundError

load_dotenv()

def check_local_requirements(requirements):
    print("Checking local environment compatibility...")
    for req in requirements:
        if '@' in req:
            continue
        if '==' in req:
            name, req_ver = req.split('==')
            try:
                inst_ver = version(name)
                if inst_ver != req_ver:
                    print(f"⚠️ WARNING: Local version of {name} is {inst_ver}, but deployment requests {req_ver}.")
                    print(f"   This mismatch can cause pickling errors during deployment.")
            except PackageNotFoundError:
                print(f"⚠️ WARNING: Package {name} is required for deployment but not found locally.")
        elif '>=' in req:
            name, min_ver = req.split('>=')
            try:
                inst_ver = version(name)
                print(f"ℹ️ Local version of {name} is {inst_ver} (requested >= {min_ver})")
            except PackageNotFoundError:
                print(f"⚠️ WARNING: Package {name} is required for deployment but not found locally.")

import agent_executor

def main():
    
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or "spark-demo-1114"
    location = os.environ.get("GOOGLE_CLOUD_LOCATION") or "us-central1"
    storage = f"gs://{project_id}-agent-engine-deploy"
    
    print(f"Initializing Vertex AI (Project: {project_id}, Location: {location}, Bucket: {storage})")
    vertexai.init(
        project=project_id,
        location=location,
        staging_bucket=storage,
    )
    
    client = vertexai.Client(
        project=project_id,
        location=location,
        http_options=types.HttpOptions(
            api_version="v1beta1",
        ),
    )
    
    # 1. Define Skills & Agent Card
    agent_skill = AgentSkill(
        id="careconnect_navigator",
        name="CareConnect Navigator",
        description="A helpful assistant for finding providers and booking appointments using A2UI.",
        tags=["CareConnect", "A2UI"],
        examples=[
            "I need a dermatologist near 30303.",
            "Check availability for Dr. Alice.",
        ],
    )
    
    agent_card = create_agent_card(
        agent_name="CareConnect Navigator Agent",
        description="A helpful assistant that uses A2UI to navigate healthcare options.",
        skills=[agent_skill],
    )
    
    # 2. Instantiate local A2aAgent
    a2a_agent = A2aAgent(
        agent_card=agent_card,
        agent_executor_builder=agent_executor.AdkAgentToA2AExecutor,
    )
    
    # 3. Create Instance
    config = {
        "display_name": "CareConnect Navigator A2UI",
        "description": "CareConnect Navigator with A2UI.",
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
            "a2ui_examples.py",
            "a2ui_schema.py",
            "agent.py",
            "tools.py",
        ],
        "env_vars": {
            "PROJECT_ID": project_id,
            "LOCATION": location,
        },
    }
    
    check_local_requirements(config["requirements"])
    
    engine_id = "2619780516978622464"
    engine_name = f"projects/{project_id}/locations/{location}/reasoningEngines/{engine_id}"
    print(f"Applying inplace update to: {engine_id}")
    remote_agent = client.agent_engines.update(name=engine_name, agent=a2a_agent, config=config)
    print(f"✓ Process settlement: {remote_agent}")

if __name__ == "__main__":
    main()
