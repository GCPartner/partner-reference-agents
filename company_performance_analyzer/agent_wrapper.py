import os
import sys
import json

# Retrieve saved environment parameters stashed by sitecustomize.py
_saved_project_id = None
_saved_location = "us-central1"
try:
    if os.path.exists("/tmp/saved_env.json"):
        with open("/tmp/saved_env.json", "r") as f:
            stashed = json.load(f)
            _saved_project_id = stashed.get("PROJECT_ID")
            _saved_location = stashed.get("LOCATION") or "us-central1"
except Exception as e:
    pass

import google.cloud.aiplatform as aiplatform
from vertexai.preview.reasoning_engines import A2aAgent
from a2a.types import AgentCard
import agent_executor

# Inject saved project parameters into agent_executor module namespace
agent_executor.PROJECT_ID = _saved_project_id
agent_executor.LOCATION = _saved_location

# Initialize Vertex AI with saved variables
if _saved_project_id:
    aiplatform.init(project=_saved_project_id, location=_saved_location)

# Load agent card from registration payload
current_dir = os.path.dirname(os.path.abspath(__file__))
payload_path = os.path.join(current_dir, "registration_payload.json")
with open(payload_path, "r") as f:
    payload = json.load(f)
    card_data = json.loads(payload["a2aAgentDefinition"]["jsonAgentCard"])
    agent_card = AgentCard(**card_data)

agent = A2aAgent(
    agent_card=agent_card,
    agent_executor_builder=agent_executor.AdkAgentToA2AExecutor,
)
