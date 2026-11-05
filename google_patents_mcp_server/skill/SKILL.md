---
name: google-patents-mcp
description: Search, retrieve, and analyze worldwide patents, claims, claim dependency trees, prior art timelines, citations, chemical structures (SMILES), CPC classifications, and automatically open interactive ui://google-patents/* MCP Apps in Sobi Live Code Preview (/workspace/deliverables/index.html) using the Google Patents MCP Server via `remote_cli mcp`.
---

# Google Patents MCP & Interactive `ui://` Apps Skill

Use this skill whenever the user asks to search Google Patents, retrieve patent claims/abstracts/descriptions, inspect claim dependency trees, analyze prior art timelines or INPADOC patent families, inspect forward/backward/NPL citations, find technically similar patents, search chemical structures (SMILES), look up CPC/IPC classification codes, or launch interactive Patent MCP Apps (`ui://google-patents/*`) via the **Google Patents MCP Server**.

---

## MANDATORY Sobi `ui://` Auto-Display Protocol (MUST FOLLOW ON EVERY TURN)

Whenever **any** tool output contains a `ui://` resource (`_meta.ui.resourceUri` or `"ui_resource_uri": "ui://google-patents/..."`), you **MUST** execute all 4 rules below in the **same turn** so the interactive MCP App **always opens automatically by default** in the right-hand Canvas / Live Code Preview pane on Turn 1 and on every subsequent turn:

1. **Rule 1 — Always Invoke `remote_cli mcp` Directly at the Top-Level Shell (NEVER Wrap in Python `subprocess`):**
   - **NEVER** call `remote_cli mcp` inside `subprocess.run(...)`, `os.system(...)`, or a background subshell.
   - Always execute `remote_cli mcp` directly as a top-level bash command and redirect stdout to `/tmp/patent_app.json`.

2. **Rule 2 — Run the Step 2 Python Extractor & Deliverable Publisher to Write Directly to `/workspace/deliverables/index.html` AND `/workspace/deliverables/patent_<slug>_<timestamp>.html`:**
   - **WHY BOTH FILES INSIDE `/workspace/deliverables/` ARE MANDATORY FOR AUTO-OPEN:**
     1. In the Gemini Enterprise UI (`chat_page.ts` $\rightarrow$ `isTaskSandboxDeliverable(path)`), the Canvas auto-open effect **only** opens files inside **`/workspace/deliverables/`** (`/^\/?(workspace\/)?deliverables\//`). Writing `/workspace/index.html` (or calling `write_file` with relative path `"index.html"`) puts the file at `/workspace/index.html` outside `/workspace/deliverables/`, which shows an `index.html` chip in chat but **skips auto-opening** (`skipped = 'the change is all outside deliverables/'`)!
     2. Furthermore, `chat_page.ts` caches `autoOpenedArtifactsKey` (`changedArtifacts().map(a => a.id).join('\0')`) across turns and across chat sessions in the same browser tab without resetting on session switch, and `bidi_task_lane.ts` skips any `kind: 'file'` whose path was already in `baseline`. If a turn only writes `/workspace/deliverables/index.html`, `key === this.autoOpenedArtifactsKey()` (`"/workspace/deliverables/index.html"`) matches the previous session and **skips auto-opening** (`skipped = 'already opened for this change'`)!
     3. Therefore, the Python script in **Step 2** below automatically deletes any stray `/workspace/index.html` and writes the complete, 100% self-contained interactive HTML application (`mcp_app_html`) directly to **BOTH**:
        - `/workspace/deliverables/index.html`
        - `/workspace/deliverables/patent_<slug>_<unix_timestamp>.html` (guaranteeing a 100% unique `changedArtifactsKey` on every single turn and every single chat session so the Canvas **always** auto-opens by default!).

3. **Rule 3 — NEVER Overwrite `/workspace/deliverables/index.html` with a `"Loading..."`/`fetch()` Stub & NEVER Write to Relative `"index.html"` or `"/workspace/index.html"`:**
   - The Step 2 Python script **already writes** the complete, 100% self-contained 30KB–65KB interactive HTML/CSS/SVG/JS application (`<!DOCTYPE html>...`) with all patent data embedded inline to `/workspace/deliverables/index.html` and `/workspace/deliverables/patent_<slug>_<timestamp>.html`.
   - **DO NOT** call `write_file` on relative path `"index.html"` or `"/workspace/index.html"` (which creates a non-deliverable root file), and **NEVER** overwrite `/workspace/deliverables/index.html` with a `<div id="loader">Loading...</div>` or `fetch()` wrapper!
   - Include clickable markdown links `[index.html](/workspace/deliverables/index.html)` and `[patent_<slug>_<timestamp>.html](/workspace/deliverables/patent_<slug>_<timestamp>.html)` in your final text response.

4. **Rule 4 — NEVER Call `emit_a2ui` (`Emit a2ui`) Storage/Chart Widgets & NEVER Generate Static `.png`/`.jpg` Files:**
   - **NEVER** call `emit_a2ui` (`build Emit a2ui`) on any turn that outputs a `ui://` MCP App! Calling `emit_a2ui` at the end of the turn hijacks the right-hand display surface and replaces/hides the interactive Canvas Live Code Preview pane.
   - Present your textual summary and tables in standard Markdown only, and let `/workspace/deliverables/index.html` remain active in the Live Code Preview panel.
   - Do **NOT** generate static `.png` or `.jpg` files via `matplotlib` or `Pillow`.

---

## Connection & Tool Invocation (`remote_cli mcp`)

Inside the Sobi VMaaS container (`/workspace`), invoke the Google Patents MCP Server using `remote_cli mcp` with **positional** `<connector> <tool>` arguments (do **NOT** use `-s` or `-t` flags, and do **NOT** waste turns running `list-tools` or `describe`):
1. **Connector Resource Name:**
   - `projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/google-patents-mcp/dataConnector`
2. **Tool Name & JSON Payload:** `<tool_name> --json '<json_arguments>'`
3. **Explicit `--endpoint` Flag:** `--endpoint 'https://<YOUR_CLOUD_RUN_SERVICE_URL>/mcp'`

> **Configuration Note:** Before zipping and uploading this `SKILL.md` as a Gemini Sobi Skill Agent, replace `<YOUR_PROJECT_NUMBER>` with your numeric Google Cloud project number and `<YOUR_CLOUD_RUN_SERVICE_URL>` with your deployed Cloud Run hostname (for example, `google-patents-mcp-server-xxxxxx-uc.a.run.app`).

---

## Standard 2-Step Turn-1 Workflow Whenever `ui://` Output Is Present

### Step 1: Run `remote_cli mcp` at the Top-Level Shell (`> /tmp/patent_app.json`)
Always prefer calling one of the 6 `open_*_app` tools (`open_patent_claim_tree_app`, `open_prior_art_timeline_app`, `open_patent_citation_graph_app`, `open_patent_landscape_app`, `open_patent_pdf_viewer_app`, `open_chemistry_explorer_app`) at the top-level shell and redirect output to `/tmp/patent_app.json`.

### Step 2: Run the Recursive Extractor & Auto-Open Deliverable Publisher in `terminal`
Immediately run this exact Python script in `terminal`. It extracts the 100% self-contained `mcp_app_html` (or fetches the pre-hydrated HTML from `live_preview_url` if a data tool was called, or builds a self-contained interactive HTML fallback), removes any stray `/workspace/index.html`, and writes the self-contained HTML directly to **BOTH** `/workspace/deliverables/index.html` and `/workspace/deliverables/patent_<slug>_<timestamp>.html` so the Gemini Enterprise Canvas **always opens it automatically by default**:
```bash
python3 - << 'EOF'
import json, pathlib, re, time, urllib.request

deliverables_dir = pathlib.Path("/workspace/deliverables")
deliverables_dir.mkdir(parents=True, exist_ok=True)
# Remove any stray root /workspace/index.html so it never shadows deliverables/
pathlib.Path("/workspace/index.html").unlink(missing_ok=True)

raw = pathlib.Path("/tmp/patent_app.json").read_text(encoding="utf-8", errors="replace").lstrip()
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
        if ("publication_number" in node or "target_patent" in node or "status" in node or "total_returned" in node or "backward_count" in node or "claims" in node or "timeline_events" in node) and not payload:
            payload = {k: v for k, v in node.items() if k != "mcp_app_html"}
        for k in ("_meta", "result", "structuredContent", "content", "resource", "mcp_app"):
            if k in node:
                walk(node[k])
    elif isinstance(node, list):
        for item in node:
            walk(item)

walk(top)

# If a data-only tool was called without inline mcp_app_html, fetch pre-hydrated HTML from live_preview_url
if not html and live_url:
    try:
        with urllib.request.urlopen(live_url, timeout=25) as resp:
            fetched = resp.read().decode("utf-8", errors="replace")
            if "<html" in fetched.lower():
                html = fetched
    except Exception as e:
        print("Warning fetching live_preview_url:", e)

# Built-in self-contained fallback HTML if neither mcp_app_html nor live_url was available
if not html:
    pub_id = payload.get("publication_number") or payload.get("target_patent") or payload.get("query") or "Patent_Analysis"
    title = payload.get("title") or f"Google Patents Interactive Workbench ({pub_id})"
    data_json = json.dumps(payload).replace("</", "<\\/")
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>{pub_id} — {title}</title>
<style>
  body {{ margin:0; font-family: system-ui, sans-serif; background:#0f172a; color:#f8fafc; }}
  header {{ padding:16px 24px; background:#1e293b; border-bottom:1px solid #334155; display:flex; justify-content:space-between; align-items:center; }}
  .badge {{ background:#2563eb; color:#fff; padding:4px 10px; border-radius:6px; font-weight:700; font-size:13px; }}
  main {{ padding:20px 24px; }}
  pre {{ background:#1e293b; padding:16px; border-radius:8px; overflow:auto; border:1px solid #334155; color:#e2e8f0; font-size:12px; }}
</style></head><body>
<header><div><span class="badge">{pub_id}</span> <strong style="margin-left:10px">{title}</strong></div><div style="font-size:12px;color:#94a3b8">{ui_uri or 'ui://google-patents/app'}</div></header>
<main><pre id="out"></pre></main>
<script>const DATA = {data_json}; document.getElementById('out').textContent = JSON.stringify(DATA, null, 2);</script>
</body></html>"""

raw_slug = str(payload.get("publication_number") or payload.get("target_patent") or payload.get("query") or "patent_app")
slug = re.sub(r"[^A-Za-z0-9_-]+", "_", raw_slug).strip("_")[:40] or "patent_app"
ts = int(time.time())
unique_name = f"patent_{slug}_{ts}.html"

index_path = deliverables_dir / "index.html"
unique_path = deliverables_dir / unique_name
index_path.write_text(html, encoding="utf-8")
unique_path.write_text(html, encoding="utf-8")
pathlib.Path("/tmp/patent_payload.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

print("AUTO_OPEN_DELIVERABLE_1:", str(index_path), f"({len(html)} bytes)")
print("AUTO_OPEN_DELIVERABLE_2:", str(unique_path), f"({len(html)} bytes)")
print("UI_RESOURCE_URI:", ui_uri)
print("LIVE_PREVIEW_URL:", live_url)
print("PAYLOAD_KEYS:", list(payload.keys()))
print(json.dumps(payload, indent=2)[:6000])
EOF
```

### Step 3: Present Your Markdown Analysis & Deliverable Links (Do NOT Overwrite `/workspace/deliverables/index.html` or Call `emit_a2ui`)
- Step 2 has **already written** the complete, 100% self-contained interactive HTML application to `/workspace/deliverables/index.html` AND `/workspace/deliverables/patent_<slug>_<timestamp>.html`, which triggers the Gemini Enterprise Canvas to **open automatically by default** as soon as your turn ends!
- **DO NOT** call `write_file` on relative path `"index.html"` or `"/workspace/index.html"`, **DO NOT** overwrite `/workspace/deliverables/index.html` with a `"Loading..."` stub, and **NEVER** call `emit_a2ui` (`Emit a2ui`).
- Include clickable markdown links `[index.html](/workspace/deliverables/index.html)` and `[patent_<slug>_<timestamp>.html](/workspace/deliverables/patent_<slug>_<timestamp>.html)` (using the exact filename printed in `AUTO_OPEN_DELIVERABLE_2`) in your final Markdown response!

---

## Part 1: Interactive `ui://google-patents/*` MCP App Tools (Tools 1–6)

Always prefer calling the dedicated `open_*_app` tool when the user asks to inspect, visualize, compare, or explore a patent's claims, prior art timeline, citation/similarity network, landscape, drawings/PDF, or chemical structure:

### 1. Claim Dependency Tree, Scope Inspector & Side-by-Side Comparator (`open_patent_claim_tree_app`)
- **UI Resource URI:** `ui://google-patents/claim-tree` (`text/html;profile=mcp-app`)
- **Live Preview Endpoint:** `https://<YOUR_CLOUD_RUN_SERVICE_URL>/apps/raw/claim-tree?patent_id=<PATENT_ID>`
- **Parameters:**
  - `patent_url_or_id` *(string, required)*: Primary patent ID (e.g., `"US8000000B2"`, `"US11435904B1"`). *(Note: parameter is `patent_url_or_id`, NOT `patent_id`.)*
  - `compare_with_patent_id` *(string, optional)*: Optional second patent ID for side-by-side claim comparison.

```bash
remote_cli mcp \
  projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/google-patents-mcp/dataConnector \
  open_patent_claim_tree_app \
  --json '{"patent_url_or_id": "US8000000B2", "compare_with_patent_id": "US11435904B1"}' \
  --endpoint 'https://<YOUR_CLOUD_RUN_SERVICE_URL>/mcp' > /tmp/patent_app.json
```

### 2. Prior Art Timeline, 20-Year Statutory Lifespan & Worldwide INPADOC Family Map (`open_prior_art_timeline_app`)
- **UI Resource URI:** `ui://google-patents/prior-art-timeline` (`text/html;profile=mcp-app`)
- **Live Preview Endpoint:** `https://<YOUR_CLOUD_RUN_SERVICE_URL>/apps/raw/prior-art-timeline?patent_id=<PATENT_ID>`
- **Parameters:**
  - `patent_id` *(string, required)*: Patent publication number (e.g., `"US8000000B2"`).

```bash
remote_cli mcp \
  projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/google-patents-mcp/dataConnector \
  open_prior_art_timeline_app \
  --json '{"patent_id": "US8000000B2"}' \
  --endpoint 'https://<YOUR_CLOUD_RUN_SERVICE_URL>/mcp' > /tmp/patent_app.json
```

### 3. Interactive Citation & ScaM Vector Similarity Network Graph (`open_patent_citation_graph_app`)
- **UI Resource URI:** `ui://google-patents/citation-graph` (`text/html;profile=mcp-app`)
- **Live Preview Endpoint:** `https://<YOUR_CLOUD_RUN_SERVICE_URL>/apps/raw/citation-graph?patent_id=<PATENT_ID>`
- **Parameters:**
  - `patent_id` *(string, required)*: Target patent ID (e.g., `"US8000000B2"`).
  - `include_similar` *(bool, optional, default `true`)*: Merge ScaM vector-similar patents into the radial network graph.
  - `limit` *(int, optional, default 20)*: Max citations per direction.

```bash
remote_cli mcp \
  projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/google-patents-mcp/dataConnector \
  open_patent_citation_graph_app \
  --json '{"patent_id": "US8000000B2", "include_similar": true, "limit": 20}' \
  --endpoint 'https://<YOUR_CLOUD_RUN_SERVICE_URL>/mcp' > /tmp/patent_app.json
```

### 4. Patent Landscape & White-Space Analytics Dashboard (`open_patent_landscape_app`)
- **UI Resource URI:** `ui://google-patents/landscape-dashboard` (`text/html;profile=mcp-app`)
- **Live Preview Endpoint:** `https://<YOUR_CLOUD_RUN_SERVICE_URL>/apps/raw/landscape-dashboard?q=<QUERY>&assignee=<ASSIGNEE>`
- **Parameters:**
  - `query` *(string, optional)*: Search keywords (e.g., `"solid state battery"`, `"autonomous lidar"`).
  - `assignee` *(string, optional)*: Company filter (e.g., `"Toyota"`, `"Waymo"`).
  - `cpc_code` *(string, optional)*: CPC prefix (e.g., `"H01M"`, `"G06N"`).
  - `country_code` *(string, optional)*: Jurisdiction (e.g., `"US"`, `"EP"`, `"WO"`).
  - `start_date` / `end_date` *(string, optional)*: Date range (`"YYYY-MM-DD"`).
  - `limit` *(int, optional, default 20)*: Number of patents (`1`–`50`).

```bash
remote_cli mcp \
  projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/google-patents-mcp/dataConnector \
  open_patent_landscape_app \
  --json '{"query": "solid state electrolyte", "assignee": "Toyota", "country_code": "US", "limit": 20}' \
  --endpoint 'https://<YOUR_CLOUD_RUN_SERVICE_URL>/mcp' > /tmp/patent_app.json
```

### 5. Synchronized Drawing Carousel, PDF & Specification Split-Viewer (`open_patent_pdf_viewer_app`)
- **UI Resource URI:** `ui://google-patents/pdf-drawing-viewer` (`text/html;profile=mcp-app`)
- **Live Preview Endpoint:** `https://<YOUR_CLOUD_RUN_SERVICE_URL>/apps/raw/pdf-drawing-viewer?patent_id=<PATENT_ID>`
- **Parameters:**
  - `patent_id` *(string, required)*: Patent ID (e.g., `"US8000000B2"`).

```bash
remote_cli mcp \
  projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/google-patents-mcp/dataConnector \
  open_patent_pdf_viewer_app \
  --json '{"patent_id": "US8000000B2"}' \
  --endpoint 'https://<YOUR_CLOUD_RUN_SERVICE_URL>/mcp' > /tmp/patent_app.json
```

### 6. 2D Chemical Structure / SMILES Explorer & Substructure Workbench (`open_chemistry_explorer_app`)
- **UI Resource URI:** `ui://google-patents/chemistry-explorer` (`text/html;profile=mcp-app`)
- **Live Preview Endpoint:** `https://<YOUR_CLOUD_RUN_SERVICE_URL>/apps/raw/chemistry-explorer?smiles=<SMILES>`
- **Parameters:**
  - `smiles` *(string, optional, default `"CC(=O)Oc1ccccc1C(=O)O"`)*: SMILES string.
  - `mode` *(string, optional, default `"SUBSTRUCTURE"`)*: `"EXACT"`, `"SUBSTRUCTURE"`, or `"SIMILARITY"`.
  - `query` *(string, optional)*: Optional keyword filter.
  - `limit` *(int, optional, default 15)*: Max results.

```bash
remote_cli mcp \
  projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/google-patents-mcp/dataConnector \
  open_chemistry_explorer_app \
  --json '{"smiles": "CC(=O)Oc1ccccc1C(=O)O", "mode": "SUBSTRUCTURE", "limit": 15}' \
  --endpoint 'https://<YOUR_CLOUD_RUN_SERVICE_URL>/mcp' > /tmp/patent_app.json
```

---

## Part 2: Core Data & Search Tools (Tools 7–18, Also Linked to `ui://google-patents/*`)

Every data tool below ALSO returns `"ui_resource_uri"` (`ui://google-patents/*`), `"live_preview_url"`, and `_meta.ui.resourceUri`. Whenever you call any of these tools, redirect output to `> /tmp/patent_app.json`, run **Step 2** above to automatically fetch and publish the pre-hydrated HTML to `/workspace/deliverables/index.html` and `/workspace/deliverables/patent_<slug>_<timestamp>.html`, and follow **Step 3** (include clickable markdown links to both files and do **NOT** call `emit_a2ui`):

### 7. Multi-Filter / Structured Patent Search (`advanced_patent_search`)
- **Linked UI Resource:** `ui://google-patents/landscape-dashboard`
- **Parameters:** `query`, `assignee`, `inventor`, `cpc_code`, `ipc_code`, `country_code`, `start_date`, `end_date`, `status` (`"GRANT"` / `"APPLICATION"`), `limit` (`1`–`50`).
```bash
remote_cli mcp \
  projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/google-patents-mcp/dataConnector \
  advanced_patent_search \
  --json '{"query": "solid state electrolyte", "assignee": "Toyota", "country_code": "US", "start_date": "2021-01-01", "limit": 10}' \
  --endpoint 'https://<YOUR_CLOUD_RUN_SERVICE_URL>/mcp' > /tmp/patent_app.json
```

### 8. Quick Keyword or URL-Parameter Search (`search_patents`)
- **Linked UI Resource:** `ui://google-patents/landscape-dashboard`
- **IMPORTANT:** Parameter is `query_url_or_params` (NOT `query`), plus `limit` (`1`–`50`).
```bash
remote_cli mcp \
  projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/google-patents-mcp/dataConnector \
  search_patents \
  --json '{"query_url_or_params": "autonomous vehicle lidar", "limit": 10}' \
  --endpoint 'https://<YOUR_CLOUD_RUN_SERVICE_URL>/mcp' > /tmp/patent_app.json
```

### 9. Full Patent Details, Abstract, Claims & Claim Tree (`get_patent_details`)
- **Linked UI Resource:** `ui://google-patents/claim-tree`
- **IMPORTANT:** Parameter is `patent_url_or_id` (NOT `patent_id`), plus `include_claims` (`true`) and `include_description` (`false`).
```bash
remote_cli mcp \
  projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/google-patents-mcp/dataConnector \
  get_patent_details \
  --json '{"patent_url_or_id": "US11435904B1", "include_claims": true, "include_description": false}' \
  --endpoint 'https://<YOUR_CLOUD_RUN_SERVICE_URL>/mcp' > /tmp/patent_app.json
```

### 10. Prior Art Timeline, INPADOC Family & Legal Key Dates (`get_prior_art_timeline`)
- **Linked UI Resource:** `ui://google-patents/prior-art-timeline`
- **Parameters:** `patent_id` *(string, required)*.
```bash
remote_cli mcp \
  projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/google-patents-mcp/dataConnector \
  get_prior_art_timeline \
  --json '{"patent_id": "US11435904B1"}' \
  --endpoint 'https://<YOUR_CLOUD_RUN_SERVICE_URL>/mcp' > /tmp/patent_app.json
```

### 11. Forward, Backward & Scholar NPL Citations (`get_patent_citations`)
- **Linked UI Resource:** `ui://google-patents/citation-graph`
- **Parameters:** `patent_id` *(string, required)*, `citation_type` (`"backward"`, `"forward"`, `"both"`), `limit` (`1`–`100`).
```bash
remote_cli mcp \
  projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/google-patents-mcp/dataConnector \
  get_patent_citations \
  --json '{"patent_id": "US11435904B1", "citation_type": "both", "limit": 25}' \
  --endpoint 'https://<YOUR_CLOUD_RUN_SERVICE_URL>/mcp' > /tmp/patent_app.json
```

### 12. Find Similar Patents (`find_similar_patents`)
- **Linked UI Resource:** `ui://google-patents/citation-graph`
- **Parameters:** `patent_id` *(string, required)*, `limit` (`1`–`20`).
```bash
remote_cli mcp \
  projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/google-patents-mcp/dataConnector \
  find_similar_patents \
  --json '{"patent_id": "US11435904B1", "limit": 10}' \
  --endpoint 'https://<YOUR_CLOUD_RUN_SERVICE_URL>/mcp' > /tmp/patent_app.json
```

### 13. Chemical Structure / SMILES Search (`search_chemistry`)
- **Linked UI Resource:** `ui://google-patents/chemistry-explorer`
- **Parameters:** `smiles` *(string, required)*, `mode` (`"EXACT"`, `"SUBSTRUCTURE"`, `"SIMILARITY"`), `query`, `limit`.
```bash
remote_cli mcp \
  projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/google-patents-mcp/dataConnector \
  search_chemistry \
  --json '{"smiles": "CC(=O)Oc1ccccc1C(=O)O", "mode": "SUBSTRUCTURE", "limit": 10}' \
  --endpoint 'https://<YOUR_CLOUD_RUN_SERVICE_URL>/mcp' > /tmp/patent_app.json
```

### 14. Patent PDF, Figure Drawings & Specification Callouts (`get_patent_pdf`)
- **Linked UI Resource:** `ui://google-patents/pdf-drawing-viewer`
- **Parameters:** `patent_id` *(string, required)*.
```bash
remote_cli mcp \
  projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/google-patents-mcp/dataConnector \
  get_patent_pdf \
  --json '{"patent_id": "US8000000B2"}' \
  --endpoint 'https://<YOUR_CLOUD_RUN_SERVICE_URL>/mcp' > /tmp/patent_app.json
```

### 15. CPC / IPC Classification Code Lookup (`lookup_classification_code`)
- **Linked UI Resource:** `ui://google-patents/landscape-dashboard`
- **Parameters:** `code` *(string, required, e.g., `"G06N3/08"` or `"H01M10/0562"`)*.
```bash
remote_cli mcp \
  projects/<YOUR_PROJECT_NUMBER>/locations/global/collections/google-patents-mcp/dataConnector \
  lookup_classification_code \
  --json '{"code": "G06N3/08"}' \
  --endpoint 'https://<YOUR_CLOUD_RUN_SERVICE_URL>/mcp' > /tmp/patent_app.json
```

### 16–18. Utility Tools (`parse_query`, `normalize_patent_number`, `set_patents_session_cookie`)
- `parse_query`: `{"query": "Waymo lidar since 2020"}`
- `normalize_patent_number`: `{"number": "10000000", "country": "US", "patent_type": "patent"}`
- `set_patents_session_cookie`: `{"cookie": "<cookie_string>"}`
