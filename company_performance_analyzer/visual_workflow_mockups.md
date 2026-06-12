# Visual Workflow Mockups: Company Performance Analyzer

This walkthrough outlines the complete, step-by-step visual workflow of the **Company Performance Analyzer** A2UI agent. It demonstrates the transition from a text-only interface to a fully interactive split-screen dashboard.

---

````carousel
### Step 1: Welcome & Pre-Upload State
When the user first opens the console, the visual surface on the right remains empty, prompting the user to upload a performance spreadsheet in the chat.

![Welcome State](/usr/local/google/home/veermuchandi/code/agents/rad-workshop/company_performance_analyzer/mockups/welcome_state_mockup_1781194646976.png)

<!-- slide -->

### Step 2: CSV Upload & Interactive Schema Mapping
Upon uploading the CSV file, the agent uses heuristics to map the column headers. Instead of text confirmation in chat, the Right Panel displays an interactive **CSV Column Schema Mapping** form containing three dropdown selectors and a **Confirm Schema** button. This lets the user inspect and adjust column matches easily.

![Schema Confirmation Form](/usr/local/google/home/veermuchandi/code/agents/rad-workshop/company_performance_analyzer/mockups/schema_confirmation_wireframe_1781194398918.png)

<!-- slide -->

### Step 3: Schema Confirmed & Chart Selection Toggles
Once confirmed, the visual surface updates to show a set of three interactive choice cards (**Pie Chart**, **Bar Chart**, and **Breakdown Table**), allowing the user to select their desired visualization directly from the visual surface.

![Chart Selection Toggles](/usr/local/google/home/veermuchandi/code/agents/rad-workshop/company_performance_analyzer/mockups/chart_selection_mockup_1781194658893.png)

<!-- slide -->

### Step 4: Active Visualization (Rizz Chart)
Selecting a visualization renders the interactive Chart.js graphic in a sandboxed iframe. Layout buttons are displayed at the top, allowing the user to toggle between views (Bar Chart, Pie Chart, or Breakdown) instantly on the visual surface.

![Pie Chart Rendered](/usr/local/google/home/veermuchandi/code/agents/rad-workshop/company_performance_analyzer/mockups/pie_chart_rendered_mockup_1781194673294.png)
````

---

## 4. Key UX Principles Implemented:
1. **Zero-Text Action confirmations**: Selecting column configurations, chart preferences, and layout switches are fully managed via A2UI visual selectors (MultipleChoice dropdowns, Buttons, and Cards).
2. **Synchronized Layouts**: Toggles on the visual surface automatically communicate with the session context on the backend, updating the visualization without bloating the conversational log.
3. **Interactive Slices (Drill-Down)**: Clicking any state bar or slice in the Chart.js visualizer automatically filters the data and updates the chart to show service-line performance in that state.
