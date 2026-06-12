import os
import json
import google.cloud.aiplatform as aiplatform
from vertexai.preview.reasoning_engines import A2aAgent
from a2a.types import AgentCard
import agent_executor

# Initialize Vertex AI to prevent project resolution failures
project_id = os.environ.get("PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
if project_id:
    aiplatform.init(project=project_id)
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id

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
