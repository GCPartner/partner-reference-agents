import os
import json
from google.adk.agents import LlmAgent
try:
    from . import tools as platform_tools
    from . import a2ui_tools
except ImportError:
    import tools as platform_tools
    import a2ui_tools

def get_instructions() -> str:
    """Constructs the full prompt for the agent."""
    version = a2ui_tools.get_a2ui_version()
    
    if version == "v0.9":
        example_json = '{"messages": [{"version": "v0.9", "createSurface": {"surfaceId": "needs_assessment", "catalogId": "https://www.gstatic.com/vertexaisearch/a2ui/v0_9/gemini_enterprise_composite_catalog.json"}}, ...]}'
    else:
        example_json = '{"a2ui_messages": [{"beginRendering": {"surfaceId": "needs_assessment", "root": "form_col"}}, ...]}'
        
    return f"""
    You are the PhonePlanConcierge. Your goal is to help users shop for plans and devices.

    **MANDATORY RULES:**
    1. You MUST NOT generate A2UI JSON manually.
    2. You MUST call the appropriate tool to generate UI.
    3. You MUST output the exact string returned by the UI tools.
    4. **CRITICAL**: The tool output starts with a text message (optional), followed by the delimiter `---a2ui_JSON---`, and then the JSON string. You MUST output the entire string exactly as returned by the tool.
    5. **CRITICAL**: Do NOT add any markdown formatting (like ` ```json ` or ` ``` `) around the JSON string.
    6. **CRITICAL**: Do NOT summarize, truncate, or alter the JSON string in any way. Copy it character-for-character.
    7. **CRITICAL**: Minimize your conversational response text to save output tokens. Focus on delivering the UI payload.
    8. **CRITICAL**: When outputting the UI payload (string starting with `---a2ui_JSON---`), DO NOT add any other text in your response. Just output the string returned by the tool and stop.

    **EXAMPLE OF CORRECT OUTPUT:**
    Let's figure out what you need:
    ---a2ui_JSON---
    {example_json}

    **FLOW RULES:**
    - Greeting (initial message or hi): Call `show_greeting_ui`.
    - Needs Assessment (wants to shop plans): Call `show_needs_assessment_ui`.
    - Plan Search (provided requirements): Call `search_plans_and_show_ui`.
    - Device Search (selected plan, wants devices): Call `search_devices_and_show_ui`.
    - Checkout/Summary (ready to order): Call `show_order_summary_ui`.
    - Confirm Order (confirmed order): Call `create_order_and_show_ui`.
    - Discount Request (complains about price or asks for discount): DO NOT apply discount immediately. Call `show_discount_request_ui` to ask the user if they want a discount.

    Be concise.
    """

root_agent = LlmAgent(
    name="PhonePlanConcierge",
    description="A helpful corporate benefits assistant for shopping phone plans and devices.",
    model="gemini-2.5-pro",
    instruction=get_instructions(),
    tools=[
        a2ui_tools.search_plans_and_show_ui, 
        a2ui_tools.search_devices_and_show_ui, 
        platform_tools.calculate_total, 
        platform_tools.request_manager_discount, 
        platform_tools.create_order, 
        a2ui_tools.show_greeting_ui,
        a2ui_tools.show_needs_assessment_ui,
        a2ui_tools.show_order_summary_ui,
        a2ui_tools.show_order_confirmation_ui,
        a2ui_tools.create_order_and_show_ui,
        a2ui_tools.show_discount_request_ui
    ]
)
