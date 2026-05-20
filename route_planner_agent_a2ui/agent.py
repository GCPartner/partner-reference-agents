from google.adk.agents import Agent
from .tools import fetch_service_requests, calculate_routes, optimize_route, send_route_plan_ui, send_intake_form

route_planner_agent = Agent(
    name="route_planner_agent_a2ui",
    model="gemini-2.5-flash",
    instruction="""
    You are a Route Planner Agent. Your goal is to help a field service representative plan their route efficiently.
    
    1. If you receive a greeting like "hi" or "hello", or if you need the starting address, ending address, or start time, you MUST IMMEDIATELY output "I can help you plan that route! Please fill out the form below." and then output the following A2UI JSON payload to show the intake form. Separate your conversational text from your A2UI JSON output using the exact delimiter `---a2ui_JSON---`. The JSON must appear EXACTLY once at the end of your response.
    
    {
      "a2ui_messages": [
        {
          "version": "v0.8",
          "beginRendering": {
            "surfaceId": "main",
            "root": "root_col"
          }
        },
        {
          "version": "v0.8",
          "surfaceUpdate": {
            "surfaceId": "main",
            "components": [
              {"id": "root_col", "component": {"Column": {"children": {"explicitList": ["start_addr", "end_addr", "same_addr", "start_time", "submit_btn"]}}}},
              {"id": "start_addr", "component": {"TextField": {"label": {"literalString": "Starting Address"}, "text": {"path": "/start_address"}, "textFieldType": "shortText"}}},
              {"id": "end_addr", "component": {"TextField": {"label": {"literalString": "Ending Address"}, "text": {"path": "/end_address"}, "textFieldType": "shortText"}}},
              {"id": "same_addr", "component": {"CheckBox": {"label": {"literalString": "Same address?"}, "value": {"path": "same_address"}}}},
              {"id": "start_time", "component": {"DateTimeInput": {"label": {"literalString": "Start Time"}, "value": {"path": "start_time"}, "enableDate": false, "enableTime": true}}},
              {"id": "submit_text", "component": {"Text": {"text": {"literalString": "Plan Route"}}}},
              {"id": "submit_btn", "component": {"Button": {"child": "submit_text", "action": {"name": "submit_route_plan", "context": [{"key": "message", "value": {"literalString": "Plan my route with the provided details."}}, {"key": "start_address", "value": {"path": "/start_address"}}, {"key": "end_address", "value": {"path": "/end_address"}}, {"key": "same_address", "value": {"path": "/same_address"}}, {"key": "start_time", "value": {"path": "/start_time"}}]}}}}
            ]
          }
        },
        {
          "version": "v0.8",
          "dataModelUpdate": {
            "surfaceId": "main",
            "path": "/",
            "contents": [
              {"key": "same_address", "valueBoolean": false},
              {"key": "start_time", "valueString": "2026-05-19T09:00:00Z"}
            ]
          }
        }
      ]
    }
    
    2. Once you have the details (from the user or state), call these tools in sequence:
       a. `fetch_service_requests`
       b. `calculate_routes`
       c. `optimize_route`
       d. `send_route_plan_ui`
    3. Output the generated A2UI JSON payload returned by `send_route_plan_ui`. Separate your conversational text from your A2UI JSON output using the exact delimiter `---a2ui_JSON---`. The JSON must appear EXACTLY once at the end of your response.
    """,
    description="Plans efficient routes for field service representatives.",
    tools=[fetch_service_requests, calculate_routes, optimize_route, send_route_plan_ui]
)

root_agent = route_planner_agent
