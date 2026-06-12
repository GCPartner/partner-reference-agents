from google.adk.agents import LlmAgent, SequentialAgent
from . import tools

## 1. Intake Agent (Interactive "Top Bread")
intake_agent = LlmAgent(
    name="intake_agent",
    model="gemini-2.5-flash",
    description="Intakes the project proposal from the user, tags it, and evaluates its alignment with the strategic plan.",
    instruction="""You are the Grants Intake Coordinator. Your job is to:
    1. Read the user's project proposal.
    2. USE the `read_strategic_plan` tool to understand the agency's current priorities.
    3. Evaluate if the proposal aligns with at least one strategic priority.
    
    If the proposal is NOT aligned, politely tell the user why and DO NOT attempt to find grants.
    If the proposal IS aligned, say "Proposal accepted and aligned with strategic priorities. Handing off to the search and drafting team... (Once you say this, IMMEDIATELY call your tool `save_intake_details` and transfer back to your parent orchestrator `Automated_Grants_Manager`.)and end your turn so the workflow can begin.
    
    CRITICAL: You are only the intake coordinator. DO NOT attempt to search for grants, draft applications, or submit them yourself. You DO NOT have tools for these actions.
    
    To help the next agents, USE the `save_intake_details` tool to save the following:
    - `project_summary`: A concise summary of the project.
    - `search_keywords`: A list of 3-5 keywords for Grants.gov.
    - `budget_required`: An integer representing the estimated budget needed (if not provided, default to 1000000).
    - `project_domain`: The general field (e.g., "Public Health", "Cybersecurity").
    """,
    tools=[tools.read_strategic_plan, tools.save_intake_details],
    output_key="intake_summary", 
    disallow_transfer_to_parent=False,
)

## 2. Headless Workflow ("The Meat")
search_agent = LlmAgent(
    name="search_agent",
    model="gemini-2.5-flash",
    description="Searches Grants.gov and selects the single best-fit opportunity.",
    instruction="""You are a Headless Grant Searcher. You operate in the background. DO NOT ask the user questions.
    1. Read the `search_keywords` from the state.
    2. USE the `search_grants_gov` tool.
    3. Evaluate the results based on the `project_summary` in the state.
    4. Select the SINGLE best grant opportunity.
    5. USE the `save_selected_grant` tool to save its details.
    6. Your turn ends immediately after calling `save_selected_grant`. DO NOT output any conversational text.
    """,
    tools=[tools.search_grants_gov, tools.save_selected_grant],
    disallow_transfer_to_parent=False,
    output_key="search_log"
)

drafting_agent = LlmAgent(
    name="drafting_agent",
    model="gemini-2.5-pro", # Pro for better long-form drafting
    description="Gathers financial and HR data to draft the final application.",
    instruction="""You are a Headless Grant Drafter. You operate in the background. DO NOT ask the user questions.
    Your goal is to write a comprehensive first draft of a grant application for the `selected_grant` in the state.
    
    1. USE `fetch_sap_financial_data` using the `budget_required` from state.
    2. USE `fetch_workday_hr_data` using the `project_domain` from state.
    3. Write a 3-paragraph application draft that integrates the project summary, the financial audit status, and the relevant HR KPIs.
    4. USE the `save_application_draft` tool to save the final string draft.
    5. Your turn ends immediately after calling `save_application_draft`. DO NOT output any conversational text.
    """,
    tools=[tools.fetch_sap_financial_data, tools.fetch_workday_hr_data, tools.save_application_draft],
    disallow_transfer_to_parent=False,
    output_key="drafting_log"
)

grants_workflow = SequentialAgent(
    name="grants_workflow",
    description="A headless workflow that searches for and drafts grants sequentially.",
    sub_agents=[search_agent, drafting_agent]
)

## 3. Review Agent (Interactive "Bottom Bread")
review_prep_agent = LlmAgent(
    name="review_prep_agent",
    model="gemini-2.5-flash",
    description="Assembles the final package and interacts with the Grant Manager for sign-off.",
    instruction="""You are the Grant Review Coordinator.
    The background workflow has finished. Your job is to present the final result to the user (the Grant Manager).
    
    1. Read the `selected_grant` and `application_draft` from the state.
    2. USE the `generate_submission_package` tool passing these values.
    3. Present a formal, polite summary to the user. Include:
       - The Grant ID and Title being applied for.
       - A VERY SHORT preview of the draft.
       - The package summary (word count, attachments).
    4. Ask the user if they are ready to approve the submission.
    """,
    tools=[tools.generate_submission_package],
    output_key="review_log"
)

## 4. The Master Orchestrator (The full "Sandwich")
root_agent = LlmAgent(
    name="Automated_Grants_Manager",
    model="gemini-2.5-flash",
    description="Orchestrator for the entire grant lifecycle from intake to draft review.",
    instruction="""You are the master coordinator for the grants process. Your job is to orchestrate the process using your sub-agents:
    1. First, MUST transfer to the `intake_agent` so they can talk to the user and gather project requirements.
    2. Wait until `intake_agent` saves the details to state. Once intake is complete, transfer to `grants_workflow` to search and draft the grant in the background. DO NOT do this step yourself.
    3. Once the workflow is finished and the draft is saved, transfer to `review_prep_agent` to present the final package to the user and ask for approval.
    """,
    sub_agents=[intake_agent, grants_workflow, review_prep_agent]
)
