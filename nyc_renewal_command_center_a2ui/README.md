# NYC Renewal Command Center — Guided 4-MCP A2UI v0.9 Canvas Skill (`nyc-renewal-command-center-a2ui`)

Enhances the `nyc-renewal-command-center` workflow in Gemini Enterprise (`Sobi`) into a **guided, minimalistic, multi-form-factor A2UI v0.9 Canvas page** (`surfaceId: "nyc_renewal_command_center"`) orchestrating **Salesforce CRM**, **Smartsheet**, **Dun & Bradstreet (D&B)**, and **Atlassian Rovo Jira**.

## Folder Contents

- `nyc_renewal_a2ui_skill/SKILL.md` — Self-contained Gemini Sobi Skill Agent definition with `a2ui_action` router and embedded CLI payload.
- `nyc_renewal_a2ui_skill/scripts/nyc_renewal_a2ui_cli.py` — Pure-stdlib 4-MCP orchestrator and A2UI v0.9 `Canvas` + `IFrameSrcdoc` synthesizer.
- `nyc_renewal_a2ui_skill.zip` — Distributable Skill archive (`SKILL.md` + `scripts/nyc_renewal_a2ui_cli.py`).
- `package_skill.py` — Standalone Python 3 stdlib packager that compresses and embeds `nyc_renewal_a2ui_cli.py` into `SKILL.md` and builds `nyc_renewal_a2ui_skill.zip`.
- `deploy_skill.py` — Standalone Gemini Enterprise Skill deployer & MCP `dataConnector` auto-binder (reads `.env` or CLI flags).
- `design/` — Approved UX architecture document (`nyc_renewal_a2ui_ux_design.md`) and phase wireframes.

## Key UX & Architectural Highlights

1. **Guided 4-Phase Journey on One Continuous Canvas Tab (`surfaceId: "nyc_renewal_command_center"`):**
   - **Phase 1 — Scope Renewals (`scope`):** Search and multi-select `1..N` upcoming renewal accounts across Salesforce Renewal Opportunities and Smartsheet `Customer Health` (`Select All` / `Clear` + live selection pill bar).
   - **Phase 2 — Two-Stage 360° Health Evidence (`analyze` -> on-demand `enrich`):**
     - **Stage 2a:** Fetches **Salesforce CRM** + **Smartsheet** internal health first across all selected companies and evaluates the deterministic `Red` / `Yellow` / `Green` rubric + Pre-Call Coaching (`3 Things to Raise` / `2 Things to Avoid`).
     - **Stage 2b (On Demand):** Hydrates **Dun & Bradstreet** (`MatchTool` -> `RiskTool` + `NewsTool`) and **Atlassian Rovo Jira** (`searchJiraIssuesUsingJql`) on demand (`Fetch D&B + Jira Signals →`, `Fetch D&B Risk & News`, `Fetch Jira Escalations`) to conserve D&B RUM and Rovo credits.
   - **Phase 3 — Granular Per-System Approvals (`stage-sync`):** Per-company, per-MCP checkboxes with official brand logos, inline editable Jira summaries and Salesforce talking points, optional unchecked Jira opt-in for `Green` renewals, and Confirmation Modal (Web/Tablet) or Thumb-Zone Bottom Sheet (Phone).
   - **Phase 4 — Verified Sync Receipts & Live-Call View (`execute-sync --execute`):** Executes approved writes in strict dependency order (`1. Jira` -> `2. Smartsheet` -> `3. Salesforce`), renders clickable verbatim deep-link chips (`↗` opening external tabs only when clicked), and keeps Talking Points + collapsible 4-MCP evidence on the same scrollable page.
2. **Multi-Form-Factor & Security Hardening:**
   - Responsive across Web Desktop, `640px` Split-Screen/Tablet (`autoFullscreen: false`), and `320px–580px` Mobile (`44px` tap targets, `16px` anti-zoom inputs, zero horizontal scroll).
   - `SafeContentFrame`-compatible CSP (`connect-src 'none'`), 7-bit ASCII JSON serialization, 100% pure-DOM rendering (zero `innerHTML`), `document.createElementNS` inline SVG brand logos, SOQL/JQL escaping, and 64-bit string-safe Smartsheet IDs.

## Packaging & Deployment

```bash
# 1. Embed CLI payload & build nyc_renewal_a2ui_skill.zip
python3 nyc_renewal_command_center_a2ui/package_skill.py

# 2. Configure target GCP project (or pass CLI flags directly)
cp nyc_renewal_command_center_a2ui/.env.example nyc_renewal_command_center_a2ui/.env

# 3. Deploy (or patch in-place) in Gemini Enterprise & optionally mount onto Sobi agent(s)
python3 nyc_renewal_command_center_a2ui/deploy_skill.py \
  --project-number "<YOUR_PROJECT_NUMBER>" \
  --engine-id "<YOUR_ENGINE_ID>" \
  --sobi-agent-ids "<OPTIONAL_SOBI_AGENT_ID>"
```
