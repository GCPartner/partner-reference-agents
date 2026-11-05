---
name: sec-edgar-mcp-apps
description: Apex Capital Institutional Research SEC EDGAR 360-Degree Financial Statement, DuPont Ratio, 10-K/8-K Filing & Peer XBRL Frame Comparator MCP Apps Server.
---

# SEC EDGAR Financial & 10-K Dossier MCP Apps Skill

Use this skill whenever the user asks for U.S. public company financial statements, 360-degree financial dossiers, interactive Financial Dossier or Peer Industry Comparator workbenches, 10-K / 10-Q / 8-K / DEF 14A SEC filings, XBRL financial metrics, YoY growth rates, profitability/liquidity/leverage ratios, peer group comparisons, or industry-wide SEC XBRL calendar frame rankings.

## Connection & Tool Invocation (`remote_cli mcp`)

Inside the Gemini Sobi VMaaS container (`/workspace`), invoke this MCP server using `remote_cli mcp` with **positional** `<connector> <tool>` arguments (do NOT use `-s` or `-t` flags):
1. **Connector Resource Name:** `projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/sec-edgar-mcp-apps/dataConnector`
2. **Tool Name & JSON Payload:** `<tool_name> --json '<json_arguments>'`
3. **Explicit `--endpoint` Flag:** `--endpoint 'https://<YOUR_CLOUD_RUN_SERVICE_URL>/mcp'`

> **Configuration Note:** Before zipping and uploading this `SKILL.md` as a Gemini Sobi Skill Agent, replace `<YOUR_PROJECT_NUMBER>` with your numeric Google Cloud project number and `<YOUR_CLOUD_RUN_SERVICE_URL>` with your deployed Cloud Run hostname (for example, `sec-edgar-mcp-apps-server-xxxxxx-uc.a.run.app`).

### Critical Sobi Sandbox Execution & `ui://` Rendering Rules
* **Rule 1 (Prevent Terminal Stdout Truncation on Multi-Period JSON):** The Sobi terminal tool truncates stdout previews after ~150 lines. If you print the raw or pretty-printed JSON of a 4- or 5-period dossier/statement directly to stdout, the 4th/5th period will appear cut off in the terminal preview even though the JSON is 100% complete! **Always redirect `remote_cli mcp` output to a file (e.g., `> /tmp/dossier.json` and `> /tmp/statements.json`) and parse/summarize the fields in Python** by iterating over `headline_financials_by_period` or `income_statement` / `balance_sheet` / `cash_flow` / `financial_ratios`.
* **Rule 2 (STRICT PROHIBITION — NEVER Call `google:browse` or Web Search on `sec.gov/*.htm` Filing URLs or External Web Pages):**
  - Raw SEC 10-K/10-Q `.htm` files (`document_url` such as `ibm-20251231.htm`, `tsla-20251231.htm`, `aapl-20250927.htm`) are **15–25 MB Inline XBRL (iXBRL) documents** whose first several megabytes are hidden `<ix:header>` machine context blocks that **will exceed the `google:browse` page size cap**.
  - The `document_url` and `filing_index_url` strings returned by this MCP server are provided **strictly for rendering clickable markdown citation links in your final answer to the user** — **NEVER pass `document_url` or `filing_index_url` to `google:browse`, `curl`, or `python`!**
  - This MCP server already queries the official U.S. SEC EDGAR `submissions` and `companyfacts` XBRL APIs (`data.sec.gov`) directly and returns all 4+ years of harmonized Income Statements, Balance Sheets (`ppe_net`, `total_debt`), Cash Flow Statements (`operating_cash_flow`, `investing_cash_flow`, `financing_cash_flow`, `capex`, `free_cash_flow`), Financial Ratios, `xbrl_tags_used`, and `accounting_structure_notes`.
  - If a company (such as IBM) does not tag a standalone `us-gaap:OperatingIncomeLoss` or `us-gaap:OperatingExpenses` subtotal in its 10-K, the MCP server automatically derives EBIT (`operating_income = pretax_income + interest_expense`), core operating expenses (`r_and_d + sga`), and `total_expense_and_other_net` (`gross_profit - pretax_income`) and documents the exact provenance in `xbrl_tags_used` and `accounting_structure_notes`. **Trust these fields directly — NEVER use `google:browse` or web search to cross-check XBRL tags!** If you ever need to inspect additional raw XBRL tags for a company, use the MCP tools `resolve_and_discover_sec_entities` (with `xbrl_tag_keyword`) or `trace_xbrl_metric_history`.
* **Rule 3 (Single-Turn Efficiency & Top-Level `remote_cli mcp` Execution):** Do NOT waste turns running `list-tools` or `describe`, and **NEVER** wrap `remote_cli mcp` inside a Python `subprocess.run(...)` script (which prevents the host from intercepting `_meta.ui.resourceUri`). Always invoke `remote_cli mcp` directly as a top-level shell command.
* **Rule 4 (MANDATORY `ui://` Auto-Display Protocol — Write Both `/workspace/deliverables/index.html` AND `/workspace/deliverables/sec_<slug>_<timestamp>.html` via Step 2 Python Publisher):**
  - Do **NOT** generate static `.png` or `.jpg` chart images via `matplotlib` or `Pillow`, and **NEVER** call `emit_a2ui` (`Emit a2ui`) on any turn that renders a `ui://` MCP App.
  - **WHY BOTH FILES INSIDE `/workspace/deliverables/` ARE MANDATORY FOR AUTO-OPEN:**
    1. In the Gemini Enterprise UI (`chat_page.ts` $\rightarrow$ `isTaskSandboxDeliverable(path)`), the Canvas auto-open effect **only** opens files inside **`/workspace/deliverables/`** (`/^\/?(workspace\/)?deliverables\//`). Writing `/workspace/index.html` at the workspace root is skipped (`skipped = 'the change is all outside deliverables/'`).
    2. Furthermore, `chat_page.ts` caches `autoOpenedArtifactsKey` across turns and across chat sessions in the same browser tab without resetting on session switch. If a turn only writes `/workspace/deliverables/index.html`, `key === this.autoOpenedArtifactsKey()` matches the previous session and skips auto-opening (`skipped = 'already opened for this change'`).
    3. Therefore, whenever you invoke any SEC EDGAR MCP tool (redirecting output to `> /tmp/sec_app.json`), immediately run the **Step 2 Python Extractor & Auto-Open Deliverable Publisher** below to remove any stray `/workspace/index.html`, extract the 100% self-contained `mcp_app_html` (or fetch `live_preview_url`), and write it directly to **BOTH** `/workspace/deliverables/index.html` AND `/workspace/deliverables/sec_<slug>_<unix_timestamp>.html`!
    4. **DO NOT** call `write_file` on relative path `"index.html"` or `"/workspace/index.html"`, and **NEVER** overwrite `/workspace/deliverables/index.html` with a `"Loading..."` or `fetch()` stub. Include clickable markdown links `[index.html](/workspace/deliverables/index.html)` and `[sec_<slug>_<timestamp>.html](/workspace/deliverables/sec_<slug>_<timestamp>.html)` in your final text response.

### Step 2 Python Extractor & Auto-Open Deliverable Publisher (Run After Every `remote_cli mcp ... > /tmp/sec_app.json`)
```bash
python3 - << 'EOF'
import json, pathlib, re, time, urllib.request

deliverables_dir = pathlib.Path("/workspace/deliverables")
deliverables_dir.mkdir(parents=True, exist_ok=True)
pathlib.Path("/workspace/index.html").unlink(missing_ok=True)

src_file = next((p for p in [pathlib.Path("/tmp/sec_app.json"), pathlib.Path("/tmp/dossier_app.json"), pathlib.Path("/tmp/comparator_app.json"), pathlib.Path("/tmp/dossier.json"), pathlib.Path("/tmp/statements.json")] if p.exists()), None)
raw = src_file.read_text(encoding="utf-8", errors="replace").lstrip() if src_file else "{}"
top, _ = json.JSONDecoder().raw_decode(raw)

html = None
live_url = None
ui_uri = None
payload = {}

def walk(node):
    global html, live_url, ui_uri, payload
    if isinstance(node, dict):
        if isinstance(node.get("ui"), dict) and node["ui"].get("resourceUri"):
            ui_uri = ui_uri or node["ui"]["resourceUri"]
        if node.get("ui/resourceUri"):
            ui_uri = ui_uri or node["ui/resourceUri"]
        if node.get("ui_resource_uri"):
            ui_uri = ui_uri or node["ui_resource_uri"]
        if node.get("live_preview_url"):
            live_url = live_url or node["live_preview_url"]
        if node.get("mcp_app_html") and isinstance(node.get("mcp_app_html"), str):
            html = html or node["mcp_app_html"]
        if node.get("type") == "resource" and isinstance(node.get("resource"), dict):
            res = node["resource"]
            ui_uri = ui_uri or res.get("uri")
            if isinstance(res.get("text"), str) and "<html" in res["text"].lower():
                html = html or res["text"]
        if node.get("type") == "text" and isinstance(node.get("text"), str):
            t = node["text"].lstrip()
            if t.startswith("{"):
                try:
                    inner, _ = json.JSONDecoder().raw_decode(t)
                    walk(inner)
                except Exception:
                    pass
        if ("company" in node or "headline_financials_by_period" in node or "income_statement" in node or "peer_comparison_table" in node or "top_companies" in node) and not payload:
            payload = {k: v for k, v in node.items() if k != "mcp_app_html"}
        for k in ("_meta", "result", "structuredContent", "content", "resource", "mcp_app"):
            if k in node:
                walk(node[k])
    elif isinstance(node, list):
        for item in node:
            walk(item)

walk(top)

if not html and live_url:
    try:
        with urllib.request.urlopen(live_url, timeout=25) as resp:
            fetched = resp.read().decode("utf-8", errors="replace")
            if "<html" in fetched.lower():
                html = fetched
    except Exception as e:
        print("Warning fetching live_preview_url:", e)

comp = payload.get("company") if isinstance(payload.get("company"), dict) else {}
raw_slug = str(comp.get("ticker") or payload.get("identifier") or payload.get("concept") or "sec_edgar_app")
slug = re.sub(r"[^A-Za-z0-9_-]+", "_", raw_slug).strip("_")[:40] or "sec_edgar_app"
ts = int(time.time())
unique_name = f"sec_{slug}_{ts}.html"

if html:
    index_path = deliverables_dir / "index.html"
    unique_path = deliverables_dir / unique_name
    index_path.write_text(html, encoding="utf-8")
    unique_path.write_text(html, encoding="utf-8")
    print("AUTO_OPEN_DELIVERABLE_1:", str(index_path), f"({len(html)} bytes)")
    print("AUTO_OPEN_DELIVERABLE_2:", str(unique_path), f"({len(html)} bytes)")

print("UI_RESOURCE_URI:", ui_uri)
print("LIVE_PREVIEW_URL:", live_url)
print("PAYLOAD_KEYS:", list(payload.keys()))
print(json.dumps(payload, indent=2)[:8000])
EOF
```

---

## Available Tools & Exact Parameter Schemas

### 1. `open_financial_dossier_workbench_app`
Opens the interactive 4-tab **SEC EDGAR Financial Statement & 10-K Dossier Workbench** (`ui://sec-edgar/financial-dossier-workbench`) pre-hydrated with full 360-degree corporate metadata, multi-period Income Statement / Balance Sheet / Cash Flow / DuPont Ratios, XBRL concept history & restatement audit trail, and searchable 10-K / 10-Q / 8-K / DEF 14A filings.
- **Parameters:**
  - `identifier` *(string, required)*: Stock ticker symbol (e.g., `"NVDA"`, `"AAPL"`, `"TSLA"`), company name, or 10-digit CIK.
  - `period_type` *(string, optional, default `"annual"`)*: `"annual"` (10-K full fiscal years) or `"quarterly"` (10-Q single quarters).
  - `periods` *(integer, optional, default `5`)*: Number of fiscal periods to hydrate (`2` to `10`).
```bash
remote_cli mcp \
  projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/sec-edgar-mcp-apps/dataConnector \
  open_financial_dossier_workbench_app \
  --json '{"identifier": "NVDA", "period_type": "annual", "periods": 5}' \
  --endpoint 'https://<YOUR_CLOUD_RUN_SERVICE_URL>/mcp' > /tmp/sec_app.json
```
*(Immediately run the **Step 2 Python Extractor & Auto-Open Deliverable Publisher** above to publish the 100% self-contained Financial Dossier Workbench HTML to `/workspace/deliverables/index.html` and `/workspace/deliverables/sec_<slug>_<timestamp>.html`, include clickable links to both files in your response, and do **NOT** call `emit_a2ui`!)*

### 2. `open_peer_industry_comparator_app`
Opens the interactive 2-tab **SEC EDGAR Peer Group Benchmark & XBRL Calendar Frame Comparator** (`ui://sec-edgar/peer-industry-comparator`) pre-hydrated with side-by-side peer group KPIs, margins, medians/means, and market-wide SEC XBRL calendar frame percentile rankings.
- **Parameters:**
  - `identifiers` *(array of strings, optional, default `["AAPL", "MSFT", "GOOGL", "NVDA"]`)*: List of 2 to 10 peer tickers, names, or CIKs.
  - `period_type` *(string, optional, default `"annual"`)*: `"annual"` or `"quarterly"`.
  - `fiscal_year` *(integer, optional)*: Optional target fiscal year (e.g., `2024` or `2025`).
  - `benchmark_concept` *(string, optional, default `"revenue"`)*: XBRL concept alias (`"revenue"`, `"net_income"`, `"operating_income"`, `"total_assets"`, `"total_cash"`, `"r_and_d"`).
  - `calendar_year` *(integer, optional, default `2024`)*: Calendar year for SEC XBRL Frame ranking.
```bash
remote_cli mcp \
  projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/sec-edgar-mcp-apps/dataConnector \
  open_peer_industry_comparator_app \
  --json '{"identifiers": ["NVDA", "AMD", "AVGO", "INTC"], "period_type": "annual", "benchmark_concept": "revenue", "calendar_year": 2024}' \
  --endpoint 'https://<YOUR_CLOUD_RUN_SERVICE_URL>/mcp' > /tmp/sec_app.json
```
*(Immediately run the **Step 2 Python Extractor & Auto-Open Deliverable Publisher** above to publish the 100% self-contained Peer Industry Comparator HTML to `/workspace/deliverables/index.html` and `/workspace/deliverables/sec_<slug>_<timestamp>.html`, include clickable links to both files in your response, and do **NOT** call `emit_a2ui`!)*

### 3. `get_company_360_financial_dossier`
Generates a comprehensive 360-degree corporate and financial dossier for a U.S. public company in a single call (resolves ticker/name to 10-digit CIK, corporate governance metadata, latest 10-K/10-Q/8-K/DEF 14A direct links, and harmonized multi-period headline financials with YoY growth and margins).
- **Parameters:**
  - `identifier` *(string, required)*: Stock ticker symbol (e.g., `"NVDA"`, `"AAPL"`), company name (e.g., `"NVIDIA"`), or CIK.
  - `period_type` *(string, optional, default `"annual"`)*: `"annual"` (10-K full fiscal years) or `"quarterly"` (10-Q single quarters).
  - `periods` *(integer, optional, default `4`)*: Number of most recent fiscal periods to include (`1` to `10`).
  - `include_recent_filings` *(boolean, optional, default `true`)*: Whether to include direct SEC EDGAR Archive links to latest 10-K, 10-Q, DEF 14A, and 8-Ks.
```bash
remote_cli mcp \
  projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/sec-edgar-mcp-apps/dataConnector \
  get_company_360_financial_dossier \
  --json '{"identifier": "NVDA", "period_type": "annual", "periods": 4}' \
  --endpoint 'https://<YOUR_CLOUD_RUN_SERVICE_URL>/mcp' > /tmp/dossier.json
```

### 4. `analyze_financial_statements_and_ratios`
Performs a structured multi-period financial statement and ratio analysis (Income Statement, Balance Sheet, Cash Flow Statement, and Financial Ratios) with US-GAAP tag harmonization, restatement deduplication, YoY/QoQ growth, and multi-year CAGR.
- **Parameters:**
  - `identifier` *(string, required)*: Company ticker (`"MSFT"`), name (`"Microsoft"`), or CIK.
  - `statement_types` *(array of strings, optional)*: Subset of `["income_statement", "balance_sheet", "cash_flow", "ratios"]` (defaults to all four).
  - `period_type` *(string, optional, default `"annual"`)*: `"annual"` or `"quarterly"`.
  - `periods` *(integer, optional, default `5`)*: Number of historical periods to align side-by-side (`2` to `10`).
```bash
remote_cli mcp \
  projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/sec-edgar-mcp-apps/dataConnector \
  analyze_financial_statements_and_ratios \
  --json '{"identifier": "AAPL", "period_type": "annual", "periods": 4}' \
  --endpoint 'https://<YOUR_CLOUD_RUN_SERVICE_URL>/mcp' > /tmp/statements.json
```

### 5. `search_and_inspect_sec_filings`
Searches and filters a company's SEC EDGAR filing history with enriched 8-K item descriptions and direct clickable SEC Archive URLs (`document_url` and `filing_index_url`).
- **Parameters:**
  - `identifier` *(string, required)*: Company ticker, name, or CIK.
  - `form_types` *(array of strings, optional)*: List of SEC form types (e.g., `["10-K", "10-Q", "8-K", "DEF 14A", "4"]`).
  - `start_date` *(string, optional)*: ISO start date (`"YYYY-MM-DD"`) filter on `filingDate`.
  - `end_date` *(string, optional)*: ISO end date (`"YYYY-MM-DD"`) filter on `filingDate`.
  - `item_8k_filter` *(string, optional)*: Form 8-K item number or keyword filter (e.g., `"2.02"` for Earnings, `"1.05"` for Cybersecurity, `"5.02"` for Officer/Director Changes).
  - `include_amendments` *(boolean, optional, default `true`)*: Whether to include amended filings (`10-K/A`, `10-Q/A`).
  - `limit` *(integer, optional, default `15`)*: Maximum number of matching filings to return (`1` to `50`).
```bash
remote_cli mcp \
  projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/sec-edgar-mcp-apps/dataConnector \
  search_and_inspect_sec_filings \
  --json '{"identifier": "GOOGL", "form_types": ["10-K", "10-Q", "8-K"], "limit": 10}' \
  --endpoint 'https://<YOUR_CLOUD_RUN_SERVICE_URL>/mcp' > /tmp/filings.json
```

### 6. `trace_xbrl_metric_history`
Retrieves the historical time-series, YoY/QoQ progression, CAGR, and restatement audit trail for a specific XBRL concept using the lightweight `companyconcept` endpoint.
- **Parameters:**
  - `identifier` *(string, required)*: Company ticker, name, or CIK.
  - `concept_or_tag` *(string, required)*: Exact XBRL tag (e.g., `"ResearchAndDevelopmentExpense"`, `"Goodwill"`, `"EntityCommonStockSharesOutstanding"`) or canonical alias (`"revenue"`, `"r_and_d"`, `"sbc"`, `"capex"`, `"operating_income"`, `"shares_outstanding"`).
  - `taxonomy` *(string, optional, default `"us-gaap"`)*: `"us-gaap"`, `"dei"`, or `"ifrs-full"`.
  - `period_type` *(string, optional, default `"annual"`)*: `"annual"`, `"quarterly"`, or `"all"`.
  - `periods` *(integer, optional, default `10`)*: Number of historical periods to return (`1` to `25`).
  - `include_restatement_audit` *(boolean, optional, default `false`)*: If `true`, includes prior restated values reported for the same fiscal period across subsequent filings.
```bash
remote_cli mcp \
  projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/sec-edgar-mcp-apps/dataConnector \
  trace_xbrl_metric_history \
  --json '{"identifier": "NVDA", "concept_or_tag": "r_and_d", "period_type": "annual", "periods": 8, "include_restatement_audit": true}' \
  --endpoint 'https://<YOUR_CLOUD_RUN_SERVICE_URL>/mcp' > /tmp/xbrl_history.json
```

### 7. `compare_peer_group_financials`
Benchmarks 2 to 10 public peer companies side-by-side in a single call across standardized financial metrics, growth rates, margins, and peer-group medians/means.
- **Parameters:**
  - `identifiers` *(array of strings, required)*: List of 2 to 10 peer tickers, company names, or CIKs (e.g., `["NVDA", "AMD", "INTC", "AVGO"]`).
  - `metrics` *(array of strings, optional)*: Optional subset of metric keys to highlight.
  - `period_type` *(string, optional, default `"annual"`)*: `"annual"` (latest 10-K) or `"quarterly"` (latest 10-Q).
  - `fiscal_year` *(integer, optional)*: Optional target year (e.g., `2024` or `2025`) to align all peers.
```bash
remote_cli mcp \
  projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/sec-edgar-mcp-apps/dataConnector \
  compare_peer_group_financials \
  --json '{"identifiers": ["NVDA", "GOOGL", "AAPL", "MSFT"], "period_type": "annual"}' \
  --endpoint 'https://<YOUR_CLOUD_RUN_SERVICE_URL>/mcp' > /tmp/peers.json
```

### 8. `benchmark_industry_xbrl_frame`
Queries the SEC Cross-Company XBRL Frames API (`frames/{taxonomy}/{tag}/{unit}/CY{YYYY}[Q{Q}][I]`) to rank all ~4,800+ reporting U.S. public companies, compute market percentiles (`p10` to `p99`), return top leaders, and benchmark a target company's exact rank and percentile.
- **Parameters:**
  - `concept_or_tag` *(string, required)*: Canonical concept (`"revenue"`, `"net_income"`, `"total_assets"`, `"total_cash"`, `"r_and_d"`) or exact XBRL tag (`"Assets"`, `"Revenues"`).
  - `calendar_year` *(integer, optional, default `2024`)*: Standardized calendar year (e.g., `2024` or `2025`).
  - `calendar_quarter` *(integer, optional)*: Optional quarter (`1`, `2`, `3`, or `4`). Omit for full calendar year.
  - `highlight_identifier` *(string, optional)*: Optional company ticker/name/CIK (e.g., `"AAPL"`) to locate and benchmark within the market distribution.
  - `unit` *(string, optional, default `"USD"`)*: Unit of measure (`"USD"`, `"shares"`, `"USD-per-shares"`).
  - `taxonomy` *(string, optional, default `"us-gaap"`)*: `"us-gaap"`, `"dei"`, or `"ifrs-full"`.
  - `top_n` *(integer, optional, default `15`)*: Number of top-ranking companies to include (`5` to `40`).
```bash
remote_cli mcp \
  projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/sec-edgar-mcp-apps/dataConnector \
  benchmark_industry_xbrl_frame \
  --json '{"concept_or_tag": "revenue", "calendar_year": 2024, "highlight_identifier": "AAPL", "top_n": 10}' \
  --endpoint 'https://<YOUR_CLOUD_RUN_SERVICE_URL>/mcp' > /tmp/frame.json
```

### 9. `resolve_and_discover_sec_entities`
Fuzzy-searches SEC-registered public companies by name/ticker/CIK with inline `submissions` previews, and optionally searches a company's reported XBRL concept tags by keyword.
- **Parameters:**
  - `company_query` *(string, required)*: Partial company name, ticker symbol, or CIK (e.g., `"Alphabet"`, `"Berkshire"`, `"GOOGL"`).
  - `xbrl_tag_keyword` *(string, optional)*: Optional keyword (e.g., `"revenue"`, `"inventory"`, `"lease"`, `"research"`) to discover reported XBRL tags.
  - `limit` *(integer, optional, default `5`)*: Maximum number of matching companies to enrich and return (`1` to `15`).
```bash
remote_cli mcp \
  projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/sec-edgar-mcp-apps/dataConnector \
  resolve_and_discover_sec_entities \
  --json '{"company_query": "Alphabet", "xbrl_tag_keyword": "revenue", "limit": 3}' \
  --endpoint 'https://<YOUR_CLOUD_RUN_SERVICE_URL>/mcp' > /tmp/entities.json
```
