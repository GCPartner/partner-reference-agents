# Grants Funding Manager - Interactive Testing Guide

This document provides specific scenarios and prompts you can use to test the `grants_funding_manager` agent interactively using the ADK Web UI.

## Initial Setup
**CRITICAL**: Always start the web server from the **parent workspace directory**, not inside the agent folder itself.

```bash
cd /usr/local/google/home/veermuchandi/code/agents/rad-workshop
adk web --port 8080
```
Open your browser to `http://127.0.0.1:8080` and select `grants_funding_manager` from the app launcher to start a new session.

---

## Test Scenarios

### Scenario 1: The Happy Path (High Alignment & Complete Info)
**Goal:** Verify the system effortlessly passes data from the interactive intake agent to the headless workflow, and then surfaces the final result via the review agent.

**Initial Prompt:**
> "We are launching a new smart city initiative focused on utilizing scalable AI infrastructure to process traffic and public health datasets. Our required budget is approximately $1,500,000. Can you help us find a grant and draft the application?"

**Expected Behavior:**
1. **Intake:** The `intake_agent` evaluates the proposal, deems it strategically aligned, and explicitly yields control to the background workflow.
2. **Background Workflow:** The UI enters a waiting state while the `search_agent` finds grants and the `drafting_agent` gathers SAP/Workday data to write the draft.
3. **Review:** After 15-30 seconds, the `review_prep_agent` presents the drafted application package and asks for your final approval.
4. **Conclusion:** You reply with "Approved, please submit it" to complete the sequence.

---

### Scenario 2: The Vague Request (Testing Missing Need Identification)
**Goal:** Verify that the `intake_agent` correctly identifies missing mandatory fields required to start a search and engages the user in a multi-turn conversation before proceeding.

**Initial Prompt:**
> "Our department has a new idea for a community outreach program and we need some grant funding to get it off ground. Can you help?"

**Expected Behavior:**
1. **Clarification:** The `intake_agent` should **not** begin searching. Instead, it should respond by asking for the missing mandatory criteria: the **estimated budget requirement** and more detail on the **specific domain**.
2. **Resolution:** You reply with the missing pieces (e.g., "We need $250,000 and it involves mobile health technology").
3. **Continuation:** Once the criteria are met, the agent validates alignment and triggers the headless workflow as usual.

---

### Scenario 3: Strategic Misalignment (Testing Early Rejection)
**Goal:** Verify that the `intake_agent` successfully utilizes the `read_strategic_plan` tool to filter out projects that fall outside the organization's funding priorities.

**Initial Prompt:**
> "We want to secure a $250,000 grant to build a luxury corporate retreat and a cryptocurrency mining farm in the corporate basement. Please find a grant and draft the application."

**Expected Behavior:**
1. **Evaluation:** The `intake_agent` cross-references the request with the strategic plan.
2. **Rejection:** It determines the project is entirely misaligned with public/organizational priorities.
3. **Termination:** It replies with a polite rejection explaining *why* the project does not fit the strategic goals. The workflow is halted early, saving computation and external API calls.
