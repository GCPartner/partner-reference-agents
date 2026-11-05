"""MCP App 2: Peer Group & SEC Cross-Market XBRL Frame Comparator.

Resource URI: `ui://sec-edgar/peer-industry-comparator`
MIME Type: `text/html;profile=mcp-app` (SEP-1865)
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from .brand_theme import (
    APEX_BRAND_THEME,
    DEFAULT_PUBLIC_API_BASE_URL,
    MCP_APP_MIME_TYPE,
    build_shared_css,
)

PEER_RESOURCE_URI = "ui://sec-edgar/peer-industry-comparator"

PEER_APP_TOOL_META: Dict[str, Any] = {
    "ui": {
        "resourceUri": PEER_RESOURCE_URI,
        "visibility": ["model", "app"],
    },
    "ui/resourceUri": PEER_RESOURCE_URI,
}

PEER_APP_RESOURCE_META: Dict[str, Any] = {
    "ui": {
        "prefersBorder": True,
        "csp": {
            "connectDomains": [d for d in [DEFAULT_PUBLIC_API_BASE_URL, "https://data.sec.gov", "https://www.sec.gov", "*"] if d],
            "resourceDomains": [d for d in [DEFAULT_PUBLIC_API_BASE_URL, "*"] if d],
            "frameDomains": [d for d in [DEFAULT_PUBLIC_API_BASE_URL, "*"] if d],
        },
    }
}

_LAST_PEER_PAYLOAD: Optional[Dict[str, Any]] = None


def set_cached_peer_payload(payload: Dict[str, Any]) -> None:
    """Stores the most recent enriched peer/industry comparator payload for `resources/read`."""
    global _LAST_PEER_PAYLOAD
    if isinstance(payload, dict):
        _LAST_PEER_PAYLOAD = payload


def get_cached_peer_payload() -> Optional[Dict[str, Any]]:
    """Returns the most recent enriched peer/industry comparator payload."""
    return _LAST_PEER_PAYLOAD


def enrich_peer_comparator_payload(
    peer_data: Optional[Dict[str, Any]] = None,
    frame_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Combines and enriches peer group matrix and SEC XBRL frame distribution payloads."""
    cached = _LAST_PEER_PAYLOAD or {}

    # Detect if a single dict was passed containing frame data vs peer data
    if isinstance(peer_data, dict) and "distribution_percentiles" in peer_data and frame_data is None:
        frame_data = peer_data
        peer_data = cached.get("peer_comparison")

    peer_sec = peer_data if isinstance(peer_data, dict) and "peer_comparison_table" in peer_data else (
        cached.get("peer_comparison") or {}
    )
    frame_sec = frame_data if isinstance(frame_data, dict) and "distribution_percentiles" in frame_data else (
        cached.get("industry_frame") or {}
    )

    peers: List[Dict[str, Any]] = list(peer_sec.get("peer_comparison_table") or [])
    benchmarks = peer_sec.get("peer_group_benchmarks") or {}
    medians = benchmarks.get("median") or {}
    means = benchmarks.get("mean") or {}

    # Compute spread vs median for each peer
    enriched_peers: List[Dict[str, Any]] = []
    for p in peers:
        if not isinstance(p, dict):
            continue
        spreads: Dict[str, Optional[float]] = {}
        for k, med_val in medians.items():
            val = p.get(k)
            if val is not None and med_val is not None:
                if k.endswith("_pct") or k in ("current_ratio", "debt_to_equity"):
                    spreads[k] = round(float(val) - float(med_val), 2)
                elif med_val != 0:
                    spreads[k] = round(((float(val) - float(med_val)) / abs(float(med_val))) * 100.0, 2)
        enriched_peers.append({
            **p,
            "spread_vs_median": spreads,
        })

    # Identify leaders for KPI strip
    rev_leader = max(
        (p for p in enriched_peers if p.get("revenue") is not None),
        key=lambda x: float(x.get("revenue") or 0),
        default={},
    )
    opm_leader = max(
        (p for p in enriched_peers if p.get("operating_margin_pct") is not None),
        key=lambda x: float(x.get("operating_margin_pct") or -999),
        default={},
    )

    enriched = {
        "status": "success",
        "app_resource_uri": PEER_RESOURCE_URI,
        "peer_comparison": {
            "period_type": peer_sec.get("period_type", "annual"),
            "fiscal_year_filter": peer_sec.get("fiscal_year_filter"),
            "peer_count": len(enriched_peers),
            "peer_comparison_table": enriched_peers,
            "peer_group_benchmarks": {
                "median": medians,
                "mean": means,
            },
            "leaders": {
                "revenue_leader_ticker": rev_leader.get("ticker"),
                "revenue_leader_val": rev_leader.get("revenue"),
                "opm_leader_ticker": opm_leader.get("ticker"),
                "opm_leader_val": opm_leader.get("operating_margin_pct"),
            },
        },
        "industry_frame": frame_sec,
    }
    set_cached_peer_payload(enriched)
    return enriched


def build_peer_comparator_html(
    initial_payload: Optional[Dict[str, Any]] = None,
    theme_overrides: Optional[Dict[str, str]] = None,
    api_base_url: Optional[str] = None,
) -> str:
    """Builds the self-contained HTML5/CSS/JS bundle for `ui://sec-edgar/peer-industry-comparator`."""
    theme = {**APEX_BRAND_THEME, **(theme_overrides or {})}
    shared_css = build_shared_css(theme)
    safe_json = json.dumps(initial_payload or get_cached_peer_payload() or None).replace("</", "<\\/")
    safe_api_base_url = json.dumps((api_base_url or DEFAULT_PUBLIC_API_BASE_URL).rstrip("/"))

    return f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Apex Capital Institutional Research | Peer &amp; Industry Comparator</title>
  <style>
    {shared_css}
    .comp-grid {{
      display: grid;
      grid-template-columns: 1.15fr 1fr;
      gap: 12px;
    }}
    @media (max-width: 920px) {{
      .comp-grid {{ grid-template-columns: 1fr; }}
    }}
    .chip-box {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 3px 8px;
      min-height: 32px;
      min-width: 340px;
    }}
    .ticker-chip {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
      background: #e2e8f0;
      border: 1px solid #cbd5e1;
      border-radius: 4px;
      padding: 2px 7px;
      font-family: var(--font-mono);
      font-size: 11.5px;
      font-weight: 700;
      color: #0f172a;
    }}
    .chip-remove {{
      cursor: pointer;
      color: #475569;
      font-weight: 800;
      border: none;
      background: transparent;
      font-size: 12px;
      line-height: 1;
    }}
    .chip-remove:hover {{
      color: var(--crimson);
    }}
    .chip-input {{
      border: none;
      outline: none;
      background: transparent;
      color: #0f172a;
      font-family: var(--font-sans);
      font-size: 12px;
      width: 95px;
    }}
    /* Slate Gold Percentile Thermometer matching Wireframe */
    .thermometer-track {{
      position: relative;
      height: 22px;
      border-radius: 4px;
      background: linear-gradient(90deg, #d97706 0%, #b45309 100%);
      margin: 24px 12px 26px 12px;
      border: 1px solid #92400e;
    }}
    .pct-marker {{
      position: absolute;
      top: -19px;
      transform: translateX(-50%);
      font-family: var(--font-sans);
      font-size: 10.5px;
      font-weight: 700;
      color: var(--text);
      text-align: center;
      white-space: nowrap;
    }}
    .pct-tick {{
      position: absolute;
      top: -3px;
      bottom: -3px;
      width: 1.5px;
      background: #0f172a;
    }}
    .pct-val {{
      position: absolute;
      top: 25px;
      transform: translateX(-50%);
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 700;
      color: var(--text);
      white-space: nowrap;
    }}
    .grouped-bar-area {{
      position: relative;
      padding: 4px 0;
    }}
  </style>
</head>
<body>
  <!-- Top Institutional Navy Bar (#0f172a) -->
  <header class="top-banner">
    <div class="brand-title">
      <span class="brand-logo">A</span>
      <span>{theme["brand_name"].upper()} | PEER &amp; INDUSTRY COMPARATOR</span>
    </div>
    <div class="control-group">
      <div class="pill-group" id="viewModePills">
        <button class="header-pill active" data-mode="split">Split Workbench</button>
        <button class="header-pill" data-mode="peers">Peer Group Matrix</button>
        <button class="header-pill" data-mode="frame">Industry XBRL Frame</button>
      </div>
      <button id="themeToggleBtn" class="btn btn-icon-header" title="Toggle Light/Dark Theme">☀️ / 🌙</button>
    </div>
  </header>

  <!-- Inset Rounded Deep Institutional Navy Control Banner (#0f172a) matching Wireframe -->
  <section class="control-strip">
    <div class="control-group" style="width:100%;justify-content:space-between;align-items:flex-end;">
      <div class="control-field" style="flex:1;min-width:320px;">
        <span class="control-label">Multi-Ticker</span>
        <div class="chip-box" id="peerChipsContainer">
          <span id="chipsList" style="display:inline-flex;gap:5px;flex-wrap:wrap;"></span>
          <input id="addPeerInput" class="chip-input" type="text" placeholder="+ Add Ticker" />
        </div>
      </div>

      <div class="control-field">
        <span class="control-label">Action</span>
        <select id="frameConceptSelect" class="select" style="min-width:165px;">
          <option value="revenue" selected>Revenues</option>
          <option value="operating_income">Operating Income (EBIT)</option>
          <option value="net_income">Net Income</option>
          <option value="total_assets">Total Assets</option>
          <option value="total_cash">Total Cash &amp; Securities</option>
          <option value="r_and_d">R&amp;D Expense</option>
          <option value="stockholders_equity">Stockholders' Equity</option>
        </select>
      </div>

      <div class="control-field">
        <span class="control-label">Period</span>
        <select id="calendarYearSelect" class="select" style="min-width:95px;">
          <option value="2024" selected>CY2024</option>
          <option value="2025">CY2025</option>
          <option value="2023">CY2023</option>
        </select>
      </div>

      <button id="comparePeersBtn" class="btn btn-neutral">Compare Peers</button>
    </div>
  </section>

  <main class="workspace">
    <!-- 4-Card KPI Strip -->
    <section class="kpi-grid" id="kpiStrip"></section>

    <div class="comp-grid" id="mainCompGrid">
      <!-- Left Column: Peer Group Financial Matrix -->
      <section class="panel" id="peerMatrixPanel" style="margin-bottom:0;">
        <div class="panel-header">
          <div>
            <span class="panel-title">PEER GROUP FINANCIAL MATRIX</span>
            <span class="panel-subtitle" id="matrixSortSubtitle">(SORTED BY GROSS MARGIN)</span>
          </div>
          <div class="pill-group" id="sortMetricPills">
            <button class="pill active" data-sort="gross_margin_pct">Gross Margin</button>
            <button class="pill" data-sort="operating_margin_pct">Op Margin</button>
            <button class="pill" data-sort="revenue">Revenue</button>
            <button class="pill" data-sort="roe_pct">ROE</button>
          </div>
        </div>
        <div class="table-wrap" id="peerMatrixTableContainer"></div>
      </section>

      <!-- Right Column: Stacked Grouped Bar Chart + SEC XBRL Frame Distribution -->
      <div id="rightStackPanel" style="display:flex;flex-direction:column;gap:12px;">
        <section class="panel" style="margin-bottom:0;">
          <div class="panel-header">
            <div>
              <div class="panel-title">GROUPED METRIC COMPARISON</div>
              <div class="panel-subtitle">(REVENUE vs OPERATING INCOME vs NET INCOME)</div>
            </div>
          </div>
          <div id="groupedBarChartContainer" class="grouped-bar-area"></div>
        </section>

        <section class="panel" id="industryFramePanel" style="margin-bottom:0;">
          <div class="panel-header">
            <div>
              <div class="panel-title">SEC XBRL FRAME INDUSTRY DISTRIBUTION</div>
              <div class="panel-subtitle" id="framePanelSubtitle">(us-gaap:Revenues — CY2024)</div>
            </div>
          </div>
          <div id="percentileThermometerContainer"></div>
          <div class="table-wrap" id="topReportersTableContainer"></div>
        </section>
      </div>
    </div>
  </main>

  <footer class="footer-bar">
    <span id="statusText">SEC EDGAR Multi-Entity XBRL Comparator</span>
    <button id="askAiPeerMemoBtn" class="btn btn-primary" style="padding:6px 14px;">[Ask Agent to Synthesize Peer Valuation &amp; Moat Analysis]</button>
  </footer>

  <script>
    const INITIAL_PAYLOAD = {safe_json};
    const API_BASE_URL = {safe_api_base_url};
    // Lock to the approved Light Mode institutional theme from mcp_apps_ux_design.md
    const LOCK_DESIGN_THEME = true;
    let currentPayload = null;
    let activePeers = ["AAPL", "MSFT", "GOOGL", "NVDA"];
    let activeSortKey = "gross_margin_pct";

    // =========================================================================
    // 1. SEP-1865 MCP Apps JSON-RPC 2.0 postMessage Bridge + HTTP Fallback
    // =========================================================================
    let rpcId = 1;
    const pendingRpc = new Map();

    function sendMcpRequest(method, params, timeoutMs = 4000) {{
      return new Promise((resolve, reject) => {{
        if (!window.parent || window.parent === window) {{
          reject(new Error("Standalone browser mode"));
          return;
        }}
        const id = String(rpcId++);
        pendingRpc.set(id, {{ resolve, reject }});
        window.parent.postMessage({{ jsonrpc: "2.0", id: Number(id), method, params }}, "*");
        setTimeout(() => {{
          if (pendingRpc.has(id)) {{
            pendingRpc.delete(id);
            reject(new Error("MCP Host RPC timeout"));
          }}
        }}, timeoutMs);
      }});
    }}

    function sendMcpNotification(method, params = {{}}) {{
      if (window.parent && window.parent !== window) {{
        window.parent.postMessage({{ jsonrpc: "2.0", method, params }}, "*");
      }}
    }}

    function extractToolPayload(raw) {{
      if (!raw) return null;
      if (typeof raw === "string") {{
        try {{
          return extractToolPayload(JSON.parse(raw));
        }} catch (_) {{
          return null;
        }}
      }}
      if (typeof raw !== "object") return null;
      if (raw.structuredContent && typeof raw.structuredContent === "object") {{
        return raw.structuredContent;
      }}
      if (raw.result) {{
        const inner = extractToolPayload(raw.result);
        if (inner) return inner;
      }}
      if (raw.toolResult) {{
        const inner = extractToolPayload(raw.toolResult);
        if (inner) return inner;
      }}
      const contentArr = Array.isArray(raw.content) ? raw.content : Array.isArray(raw) ? raw : null;
      if (contentArr) {{
        for (const block of contentArr) {{
          if (block && typeof block === "object") {{
            if (typeof block.text === "string" && block.text.trim()) {{
              try {{
                return JSON.parse(block.text);
              }} catch (_) {{}}
            }}
            if (block.json && typeof block.json === "object") return block.json;
            if (block.data && typeof block.data === "object") return block.data;
          }}
        }}
      }}
      if (
        raw.peer_comparison ||
        Array.isArray(raw.peer_comparison_matrix) ||
        Array.isArray(raw.peer_comparison_table) ||
        raw.industry_frame ||
        raw.distribution_statistics ||
        Array.isArray(raw.top_entities)
      ) {{
        return raw;
      }}
      return null;
    }}

    async function fetchDirectToolCall(toolName, args) {{
      const endpoints = [];
      if (
        typeof window !== "undefined" &&
        window.location &&
        window.location.origin &&
        window.location.origin !== "null" &&
        window.location.protocol.startsWith("http")
      ) {{
        endpoints.push(`${{window.location.origin}}/apps/api/tool-call`);
      }}
      if (API_BASE_URL && !endpoints.includes(`${{API_BASE_URL}}/apps/api/tool-call`)) {{
        endpoints.push(`${{API_BASE_URL}}/apps/api/tool-call`);
      }}
      for (const url of endpoints) {{
        try {{
          const resp = await fetch(url, {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify({{ name: toolName, arguments: args }}),
          }});
          if (resp.ok) {{
            const data = await resp.json();
            const extracted = extractToolPayload(data);
            if (extracted) return extracted;
          }}
        }} catch (_) {{}}
      }}
      return null;
    }}

    async function callMcpToolWithFallback(toolName, args) {{
      document.getElementById("statusText").textContent = `Calling MCP tool ${{toolName}}...`;
      try {{
        const res = await sendMcpRequest("tools/call", {{ name: toolName, arguments: args }}, 2500);
        const extracted = extractToolPayload(res);
        if (extracted) {{
          document.getElementById("statusText").textContent = `Updated via MCP Host tools/call (${{toolName}})`;
          return extracted;
        }}
      }} catch (_) {{}}

      const directData = await fetchDirectToolCall(toolName, args);
      if (directData) {{
        document.getElementById("statusText").textContent = `Updated via live SEC EDGAR API (${{toolName}})`;
        return directData;
      }}
      document.getElementById("statusText").textContent = `Completed tool call (${{toolName}})`;
      return null;
    }}

    window.addEventListener("message", (event) => {{
      let msg = event.data;
      if (typeof msg === "string") {{
        try {{
          msg = JSON.parse(msg);
        }} catch (_) {{
          return;
        }}
      }}
      if (!msg || typeof msg !== "object" || msg.jsonrpc !== "2.0") return;

      const msgIdKey = msg.id !== undefined && msg.id !== null ? String(msg.id) : null;
      if (msgIdKey && pendingRpc.has(msgIdKey)) {{
        const {{ resolve, reject }} = pendingRpc.get(msgIdKey);
        pendingRpc.delete(msgIdKey);
        if (msg.error) reject(msg.error);
        else resolve(msg.result);
        return;
      }}

      if (msg.method === "ui/notifications/tool-input" && msg.params?.arguments) {{
        const ids = msg.params.arguments.identifiers;
        if (Array.isArray(ids) && ids.length) {{
          activePeers = ids.map((x) => String(x).toUpperCase());
          renderPeerChips();
        }}
      }} else if ((msg.method === "ui/notifications/tool-result" || msg.method === "notifications/tool-result") && msg.params) {{
        const extracted = extractToolPayload(msg.params);
        if (extracted) hydratePayload(extracted);
      }} else if (msg.method === "ui/notifications/host-context-changed") {{
        if (!LOCK_DESIGN_THEME) {{
          const t = msg.params?.theme;
          if (t === "dark" || t === "light") {{
            document.documentElement.setAttribute("data-theme", t);
          }}
        }}
      }}
    }});

    async function initBridge() {{
      if (window.parent && window.parent !== window) {{
        try {{
          const res = await sendMcpRequest("ui/initialize", {{
            protocolVersion: "2025-06-18",
            appInfo: {{ name: "Apex Capital Peer & Industry Comparator", version: "1.0.0" }},
            appCapabilities: {{}},
          }}, 4000);
          if (!LOCK_DESIGN_THEME && res?.hostContext?.theme) {{
            document.documentElement.setAttribute("data-theme", res.hostContext.theme);
          }}
        }} catch (_) {{}}
        sendMcpNotification("ui/notifications/initialized", {{}});
      }}
      if (typeof ResizeObserver !== "undefined") {{
        new ResizeObserver(() => {{
          sendMcpNotification("ui/notifications/size-changed", {{
            width: document.documentElement.scrollWidth,
            height: document.documentElement.scrollHeight,
          }});
        }}).observe(document.body);
      }}
    }}

    // =========================================================================
    // 2. Formatting Helpers
    // =========================================================================
    function escapeHtml(s) {{
      return String(s ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }}

    function fmtUsdCompact(v) {{
      if (v === null || v === undefined || Number.isNaN(Number(v))) return "—";
      const n = Number(v);
      const sign = n < 0 ? "-" : "";
      const abs = Math.abs(n);
      if (abs >= 1e12) return `${{sign}}$${{(abs / 1e12).toFixed(2)}}T`;
      if (abs >= 1e9) return `${{sign}}$${{(abs / 1e9).toFixed(1)}}B`;
      if (abs >= 1e6) return `${{sign}}$${{(abs / 1e6).toFixed(0)}}M`;
      if (abs >= 1e3) return `${{sign}}$${{(abs / 1e3).toFixed(1)}}K`;
      return `${{sign}}$${{abs.toFixed(0)}}`;
    }}

    function fmtPct(v) {{
      if (v === null || v === undefined || Number.isNaN(Number(v))) return "—";
      return `${{Number(v).toFixed(1)}}%`;
    }}

    function renderPeerChips() {{
      document.getElementById("chipsList").innerHTML = activePeers
        .map(
          (t) => `
        <span class="ticker-chip">
          ${{escapeHtml(t)}}
          <button class="chip-remove" data-remove-peer="${{escapeHtml(t)}}" title="Remove ${{escapeHtml(t)}}">×</button>
        </span>`
        )
        .join("");

      document.querySelectorAll("[data-remove-peer]").forEach((btn) => {{
        btn.addEventListener("click", () => {{
          const rm = btn.getAttribute("data-remove-peer");
          if (activePeers.length > 2) {{
            activePeers = activePeers.filter((x) => x !== rm);
            renderPeerChips();
          }}
        }});
      }});
    }}

    // =========================================================================
    // 3. Payload Hydration & Rendering
    // =========================================================================
    function hydratePayload(raw) {{
      if (!raw || typeof raw !== "object") return;
      const prev = currentPayload && typeof currentPayload === "object" ? currentPayload : {{}};
      const nextPayload = {{ ...prev }};

      if (raw.peer_comparison && Array.isArray(raw.peer_comparison.peer_comparison_table)) {{
        nextPayload.peer_comparison = raw.peer_comparison;
      }} else if (Array.isArray(raw.peer_comparison_table)) {{
        nextPayload.peer_comparison = raw;
      }}

      if (raw.industry_frame && (raw.industry_frame.distribution_percentiles || raw.industry_frame.top_leaders)) {{
        nextPayload.industry_frame = raw.industry_frame;
      }} else if (raw.distribution_percentiles || raw.top_leaders) {{
        nextPayload.industry_frame = {{
          taxonomy: raw.frame?.taxonomy || raw.taxonomy || "us-gaap",
          tag_resolved: raw.frame?.tag || raw.tag_resolved || "Revenues",
          frame_period: raw.frame?.frame_id || raw.frame_period || "CY2024",
          total_reporting_entities: raw.total_reporting_entities || 0,
          distribution_percentiles: raw.distribution_percentiles || {{}},
          highlighted_company_benchmark: raw.highlighted_company || raw.highlighted_company_benchmark || null,
          top_leaders: raw.top_leaders || [],
        }};
      }}

      currentPayload = nextPayload;

      const peerTable = currentPayload.peer_comparison?.peer_comparison_table || [];
      if (peerTable.length) {{
        activePeers = peerTable.map((p) => p.ticker || p.cik).filter(Boolean);
      }}
      renderPeerChips();
      renderKpiStrip();
      renderPeerMatrix();
      renderGroupedBars();
      renderIndustryFrame();
    }}

    function renderKpiStrip() {{
      const pc = currentPayload?.peer_comparison || currentPayload || {{}};
      const leaders = pc.leaders || {{}};
      const medians = pc.peer_group_benchmarks?.median || {{}};
      const frame = currentPayload?.industry_frame || {{}};
      const hl = frame.highlighted_company_benchmark;

      const cards = [
        {{
          label: "Revenue Leader",
          val: leaders.revenue_leader_ticker ? `${{leaders.revenue_leader_ticker}} (${{fmtUsdCompact(leaders.revenue_leader_val)}})` : "—",
          sub: `<span class="text-muted-mono">Peer Median: ${{fmtUsdCompact(medians.revenue)}}</span>`,
        }},
        {{
          label: "Operating Margin Leader",
          val: leaders.opm_leader_ticker ? `${{leaders.opm_leader_ticker}} (${{fmtPct(leaders.opm_leader_val)}})` : "—",
          sub: `<span class="text-emerald">Top Operating Leverage</span>`,
        }},
        {{
          label: "Peer Group Median Margins",
          val: `GM ${{fmtPct(medians.gross_margin_pct)}} | OPM ${{fmtPct(medians.operating_margin_pct)}}`,
          sub: `<span class="text-gold">Median ROE: ${{fmtPct(medians.roe_pct)}}</span>`,
        }},
        {{
          label: "SEC Market Frame Scope",
          val: hl ? `#${{hl.rank}} / ${{(frame.total_reporting_entities || 0).toLocaleString()}}` : `${{(frame.total_reporting_entities || 0).toLocaleString()}} Entities`,
          sub: hl
            ? `<span class="text-emerald">${{escapeHtml(hl.entity_name || "")}} (${{hl.percentile_rank}}th %ile)</span>`
            : `<span class="text-muted-mono">Frame ${{escapeHtml(frame.frame_period || "CY2024")}}</span>`,
        }},
      ];

      document.getElementById("kpiStrip").innerHTML = cards
        .map(
          (c) => `
        <div class="kpi-card">
          <div class="kpi-label">${{escapeHtml(c.label)}}</div>
          <div class="kpi-val" style="font-size:17px;">${{escapeHtml(c.val)}}</div>
          <div class="kpi-sub">${{c.sub}}</div>
        </div>`
        )
        .join("");
    }}

    function renderPeerMatrix() {{
      const pc = currentPayload?.peer_comparison || currentPayload || {{}};
      const peers = (pc.peer_comparison_table || []).slice();
      const medians = pc.peer_group_benchmarks?.median || {{}};

      peers.sort((a, b) => Number(b[activeSortKey] ?? -999999) - Number(a[activeSortKey] ?? -999999));

      const sortLabels = {{
        gross_margin_pct: "(SORTED BY GROSS MARGIN)",
        operating_margin_pct: "(SORTED BY OPERATING MARGIN)",
        revenue: "(SORTED BY REVENUE)",
        roe_pct: "(SORTED BY ROE)",
      }};
      document.getElementById("matrixSortSubtitle").textContent = sortLabels[activeSortKey] || "(SORTED BY GROSS MARGIN)";

      if (!peers.length) {{
        document.getElementById("peerMatrixTableContainer").innerHTML = `<div style="padding:14px;color:var(--text-muted)">No peer comparison data loaded.</div>`;
        return;
      }}

      const maxGm = Math.max(...peers.map((p) => Number(p.gross_margin_pct ?? -999)));

      let html = `<table class="fin-table"><thead><tr>
        <th>Metric</th>
        <th>Rev</th>
        <th>Gross Margin</th>
        <th>Op Margin</th>
        <th>ROE</th>
        <th>Current Ratio</th>
      </tr></thead><tbody>`;

      for (const p of peers) {{
        const gm = p.gross_margin_pct;
        const roe = p.roe_pct;
        // Solid emerald pill on top Gross Margin leader matching Wireframe (75.0%)
        const gmBadge = gm != null && Number(gm) === maxGm
          ? `<span class="badge-emerald-solid">${{fmtPct(gm)}}</span>`
          : fmtPct(gm);

        // Solid emerald / solid crimson pills on ROE matching Wireframe (147.2%, 37.1%, 115.4%)
        let roeCell = fmtPct(roe);
        if (roe != null && medians.roe_pct != null) {{
          const cls = Number(roe) >= Number(medians.roe_pct) ? "badge-emerald-solid" : "badge-crimson-solid";
          roeCell = `<span class="${{cls}}">${{fmtPct(roe)}}</span>`;
        }}

        html += `<tr>
          <td>
            <a class="ext-link" style="font-family:var(--font-mono);font-weight:700;" href="/apps/raw/financial-dossier-workbench?identifier=${{encodeURIComponent(p.ticker || p.cik)}}" target="_blank" rel="noopener noreferrer" title="Open ${{escapeHtml(p.name || p.ticker)}} in 360° Dossier">${{escapeHtml(p.ticker || p.cik)}}</a>
          </td>
          <td>${{fmtUsdCompact(p.revenue)}}</td>
          <td>${{gmBadge}}</td>
          <td>${{fmtPct(p.operating_margin_pct)}}</td>
          <td>${{roeCell}}</td>
          <td>${{p.current_ratio != null ? Number(p.current_ratio).toFixed(2) + "x" : "—"}}</td>
        </tr>`;
      }}

      html += `<tr class="median-row">
        <td style="font-family:var(--font-sans);font-weight:800;">PEER GROUP MEDIAN</td>
        <td>${{fmtUsdCompact(medians.revenue)}}</td>
        <td>${{fmtPct(medians.gross_margin_pct)}}</td>
        <td>${{fmtPct(medians.operating_margin_pct)}}</td>
        <td>${{fmtPct(medians.roe_pct)}}</td>
        <td>${{medians.current_ratio != null ? Number(medians.current_ratio).toFixed(2) + "x" : "—"}}</td>
      </tr></tbody></table>`;

      document.getElementById("peerMatrixTableContainer").innerHTML = html;
    }}

    function renderGroupedBars() {{
      const pc = currentPayload?.peer_comparison || currentPayload || {{}};
      const peers = (pc.peer_comparison_table || []).slice();
      if (!peers.length) return;

      const maxVal = Math.max(
        1,
        ...peers.flatMap((p) => [
          Math.abs(Number(p.revenue || 0)),
          Math.abs(Number(p.operating_income || 0)),
          Math.abs(Number(p.net_income || 0)),
        ])
      );

      let html = `
        <div style="display:flex;gap:14px;font-size:11px;font-weight:600;margin-bottom:8px;justify-content:flex-end;">
          <span style="display:inline-flex;align-items:center;gap:5px;"><span style="display:inline-block;width:12px;height:8px;background:var(--navy-bar);border-radius:1.5px;"></span> Revenue</span>
          <span style="display:inline-flex;align-items:center;gap:5px;"><span style="display:inline-block;width:12px;height:8px;background:var(--emerald);border-radius:1.5px;"></span> Operating Income</span>
          <span style="display:inline-flex;align-items:center;gap:5px;"><span style="display:inline-block;width:12px;height:8px;background:var(--gold);border-radius:1.5px;"></span> Net Income</span>
        </div>`;

      for (const p of peers) {{
        const revW = Math.max(3, Math.round((Math.abs(Number(p.revenue || 0)) / maxVal) * 100));
        const opW = Math.max(3, Math.round((Math.abs(Number(p.operating_income || 0)) / maxVal) * 100));
        const niW = Math.max(3, Math.round((Math.abs(Number(p.net_income || 0)) / maxVal) * 100));

        html += `
          <div style="display:grid;grid-template-columns:56px 1fr;align-items:center;gap:10px;margin-bottom:10px;">
            <strong style="font-family:var(--font-mono);font-size:12px;text-align:right;color:var(--text);">${{escapeHtml(p.ticker || p.cik)}}</strong>
            <div style="display:flex;flex-direction:column;gap:3px;border-left:1px solid var(--border);padding-left:6px;background:linear-gradient(90deg, transparent 24.8%, var(--border-subtle) 25%, transparent 25.2%, transparent 49.8%, var(--border-subtle) 50%, transparent 50.2%, transparent 74.8%, var(--border-subtle) 75%, transparent 75.2%);">
              <div style="height:8px;width:${{revW}}%;background:var(--navy-bar);border-radius:1.5px;" title="Revenue: ${{fmtUsdCompact(p.revenue)}}"></div>
              <div style="height:8px;width:${{opW}}%;background:var(--emerald);border-radius:1.5px;" title="Operating Income: ${{fmtUsdCompact(p.operating_income)}}"></div>
              <div style="height:8px;width:${{niW}}%;background:var(--gold);border-radius:1.5px;" title="Net Income: ${{fmtUsdCompact(p.net_income)}}"></div>
            </div>
          </div>`;
      }}

      document.getElementById("groupedBarChartContainer").innerHTML = html;
    }}

    function renderIndustryFrame() {{
      const frame = currentPayload?.industry_frame || (currentPayload?.distribution_percentiles ? currentPayload : {{}});
      const pcts = frame.distribution_percentiles || {{}};
      const topLeaders = frame.top_leaders || [];

      if (!frame.tag_resolved && !topLeaders.length) {{
        document.getElementById("percentileThermometerContainer").innerHTML = `<div style="padding:10px;color:var(--text-muted)">No XBRL Frame distribution loaded.</div>`;
        document.getElementById("topReportersTableContainer").innerHTML = "";
        return;
      }}

      const entityCount = (frame.total_reporting_entities || 0).toLocaleString();
      document.getElementById("framePanelSubtitle").textContent = `(${{frame.taxonomy || "us-gaap"}}:${{frame.tag_resolved || "Revenues"}} — ${{frame.frame_period || "CY2024"}}, N=${{entityCount}} Entities)`;

      const markers = [
        {{ label: "P25", pos: 16, val: pcts.p25 }},
        {{ label: "P50 Median", pos: 46, val: pcts.p50_median }},
        {{ label: "P75", pos: 74, val: pcts.p75 }},
        {{ label: "P90", pos: 92, val: pcts.p90 }},
      ];

      let thermHtml = `<div style="display:flex;align-items:center;gap:8px;">
        <span style="font-size:11.5px;font-weight:600;color:var(--text);width:64px;">Percentile</span>
        <div class="thermometer-track" style="flex:1;">`;

      for (const m of markers) {{
        thermHtml += `
          <div class="pct-marker" style="left:${{m.pos}}%;">${{escapeHtml(m.label)}}</div>
          <div class="pct-tick" style="left:${{m.pos}}%;"></div>
          <div class="pct-val" style="left:${{m.pos}}%;">${{fmtUsdCompact(m.val)}}</div>`;
      }}
      thermHtml += `</div></div>`;
      document.getElementById("percentileThermometerContainer").innerHTML = thermHtml;

      let tbl = `<table class="fin-table" style="margin-top:6px;"><thead><tr>
        <th>Top Industry Reporters</th>
        <th>Reported Value</th>
        <th>Action</th>
      </tr></thead><tbody>`;

      for (const item of topLeaders.slice(0, 6)) {{
        tbl += `<tr>
          <td style="font-family:var(--font-sans);"><strong>#${{item.rank}}</strong> ${{escapeHtml(item.entity_name)}}</td>
          <td>${{fmtUsdCompact(item.val)}}</td>
          <td><a class="ext-link" href="/apps/raw/financial-dossier-workbench?identifier=${{encodeURIComponent(item.cik)}}" target="_blank" rel="noopener noreferrer">Open in Dossier ↗</a></td>
        </tr>`;
      }}
      tbl += `</tbody></table>`;
      document.getElementById("topReportersTableContainer").innerHTML = tbl;
    }}

    // =========================================================================
    // 4. Interactive Event Listeners
    // =========================================================================
    document.getElementById("themeToggleBtn").addEventListener("click", () => {{
      const cur = document.documentElement.getAttribute("data-theme") || "light";
      document.documentElement.setAttribute("data-theme", cur === "dark" ? "light" : "dark");
    }});

    document.querySelectorAll("#viewModePills .header-pill").forEach((pill) => {{
      pill.addEventListener("click", () => {{
        document.querySelectorAll("#viewModePills .header-pill").forEach((p) => p.classList.remove("active"));
        pill.classList.add("active");
        const mode = pill.getAttribute("data-mode");
        const grid = document.getElementById("mainCompGrid");
        const peerPanel = document.getElementById("peerMatrixPanel");
        const rightPanel = document.getElementById("rightStackPanel");
        if (mode === "peers") {{
          grid.style.gridTemplateColumns = "1fr";
          peerPanel.style.display = "block";
          rightPanel.style.display = "none";
        }} else if (mode === "frame") {{
          grid.style.gridTemplateColumns = "1fr";
          peerPanel.style.display = "none";
          rightPanel.style.display = "flex";
        }} else {{
          grid.style.gridTemplateColumns = "";
          peerPanel.style.display = "block";
          rightPanel.style.display = "flex";
        }}
      }});
    }});

    document.querySelectorAll("#sortMetricPills .pill").forEach((pill) => {{
      pill.addEventListener("click", () => {{
        document.querySelectorAll("#sortMetricPills .pill").forEach((p) => p.classList.remove("active"));
        pill.classList.add("active");
        activeSortKey = pill.getAttribute("data-sort");
        renderPeerMatrix();
      }});
    }});

    document.getElementById("addPeerInput").addEventListener("keydown", (e) => {{
      if (e.key === "Enter" || e.key === ",") {{
        e.preventDefault();
        const val = e.target.value.replace(/,/g, "").trim().toUpperCase();
        if (val && !activePeers.includes(val) && activePeers.length < 10) {{
          activePeers.push(val);
          e.target.value = "";
          renderPeerChips();
        }}
      }}
    }});

    document.getElementById("comparePeersBtn").addEventListener("click", async () => {{
      const pendingTicker = document.getElementById("addPeerInput").value.trim().toUpperCase();
      if (pendingTicker && !activePeers.includes(pendingTicker) && activePeers.length < 10) {{
        activePeers.push(pendingTicker);
        document.getElementById("addPeerInput").value = "";
        renderPeerChips();
      }}
      const benchmark_concept = document.getElementById("frameConceptSelect").value;
      const calendar_year = Number(document.getElementById("calendarYearSelect").value || 2024);

      const data = await callMcpToolWithFallback("open_peer_industry_comparator_app", {{
        identifiers: activePeers,
        period_type: "annual",
        benchmark_concept,
        calendar_year,
      }});
      if (data) hydratePayload(data);
    }});

    document.getElementById("frameConceptSelect").addEventListener("change", () => {{
      document.getElementById("comparePeersBtn").click();
    }});

    document.getElementById("calendarYearSelect").addEventListener("change", () => {{
      document.getElementById("comparePeersBtn").click();
    }});

    document.getElementById("askAiPeerMemoBtn").addEventListener("click", () => {{
      const pc = currentPayload?.peer_comparison || currentPayload || {{}};
      const peers = pc.peer_comparison_table || [];
      const medians = pc.peer_group_benchmarks?.median || {{}};
      const lines = peers.map(
        (p) => `- ${{p.ticker}}: Rev ${{fmtUsdCompact(p.revenue)}}, Gross Margin ${{fmtPct(p.gross_margin_pct)}}, Op Margin ${{fmtPct(p.operating_margin_pct)}}, ROE ${{fmtPct(p.roe_pct)}}, Current Ratio ${{p.current_ratio != null ? Number(p.current_ratio).toFixed(2) + "x" : "—"}}`
      );
      sendMcpNotification("ui/message", {{
        role: "user",
        content: [{{
          type: "text",
          text: `Please synthesize an institutional Peer Valuation, Competitive Moat & Operating Margin spread analysis across (${{activePeers.join(", ")}}) relative to the Peer Group Median (Median Rev ${{fmtUsdCompact(medians.revenue)}}, Median Gross Margin ${{fmtPct(medians.gross_margin_pct)}}, Median Op Margin ${{fmtPct(medians.operating_margin_pct)}}):\\n${{lines.join("\\n")}}`
        }}],
      }});
      document.getElementById("statusText").textContent = "Sent Peer Valuation & Moat synthesis prompt to AI host";
    }});

    renderPeerChips();
    initBridge();
    if (INITIAL_PAYLOAD) hydratePayload(INITIAL_PAYLOAD);
  </script>
</body>
</html>"""
