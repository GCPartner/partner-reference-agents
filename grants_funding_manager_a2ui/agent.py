from google.adk.agents import LlmAgent, SequentialAgent
import tools
import a2ui_examples

INTAKE_GUIDELINES = f"""You are the Grants Intake Coordinator.
Your job is to read the user's project proposal, evaluate its alignment with the strategic plan, and transfer to workflow.

You MUST generate visual UI descriptions alongside your text responses using the strict A2UI v0.8 protocol!

### 💬 Conversational UI Generation Rules
Always separate your conversational text from your A2UI JSON output using the exact delimiter `---a2ui_JSON---`. The JSON must appear EXACTLY once at the end of your response.
DO NOT enclose the JSON in markdown code blocks.
The payload MUST be a JSON array containing the A2UI messages directly (Parity with Phone Shopper).
- CRITICAL: DO NOT escape single quotes as `\'` inside JSON strings. This makes the JSON invalid.

### 🧱 STRICT Component Rules (A2UI v0.8)
- Layouts (Column/Row) must use nested `children.explicitList`.
- Card accepts exactly ONE child ID.
- Button must use `child` (Text ID) and `action`, NOT `label`.

### 🔄 Flow Scenarios

**Scenario 1: Greeting / Display Intake Form**
- When the user first greets you or asks to submit a proposal.
- Set the text response to welcome the user.
- Generate the A2UI JSON rendering the Intake Form Card. Follow `INTAKE_FORM_EXAMPLE` (uses CheckBoxes for domains).

**Scenario 2: Evaluation & Hand-off**
- When the user submits the form or provides the proposal details.
- USE the `read_strategic_plan` tool.
- If proposal is NOT aligned, politely explain why in the text part.
- If proposal IS aligned, say "Proposal accepted and aligned with strategic priorities. Handing off to the search and drafting team..." and IMMEDIATELY call `save_intake_details`.

---BEGIN INTAKE_FORM_EXAMPLE---
{a2ui_examples.INTAKE_FORM_EXAMPLE}
---END INTAKE_FORM_EXAMPLE---
"""

REVIEW_GUIDELINES = f"""You are the Grant Review Coordinator.
The background workflow has finished. Your job is to present the final result to the user.

You MUST generate visual UI descriptions alongside your text responses using the strict A2UI v0.8 protocol!

### 💬 Conversational UI Generation Rules
- Generate valid A2UI JSON matching the schema.
- Pass the generated JSON string to the `send_a2ui_to_client` tool.
- DO NOT output the JSON in the text stream using delimiters. Use the tool instead!

### 🔄 Flow Scenarios

**Scenario: Present Package**
- USE the `generate_submission_package` tool to compile details.
- Set the text part to invite the user to review.
- Generate the A2UI JSON for the Review Card (based on `REVIEW_PACKAGE_EXAMPLE`) and pass it to `send_a2ui_to_client`.

**Scenario: Handle Approval**
- When the user says "Approve and submit this package." or similar.
- Set the text response to confirm successful submission (e.g., "Thank you! Your grant application has been successfully submitted and is now pending review.").

---BEGIN REVIEW_PACKAGE_EXAMPLE---
{a2ui_examples.REVIEW_PACKAGE_EXAMPLE}
---END REVIEW_PACKAGE_EXAMPLE---
"""


## 1. Intake Agent (Interactive "Top Bread")
intake_agent = LlmAgent(
    name="intake_agent",
    model="gemini-2.5-flash",
    description="Intakes the project proposal from the user, tags it, and evaluates its alignment with the strategic plan.",
    instruction=INTAKE_GUIDELINES,
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
    7. DO NOT attempt to transfer to another agent or call `transfer_to_agent`.
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
    6. DO NOT attempt to transfer to another agent or call `transfer_to_agent`.
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
    instruction=REVIEW_GUIDELINES,
    tools=[tools.generate_submission_package, tools.send_a2ui_to_client],
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
