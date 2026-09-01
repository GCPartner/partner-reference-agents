"""A2A ASGI server for App in Iframe A2UI agent."""

import logging
import os
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentCapabilities, AgentSkill

try:
    from .agent_executor import AdkAgentToA2AExecutor
except ImportError:
    from agent_executor import AdkAgentToA2AExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build_agent_card(base_url: str) -> AgentCard:
    """Build the A2A agent card with A2UI extension."""
    skill = AgentSkill(
        id="app_in_iframe",
        name="App in Iframe A2UI",
        description="Prompts for application URLs and renders them within in-line A2UI iframes.",
        tags=["Iframe", "A2UI", "Web"],
        examples=[
            "Embed an application",
            "Show me https://cloud.google.com",
        ],
    )

    return AgentCard(
        name="App in Iframe A2UI",
        description="Assistant for embedding and viewing web applications inside interactive A2UI iframes.",
        url=base_url,
        version="1.0.0",
        protocolVersion="0.3.0",
        defaultInputModes=["text/plain"],
        defaultOutputModes=["application/json"],
        capabilities=AgentCapabilities(
            streaming=False,
            extensions=[{
                "uri": "https://a2ui.org/a2a-extension/a2ui/v0.9",
                "description": "Ability to render A2UI",
                "required": False,
                "params": {
                    "supportedCatalogIds": [
                        "https://www.gstatic.com/vertexaisearch/a2ui/v0_9/gemini_enterprise_composite_catalog.json"
                    ]
                },
            }],
        ),
        skills=[skill],
    )


def create_app():
    """Create the Starlette ASGI application with root and namespaced routes."""
    base_url = os.environ.get("SERVICE_URL", "http://localhost:8080")
    
    agent_card = build_agent_card(base_url)
    executor = AdkAgentToA2AExecutor()
    task_store = InMemoryTaskStore()
    handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=task_store,
    )

    a2a_app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=handler,
    ).build()

    async def health_check(request):
        return JSONResponse({"status": "ok", "service": "app_in_iframe_a2ui"})

    main_app = Starlette(
        routes=[
            Route("/healthz", health_check, methods=["GET"]),
            Route("/health", health_check, methods=["GET"]),
            Mount("/a2a/app_in_iframe_a2ui", a2a_app),
            Mount("/", a2a_app),
        ]
    )
    return main_app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    logger.info("Starting App in Iframe A2UI server on port %d", port)
    uvicorn.run(app, host="0.0.0.0", port=port)
