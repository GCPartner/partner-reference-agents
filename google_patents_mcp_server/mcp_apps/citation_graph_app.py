"""View 3: Interactive Patent Citation & ScaM Similarity Network Graph MCP App.

Implements `ui://google-patents/citation-graph` (`mimeType="text/html;profile=mcp-app"`):
1. Supports payloads from `get_patent_citations`, `find_similar_patents`, and
   `open_patent_citation_graph_app`.
2. Interactive 3-Tab Workbench:
   - Tab 1: Interactive SVG Directed Citation & Similarity Network Graph + Multi-Hop Node Inspector
   - Tab 2: Backward / Forward / Similar Patent Matrix with Examiner-Cited Filter
   - Tab 3: Non-Patent Literature (NPL) Citation Inspector
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from .claim_tree_app import CLAIM_TREE_RESOURCE_META, MCP_APP_MIME_TYPE

CITATION_GRAPH_RESOURCE_URI = "ui://google-patents/citation-graph"

CITATION_GRAPH_TOOL_META: Dict[str, Any] = {
    "ui": {
        "resourceUri": CITATION_GRAPH_RESOURCE_URI,
        "visibility": ["model", "app"],
    },
    "ui/resourceUri": CITATION_GRAPH_RESOURCE_URI,
}

_CITATION_GRAPH_CACHE: Dict[str, Dict[str, Any]] = {}
_LAST_CITATION_KEY: Optional[str] = None


def set_cached_citation_payload(patent_id: str, payload: Dict[str, Any]) -> None:
    global _LAST_CITATION_KEY
    if not patent_id or not isinstance(payload, dict):
        return
    clean = patent_id.replace("-", "").strip().upper()
    existing = _CITATION_GRAPH_CACHE.get(clean, {})
    merged = dict(existing)
    merged.update(payload)
    _CITATION_GRAPH_CACHE[clean] = merged
    _CITATION_GRAPH_CACHE[patent_id.strip().upper()] = merged
    _LAST_CITATION_KEY = clean


def get_cached_citation_payload(patent_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    if patent_id:
        clean = patent_id.replace("-", "").strip().upper()
        if clean in _CITATION_GRAPH_CACHE:
            return _CITATION_GRAPH_CACHE[clean]
        if patent_id.strip().upper() in _CITATION_GRAPH_CACHE:
            return _CITATION_GRAPH_CACHE[patent_id.strip().upper()]
    if _LAST_CITATION_KEY and _LAST_CITATION_KEY in _CITATION_GRAPH_CACHE:
        return _CITATION_GRAPH_CACHE[_LAST_CITATION_KEY]
    return None


def enrich_citation_or_similar_payload(data: Dict[str, Any], mode: Optional[str] = None) -> Dict[str, Any]:
    """Normalizes and caches output from `get_patent_citations` or `find_similar_patents`."""
    if not isinstance(data, dict) or data.get("error"):
        return data

    enriched = dict(data)
    pub_num = (
        enriched.get("publication_number")
        or enriched.get("target_patent")
        or enriched.get("patent_id")
        or ""
    )
    if pub_num and "publication_number" not in enriched:
        enriched["publication_number"] = pub_num

    # Merge with any previously cached similar/citation slice for the same patent
    prev = get_cached_citation_payload(str(pub_num)) if pub_num else None
    if prev:
        if "backward_citations" not in enriched and "backward_citations" in prev:
            enriched["backward_citations"] = prev["backward_citations"]
            enriched["backward_count"] = prev.get("backward_count", len(prev["backward_citations"]))
        if "forward_citations" not in enriched and "forward_citations" in prev:
            enriched["forward_citations"] = prev["forward_citations"]
            enriched["forward_count"] = prev.get("forward_count", len(prev["forward_citations"]))
        if "similar_patents" not in enriched and "similar_patents" in prev:
            enriched["similar_patents"] = prev["similar_patents"]
            enriched["total_similar_found"] = len(prev["similar_patents"])

    back = enriched.get("backward_citations") or []
    fwd = enriched.get("forward_citations") or []
    sim = enriched.get("similar_patents") or []
    npl = enriched.get("non_patent_literature_citations") or []

    examiner_count = sum(
        1
        for c in (back + fwd)
        if any(
            tok in str(c.get("category") or "").upper()
            for tok in ("EXA", "SEA", "*", "X", "Y")
        )
    )
    enriched["examiner_cited_count"] = examiner_count
    enriched["similar_count"] = len(sim)
    enriched["npl_count"] = len(npl)
    enriched["mcp_app"] = {
        "resource_uri": CITATION_GRAPH_RESOURCE_URI,
        "mime_type": MCP_APP_MIME_TYPE,
        "view": "citation-graph",
    }

    if pub_num:
        set_cached_citation_payload(str(pub_num), enriched)
    return enriched


def build_citation_graph_app_html(initial_data: Optional[Dict[str, Any]] = None) -> str:
    """Builds the self-contained HTML/CSS/JS bundle for `ui://google-patents/citation-graph`."""
    import os
    initial_json = json.dumps(initial_data or {}).replace("</", "<\\/")
    server_base_json = json.dumps(os.environ.get("MCP_PUBLIC_BASE_URL", "").rstrip("/"))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Google Patents — Citation & Similarity Network Graph (MCP App)</title>
  <style>
    :root {{
      --bg-app: #f8fafc;
      --bg-surface: #ffffff;
      --bg-muted: #f1f5f9;
      --bg-accent: #eff6ff;
      --text-main: #0f172a;
      --text-secondary: #334155;
      --text-muted: #64748b;
      --border-color: #e2e8f0;
      --border-strong: #cbd5e1;
      --brand-blue: #1a73e8;
      --brand-green: #059669;
      --brand-purple: #7c3aed;
      --brand-amber: #d97706;
      --radius-sm: 6px;
      --radius-md: 10px;
      --radius-lg: 14px;
      --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, sans-serif;
      --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }}
    [data-theme="dark"] {{
      --bg-app: #0f172a;
      --bg-surface: #1e293b;
      --bg-muted: #334155;
      --bg-accent: #1e3a8a;
      --text-main: #f8fafc;
      --text-secondary: #cbd5e1;
      --text-muted: #94a3b8;
      --border-color: #334155;
      --border-strong: #475569;
      --brand-blue: #60a5fa;
      --brand-green: #34d399;
      --brand-purple: #a78bfa;
      --brand-amber: #fbbf24;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      padding: 0;
      font-family: var(--font-sans);
      background: var(--bg-app);
      color: var(--text-main);
      font-size: 13.5px;
    }}
    .app-shell {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}
    .header-card {{
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-lg);
      padding: 14px 18px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}
    .header-top {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 12px;
      flex-wrap: wrap;
    }}
    .mcp-badge {{
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      padding: 3px 8px;
      border-radius: 999px;
      background: var(--bg-accent);
      color: var(--brand-blue);
    }}
    .pub-badge {{
      font-family: var(--font-mono);
      font-size: 12.5px;
      font-weight: 700;
      padding: 3px 9px;
      border-radius: var(--radius-sm);
      background: var(--brand-green);
      color: #fff;
    }}
    .patent-title {{
      margin: 4px 0 0 0;
      font-size: 17px;
      font-weight: 700;
    }}
    .loader-bar {{
      display: flex;
      gap: 6px;
      align-items: center;
      flex-wrap: wrap;
    }}
    .input-box {{
      padding: 6px 10px;
      border: 1px solid var(--border-strong);
      border-radius: var(--radius-sm);
      background: var(--bg-surface);
      color: var(--text-main);
      font-family: var(--font-mono);
      font-size: 12.5px;
    }}
    .btn {{
      padding: 6px 12px;
      border-radius: var(--radius-sm);
      font-size: 12.5px;
      font-weight: 600;
      cursor: pointer;
      border: 1px solid var(--border-strong);
      background: var(--bg-surface);
      color: var(--text-main);
    }}
    .btn-primary {{
      background: var(--brand-blue);
      color: #fff;
      border-color: var(--brand-blue);
    }}
    .btn-sm {{ padding: 4px 8px; font-size: 11.5px; }}
    .kpi-strip {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(145px, 1fr));
      gap: 8px;
      padding-top: 8px;
      border-top: 1px solid var(--border-color);
    }}
    .kpi-box {{
      background: var(--bg-muted);
      border-radius: var(--radius-sm);
      padding: 8px 11px;
      display: flex;
      flex-direction: column;
    }}
    .kpi-label {{
      font-size: 10.5px;
      text-transform: uppercase;
      color: var(--text-muted);
      font-weight: 600;
    }}
    .kpi-value {{
      font-size: 16px;
      font-weight: 700;
    }}
    .tabs-bar {{
      display: flex;
      gap: 6px;
      border-bottom: 1px solid var(--border-color);
    }}
    .tab-btn {{
      padding: 8px 14px;
      border: none;
      background: transparent;
      color: var(--text-muted);
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      border-bottom: 2.5px solid transparent;
    }}
    .tab-btn.active {{
      color: var(--brand-blue);
      border-bottom-color: var(--brand-blue);
      background: var(--bg-surface);
    }}
    .graph-workbench {{
      display: grid;
      grid-template-columns: 1fr 340px;
      gap: 12px;
      align-items: start;
    }}
    @media (max-width: 860px) {{
      .graph-workbench {{ grid-template-columns: 1fr; }}
    }}
    .panel-card {{
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      overflow: hidden;
    }}
    .panel-header {{
      padding: 10px 14px;
      background: var(--bg-muted);
      border-bottom: 1px solid var(--border-color);
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .panel-title {{
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      color: var(--text-secondary);
    }}
    .svg-canvas-wrap {{
      width: 100%;
      height: 540px;
      background: radial-gradient(circle at center, var(--bg-surface) 0%, var(--bg-app) 100%);
      position: relative;
      overflow: hidden;
    }}
    svg.network-svg {{
      width: 100%;
      height: 100%;
      user-select: none;
    }}
    .node-group {{
      cursor: pointer;
      transition: opacity 0.15s;
    }}
    .node-group:hover circle, .node-group:hover rect {{
      stroke-width: 3px;
    }}
    .legend-bar {{
      display: flex;
      gap: 14px;
      padding: 8px 14px;
      border-top: 1px solid var(--border-color);
      font-size: 11.5px;
      flex-wrap: wrap;
      background: var(--bg-muted);
    }}
    .legend-dot {{
      display: inline-block;
      width: 10px;
      height: 10px;
      border-radius: 50%;
      margin-right: 4px;
    }}
    .data-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 12.5px;
    }}
    .data-table th, .data-table td {{
      padding: 8px 12px;
      border-bottom: 1px solid var(--border-color);
      text-align: left;
    }}
    .data-table th {{
      background: var(--bg-muted);
      font-weight: 700;
    }}
    .toast-banner {{
      position: fixed;
      bottom: 14px;
      right: 14px;
      background: #0f172a;
      color: #fff;
      padding: 8px 14px;
      border-radius: 6px;
      font-size: 12px;
      display: none;
      z-index: 1000;
    }}
  </style>
</head>
<body>
  <div class="app-shell">
    <div class="header-card">
      <div class="header-top">
        <div>
          <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
            <span class="mcp-badge">🕸️ MCP App • ui://google-patents/citation-graph</span>
            <span class="pub-badge" id="hdrPubNum">Loading...</span>
          </div>
          <h1 class="patent-title" id="hdrTitle">Interactive Patent Citation & ScaM Similarity Network Graph</h1>
          <div style="font-size:12.5px;color:var(--text-muted)" id="hdrSubtitle">
            Click any node in the graph to inspect or hop to its citation network via MCP tools/call.
          </div>
        </div>
        <div class="loader-bar">
          <input type="text" class="input-box" id="patentInput" placeholder="e.g. US8000000B2" />
          <button class="btn btn-primary" id="loadBtn" onclick="loadGraphFromInput()">🔄 Load / Hop Graph</button>
          <button class="btn" onclick="askAiCitationSummary()">✨ Ask AI Citation Analysis</button>
        </div>
      </div>

      <div class="kpi-strip">
        <div class="kpi-box">
          <span class="kpi-label">⬅️ Backward Citations (Prior Art)</span>
          <span class="kpi-value" id="kpiBack" style="color:var(--brand-blue)">0</span>
        </div>
        <div class="kpi-box">
          <span class="kpi-label">➡️ Forward Citations (Citing)</span>
          <span class="kpi-value" id="kpiFwd" style="color:var(--brand-purple)">0</span>
        </div>
        <div class="kpi-box">
          <span class="kpi-label">✨ ScaM Similar Patents</span>
          <span class="kpi-value" id="kpiSim" style="color:var(--brand-amber)">0</span>
        </div>
        <div class="kpi-box">
          <span class="kpi-label">★ Examiner Cited</span>
          <span class="kpi-value" id="kpiExam" style="color:var(--brand-green)">0</span>
        </div>
        <div class="kpi-box">
          <span class="kpi-label">📚 Scholar NPL Citations</span>
          <span class="kpi-value" id="kpiNpl">0</span>
        </div>
      </div>
    </div>

    <div class="tabs-bar">
      <button class="tab-btn active" data-tab="graph" onclick="switchTab('graph')">
        🕸️ 1. Interactive Citation & Similarity Network Graph
      </button>
      <button class="tab-btn" data-tab="table" onclick="switchTab('table')">
        📊 2. Citation & Similarity Matrix Table
      </button>
      <button class="tab-btn" data-tab="npl" onclick="switchTab('npl')">
        📚 3. Non-Patent Literature (NPL)
      </button>
    </div>

    <!-- TAB 1: Interactive SVG Network Graph + Node Inspector -->
    <div id="tab-graph">
      <div class="graph-workbench">
        <div class="panel-card">
          <div class="panel-header">
            <span class="panel-title">Directed Citation & Vector Similarity Topology</span>
            <div style="display:flex;gap:4px;flex-wrap:wrap">
              <button class="btn btn-sm" onclick="setGraphFilter('all')">All</button>
              <button class="btn btn-sm" onclick="setGraphFilter('backward')">⬅️ Backward</button>
              <button class="btn btn-sm" onclick="setGraphFilter('forward')">➡️ Forward</button>
              <button class="btn btn-sm" onclick="setGraphFilter('similar')">✨ Similar</button>
              <button class="btn btn-sm" onclick="setGraphFilter('examiner')">★ Examiner Only</button>
            </div>
          </div>
          <div class="svg-canvas-wrap">
            <svg class="network-svg" id="networkSvg" viewBox="0 0 820 520"></svg>
          </div>
          <div class="legend-bar">
            <span><i class="legend-dot" style="background:#059669"></i>Target Patent (Hub)</span>
            <span><i class="legend-dot" style="background:#1a73e8"></i>Backward Citation (Cited Prior Art)</span>
            <span><i class="legend-dot" style="background:#7c3aed"></i>Forward Citation (Later Citing Patent)</span>
            <span><i class="legend-dot" style="background:#d97706"></i>ScaM Vector Similar Patent</span>
            <span><strong>★</strong> = Cited by Patent Examiner</span>
          </div>
        </div>

        <div class="panel-card">
          <div class="panel-header">
            <span class="panel-title">Selected Node Inspector</span>
          </div>
          <div style="padding:14px;display:flex;flex-direction:column;gap:12px" id="nodeInspector">
            <div style="color:var(--text-muted)">Click any node in the graph to inspect details or expand its citation network.</div>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 2: Citation & Similarity Matrix Table -->
    <div id="tab-table" style="display:none">
      <div class="panel-card">
        <div class="panel-header">
          <span class="panel-title">Complete Citation & Similarity Records</span>
          <input type="search" class="input-box" id="tableSearch" placeholder="Filter by Patent ID or Category..." oninput="renderMatrixTable()" />
        </div>
        <div style="overflow-x:auto" id="matrixTableContainer"></div>
      </div>
    </div>

    <!-- TAB 3: NPL Citations -->
    <div id="tab-npl" style="display:none">
      <div class="panel-card">
        <div class="panel-header">
          <span class="panel-title">Google Scholar & Scientific Non-Patent Literature Citations</span>
        </div>
        <div style="padding:14px" id="nplListContainer"></div>
      </div>
    </div>
  </div>

  <div class="toast-banner" id="toastBanner"></div>

  <script>
    const INITIAL_DATA = {initial_json};
    const SERVER_BASE = {server_base_json} || ((window.location.origin && window.location.origin.startsWith("http") && !window.location.origin.includes("usercontent")) ? window.location.origin : "");
    const state = {{
      data: INITIAL_DATA && (INITIAL_DATA.publication_number || INITIAL_DATA.target_patent) ? INITIAL_DATA : null,
      filter: "all",
      selectedNode: null,
      nextRpcId: 1,
      pendingRpc: new Map(),
    }};

    function showToast(msg) {{
      const el = document.getElementById("toastBanner");
      el.textContent = msg;
      el.style.display = "block";
      clearTimeout(window.__t);
      window.__t = setTimeout(() => (el.style.display = "none"), 3000);
    }}

    function escapeHtml(s) {{
      return String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }}

    function isExaminerCited(cat) {{
      const u = String(cat || "").toUpperCase();
      return u.includes("EXA") || u.includes("SEA") || u.includes("*") || u.includes("X") || u.includes("Y");
    }}

    function sendMcpRequest(method, params) {{
      return new Promise((resolve, reject) => {{
        const id = ++state.nextRpcId;
        state.pendingRpc.set(id, {{ resolve, reject }});
        window.parent.postMessage({{ jsonrpc: "2.0", id, method, params }}, "*");
        setTimeout(() => {{
          if (state.pendingRpc.has(id)) {{
            state.pendingRpc.delete(id);
            reject(new Error("RPC timeout"));
          }}
        }}, 12000);
      }});
    }}

    function extractPayload(params) {{
      if (!params) return null;
      if (params.structuredContent && typeof params.structuredContent === "object") {{
        const sc = params.structuredContent;
        if (sc.publication_number || sc.backward_citations || sc.similar_patents) return sc;
      }}
      if (Array.isArray(params.content)) {{
        for (const c of params.content) {{
          if (c?.type === "text" && c.text) {{
            try {{
              const p = JSON.parse(c.text);
              if (p && (p.publication_number || p.backward_citations || p.similar_patents || p.target_patent)) return p;
            }} catch (_) {{}}
          }}
        }}
      }}
      return params.publication_number || params.similar_patents ? params : null;
    }}

    window.addEventListener("message", (event) => {{
      const msg = event.data;
      if (!msg || msg.jsonrpc !== "2.0") return;
      if (msg.id !== undefined && state.pendingRpc.has(msg.id)) {{
        const {{ resolve, reject }} = state.pendingRpc.get(msg.id);
        state.pendingRpc.delete(msg.id);
        if (msg.error) reject(msg.error);
        else resolve(msg.result);
        return;
      }}
      if (msg.method === "ui/notifications/tool-result") {{
        const p = extractPayload(msg.params);
        if (p) {{
          if (!state.data || (p.publication_number && p.publication_number !== state.data.publication_number)) {{
            state.data = p;
          }} else {{
            state.data = Object.assign({{}}, state.data, p);
          }}
          renderAll();
          showToast(`Updated citation graph for ${{state.data.publication_number || state.data.target_patent}}`);
        }}
      }} else if (msg.method === "ui/notifications/host-context-changed") {{
        if (msg.params?.theme) document.documentElement.setAttribute("data-theme", msg.params.theme);
      }}
    }});

    async function initBridge() {{
      if (window.parent && window.parent !== window) {{
        try {{
          const res = await sendMcpRequest("ui/initialize", {{
            protocolVersion: "2025-06-18",
            appInfo: {{ name: "Google Patents Citation Graph", version: "1.0.0" }},
            appCapabilities: {{}},
          }});
          if (res?.hostContext?.theme) document.documentElement.setAttribute("data-theme", res.hostContext.theme);
        }} catch (_) {{}}
        window.parent.postMessage({{ jsonrpc: "2.0", method: "ui/notifications/initialized", params: {{}} }}, "*");
      }}
    }}

    async function hopToPatent(patentId) {{
      const clean = (patentId || "").trim();
      if (!clean) return;
      document.getElementById("patentInput").value = clean;
      const btn = document.getElementById("loadBtn");
      btn.textContent = "⏳ Expanding...";
      try {{
        if (window.parent && window.parent !== window) {{
          const [citRpc, simRpc] = await Promise.allSettled([
            sendMcpRequest("tools/call", {{ name: "get_patent_citations", arguments: {{ patent_id: clean, limit: 20 }} }}),
            sendMcpRequest("tools/call", {{ name: "find_similar_patents", arguments: {{ patent_id: clean, limit: 8 }} }}),
          ]);
          const citData = citRpc.status === "fulfilled" ? extractPayload(citRpc.value) : null;
          const simData = simRpc.status === "fulfilled" ? extractPayload(simRpc.value) : null;
          if (citData || simData) {{
            state.data = Object.assign({{}}, citData || {{}}, simData || {{}});
            renderAll();
            btn.textContent = "🔄 Load / Hop Graph";
            showToast(`Centered graph on ${{clean}}`);
            return;
          }}
        }}
      }} catch (_) {{}}

      try {{
        const r = await fetch(`${{SERVER_BASE}}/apps/api/citations?patent_id=${{encodeURIComponent(clean)}}`);
        if (r.ok) {{
          state.data = await r.json();
          renderAll();
          showToast(`Centered graph on ${{clean}}`);
        }}
      }} catch (_) {{}}
      btn.textContent = "🔄 Load / Hop Graph";
    }}

    function loadGraphFromInput() {{
      hopToPatent(document.getElementById("patentInput").value);
    }}

    function switchTab(t) {{
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.toggle("active", b.getAttribute("data-tab") === t));
      ["graph", "table", "npl"].forEach((id) => {{
        document.getElementById(`tab-${{id}}`).style.display = id === t ? "block" : "none";
      }});
    }}

    function setGraphFilter(f) {{
      state.filter = f;
      renderSvgGraph();
    }}

    function renderAll() {{
      const d = state.data;
      if (!d) return;
      const pub = d.publication_number || d.target_patent || "PATENT";
      document.getElementById("hdrPubNum").textContent = pub;
      document.getElementById("patentInput").value = pub;

      const back = d.backward_citations || [];
      const fwd = d.forward_citations || [];
      const sim = d.similar_patents || [];
      const npl = d.non_patent_literature_citations || [];
      const examCount = [...back, ...fwd].filter((c) => isExaminerCited(c.category)).length;

      document.getElementById("kpiBack").textContent = back.length;
      document.getElementById("kpiFwd").textContent = fwd.length;
      document.getElementById("kpiSim").textContent = sim.length;
      document.getElementById("kpiExam").textContent = examCount;
      document.getElementById("kpiNpl").textContent = npl.length;

      renderSvgGraph();
      renderMatrixTable();
      renderNplList();
    }}

    function renderSvgGraph() {{
      const svg = document.getElementById("networkSvg");
      const d = state.data;
      if (!d) return;
      const centerPub = d.publication_number || d.target_patent || "TARGET";

      let back = (d.backward_citations || []).slice(0, 14);
      let fwd = (d.forward_citations || []).slice(0, 14);
      let sim = (d.similar_patents || []).slice(0, 8);

      if (state.filter === "backward") {{ fwd = []; sim = []; }}
      if (state.filter === "forward") {{ back = []; sim = []; }}
      if (state.filter === "similar") {{ back = []; fwd = []; }}
      if (state.filter === "examiner") {{
        back = back.filter((c) => isExaminerCited(c.category));
        fwd = fwd.filter((c) => isExaminerCited(c.category));
        sim = [];
      }}

      const cx = 410, cy = 240;
      const edges = [];
      const nodes = [];

      // Backward nodes on left column (x = 125)
      back.forEach((b, i) => {{
        const y = 45 + (i * Math.min(34, 410 / Math.max(1, back.length)));
        const x = 130 + (i % 2) * 28;
        const exam = isExaminerCited(b.category);
        edges.push(`<path d="M ${{x + 48}} ${{y}} C ${{(x + cx) / 2}} ${{y}}, ${{(x + cx) / 2}} ${{cy}}, ${{cx - 58}} ${{cy}}" stroke="#1a73e8" stroke-width="${{exam ? 2.2 : 1.3}}" fill="none" stroke-opacity="0.55" />`);
        nodes.push({{
          id: b.publication_number,
          x, y,
          color: "#1a73e8",
          kind: "Backward Citation (Prior Art)",
          category: b.category || "cited",
          examiner: exam,
          title: b.title || "",
          assignee: "",
        }});
      }});

      // Forward nodes on right column (x = 680)
      fwd.forEach((f, i) => {{
        const y = 45 + (i * Math.min(34, 410 / Math.max(1, fwd.length)));
        const x = 680 - (i % 2) * 28;
        const exam = isExaminerCited(f.category);
        edges.push(`<path d="M ${{cx + 58}} ${{cy}} C ${{(cx + x) / 2}} ${{cy}}, ${{(cx + x) / 2}} ${{y}}, ${{x - 48}} ${{y}}" stroke="#7c3aed" stroke-width="${{exam ? 2.2 : 1.3}}" fill="none" stroke-opacity="0.55" />`);
        nodes.push({{
          id: f.publication_number,
          x, y,
          color: "#7c3aed",
          kind: "Forward Citation (Citing Patent)",
          category: f.category || "citing",
          examiner: exam,
          title: f.title || "",
          assignee: "",
        }});
      }});

      // Similar patents along bottom arc
      sim.forEach((s, i) => {{
        const span = 500;
        const startX = 410 - span / 2;
        const x = startX + (sim.length > 1 ? (i * span) / (sim.length - 1) : 250);
        const y = 465 - (i % 2) * 24;
        edges.push(`<line x1="${{cx}}" y1="${{cy + 32}}" x2="${{x}}" y2="${{y - 16}}" stroke="#d97706" stroke-width="1.5" stroke-dasharray="5,4" stroke-opacity="0.65" />`);
        nodes.push({{
          id: s.publication_number,
          x, y,
          color: "#d97706",
          kind: "ScaM Vector Similar Patent",
          category: "ScaM Similarity",
          examiner: false,
          title: s.title || "",
          assignee: (s.assignees || []).join(", "),
          publication_date: s.publication_date || "",
        }});
      }});

      window.__graphNodes = nodes;

      const nodesSvg = nodes
        .map(
          (n, idx) => `
          <g class="node-group" onclick="selectGraphNode(${{idx}})">
            <rect x="${{n.x - 54}}" y="${{n.y - 13}}" width="108" height="26" rx="6" fill="${{n.color}}" fill-opacity="0.14" stroke="${{n.color}}" stroke-width="1.6" />
            <text x="${{n.x}}" y="${{n.y + 4}}" text-anchor="middle" font-family="monospace" font-size="10.5" font-weight="700" fill="currentColor">
              ${{n.examiner ? "★ " : ""}}${{escapeHtml(n.id)}}
            </text>
          </g>
        `
        )
        .join("");

      const centerSvg = `
        <g class="node-group" onclick="selectCenterHub()">
          <rect x="${{cx - 66}}" y="${{cy - 24}}" width="132" height="48" rx="12" fill="#059669" stroke="#047857" stroke-width="2.5" />
          <text x="${{cx}}" y="${{cy - 3}}" text-anchor="middle" font-family="monospace" font-size="12" font-weight="700" fill="#ffffff">
            ${{escapeHtml(centerPub)}}
          </text>
          <text x="${{cx}}" y="${{cy + 13}}" text-anchor="middle" font-size="10" font-weight="600" fill="#d1fae5">
            TARGET HUB
          </text>
        </g>
      `;

      svg.innerHTML = edges.join("") + nodesSvg + centerSvg;
      if (nodes.length > 0 && !state.selectedNode) {{
        selectGraphNode(0);
      }}
    }}

    function selectCenterHub() {{
      const pub = state.data?.publication_number || state.data?.target_patent || "";
      document.getElementById("nodeInspector").innerHTML = `
        <div style="font-family:var(--font-mono);font-size:15px;font-weight:700;color:var(--brand-green)">
          🎯 Target Hub: ${{escapeHtml(pub)}}
        </div>
        <div style="font-size:12.5px;color:var(--text-secondary)">
          Backward Citations: <strong>${{(state.data?.backward_citations || []).length}}</strong><br/>
          Forward Citations: <strong>${{(state.data?.forward_citations || []).length}}</strong><br/>
          ScaM Similar Patents: <strong>${{(state.data?.similar_patents || []).length}}</strong>
        </div>
      `;
    }}

    function selectGraphNode(idx) {{
      const n = (window.__graphNodes || [])[idx];
      if (!n) return;
      state.selectedNode = n;
      document.getElementById("nodeInspector").innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span class="pub-badge" style="background:${{n.color}}">${{escapeHtml(n.id)}}</span>
          <span style="font-size:11px;font-weight:700;color:var(--text-muted)">${{n.examiner ? "★ Examiner Cited" : escapeHtml(n.category)}}</span>
        </div>
        <div style="font-weight:700;font-size:13px">${{escapeHtml(n.kind)}}</div>
        ${{n.title ? `<div style="font-size:13px"><strong>Title:</strong> ${{escapeHtml(n.title)}}</div>` : ""}}
        ${{n.assignee ? `<div style="font-size:12px;color:var(--text-muted)"><strong>Assignee:</strong> ${{escapeHtml(n.assignee)}}</div>` : ""}}
        <div style="display:flex;flex-direction:column;gap:6px;margin-top:6px">
          <button class="btn btn-primary" onclick="hopToPatent('${{n.id}}')">
            🔄 Re-Center & Expand Citation Graph on ${{escapeHtml(n.id)}}
          </button>
          <button class="btn" onclick="askAiNodeRelation('${{n.id}}', '${{escapeHtml(n.kind)}}')">
            ✨ Ask AI How ${{escapeHtml(n.id)}} Relates to Target
          </button>
          <button class="btn" onclick="window.open('${{SERVER_BASE}}/apps/patent/${{n.id.replace(/-/g, '')}}', '_blank')">
            ↗ Open ${{escapeHtml(n.id)}} Patent Reader &amp; PDF
          </button>
        </div>
      `;
    }}

    function renderMatrixTable() {{
      const d = state.data;
      if (!d) return;
      const kw = (document.getElementById("tableSearch")?.value || "").toLowerCase();
      const rows = [
        ...(d.backward_citations || []).map((c) => ({{
          id: c.publication_number,
          rel: "⬅️ Backward Citation (Prior Art)",
          cat: c.category || "—",
          title: c.title || "—",
        }})),
        ...(d.forward_citations || []).map((c) => ({{
          id: c.publication_number,
          rel: "➡️ Forward Citation (Citing)",
          cat: c.category || "—",
          title: c.title || "—",
        }})),
        ...(d.similar_patents || []).map((s) => ({{
          id: s.publication_number,
          rel: "✨ ScaM Similar Patent",
          cat: (s.assignees || []).join(", ") || "ScaM Vector",
          title: s.title || "—",
        }})),
      ].filter((r) => !kw || r.id.toLowerCase().includes(kw) || r.rel.toLowerCase().includes(kw) || r.title.toLowerCase().includes(kw));

      document.getElementById("matrixTableContainer").innerHTML = `
        <table class="data-table">
          <thead>
            <tr>
              <th>Publication Number</th>
              <th>Relationship</th>
              <th>Category / Assignee</th>
              <th>Title</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            ${{rows
              .map(
                (r) => `
              <tr>
                <td style="font-family:var(--font-mono);font-weight:700;color:var(--brand-blue)">${{escapeHtml(r.id)}}</td>
                <td>${{escapeHtml(r.rel)}}</td>
                <td>${{escapeHtml(r.cat)}}</td>
                <td>${{escapeHtml(r.title)}}</td>
                <td><button class="btn btn-sm" onclick="hopToPatent('${{r.id}}')">🔄 Hop</button></td>
              </tr>
            `
              )
              .join("")}}
          </tbody>
        </table>
      `;
    }}

    function renderNplList() {{
      const npls = state.data?.non_patent_literature_citations || [];
      if (!npls.length) {{
        document.getElementById("nplListContainer").innerHTML = `<div style="color:var(--text-muted)">No NPL citations recorded in this citation slice.</div>`;
        return;
      }}
      document.getElementById("nplListContainer").innerHTML = npls
        .map(
          (n, i) => `
          <div style="padding:10px;border:1px solid var(--border-color);border-radius:6px;margin-bottom:8px">
            <strong>[NPL ${{i + 1}}]</strong> ${{escapeHtml(n.npl_text)}}
            <div style="font-size:11px;color:var(--text-muted);margin-top:3px">Category: ${{escapeHtml(n.category || "cited")}}</div>
          </div>
        `
        )
        .join("");
    }}

    function askAiNodeRelation(nodeId, kind) {{
      const target = state.data?.publication_number || state.data?.target_patent || "";
      sendMcpRequest("ui/message", {{
        role: "user",
        content: [{{
          type: "text",
          text: `Retrieve details for ${{nodeId}} (${{kind}}) and explain how its technical disclosure and claims compare to target patent ${{target}}.`,
        }}],
      }}).catch(() => {{}});
      showToast(`Sent comparison prompt for ${{nodeId}} to AI host`);
    }}

    function askAiCitationSummary() {{
      const d = state.data;
      if (!d) return;
      const pub = d.publication_number || d.target_patent;
      sendMcpRequest("ui/message", {{
        role: "user",
        content: [{{
          type: "text",
          text: `Analyze the citation network for ${{pub}} (${{(d.backward_citations || []).length}} backward citations, ${{(d.forward_citations || []).length}} forward citations, ${{(d.similar_patents || []).length}} ScaM similar patents). Which cited prior-art references or citing patents are most critical?`,
        }}],
      }}).catch(() => {{}});
      showToast("Sent citation network analysis prompt to AI host");
    }}

    window.addEventListener("DOMContentLoaded", () => {{
      initBridge();
      if (state.data) renderAll();
    }});
  </script>
</body>
</html>"""
