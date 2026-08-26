import os
import json
import vertexai
from dotenv import load_dotenv

load_dotenv()

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    folder_name = os.path.basename(current_dir)
    
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("PROJECT_ID")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION") or "us-central1"
    storage = os.environ.get("STORAGE_BUCKET") or f"gs://careconnect-nav-canvas-assets-{project_id}"
    existing_engine_id = os.environ.get("EXISTING_ENGINE_ID") or os.environ.get("REASONING_ENGINE_ID")

    print(f"Initializing Vertex AI with project={project_id}, location={location}, bucket={storage}")
    vertexai.init(project=project_id, location=location, staging_bucket=storage)
    client = vertexai.Client(project=project_id, location=location)

    payload_path = os.path.join(current_dir, "registration_payload.json")
    with open(payload_path, "r") as f:
        payload = json.load(f)
        agent_card_json = payload["a2aAgentDefinition"]["jsonAgentCard"]

    class_methods = [
        {
            "name": "on_message_send",
            "api_mode": "a2a_extension",
            "a2a_agent_card": agent_card_json,
            "parameters": {"type": "object", "properties": {}, "required": ["request", "context"]},
        },
        {
            "name": "on_get_task",
            "api_mode": "a2a_extension",
            "a2a_agent_card": agent_card_json,
            "parameters": {"type": "object", "properties": {}, "required": ["request", "context"]},
        },
        {
            "name": "on_cancel_task",
            "api_mode": "a2a_extension",
            "a2a_agent_card": agent_card_json,
            "parameters": {"type": "object", "properties": {}, "required": ["request", "context"]},
        },
        {
            "name": "handle_authenticated_agent_card",
            "api_mode": "a2a_extension",
            "a2a_agent_card": agent_card_json,
            "parameters": {"type": "object", "properties": {}, "required": ["request", "context"]},
        },
    ]

    # Change working directory to parent_dir for clean source packaging
    os.chdir(parent_dir)

    source_files = [
        os.path.join(folder_name, "__init__.py"),
        os.path.join(folder_name, "agent_wrapper.py"),
        os.path.join(folder_name, "agent_executor.py"),
        os.path.join(folder_name, "agent.py"),
        os.path.join(folder_name, "tools.py"),
        os.path.join(folder_name, "ui_renderer.py"),
        os.path.join(folder_name, "a2ui_utils.py"),
        os.path.join(folder_name, "a2ui_schema.json"),
        os.path.join(folder_name, "composite_catalog_v0_9.json"),
        os.path.join(folder_name, "common_types_v0_9.json"),
        os.path.join(folder_name, "server_to_client_v0_9.json"),
        os.path.join(folder_name, "registration_payload.json"),
        os.path.join(folder_name, "agent_card.json"),
        os.path.join(folder_name, "requirements.txt"),
    ]
    # Filter only existing files
    source_files = [f for f in source_files if os.path.exists(f)]

    config = {
        "display_name": "CareConnect Navigator Canvas A2UI",
        "agent_framework": "google-adk",
        "source_packages": source_files,
        "entrypoint_module": f"{folder_name}.agent_wrapper",
        "entrypoint_object": "agent",
        "requirements_file": f"{folder_name}/requirements.txt",
        "class_methods": class_methods,
        "env_vars": {
            "PROJECT_ID": project_id,
            "LOCATION": location,
            "GOOGLE_GENAI_USE_VERTEXAI": "1",
            "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true",
            "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "true",
            "NUM_WORKERS": "1",
        },
    }

    if existing_engine_id:
        engine_name = f"projects/{project_id}/locations/{location}/reasoningEngines/{existing_engine_id}"
        print(f"Applying inplace update to: {existing_engine_id} ({engine_name})")
        remote_agent = client.agent_engines.update(name=engine_name, config=config)
    else:
        print("Spinning up fresh create instance...")
        remote_agent = client.agent_engines.create(config=config)

    print(f"✓ Deployment complete: {existing_engine_id or remote_agent}")

if __name__ == "__main__":
    main()
