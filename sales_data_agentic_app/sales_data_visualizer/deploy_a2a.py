import os
import vertexai
from vertexai.preview.reasoning_engines import A2aAgent
from vertexai.preview.reasoning_engines.templates.a2a import create_agent_card
from a2a.types import AgentSkill
from dotenv import load_dotenv
from google.genai import types
import json

def deploy():
    # Load .env vars from consolidator .env
    dotenv_path = "../sales_data_consolidator/.env"
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
    else:
        load_dotenv()
    
    project_id = os.environ.get("PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT") or "agentspace-demo-1145-b"
    location = os.environ.get("LOCATION") or os.environ.get("GOOGLE_CLOUD_LOCATION") or "us-central1"
    staging_bucket = f"gs://{project_id}-sales-data-archive"
    
    print(f"Initializing Vertex AI (Project: {project_id}, Location: {location}, Staging Bucket: {staging_bucket})")
    vertexai.init(
        project=project_id,
        location=location,
        staging_bucket=staging_bucket,
    )

    # 1. Define Skills & Agent Card
    visualizer_skill = AgentSkill(
        id="sales_data_visualizer",
        name="Sales Data Visualizer",
        description="Analyzes consolidated sales performance data and generates premium, animated interactive charts.",
        tags=["Sales", "A2UI"],
        examples=[
            "Show me total sales by product line in a bar graph.",
            "Show top 5 states by sales in a pie chart.",
        ],
    )

    visualizer_card = create_agent_card(
        agent_name="Sales Data Visualizer Agent",
        description="Analyzes consolidated sales performance data and generates premium, animated interactive charts.",
        skills=[visualizer_skill],
    )
    
    # Print the JSON agent card for registration
    print(f"JSON_AGENT_CARD_START{json.dumps(visualizer_card, default=lambda o: o.__dict__)}JSON_AGENT_CARD_END")
    print("✓ Agent card created.")
    
    # Import the local executor module
    import agent_executor
    
    # 2. Instantiate A2aAgent
    a2a_agent = A2aAgent(
        agent_card=visualizer_card,
        agent_executor_builder=agent_executor.AdkAgentToA2AExecutor,
    )
    print("✓ Local A2aAgent created.")

    # 3. Instantiate Vertex Client for Creation
    client = vertexai.Client(
        project=project_id,
        location=location,
        http_options=types.HttpOptions(
            api_version="v1beta1",
        ),
    )
    print("✓ Vertex AI client created.")

    # 4. Define deployment configuration
    config = {
        "display_name": "Sales Data Visualizer A2A",
        "description": "Sales Data Visualizer with A2UI and A2A Golden Template.",
        "agent_framework": "google-adk",
        "staging_bucket": staging_bucket,
        "requirements": [
            "google-adk==1.28.1",
            "google-cloud-aiplatform[agent_engines,adk]==1.143.0",
            "a2a-sdk==0.3.22",
            "pydantic==2.12.5",
            "cloudpickle==3.1.2",
            "protobuf==6.33.6",
            "jsonschema==4.26.0",
            "a2ui-agent-sdk",
            "cloud-sql-python-connector[pg8000]",
            "pg8000",
            "sqlalchemy",
            "python-dotenv",
        ],
        "http_options": {
            "api_version": "v1beta1",
        },
        "max_instances": 1,
        "extra_packages": [
            "agent_executor.py",
            "a2ui_schema.py",
            "agent.py",
            "tools.py",
        ],
        "env_vars": {
            "NUM_WORKERS": "1",
            "GOOGLE_GENAI_USE_VERTEXAI": "True",
            "CHART_SERVICE_URL": "https://chart-service-121968733869.us-central1.run.app",
            "DB_CONNECTION_NAME": "agentspace-demo-1145-b:us-central1:adk-db-3a972f08",
            "DB_USER": "sales_agent",
            "DB_PASSWORD": "1A$bLPsC3yYb*yK=",
            "DB_NAME": "sales_consolidator_db",
        },
    }

    print("Deploying A2A Agent inplace update to Vertex AI Agent Engine...")
    remote_agent = client.agent_engines.update(
        name="projects/121968733869/locations/us-central1/reasoningEngines/5864168850685165568",
        agent=a2a_agent, 
        config=config
    )
    print(f"✓ A2A Agent inplace update completed successfully!")
    print(f"Reasoning Engine Resource ID: {remote_agent.api_resource.name if hasattr(remote_agent, 'api_resource') else remote_agent}")

if __name__ == "__main__":
    deploy()
