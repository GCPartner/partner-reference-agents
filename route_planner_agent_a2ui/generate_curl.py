import json

card = {
  "name": "route_planner_agent",
  "description": "Helps field service reps plan their routes efficiently using A2UI.",
  "url": "https://us-central1-aiplatform.googleapis.com/v1beta1/projects/<YOUR_PROJECT_ID>/locations/us-central1/reasoningEngines/<YOUR_REASONING_ENGINE_ID>/a2a",
  "protocolVersion": "0.3.0",
  "version": "1.0.0",
  "skills": [
    {
      "id": "route_planning",
      "name": "Route Planning",
      "description": "Plan optimized routes for service reps.",
      "tags": ["Route-Planning", "A2UI"],
      "examples": ["Plan my route for today"]
    }
  ],
  "capabilities": {
    "extensions": [
      {
        "uri": "https://a2ui.org/a2a-extension/a2ui/v0.8",
        "description": "Ability to render A2UI",
        "required": False,
        "params": {
          "supportedCatalogIds": ["https://a2ui.org/specification/v0_8/standard_catalog_definition.json"]
        }
      }
    ],
    "streaming": False
  },
  "defaultInputModes": ["text/plain"],
  "defaultOutputModes": ["application/json"],
  "supportsAuthenticatedExtendedCard": True
}

card_str = json.dumps(card)

# Escape double quotes for bash -d argument!
escaped_card_str = card_str.replace('"', '\\"')

project_id = "<YOUR_PROJECT_ID>"
app_id = "<YOUR_APP_ID>"
agent_id = "route_planner_agent"
project_number = "<YOUR_PROJECT_NUMBER>"
auth_id = "route_planner_auth"

curl_cmd = f"""curl -X POST \\
  -H "Authorization: Bearer \\$(gcloud auth print-access-token)" \\
  -H "Content-Type: application/json" \\
  -H "X-Goog-User-Project: {project_id}" \\
  "https://global-discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/collections/default_collection/engines/{app_id}/assistants/default_assistant/agents?agentId={agent_id}" \\
  -d '{{
    "name": "projects/{project_id}/locations/global/collections/default_collection/engines/{app_id}/assistants/default_assistant/agents/{agent_id}",
    "displayName": "Route Planner Agent",
    "description": "Helps field service reps plan their routes efficiently using A2UI.",
    "a2aAgentDefinition": {{
      "jsonAgentCard": "{escaped_card_str}"
    }},
    "authorizationConfig": {{
      "agentAuthorization": "projects/{project_number}/locations/global/authorizations/{auth_id}"
    }}
  }}'"""

print(curl_cmd)
