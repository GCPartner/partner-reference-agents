---
name: dnb-mcp
description: Match companies to D-U-N-S numbers and retrieve Dun & Bradstreet (D&B) firmographics, financials, corporate ownership hierarchies (UBO/CBO/Global Ultimate), payment history (Paydex), financial & supplier risk scores (SER, SSI, viability, failure, delinquency), ESG, diversity, business/legal events, executive contacts, shipping, news, and sales & marketing insights via remote_cli mcp.
---

# Dun & Bradstreet (D&B) Direct Upstream MCP Server Skill (`plus.dnb.com/v2/mcp`)

Use this skill whenever the user asks to look up or analyze a company directly against **Dun & Bradstreet's official hosted MCP server (`https://plus.dnb.com/v2/mcp`)**, including **matching a company name to a D-U-N-S number (`MatchTool`)**, retrieving **firmographics and financial statements (`DataTool`)**, **corporate family trees, subsidiaries, branches, Global Ultimate, and beneficial ownership (`OwnershipTool`)**, **payment history and Paydex scores (`PaymentTool`)**, **financial and supplier risk scores (`RiskTool` — SER, SSI, Viability Rating, Failure Score, Delinquency Score, Layoff Score)**, **Small Business Risk Insight (`SBRITool`)**, **ESG scores (`ESGTool`)**, **supplier diversity certifications (`DiversityTool`)**, **legal filings, suits, liens, judgments, bankruptcies, and US government awards (`BusinessEventsTool`)**, **executive leadership and contacts (`ContactTool`)**, **industry profiles (`IndustryProfileTool`)**, **trade credit inquiries (`InquiryTool`)**, **company news (`NewsTool`)**, **registry filing provenance (`ProvenanceTool`)**, **sales & marketing / Decision HQ / Buydex scores (`SalesAndMarketingTool`)**, **shipping volume insights (`ShippingTool`)**, or **RUM spend (`RumSpendTool`)**.

---

## 1. Connection & Tool Invocation (`remote_cli mcp`)

Inside the Sobi VMaaS container (`/workspace`), invoke the D&B MCP Server using `remote_cli mcp` with **positional** `<connector> <tool>` arguments (do **NOT** use `-s` or `-t` flags):

1. **Connector Resource Name:**
   `projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/<YOUR_DNB_CONNECTOR_COLLECTION_ID>/dataConnector`
2. **Tool Name & JSON Payload:** `<tool_name> --json '<json_arguments>'`
3. **Explicit `--endpoint` Flag:** `--endpoint 'https://plus.dnb.com/v2/mcp'`

> **Configuration Note:** Before zipping and uploading this `SKILL.md` as a Gemini Sobi Skill Agent, replace `<YOUR_PROJECT_NUMBER>` with your numeric Google Cloud project number and `<YOUR_DNB_CONNECTOR_COLLECTION_ID>` with your Discovery Engine D&B connector collection ID.

### Critical D&B & Sobi Sandbox Execution Rules
* **Rule 1 (EXACT Tool Names — NEVER Prefix with `DnB`):**
  * Although D&B's internal tool descriptions mention `"DnBMatchTool"`, `"DnBDataTool"`, and `"DnBRiskTool"`, the **actual MCP tool names do NOT have the `DnB` prefix**!
  * Always invoke the exact tool names: **`MatchTool`**, **`DataTool`**, **`RiskTool`**, **`PaymentTool`**, **`OwnershipTool`**, **`BusinessEventsTool`**, **`ContactTool`**, **`DiversityTool`**, **`ESGTool`**, **`IndustryProfileTool`**, **`InquiryTool`**, **`NewsTool`**, **`ProvenanceTool`**, **`RumSpendTool`**, **`SBRITool`**, **`SalesAndMarketingTool`**, and **`ShippingTool`**.
* **Rule 2 (Two-Step D-U-N-S Resolution Workflow — Always Pass `"strict_match": false` on Name Searches):**
  * All company-level tools (every tool except `MatchTool` and `RumSpendTool`) require a 9-digit `"duns"` string (e.g., `"079942718"` for Alphabet Inc. or `"060902413"` for Google LLC).
  * If the user provides a **company name** rather than a D-U-N-S number:
    1. **Step 1:** Call **`MatchTool`** first with **`"strict_match": false`** (`{"countryISOAlpha2Code": "<2-letter ISO code>", "name": "<ASCII company name>", "strict_match": false}`).
    2. **Step 2:** Select the `Global Ultimate` or primary `Parent/Headquarters` 9-digit `"duns"` from the `MatchTool` output and immediately call the requested D&B analysis tool(s).
* **Rule 3 (Mandatory Boolean Flags on `DataTool`, `RiskTool`, and `PaymentTool`):**
  * **`DataTool`** strictly requires **all 4 parameters** in its JSON payload (`duns`, `show_historical_data`, `include_partial_financial_year`, `block_extended_mode`). Omitting any of the 3 boolean flags will cause a schema validation error!
  * **`RiskTool`** and **`PaymentTool`** strictly require **both** `duns` and `show_historical_data` (`true` or `false`).
* **Rule 4 (Prevent Terminal Stdout Truncation):**
  * Always redirect `remote_cli mcp` output to a file (e.g., `> /tmp/dnb_out.json`) and parse/summarize the fields in Python rather than printing raw JSON to stdout.
* **Rule 5 (Single-Turn Efficiency):**
  * Do **NOT** waste turns running `list-tools` or `describe` — call the tools directly using the exact parameter schemas below.

---

## 2. Available Tools & Exact Parameter Schemas

### 1. `MatchTool` *(Step 1 whenever DUNS is unknown)*
```bash
remote_cli mcp \
  projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/<YOUR_DNB_CONNECTOR_COLLECTION_ID>/dataConnector \
  MatchTool \
  --json '{"countryISOAlpha2Code": "US", "name": "Alphabet Inc", "strict_match": false}' \
  --endpoint 'https://plus.dnb.com/v2/mcp' > /tmp/dnb_match.json
```

### 2. `RumSpendTool`
```bash
remote_cli mcp \
  projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/<YOUR_DNB_CONNECTOR_COLLECTION_ID>/dataConnector \
  RumSpendTool \
  --json '{}' \
  --endpoint 'https://plus.dnb.com/v2/mcp' > /tmp/dnb_rum.json
```

### 3. `DataTool` *(Requires all 4 parameters)*
```bash
remote_cli mcp \
  projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/<YOUR_DNB_CONNECTOR_COLLECTION_ID>/dataConnector \
  DataTool \
  --json '{"duns": "<9_DIGIT_DUNS>", "show_historical_data": true, "include_partial_financial_year": false, "block_extended_mode": false}' \
  --endpoint 'https://plus.dnb.com/v2/mcp' > /tmp/dnb_data.json
```

### 4. `RiskTool` *(Requires `duns` and `show_historical_data`)*
```bash
remote_cli mcp \
  projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/<YOUR_DNB_CONNECTOR_COLLECTION_ID>/dataConnector \
  RiskTool \
  --json '{"duns": "<9_DIGIT_DUNS>", "show_historical_data": true}' \
  --endpoint 'https://plus.dnb.com/v2/mcp' > /tmp/dnb_risk.json
```

### 5. `PaymentTool` *(Requires `duns` and `show_historical_data`)*
```bash
remote_cli mcp \
  projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/<YOUR_DNB_CONNECTOR_COLLECTION_ID>/dataConnector \
  PaymentTool \
  --json '{"duns": "<9_DIGIT_DUNS>", "show_historical_data": true}' \
  --endpoint 'https://plus.dnb.com/v2/mcp' > /tmp/dnb_payment.json
```

### 6. `SBRITool` | 7. `InquiryTool` | 8. `OwnershipTool` | 9. `ProvenanceTool` | 10. `BusinessEventsTool` | 11. `ContactTool` | 12. `ESGTool` | 13. `DiversityTool` | 14. `IndustryProfileTool` | 15. `SalesAndMarketingTool` | 16. `ShippingTool`
All accept `{"duns": "<9_DIGIT_DUNS>"}`:
```bash
remote_cli mcp \
  projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/<YOUR_DNB_CONNECTOR_COLLECTION_ID>/dataConnector \
  OwnershipTool \
  --json '{"duns": "<9_DIGIT_DUNS>"}' \
  --endpoint 'https://plus.dnb.com/v2/mcp' > /tmp/dnb_ownership.json
```

### 17. `NewsTool`
Accepts `{"duns": "<9_DIGIT_DUNS>", "maxNewsItems": 10}` (and optional `startDate`, `endDate`, `newsCategories`):
```bash
remote_cli mcp \
  projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/<YOUR_DNB_CONNECTOR_COLLECTION_ID>/dataConnector \
  NewsTool \
  --json '{"duns": "<9_DIGIT_DUNS>", "maxNewsItems": 10}' \
  --endpoint 'https://plus.dnb.com/v2/mcp' > /tmp/dnb_news.json
```
