import json
from vertexai.preview.reasoning_engines.templates.a2a import create_agent_card
from a2a.types import AgentSkill

agent_skill = AgentSkill(
    id="company_performance_analyzer",
    name="Company Performance Analyzer",
    description="An expert assistant for parsing and dynamically charting annual company performance spreadsheet data using A2UI.",
    tags=["Performance-Analysis", "Charts", "A2UI"],
    examples=[
        "Analyze this company performance data.",
        "Show me a pie chart for the top 5 states.",
    ],
)

analyzer_card = create_agent_card(
    agent_name="Company Performance Analyzer Agent",
    description="An expert assistant for parsing and dynamically charting annual company performance spreadsheet data using A2UI.",
    skills=[agent_skill],
)

def serialize_card(card):
    if isinstance(card, dict):
        return card
    if hasattr(card, "model_dump"):
        return card.model_dump()
    elif hasattr(card, "dict"):
        return card.dict()
    return card.__dict__

card_dict = serialize_card(analyzer_card)
if "skills" in card_dict:
    card_dict["skills"] = [serialize_card(s) for s in card_dict["skills"]]

payload = {
    "a2aAgentDefinition": {
        "jsonAgentCard": json.dumps(card_dict)
    }
}

with open("registration_payload.json", "w") as f:
    json.dump(payload, f, indent=2)
print("✓ registration_payload.json generated successfully.")
