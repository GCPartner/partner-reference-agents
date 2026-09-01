import json

agent_card = {
    "capabilities": {
        "extensions": [
            {
                "uri": "https://a2ui.org/a2a-extension/a2ui/v0.9",
                "description": "Ability to render A2UI",
                "required": False,
                "params": {
                    "supportedCatalogIds": [
                        "https://www.gstatic.com/vertexaisearch/a2ui/v0_9/gemini_enterprise_composite_catalog.json"
                    ]
                }
            }
        ],
        "streaming": False
    },
    "defaultInputModes": ["text/plain"],
    "defaultOutputModes": ["application/json"],
    "description": "Assistant for embedding and viewing web applications inside interactive A2UI iframes.",
    "name": "App in Iframe A2UI",
    "preferredTransport": "JSONRPC",
    "protocolVersion": "0.3.0",
    "skills": [
        {
            "description": "Prompts for application URLs and renders them within in-line A2UI iframes.",
            "examples": ["Embed an application", "Show me https://cloud.google.com"],
            "id": "app_in_iframe",
            "name": "App in Iframe A2UI",
            "tags": ["Iframe", "A2UI", "Web"]
        }
    ],
    "supportsAuthenticatedExtendedCard": True,
    "url": "https://app-in-iframe-a2ui-kgyhlndeoq-uc.a.run.app/a2a/app_in_iframe_a2ui",
    "version": "1.0.0"
}

payload = {
    "displayName": "App in Iframe",
    "description": "Embeds and displays web applications inside interactive in-line A2UI iframes.",
    "a2aAgentDefinition": {
        "jsonAgentCard": json.dumps(agent_card)
    },
    "authorizationConfig": {
        "agentAuthorization": "projects/121968733869/locations/global/authorizations/app-in-iframe-auth"
    },
    "sharingConfig": {
        "scope": "ALL_USERS"
    }
}

with open("/usr/local/google/home/veermuchandi/code/agents/rad-workshop/app_in_iframe_a2ui/registration_payload.json", "w") as f:
    json.dump(payload, f, indent=2)

print("Generated registration_payload.json successfully.")
