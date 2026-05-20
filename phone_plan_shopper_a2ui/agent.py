import os
import json
from google.adk.agents import LlmAgent
import tools as platform_tools
import a2ui_tools

def get_instructions() -> str:
    """Constructs the full prompt for the agent."""
    
    return f"""
    You are the PhonePlanConcierge. Your goal is to help users shop for plans and devices.

    **MANDATORY RULES:**
    1. You MUST NOT generate A2UI JSON manually.
    2. You MUST call the appropriate tool to generate UI.
    3. You MUST output the exact string returned by the UI tools.

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
    model="gemini-2.5-flash",
    instruction=get_instructions(),
    tools=[
        a2ui_tools.search_plans_and_show_ui, 
        a2ui_tools.search_devices_and_show_ui, 
        platform_tools.calculate_total, 
        platform_tools.request_manager_discount, 
        platform_tools.create_order, # Re-adding these just in case the helper tools need them or the agent needs to check them, but instructions say to use wrappers.
        a2ui_tools.show_greeting_ui,
        a2ui_tools.show_needs_assessment_ui,
        a2ui_tools.show_order_summary_ui,
        a2ui_tools.show_order_confirmation_ui,
        a2ui_tools.create_order_and_show_ui,
        a2ui_tools.show_discount_request_ui
    ]
)
