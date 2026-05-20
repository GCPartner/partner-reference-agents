# Route Planner Agent Testing Guide

This document outlines the test scenarios for the Route Planner Agent and how to execute them.

## Automated Replay Tests

Replay tests allow for deterministic verification of the agent's conversational flow and tool usage.

### Scenario 1: Capacity Limit & Optimization (Verified)
*   **Goal**: Verify that the agent fits as many customers as possible within the 6-hour limit and skips the rest.
*   **Input**: Start/End at "100 Main St". Mock API provides 10 requests.
*   **Execution**:
    ```bash
    unset GOOGLE_GEMINI_BASE_URL HTTP_PROXY HTTPS_PROXY ALL_PROXY
    adk run route_planner_agent/ --replay route_planner_agent/test_replay.json
    ```
*   **Expected Result**: The agent schedules 5 customers and lists 5 as skipped, totaling under 360 minutes.

### Scenario 2: Different Start and End Locations (Verified)
*   **Goal**: Verify the agent correctly handles the flow when start and end addresses are different.
*   **Input**: Start at "100 Main St", End at "1000 Main St".
*   **Execution**:
    ```bash
    unset GOOGLE_GEMINI_BASE_URL HTTP_PROXY HTTPS_PROXY ALL_PROXY
    adk run route_planner_agent/ --replay route_planner_agent/test_replay_diff.json
    ```
*   **Result**: The agent successfully recognized the different addresses, calculated the route including the longer return trip to the end location, and scheduled 5 customers within 345 minutes.

## Manual Test Scenarios

To test interactively via the terminal:
```bash
unset GOOGLE_GEMINI_BASE_URL HTTP_PROXY HTTPS_PROXY ALL_PROXY
adk run route_planner_agent/
```

### Scenario 3: Invalid Input Handling
*   **Prompt**: "Plan my route"
*   **Inputs**: Provide a gibberish address like "xyz123".
*   **Expected Behavior**: The agent should ask for clarification or handle the failure gracefully.
