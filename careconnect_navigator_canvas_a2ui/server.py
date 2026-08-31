"""A2A server for CareConnect Navigator — runs on Cloud Run."""

import logging
import os

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentCapabilities, AgentSkill
from agent_executor import AdkAgentToA2AExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build_agent_card(base_url: str) -> AgentCard:
    """Build the A2A agent card with A2UI extension."""
    skill = AgentSkill(
        id="careconnect_navigator_a2ui",
        name="CareConnect Navigator A2UI",
        description="Helpful assistant for finding doctors and booking appointments in Atlanta.",
        tags=["Healthcare", "Booking"],
        examples=[
            "Find a physical therapist near 30303",
        ],
    )

    return AgentCard(
        name="CareConnect Navigator Canvas A2UI",
        description="Helpful assistant for finding doctors and booking appointments in Atlanta using canvas-based A2UI v0.9.",
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
    """Create the Starlette ASGI application."""
    base_url = os.environ.get("SERVICE_URL", "http://localhost:8080")
    
    agent_card = build_agent_card(base_url)
    logger.info("Agent card URL: %s", agent_card.url)

    executor = AdkAgentToA2AExecutor()
    task_store = InMemoryTaskStore()
    handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=task_store,
    )

    app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=handler,
    )
    return app.build()


app = create_app()

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
