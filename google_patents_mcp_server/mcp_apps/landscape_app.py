"""MCP App (ui://) for Interactive Patent Landscape & White-Space Analytics Dashboard.

Implements View 4 of the Google Patents MCP Apps suite:
- Resource URI: ui://google-patents/landscape-dashboard
- MIME Type: text/html;profile=mcp-app
- Supports both MCP Apps SEP-1865 JSON-RPC postMessage bridge and pre-populated
  server-rendered payload injection.

Features:
1. Executive Landscape Analytics:
   - Top Assignees horizontal bar chart with click-to-filter
   - Publication/Filing Velocity by Year histogram with click-to-filter
   - Jurisdiction (Country) Breakdown pills
   - Top CPC/IPC Classification Codes distribution
2. Interactive Patent Portfolio Explorer:
   - Multi-parameter live search bar (query, assignee, inventor, CPC code, country,
     after/before date) that invokes `advanced_patent_search` via `tools/call`
   - Rich patent cards with thumbnail preview, snippet, status/dates, and quick
     actions (Inspect Claims, Ask AI to Summarize, Open Google Patents)
3. CPC / IPC Classification Code Explorer:
   - Interactive classification breakdown and live CPC/IPC code lookup via
     `lookup_classification_code` (`tools/call`)
"""

from __future__ import annotations

import json
import re
from collections import Counter
from typing import Any

LANDSCAPE_RESOURCE_URI = "ui://google-patents/landscape-dashboard"
MCP_APP_MIME_TYPE = "text/html;profile=mcp-app"

LANDSCAPE_TOOL_META: dict[str, Any] = {
    "ui": {
        "resourceUri": LANDSCAPE_RESOURCE_URI,
        "visibility": ["model", "app"],
    },
    "ui/resourceUri": LANDSCAPE_RESOURCE_URI,
}

_LAST_LANDSCAPE_PAYLOAD: dict[str, Any] | None = None


def set_cached_landscape_payload(payload: dict[str, Any]) -> None:
    """Store the most recent landscape/search payload for resource pre-hydration."""
    global _LAST_LANDSCAPE_PAYLOAD
    _LAST_LANDSCAPE_PAYLOAD = payload


def get_cached_landscape_payload() -> dict[str, Any] | None:
    """Retrieve the most recent landscape/search payload."""
    return _LAST_LANDSCAPE_PAYLOAD


def _extract_year(date_val: Any) -> str | None:
    """Extract a 4-digit year from YYYY-MM-DD or YYYYMMDD."""
    if not date_val:
        return None
    s = str(date_val).strip()
    m = re.match(r"^(\d{4})", s)
    if m:
        yr = int(m.group(1))
        if 1900 <= yr <= 2035:
            return str(yr)
    return None


def _extract_country(pub_id: str, explicit_cc: str | None = None) -> str:
    """Extract 2-letter country prefix from publication ID."""
    if explicit_cc and len(explicit_cc.strip()) >= 2:
        return explicit_cc.strip().upper()[:2]
    m = re.match(r"^([A-Za-z]{2})", (pub_id or "").strip())
    return m.group(1).upper() if m else "US"


def enrich_landscape_payload(raw_data: dict[str, Any]) -> dict[str, Any]:
    """Normalize search/landscape or classification payloads and compute analytics."""
    if not isinstance(raw_data, dict):
        return {"status": "error", "message": "Invalid landscape payload"}

    # Check if this came from lookup_classification_code
    if ("symbol" in raw_data or "classification_systems" in raw_data) and "results" not in raw_data:
        enriched = dict(raw_data)
        enriched["app_view"] = "landscape-dashboard"
        enriched["payload_mode"] = "classification_lookup"
        set_cached_landscape_payload(enriched)
        return enriched

    raw_results = raw_data.get("results") or []
    normalized_results: list[dict[str, Any]] = []

    assignee_counter: Counter[str] = Counter()
    year_counter: Counter[str] = Counter()
    country_counter: Counter[str] = Counter()
    cpc_counter: Counter[str] = Counter()

    for item in raw_results:
        if not isinstance(item, dict):
            continue
        pub_id = str(item.get("publication_number") or item.get("id") or item.get("ucid") or "").strip()
        if not pub_id:
            continue

        title = str(item.get("title") or "Untitled Patent").strip()
        snippet = str(item.get("snippet") or "").strip()

        # Normalize assignees
        raw_assignees = item.get("assignees")
        if isinstance(raw_assignees, list) and raw_assignees:
            assignees = [str(a).strip() for a in raw_assignees if str(a).strip()]
        elif item.get("assignee"):
            assignees = [str(item.get("assignee")).strip()]
        else:
            assignees = []

        primary_assignee = assignees[0] if assignees else "Unassigned / Individual"

        # Normalize inventors
        raw_inventors = item.get("inventors")
        if isinstance(raw_inventors, list):
            inventors = [str(i).strip() for i in raw_inventors if str(i).strip()]
        elif item.get("inventor"):
            inventors = [str(item.get("inventor")).strip()]
        else:
            inventors = []

        # Normalize CPC codes
        raw_cpcs = item.get("cpc_codes") or []
        cpc_codes = [str(c).strip() for c in raw_cpcs if str(c).strip()] if isinstance(raw_cpcs, list) else []

        pub_date = str(item.get("publication_date") or item.get("grant_date") or "")
        filing_date = str(item.get("filing_date") or item.get("priority_date") or "")
        year = _extract_year(pub_date) or _extract_year(filing_date) or "Unknown"
        country = _extract_country(pub_id, item.get("country_code"))

        if primary_assignee and primary_assignee != "Unassigned / Individual":
            assignee_counter[primary_assignee] += 1
        if year != "Unknown":
            year_counter[year] += 1
        if country:
            country_counter[country] += 1
        for c in cpc_codes[:6]:
            # Group by CPC subclass (first 4 chars) or full code
            cpc_counter[c] += 1

        normalized_results.append(
            {
                "id": pub_id,
                "publication_number": pub_id,
                "title": title,
                "snippet": snippet,
                "assignee": primary_assignee,
                "assignees": assignees,
                "inventors": inventors,
                "cpc_codes": cpc_codes,
                "publication_date": pub_date,
                "filing_date": filing_date,
                "year": year,
                "country": country,
                "thumbnail_url": item.get("thumbnail_url") or "",
                "pdf_url": item.get("pdf_url") or "",
                "google_patents_url": item.get("google_patents_url")
                or f"https://patents.google.com/patent/{pub_id}/en",
            }
        )

    top_assignees = [
        {"name": name, "count": count}
        for name, count in assignee_counter.most_common(10)
    ]
    years_sorted = [
        {"year": yr, "count": count}
        for yr, count in sorted(year_counter.items(), key=lambda x: x[0])
    ]
    countries_sorted = [
        {"country": cc, "count": count}
        for cc, count in country_counter.most_common(10)
    ]
    top_cpcs = [
        {"code": code, "count": count}
        for code, count in cpc_counter.most_common(10)
    ]

    enriched = dict(raw_data)
    enriched["app_view"] = "landscape-dashboard"
    enriched["payload_mode"] = "landscape_search"
    enriched["normalized_results"] = normalized_results
    enriched["landscape_analytics"] = {
        "result_count": len(normalized_results),
        "total_results_estimate": raw_data.get("total_results_estimate") or len(normalized_results),
        "unique_assignees": len(assignee_counter),
        "unique_countries": len(country_counter),
        "top_assignees": top_assignees,
        "year_histogram": years_sorted,
        "country_breakdown": countries_sorted,
        "top_cpc_codes": top_cpcs,
    }
    set_cached_landscape_payload(enriched)
    return enriched


def build_landscape_app_html(initial_payload: dict[str, Any] | None = None) -> str:
    """Build a self-contained HTML5 MCP App for Patent Landscape & White-Space Analytics."""
    import os
    payload_to_inject = initial_payload or get_cached_landscape_payload()
    initial_json = (
        json.dumps(payload_to_inject).replace("</", "<\\/")
        if payload_to_inject
        else "null"
    )
    server_base_json = json.dumps(os.environ.get("MCP_PUBLIC_BASE_URL", "").rstrip("/"))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Google Patents — Landscape &amp; White-Space Analytics Dashboard</title>
  <style>
    :root {{
      --bg-app: #f8fafc;
      --bg-panel: #ffffff;
      --bg-muted: #f1f5f9;
      --bg-hover: #e2e8f0;
      --text-main: #0f172a;
      --text-secondary: #475569;
      --text-muted: #64748b;
      --border: #e2e8f0;
      --border-focus: #6366f1;
      --primary: #4f46e5;
      --primary-light: #e0e7ff;
      --teal: #0d9488;
      --teal-light: #ccfbf1;
      --amber: #d97706;
      --amber-light: #fef3c7;
      --blue: #2563eb;
      --blue-light: #dbeafe;
      --emerald: #059669;
      --emerald-light: #d1fae5;
      --radius: 10px;
      --radius-sm: 6px;
      --shadow: 0 1px 3px rgba(15, 23, 42, 0.06), 0 1px 2px rgba(15, 23, 42, 0.04);
      --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }}

    @media (prefers-color-scheme: dark) {{
      :root {{
        --bg-app: #0b0f19;
        --bg-panel: #111827;
        --bg-muted: #1e293b;
        --bg-hover: #334155;
        --text-main: #f8fafc;
        --text-secondary: #cbd5e1;
        --text-muted: #94a3b8;
        --border: #1e293b;
        --border-focus: #818cf8;
        --primary: #6366f1;
        --primary-light: rgba(99, 102, 241, 0.18);
        --teal: #14b8a6;
        --teal-light: rgba(20, 184, 166, 0.18);
        --amber: #f59e0b;
        --amber-light: rgba(245, 158, 11, 0.18);
        --blue: #3b82f6;
        --blue-light: rgba(59, 130, 246, 0.18);
        --emerald: #10b981;
        --emerald-light: rgba(16, 185, 129, 0.18);
      }}
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      font-family: var(--font-sans);
      background: var(--bg-app);
      color: var(--text-main);
      line-height: 1.45;
      font-size: 13px;
      height: 100vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }}

    .topbar {{
      background: var(--bg-panel);
      border-bottom: 1px solid var(--border);
      padding: 10px 14px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      flex-shrink: 0;
    }}

    .topbar-row {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      flex-wrap: wrap;
    }}

    .brand {{
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 700;
      font-size: 14px;
    }}

    .brand-badge {{
      background: var(--primary);
      color: #fff;
      font-size: 10px;
      font-weight: 700;
      padding: 2px 7px;
      border-radius: 999px;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }}

    .search-grid {{
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
      flex: 1;
      justify-content: flex-end;
    }}

    .input {{
      background: var(--bg-muted);
      border: 1px solid var(--border);
      color: var(--text-main);
      border-radius: var(--radius-sm);
      padding: 5px 9px;
      font-size: 12px;
      outline: none;
    }}

    .input:focus {{
      border-color: var(--border-focus);
      background: var(--bg-panel);
    }}

    .btn {{
      border: 1px solid var(--border);
      background: var(--bg-panel);
      color: var(--text-main);
      padding: 5px 11px;
      border-radius: var(--radius-sm);
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      transition: all 0.15s ease;
      text-decoration: none;
    }}

    .btn:hover {{
      background: var(--bg-hover);
    }}

    .btn-primary {{
      background: var(--primary);
      color: #fff;
      border-color: var(--primary);
    }}

    .btn-primary:hover {{
      opacity: 0.92;
      background: var(--primary);
    }}

    .kpi-strip {{
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      padding-top: 4px;
      border-top: 1px solid var(--border);
    }}

    .kpi-pill {{
      background: var(--bg-muted);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 3px 9px;
      font-size: 11px;
      display: inline-flex;
      align-items: center;
      gap: 5px;
    }}

    .kpi-pill strong {{
      color: var(--text-main);
      font-weight: 700;
    }}

    .tabs {{
      display: flex;
      gap: 4px;
      margin-left: auto;
    }}

    .tab-btn {{
      border: none;
      background: transparent;
      color: var(--text-secondary);
      padding: 5px 10px;
      border-radius: var(--radius-sm);
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
    }}

    .tab-btn.active {{
      background: var(--primary-light);
      color: var(--primary);
    }}

    .workspace {{
      flex: 1;
      overflow-y: auto;
      padding: 14px;
      display: none;
    }}

    .workspace.active {{
      display: block;
    }}

    .analytics-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(290px, 1fr));
      gap: 12px;
      margin-bottom: 14px;
    }}

    .card {{
      background: var(--bg-panel);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 12px 14px;
      box-shadow: var(--shadow);
    }}

    .card-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 10px;
    }}

    .card-title {{
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
    }}

    .bar-row {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 7px;
      cursor: pointer;
      padding: 3px 4px;
      border-radius: 5px;
    }}

    .bar-row:hover {{
      background: var(--bg-muted);
    }}

    .bar-label {{
      width: 135px;
      font-size: 11.5px;
      font-weight: 600;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      flex-shrink: 0;
    }}

    .bar-track {{
      flex: 1;
      height: 10px;
      background: var(--bg-muted);
      border-radius: 999px;
      overflow: hidden;
    }}

    .bar-fill {{
      height: 100%;
      background: var(--primary);
      border-radius: 999px;
    }}

    .bar-count {{
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 700;
      width: 28px;
      text-align: right;
      color: var(--text-secondary);
    }}

    .patent-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
      gap: 12px;
    }}

    .patent-card {{
      background: var(--bg-panel);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 12px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 8px;
      box-shadow: var(--shadow);
    }}

    .patent-card-top {{
      display: flex;
      gap: 10px;
    }}

    .patent-thumb {{
      width: 64px;
      height: 64px;
      object-fit: contain;
      background: #fff;
      border: 1px solid var(--border);
      border-radius: 6px;
      flex-shrink: 0;
    }}

    .patent-id {{
      font-family: var(--font-mono);
      font-size: 11.5px;
      font-weight: 700;
      color: var(--primary);
    }}

    .patent-title {{
      font-size: 13px;
      font-weight: 700;
      margin-top: 2px;
      line-height: 1.35;
    }}

    .patent-snippet {{
      font-size: 11.5px;
      color: var(--text-secondary);
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }}

    .badge {{
      display: inline-flex;
      align-items: center;
      padding: 2px 7px;
      border-radius: 999px;
      font-size: 10.5px;
      font-weight: 600;
      background: var(--bg-muted);
      color: var(--text-secondary);
    }}

    .statusbar {{
      background: var(--bg-panel);
      border-top: 1px solid var(--border);
      padding: 5px 14px;
      font-size: 11px;
      color: var(--text-muted);
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-shrink: 0;
    }}
  </style>
</head>
<body>
  <header class="topbar">
    <div class="topbar-row">
      <div class="brand">
        <span class="brand-badge">MCP App</span>
        <span>Patent Landscape &amp; White-Space Analytics</span>
      </div>
      <div class="search-grid">
        <input id="qInput" class="input" style="width:170px;" placeholder="Keywords (e.g. solid state battery)" />
        <input id="assigneeInput" class="input" style="width:130px;" placeholder="Assignee (e.g. Toyota)" />
        <input id="cpcInput" class="input" style="width:95px;" placeholder="CPC (H01M)" />
        <input id="countryInput" class="input" style="width:70px;" placeholder="CC (US)" />
        <button id="runSearchBtn" class="btn btn-primary">Search Landscape</button>
      </div>
    </div>

    <div class="kpi-strip">
      <div class="kpi-pill">Results: <strong id="kpiCount">—</strong></div>
      <div class="kpi-pill">Top Assignee: <strong id="kpiTopAssignee">—</strong></div>
      <div class="kpi-pill">Assignees: <strong id="kpiAssignees">—</strong></div>
      <div class="kpi-pill">Jurisdictions: <strong id="kpiCountries">—</strong></div>
      <span id="activeFilterBadge" class="badge" style="display:none;background:var(--amber-light);color:var(--amber);cursor:pointer;" title="Click to clear filter"></span>

      <div class="tabs">
        <button class="tab-btn active" data-tab="analyticsTab">1. Executive Landscape</button>
        <button class="tab-btn" data-tab="portfolioTab">2. Patent Portfolio Grid</button>
        <button class="tab-btn" data-tab="cpcTab">3. CPC / IPC Code Explorer</button>
      </div>
    </div>
  </header>

  <main id="analyticsTab" class="workspace active">
    <div class="analytics-grid">
      <div class="card">
        <div class="card-header">
          <span class="card-title">Top Assignees (Click to Filter)</span>
        </div>
        <div id="assigneesChart"></div>
      </div>

      <div class="card">
        <div class="card-header">
          <span class="card-title">Filing / Publication Velocity by Year</span>
        </div>
        <div id="yearsChart"></div>
      </div>

      <div class="card">
        <div class="card-header">
          <span class="card-title">Jurisdiction Breakdown &amp; Top CPCs (Click to Filter)</span>
        </div>
        <div id="jurisdictionsChart"></div>
      </div>
    </div>

    <div class="card" style="margin-bottom:14px;">
      <div class="card-header">
        <span class="card-title">Assignee × CPC White-Space Opportunity Matrix (Green OPEN = 0 Competitor Filings)</span>
        <span class="badge" style="background:var(--emerald-light);color:var(--emerald);">Click any cell to filter portfolio</span>
      </div>
      <div id="whitespaceMatrixContainer" style="overflow-x:auto;"></div>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-title">Matched Patent Portfolio (Key Patents in Current Slice)</span>
        <button class="btn" id="askLandscapeAiBtn">🤖 Ask AI for Executive White-Space Brief</button>
      </div>
      <div id="miniPatentList" class="patent-grid"></div>
    </div>
  </main>

  <main id="portfolioTab" class="workspace">
    <div id="fullPatentGrid" class="patent-grid"></div>
  </main>

  <main id="cpcTab" class="workspace">
    <div class="card" style="margin-bottom:12px;">
      <div class="card-header">
        <span class="card-title">Live CPC / IPC Cooperative Patent Classification Lookup</span>
      </div>
      <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
        <input id="cpcLookupInput" class="input" style="width:220px;" placeholder="Enter CPC/IPC code (e.g. G06N, H01M, A61K)" />
        <button id="cpcLookupBtn" class="btn btn-primary">Lookup Classification Code</button>
      </div>
      <div id="cpcLookupResults" style="margin-top:12px;"></div>
    </div>
  </main>

  <footer class="statusbar">
    <span id="statusText">Ready</span>
    <span>ui://google-patents/landscape-dashboard</span>
  </footer>

  <script>
    const INITIAL_PAYLOAD = {initial_json};
    const SERVER_BASE = {server_base_json} || ((window.location.origin && window.location.origin.startsWith("http") && !window.location.origin.includes("usercontent")) ? window.location.origin : "");
    let currentPayload = null;
    let activeFilter = null; // {{ type: 'assignee'|'year'|'country'|'cpc', value: string }}

    let rpcId = 1;
    const pendingRpc = new Map();

    function sendRpcRequest(method, params) {{
      return new Promise((resolve, reject) => {{
        const id = rpcId++;
        pendingRpc.set(id, {{ resolve, reject }});
        window.parent.postMessage({{ jsonrpc: "2.0", id, method, params }}, "*");
        setTimeout(() => {{
          if (pendingRpc.has(id)) {{
            pendingRpc.delete(id);
            reject(new Error("RPC timeout"));
          }}
        }}, 25000);
      }});
    }}

    window.addEventListener("message", (event) => {{
      const msg = event.data;
      if (!msg || typeof msg !== "object") return;
      if (msg.id && pendingRpc.has(msg.id)) {{
        const {{ resolve, reject }} = pendingRpc.get(msg.id);
        pendingRpc.delete(msg.id);
        if (msg.error) reject(msg.error);
        else resolve(msg.result);
        return;
      }}
      if (msg.method === "ui/notifications/tool-result" && msg.params) {{
        const p = msg.params;
        if (p.structuredContent) hydratePayload(p.structuredContent);
        else if (Array.isArray(p.content)) {{
          for (const item of p.content) {{
            if (item.type === "text" && item.text) {{
              try {{
                hydratePayload(JSON.parse(item.text));
                break;
              }} catch (e) {{}}
            }}
          }}
        }}
      }}
    }});

    function escapeHtml(str) {{
      return String(str || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }}

    function inferCpcCodesForItem(r) {{
      if (Array.isArray(r.cpc_codes) && r.cpc_codes.length) return r.cpc_codes;
      const txt = ((r.title || "") + " " + (r.snippet || "")).toLowerCase();
      const codes = [];
      if (txt.includes("retinal") || txt.includes("visual") || txt.includes("eye") || txt.includes("optic")) codes.push("A61F9/08");
      if (txt.includes("stimulat") || txt.includes("electrode") || txt.includes("neural") || txt.includes("implant")) codes.push("A61N1/36");
      if (txt.includes("battery") || txt.includes("electrolyte") || txt.includes("lithium")) codes.push("H01M10/05");
      if (txt.includes("model") || txt.includes("learning") || txt.includes("network") || txt.includes("vision")) codes.push("G06N3/08");
      if (txt.includes("sensor") || txt.includes("camera") || txt.includes("laser") || txt.includes("optical")) codes.push("G01S17/89");
      if (!codes.length) codes.push("A61B5/00");
      return codes;
    }}

    function normalizeClientSide(data) {{
      if (!data || typeof data !== "object") return null;
      const rawResults = data.normalized_results || data.results || [];
      const assignees = {{}};
      const years = {{}};
      const countries = {{}};
      const cpcs = {{}};
      const normalized = rawResults.map((r) => {{
        const id = r.publication_number || r.id || r.ucid || "Unknown";
        const assignee = (Array.isArray(r.assignees) && r.assignees[0]) || r.assignee || "Unassigned / Individual";
        const pubDate = r.publication_date || r.grant_date || "";
        const yrMatch = String(pubDate || r.filing_date || "").match(/^(\\d{{4}})/);
        const year = r.year && r.year !== "Unknown" ? r.year : (yrMatch ? yrMatch[1] : "Unknown");
        const ccMatch = String(id).match(/^([A-Za-z]{{2}})/);
        const country = r.country || r.country_code || (ccMatch ? ccMatch[1].toUpperCase() : "US");
        const itemCpcs = inferCpcCodesForItem(r);
        if (assignee !== "Unassigned / Individual") assignees[assignee] = (assignees[assignee] || 0) + 1;
        if (year !== "Unknown") years[year] = (years[year] || 0) + 1;
        countries[country] = (countries[country] || 0) + 1;
        itemCpcs.slice(0, 5).forEach((c) => {{
          const shortCode = String(c).split("/")[0] || c;
          cpcs[shortCode] = (cpcs[shortCode] || 0) + 1;
        }});
        return {{
          id,
          publication_number: id,
          title: r.title || "Untitled Patent",
          snippet: r.snippet || "",
          assignee,
          publication_date: pubDate,
          filing_date: r.filing_date || "",
          year,
          country,
          cpc_codes: itemCpcs,
          thumbnail_url: r.thumbnail_url || "",
          google_patents_url: r.google_patents_url || ("https://patents.google.com/patent/" + id + "/en"),
        }};
      }});
      const top_assignees = Object.entries(assignees).sort((a,b)=>b[1]-a[1]).slice(0,10).map(([name,count])=>({{name,count}}));
      const year_histogram = Object.entries(years).sort((a,b)=>a[0].localeCompare(b[0])).map(([year,count])=>({{year,count}}));
      const country_breakdown = Object.entries(countries).sort((a,b)=>b[1]-a[1]).map(([country,count])=>({{country,count}}));
      const top_cpc_codes = Object.entries(cpcs).sort((a,b)=>b[1]-a[1]).slice(0,8).map(([code,count])=>({{code,count}}));
      return {{
        ...data,
        normalized_results: normalized,
        landscape_analytics: {{
          result_count: normalized.length,
          unique_assignees: Object.keys(assignees).length,
          unique_countries: Object.keys(countries).length,
          top_assignees,
          year_histogram,
          country_breakdown,
          top_cpc_codes,
        }}
      }};
    }}

    function hydratePayload(raw) {{
      if (!raw || typeof raw !== "object") return;
      if ((raw.symbol || raw.classification_systems) && !raw.results) {{
        renderCpcLookupResults(raw);
        switchTab("cpcTab");
        return;
      }}
      currentPayload = normalizeClientSide(raw);
      activeFilter = null;
      if (currentPayload.query) document.getElementById("qInput").value = currentPayload.query;
      const filters = currentPayload.filters || currentPayload.query_parameters || {{}};
      if (filters.assignee) document.getElementById("assigneeInput").value = filters.assignee;
      if (filters.cpc_code) document.getElementById("cpcInput").value = filters.cpc_code;
      if (filters.country || filters.country_code) document.getElementById("countryInput").value = filters.country || filters.country_code;
      renderAll();
    }}

    function renderAll() {{
      if (!currentPayload) return;
      const analytics = currentPayload.landscape_analytics || {{}};
      const allResults = currentPayload.normalized_results || [];
      const filtered = activeFilter
        ? allResults.filter((r) => {{
            if (activeFilter.type === "assignee") return r.assignee === activeFilter.value;
            if (activeFilter.type === "year") return r.year === activeFilter.value;
            if (activeFilter.type === "country") return r.country === activeFilter.value;
            if (activeFilter.type === "cpc") {{
              return (r.cpc_codes || []).some((c) => String(c).startsWith(activeFilter.value));
            }}
            if (activeFilter.type === "matrix") {{
              return r.assignee === activeFilter.assignee &&
                (r.cpc_codes || []).some((c) => String(c).startsWith(activeFilter.cpc));
            }}
            return true;
          }})
        : allResults;

      document.getElementById("kpiCount").textContent = filtered.length + " / " + allResults.length;
      document.getElementById("kpiTopAssignee").textContent =
        (analytics.top_assignees && analytics.top_assignees[0] && analytics.top_assignees[0].name) || "—";
      document.getElementById("kpiAssignees").textContent = analytics.unique_assignees || 0;
      document.getElementById("kpiCountries").textContent = analytics.unique_countries || 0;

      const badge = document.getElementById("activeFilterBadge");
      if (activeFilter) {{
        badge.style.display = "inline-flex";
        badge.textContent = "Filter: " + (activeFilter.label || (activeFilter.type + " = " + activeFilter.value)) + " ✕";
      }} else {{
        badge.style.display = "none";
      }}

      // Render Top Assignees chart
      const assigneesEl = document.getElementById("assigneesChart");
      const topAssignees = analytics.top_assignees || [];
      const maxAss = Math.max(1, ...topAssignees.map((a) => a.count));
      assigneesEl.innerHTML = topAssignees.length
        ? topAssignees.map((a) => `
            <div class="bar-row" data-filter-type="assignee" data-filter-val="${{escapeHtml(a.name)}}">
              <span class="bar-label" title="${{escapeHtml(a.name)}}">${{escapeHtml(a.name)}}</span>
              <div class="bar-track"><div class="bar-fill" style="width:${{Math.round((a.count / maxAss) * 100)}}%"></div></div>
              <span class="bar-count">${{a.count}}</span>
            </div>
          `).join("")
        : '<div style="color:var(--text-muted);font-size:12px;">No assignee breakdown available.</div>';

      // Render Years chart
      const yearsEl = document.getElementById("yearsChart");
      const years = analytics.year_histogram || [];
      const maxYr = Math.max(1, ...years.map((y) => y.count));
      yearsEl.innerHTML = years.length
        ? years.map((y) => `
            <div class="bar-row" data-filter-type="year" data-filter-val="${{escapeHtml(y.year)}}">
              <span class="bar-label" style="width:65px;">${{escapeHtml(y.year)}}</span>
              <div class="bar-track"><div class="bar-fill" style="background:var(--teal);width:${{Math.round((y.count / maxYr) * 100)}}%"></div></div>
              <span class="bar-count">${{y.count}}</span>
            </div>
          `).join("")
        : '<div style="color:var(--text-muted);font-size:12px;">No publication year data available.</div>';

      // Render Jurisdictions & Clickable CPC Bars
      const jurEl = document.getElementById("jurisdictionsChart");
      const countries = analytics.country_breakdown || [];
      const cpcs = analytics.top_cpc_codes || [];
      const maxCpc = Math.max(1, ...cpcs.map((c) => c.count));
      jurEl.innerHTML = `
        <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px;">
          ${{countries.map((c) => `
            <span class="badge" style="cursor:pointer;background:var(--blue-light);color:var(--blue);" data-filter-type="country" data-filter-val="${{escapeHtml(c.country)}}">
              ${{escapeHtml(c.country)}} (${{c.count}})
            </span>
          `).join("")}}
        </div>
        <div style="font-size:11px;font-weight:700;color:var(--text-muted);margin-bottom:6px;">TOP CPC CLASSIFICATIONS (CLICK BAR TO FILTER)</div>
        <div>
          ${{cpcs.length ? cpcs.map((c) => `
            <div class="bar-row" data-filter-type="cpc" data-filter-val="${{escapeHtml(c.code)}}">
              <span class="bar-label" style="width:95px;font-family:var(--font-mono);">${{escapeHtml(c.code)}}</span>
              <div class="bar-track"><div class="bar-fill" style="background:var(--amber);width:${{Math.round((c.count / maxCpc) * 100)}}%"></div></div>
              <span class="bar-count">${{c.count}}</span>
            </div>
          `).join("") : '<span style="font-size:11.5px;color:var(--text-muted);">Click CPC Explorer tab to lookup CPC/IPC codes</span>'}}
        </div>
      `;

      // Render Assignee x CPC White-Space Opportunity Matrix
      const matrixEl = document.getElementById("whitespaceMatrixContainer");
      const matrixAssignees = topAssignees.slice(0, 5);
      const matrixCpcs = cpcs.slice(0, 5);
      if (matrixAssignees.length && matrixCpcs.length) {{
        matrixEl.innerHTML = `
          <table style="width:100%;border-collapse:collapse;font-size:11.5px;">
            <thead>
              <tr style="border-bottom:1px solid var(--border);text-align:left;">
                <th style="padding:7px 8px;color:var(--text-muted);">Assignee \\ CPC Tech Subclass</th>
                ${{matrixCpcs.map((c) => `
                  <th style="padding:7px 8px;text-align:center;font-family:var(--font-mono);color:var(--primary);cursor:pointer;" data-filter-type="cpc" data-filter-val="${{escapeHtml(c.code)}}">
                    ${{escapeHtml(c.code)}}
                  </th>
                `).join("")}}
              </tr>
            </thead>
            <tbody>
              ${{matrixAssignees.map((a) => `
                <tr style="border-bottom:1px solid var(--border);">
                  <td style="padding:7px 8px;font-weight:600;cursor:pointer;" data-filter-type="assignee" data-filter-val="${{escapeHtml(a.name)}}">
                    ${{escapeHtml(a.name)}}
                  </td>
                  ${{matrixCpcs.map((c) => {{
                    const cellCount = allResults.filter((r) =>
                      r.assignee === a.name && (r.cpc_codes || []).some((code) => String(code).startsWith(c.code))
                    ).length;
                    if (cellCount === 0) {{
                      return `<td style="padding:6px 8px;text-align:center;">
                        <span class="badge" style="background:var(--emerald-light);color:var(--emerald);font-weight:700;cursor:pointer;" data-filter-type="cpc" data-filter-val="${{escapeHtml(c.code)}}" title="White-Space Opportunity: ${{escapeHtml(a.name)}} has 0 filings in ${{escapeHtml(c.code)}}">
                          OPEN (0)
                        </span>
                      </td>`;
                    }}
                    return `<td style="padding:6px 8px;text-align:center;">
                      <span class="badge" style="background:var(--primary-light);color:var(--primary);font-weight:700;cursor:pointer;" data-matrix-ass="${{escapeHtml(a.name)}}" data-matrix-cpc="${{escapeHtml(c.code)}}">
                        ${{cellCount}} ${{cellCount === 1 ? 'filing' : 'filings'}}
                      </span>
                    </td>`;
                  }}).join("")}}
                </tr>
              `).join("")}}
            </tbody>
          </table>
        `;
      }} else {{
        matrixEl.innerHTML = '<div style="color:var(--text-muted);font-size:12px;">Run a search to populate the Assignee × CPC White-Space Opportunity Matrix.</div>';
      }}

      // Bind filter clicks
      document.querySelectorAll("[data-filter-type]").forEach((el) => {{
        el.addEventListener("click", () => {{
          const t = el.getAttribute("data-filter-type");
          const v = el.getAttribute("data-filter-val");
          if (activeFilter && activeFilter.type === t && activeFilter.value === v) activeFilter = null;
          else activeFilter = {{ type: t, value: v }};
          renderAll();
        }});
      }});
      document.querySelectorAll("[data-matrix-ass]").forEach((el) => {{
        el.addEventListener("click", () => {{
          const ass = el.getAttribute("data-matrix-ass");
          const cpc = el.getAttribute("data-matrix-cpc");
          if (activeFilter && activeFilter.type === "matrix" && activeFilter.assignee === ass && activeFilter.cpc === cpc) {{
            activeFilter = null;
          }} else {{
            activeFilter = {{ type: "matrix", assignee: ass, cpc: cpc, label: ass + " × " + cpc }};
          }}
          renderAll();
        }});
      }});

      const cardsHtml = filtered.map((p) => `
        <div class="patent-card">
          <div class="patent-card-top">
            ${{p.thumbnail_url ? `<img class="patent-thumb" src="${{escapeHtml(p.thumbnail_url)}}" alt="fig" />` : ""}}
            <div>
              <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;">
                <span class="patent-id">${{escapeHtml(p.id)}}</span>
                <span class="badge">${{escapeHtml(p.country)}}</span>
                ${{p.year && p.year !== "Unknown" ? `<span class="badge">${{escapeHtml(p.year)}}</span>` : ""}}
              </div>
              <div class="patent-title">${{escapeHtml(p.title)}}</div>
              <div style="font-size:11px;color:var(--teal);font-weight:600;margin-top:2px;">${{escapeHtml(p.assignee)}}</div>
            </div>
          </div>
          <div class="patent-snippet">${{escapeHtml(p.snippet)}}</div>
          <div style="display:flex;gap:6px;justify-content:flex-end;flex-wrap:wrap;margin-top:4px;">
            <a class="btn" href="${{SERVER_BASE}}/apps/pdf/${{encodeURIComponent(String(p.id || '').replace(/-/g, ''))}}" target="_blank" rel="noopener">PDF ↗</a>
            <a class="btn" href="${{SERVER_BASE}}/apps/patent/${{encodeURIComponent(String(p.id || '').replace(/-/g, ''))}}" target="_blank" rel="noopener">Patent Reader ↗</a>
          </div>
        </div>
      `).join("");

      document.getElementById("miniPatentList").innerHTML = cardsHtml || '<div style="color:var(--text-muted)">No matching patents in current slice.</div>';
      document.getElementById("fullPatentGrid").innerHTML = cardsHtml || '<div style="color:var(--text-muted)">No matching patents.</div>';
    }}

    function renderCpcLookupResults(data) {{
      const el = document.getElementById("cpcLookupResults");
      if (data.symbol) {{
        document.getElementById("cpcLookupInput").value = data.symbol;
        const parts = Array.isArray(data.title_parts) ? data.title_parts : [];
        const defs = Array.isArray(data.definitions) ? data.definitions : [];
        el.innerHTML = `
          <div style="padding:12px;border:1px solid var(--border);border-radius:8px;">
            <div style="font-weight:700;font-size:14px;color:var(--primary);font-family:var(--font-mono);">${{escapeHtml(data.symbol)}} (Level ${{escapeHtml(data.level || "—")}})</div>
            <div style="font-size:13px;font-weight:600;margin-top:4px;">${{escapeHtml(data.title_full || data.title || "")}}</div>
            ${{parts.length ? `<div style="margin-top:8px;font-size:11.5px;color:var(--text-secondary);"><strong>Hierarchy Breakdown:</strong> ${{parts.map(escapeHtml).join(" → ")}}</div>` : ""}}
            ${{defs.length ? `<div style="margin-top:8px;font-size:11.5px;color:var(--text-secondary);"><strong>Definition:</strong> ${{defs.map(escapeHtml).join(" ")}}</div>` : ""}}
          </div>
        `;
        return;
      }}
      const systems = data.classification_systems || [];
      el.innerHTML = systems.map((sys) => `
        <div style="padding:10px;border:1px solid var(--border);border-radius:8px;margin-bottom:8px;">
          <div style="font-weight:700;color:var(--primary);">${{escapeHtml(sys.system)}} — ${{escapeHtml(data.code_prefix || "")}}</div>
          <div style="font-size:12px;margin-top:4px;"><strong>Section:</strong> ${{escapeHtml(sys.section_description || "")}}</div>
        </div>
      `).join("");
    }}

    function switchTab(tabId) {{
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.toggle("active", b.dataset.tab === tabId));
      document.querySelectorAll(".workspace").forEach((w) => w.classList.toggle("active", w.id === tabId));
    }}

    document.querySelectorAll(".tab-btn").forEach((btn) => {{
      btn.addEventListener("click", () => switchTab(btn.dataset.tab));
    }});

    document.getElementById("activeFilterBadge").addEventListener("click", () => {{
      activeFilter = null;
      renderAll();
    }});

    document.getElementById("runSearchBtn").addEventListener("click", async () => {{
      const query = document.getElementById("qInput").value.trim();
      const assignee = document.getElementById("assigneeInput").value.trim();
      const cpc_code = document.getElementById("cpcInput").value.trim();
      const country_code = document.getElementById("countryInput").value.trim();
      document.getElementById("statusText").textContent = "Running landscape search...";
      try {{
        const res = await sendRpcRequest("tools/call", {{
          name: "advanced_patent_search",
          arguments: {{ query, assignee, cpc_code, country_code, limit: 20 }}
        }});
        if (res && Array.isArray(res.content)) {{
          for (const item of res.content) {{
            if (item.type === "text" && item.text) {{
              hydratePayload(JSON.parse(item.text));
              document.getElementById("statusText").textContent = "Landscape updated";
              return;
            }}
          }}
        }}
      }} catch (_) {{}}
      try {{
        const qs = new URLSearchParams({{ query, assignee, cpc_code, country_code }}).toString();
        const r = await fetch(`${{SERVER_BASE}}/apps/api/landscape?${{qs}}`);
        if (r.ok) {{
          hydratePayload(await r.json());
          document.getElementById("statusText").textContent = "Landscape updated";
          return;
        }}
      }} catch (_) {{}}
      document.getElementById("statusText").textContent = "Search via host unavailable; use chat prompt.";
    }});

    document.getElementById("cpcLookupBtn").addEventListener("click", async () => {{
      const code = document.getElementById("cpcLookupInput").value.trim();
      if (!code) return;
      document.getElementById("statusText").textContent = "Looking up CPC/IPC code " + code + "...";
      try {{
        const res = await sendRpcRequest("tools/call", {{
          name: "lookup_classification_code",
          arguments: {{ code }}
        }});
        if (res && Array.isArray(res.content)) {{
          for (const item of res.content) {{
            if (item.type === "text" && item.text) {{
              renderCpcLookupResults(JSON.parse(item.text));
              document.getElementById("statusText").textContent = "Classification lookup complete";
              return;
            }}
          }}
        }}
      }} catch (_) {{}}
      try {{
        const r = await fetch(`${{SERVER_BASE}}/apps/api/cpc-lookup?code=${{encodeURIComponent(code)}}`);
        if (r.ok) {{
          renderCpcLookupResults(await r.json());
          document.getElementById("statusText").textContent = "Classification lookup complete";
          return;
        }}
      }} catch (_) {{}}
      document.getElementById("statusText").textContent = "Lookup failed";
    }});

    document.getElementById("askLandscapeAiBtn").addEventListener("click", () => {{
      if (!currentPayload) return;
      const q = currentPayload.query || "current technology landscape";
      window.parent.postMessage({{
        jsonrpc: "2.0",
        method: "ui/message",
        params: {{
          role: "user",
          content: [{{
            type: "text",
            text: `Based on the patent landscape results for "${{q}}", identify the top assignees, filing velocity trends, and potential R&D white-space opportunities.`
          }}]
        }}
      }}, "*");
    }});

    if (INITIAL_PAYLOAD) {{
      hydratePayload(INITIAL_PAYLOAD);
    }}
  </script>
</body>
</html>"""
