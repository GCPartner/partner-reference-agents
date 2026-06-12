import sys
import google.cloud.aiplatform as aiplatform
from vertexai.preview.reasoning_engines import ReasoningEngine

PROJECT_ID = "partner-engg-agents"
LOCATION = "us-central1"
ENGINE_ID = "projects/partner-engg-agents/locations/us-central1/reasoningEngines/7299708824095555584"

print("Initializing AI Platform...")
aiplatform.init(project=PROJECT_ID, location=LOCATION)

print("Loading reasoning engine...")
engine = ReasoningEngine(ENGINE_ID)

print("Sending test query...")
try:
    # A2aAgent expects an A2A message format (e.g. methods like query, etc. are routed to execute)
    # But wait! A2aAgent query signature takes `request` payload
    response = engine.query(
        request={
            "message": {
                "text": "hi"
            }
        }
    )
    print("Response received successfully:")
    print(response)
except Exception as e:
    print("Remote execution failed with exception:")
    print(e)
