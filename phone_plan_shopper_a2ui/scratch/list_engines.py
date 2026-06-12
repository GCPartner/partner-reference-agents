import os
import vertexai
from dotenv import load_dotenv

def list_engines():
    load_dotenv()
    project_id = os.environ.get("PROJECT_ID")
    location = os.environ.get("LOCATION") or "us-central1"
    storage = os.environ.get("STORAGE_BUCKET")
    
    vertexai.init(project=project_id, location=location, staging_bucket=storage)
    
    from google.genai import types
    client = vertexai.Client(
        project=project_id,
        location=location,
        http_options=types.HttpOptions(api_version="v1beta1"),
    )
    
    # client.agent_engines.list() might not exist in the new SDK or it might be different!
    # Let's try to use the traditional vertexai.preview.reasoning_engines.ReasoningEngine.list()
    from vertexai.preview.reasoning_engines import ReasoningEngine
    
    engines = ReasoningEngine.list()
    for engine in engines:
        print(f"ID: {engine.name}, Display Name: {engine.display_name}")

if __name__ == "__main__":
    list_engines()
