"""View 2: Visual Prior Art Timeline, Legal Lifespan & Worldwide INPADOC Family Map MCP App.

Implements `ui://google-patents/prior-art-timeline` (`mimeType="text/html;profile=mcp-app"`):
1. Server-side enrichment (`enrich_timeline_payload`): computes estimated 20-year statutory
   expiration date, active/expired legal status, jurisdiction distribution across INPADOC
   family members, and chronological milestones.
2. Interactive 3-Tab MCP App:
   - Tab 1: Interactive Priority Cutoff & 20-Year Patent Lifespan Timeline + Chronological Swimlane
   - Tab 2: Global INPADOC Family Jurisdiction Matrix & Country Drill-Down
   - Tab 3: Google Scholar & Non-Patent Literature (NPL) Prior Art Inspector
"""

from __future__ import annotations

from datetime import datetime
import json
import re
from typing import Any, Dict, List, Optional

from .claim_tree_app import CLAIM_TREE_RESOURCE_META, MCP_APP_MIME_TYPE

TIMELINE_RESOURCE_URI = "ui://google-patents/prior-art-timeline"

TIMELINE_TOOL_META: Dict[str, Any] = {
    "ui": {
        "resourceUri": TIMELINE_RESOURCE_URI,
        "visibility": ["model", "app"],
    },
    "ui/resourceUri": TIMELINE_RESOURCE_URI,
}

_TIMELINE_CACHE: Dict[str, Dict[str, Any]] = {}
_LAST_TIMELINE_KEY: Optional[str] = None

COUNTRY_META: Dict[str, Dict[str, str]] = {
    "US": {"name": "United States (USPTO)", "flag": "🇺🇸"},
    "EP": {"name": "European Patent Office (EPO)", "flag": "🇪🇺"},
    "WO": {"name": "WIPO (PCT International)", "flag": "🌐"},
    "CN": {"name": "China (CNIPA)", "flag": "🇨🇳"},
    "JP": {"name": "Japan (JPO)", "flag": "🇯🇵"},
    "KR": {"name": "South Korea (KIPO)", "flag": "🇰🇷"},
    "DE": {"name": "Germany (DPMA)", "flag": "🇩🇪"},
    "GB": {"name": "United Kingdom (UKIPO)", "flag": "🇬🇧"},
    "FR": {"name": "France (INPI)", "flag": "🇫🇷"},
    "CA": {"name": "Canada (CIPO)", "flag": "🇨🇦"},
    "AU": {"name": "Australia (IP Australia)", "flag": "🇦🇺"},
    "TW": {"name": "Taiwan (TIPO)", "flag": "🇹🇼"},
    "IN": {"name": "India (IPO)", "flag": "🇮🇳"},
    "BR": {"name": "Brazil (INPI)", "flag": "🇧🇷"},
    "IL": {"name": "Israel (ILPO)", "flag": "🇮🇱"},
}


def set_cached_timeline_payload(patent_id: str, payload: Dict[str, Any]) -> None:
    global _LAST_TIMELINE_KEY
    if not patent_id or not isinstance(payload, dict):
        return
    clean = patent_id.replace("-", "").strip().upper()
    _TIMELINE_CACHE[clean] = payload
    _TIMELINE_CACHE[patent_id.strip().upper()] = payload
    _LAST_TIMELINE_KEY = clean


def get_cached_timeline_payload(patent_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    if patent_id:
        clean = patent_id.replace("-", "").strip().upper()
        if clean in _TIMELINE_CACHE:
            return _TIMELINE_CACHE[clean]
        if patent_id.strip().upper() in _TIMELINE_CACHE:
            return _TIMELINE_CACHE[patent_id.strip().upper()]
    if _LAST_TIMELINE_KEY and _LAST_TIMELINE_KEY in _TIMELINE_CACHE:
        return _TIMELINE_CACHE[_LAST_TIMELINE_KEY]
    return None


def _compute_expiration_and_status(key_dates: Dict[str, Any]) -> Dict[str, Any]:
    """Computes estimated 20-year statutory expiration date from filing/priority date."""
    filing = key_dates.get("filing_date") or key_dates.get("priority_date")
    grant = key_dates.get("grant_date")
    if not filing or not re.match(r"^\d{4}-\d{2}-\d{2}$", str(filing)):
        return {
            "estimated_expiration_date": None,
            "legal_status_estimate": "GRANTED" if grant else "APPLICATION",
            "years_remaining": None,
        }
    try:
        year = int(str(filing)[:4])
        exp_date_str = f"{year + 20}{str(filing)[4:]}"
        exp_dt = datetime.strptime(exp_date_str, "%Y-%m-%d")
        now_dt = datetime.utcnow()
        days_left = (exp_dt - now_dt).days
        years_left = round(days_left / 365.25, 1)
        if days_left < 0:
            status = "EXPIRED (20-Yr Term Elapsed)"
        elif grant:
            status = "ACTIVE (Granted)"
        else:
            status = "PENDING / PUBLISHED"
        return {
            "estimated_expiration_date": exp_date_str,
            "legal_status_estimate": status,
            "years_remaining": max(0.0, years_left) if days_left >= 0 else 0.0,
        }
    except Exception:
        return {
            "estimated_expiration_date": None,
            "legal_status_estimate": "GRANTED" if grant else "APPLICATION",
            "years_remaining": None,
        }


def enrich_timeline_payload(timeline_data: Dict[str, Any]) -> Dict[str, Any]:
    """Enriches `get_prior_art_timeline` output with jurisdiction breakdown, lifespan & milestones."""
    if not isinstance(timeline_data, dict) or timeline_data.get("error"):
        return timeline_data

    enriched = dict(timeline_data)
    key_dates = dict(enriched.get("key_dates") or {})
    exp_info = _compute_expiration_and_status(key_dates)
    key_dates["estimated_expiration_date"] = exp_info["estimated_expiration_date"]
    enriched["key_dates"] = key_dates
    enriched["legal_status_estimate"] = exp_info["legal_status_estimate"]
    enriched["years_remaining"] = exp_info["years_remaining"]

    # Group INPADOC family members by jurisdiction
    members = enriched.get("inpadoc_family_members") or []
    jur_map: Dict[str, Dict[str, Any]] = {}
    all_milestones: List[Dict[str, Any]] = []

    if key_dates.get("priority_date"):
        all_milestones.append({
            "date": key_dates["priority_date"],
            "type": "PRIORITY_CUTOFF",
            "label": "Earliest Priority Date (Prior Art Cutoff)",
            "detail": f"References published before {key_dates['priority_date']} qualify as prior art.",
            "badge": "CRITICAL CUTOFF",
        })
    if key_dates.get("filing_date"):
        all_milestones.append({
            "date": key_dates["filing_date"],
            "type": "FILING",
            "label": "Application Filing Date",
            "detail": f"Primary application filed for {enriched.get('publication_number', '')}.",
            "badge": "FILING",
        })
    if key_dates.get("publication_date"):
        all_milestones.append({
            "date": key_dates["publication_date"],
            "type": "PUBLICATION",
            "label": "Primary Publication Date",
            "detail": f"Published as {enriched.get('publication_number', '')}.",
            "badge": "PUBLISHED",
        })
    if key_dates.get("grant_date"):
        all_milestones.append({
            "date": key_dates["grant_date"],
            "type": "GRANT",
            "label": "Patent Grant Date",
            "detail": f"Patent granted ({enriched.get('publication_number', '')}).",
            "badge": "GRANTED",
        })
    if exp_info.get("estimated_expiration_date"):
        all_milestones.append({
            "date": exp_info["estimated_expiration_date"],
            "type": "EXPIRATION",
            "label": "Estimated 20-Year Statutory Expiration",
            "detail": "Standard 20-year patent term from earliest filing date (excluding PTA/PTE).",
            "badge": "EXPIRATION",
        })

    for m in members:
        cc = (m.get("country_code") or "OTHER").upper()
        meta = COUNTRY_META.get(cc, {"name": f"Jurisdiction ({cc})", "flag": "🏳️"})
        if cc not in jur_map:
            jur_map[cc] = {
                "country_code": cc,
                "country_name": meta["name"],
                "flag": meta["flag"],
                "count": 0,
                "grants": 0,
                "applications": 0,
                "earliest_date": m.get("publication_date"),
                "publications": [],
            }
        jur_map[cc]["count"] += 1
        kind = (m.get("kind_code") or "").upper()
        if kind.startswith(("B", "C")):
            jur_map[cc]["grants"] += 1
        else:
            jur_map[cc]["applications"] += 1
        jur_map[cc]["publications"].append(m.get("publication_number"))

        if m.get("publication_date"):
            all_milestones.append({
                "date": m["publication_date"],
                "type": "FAMILY_MEMBER",
                "label": f"{meta['flag']} {m.get('publication_number')} ({cc} {kind})",
                "detail": m.get("title") or "INPADOC Family Publication",
                "badge": f"{cc} {kind}".strip(),
                "publication_number": m.get("publication_number"),
            })

    all_milestones.sort(key=lambda x: str(x.get("date") or "9999-99-99"))
    jurisdictions_list = sorted(jur_map.values(), key=lambda x: (-x["count"], x["country_code"]))

    enriched["jurisdictions_summary"] = jurisdictions_list
    enriched["jurisdictions_count"] = len(jurisdictions_list)
    enriched["chronological_milestones"] = all_milestones
    enriched["mcp_app"] = {
        "resource_uri": TIMELINE_RESOURCE_URI,
        "mime_type": MCP_APP_MIME_TYPE,
        "view": "prior-art-timeline",
    }

    pub_num = enriched.get("publication_number") or ""
    if pub_num:
        set_cached_timeline_payload(str(pub_num), enriched)
    return enriched


def build_timeline_app_html(initial_data: Optional[Dict[str, Any]] = None) -> str:
    """Builds the self-contained HTML/CSS/JS bundle for `ui://google-patents/prior-art-timeline`."""
    import os
    initial_json = json.dumps(initial_data or {}).replace("</", "<\\/")
    server_base_json = json.dumps(os.environ.get("MCP_PUBLIC_BASE_URL", "").rstrip("/"))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Google Patents — Prior Art Timeline & INPADOC Family Map (MCP App)</title>
  <style>
    :root {{
      --bg-app: #f8fafc;
      --bg-surface: #ffffff;
      --bg-muted: #f1f5f9;
      --bg-accent: #eff6ff;
      --bg-green: #ecfdf5;
      --bg-amber: #fffbeb;
      --bg-red: #fef2f2;
      --text-main: #0f172a;
      --text-secondary: #334155;
      --text-muted: #64748b;
      --border-color: #e2e8f0;
      --border-strong: #cbd5e1;
      --brand-blue: #1a73e8;
      --brand-green: #059669;
      --brand-amber: #d97706;
      --brand-red: #dc2626;
      --brand-purple: #7c3aed;
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
      --bg-green: #064e3b;
      --bg-amber: #78350f;
      --bg-red: #7f1d1d;
      --text-main: #f8fafc;
      --text-secondary: #cbd5e1;
      --text-muted: #94a3b8;
      --border-color: #334155;
      --border-strong: #475569;
      --brand-blue: #60a5fa;
      --brand-green: #34d399;
      --brand-amber: #fbbf24;
      --brand-red: #f87171;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      padding: 0;
      font-family: var(--font-sans);
      background: var(--bg-app);
      color: var(--text-main);
      font-size: 13.5px;
      line-height: 1.5;
    }}
    .app-shell {{
      max-width: 1260px;
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
      display: inline-flex;
      align-items: center;
      gap: 5px;
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
      background: var(--brand-blue);
      color: #fff;
    }}
    .status-pill {{
      font-size: 11px;
      font-weight: 700;
      padding: 2px 9px;
      border-radius: 999px;
      background: var(--bg-green);
      color: var(--brand-green);
    }}
    .status-pill.expired {{
      background: var(--bg-red);
      color: var(--brand-red);
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
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
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
      font-size: 15px;
      font-weight: 700;
      margin-top: 2px;
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
      font-size: 12.5px;
      font-weight: 700;
      text-transform: uppercase;
      color: var(--text-secondary);
    }}
    /* Lifespan Track */
    .lifespan-track {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      gap: 10px;
      padding: 16px;
    }}
    .stage-node {{
      padding: 12px;
      border-radius: var(--radius-md);
      border: 1px solid var(--border-color);
      background: var(--bg-surface);
      position: relative;
      border-top: 4px solid var(--brand-blue);
    }}
    .stage-node.priority {{ border-top-color: var(--brand-red); background: var(--bg-red); }}
    .stage-node.grant {{ border-top-color: var(--brand-green); background: var(--bg-green); }}
    .stage-node.expiry {{ border-top-color: var(--brand-purple); }}
    /* Timeline Swimlane */
    .swimlane-list {{
      padding: 14px 18px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      max-height: 520px;
      overflow-y: auto;
    }}
    .milestone-row {{
      display: grid;
      grid-template-columns: 115px 150px 1fr auto;
      gap: 12px;
      align-items: center;
      padding: 9px 12px;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-color);
      background: var(--bg-surface);
    }}
    @media (max-width: 720px) {{
      .milestone-row {{ grid-template-columns: 1fr; }}
    }}
    .milestone-row.priority_cutoff {{
      border-left: 4px solid var(--brand-red);
      background: var(--bg-red);
    }}
    .milestone-row.grant {{
      border-left: 4px solid var(--brand-green);
    }}
    .milestone-row.family_member {{
      border-left: 4px solid var(--brand-blue);
    }}
    /* Jurisdiction Grid */
    .jur-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(185px, 1fr));
      gap: 10px;
      padding: 14px;
    }}
    .jur-card {{
      padding: 12px;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-color);
      background: var(--bg-surface);
      cursor: pointer;
      transition: all 0.12s ease;
    }}
    .jur-card:hover, .jur-card.active {{
      border-color: var(--brand-blue);
      background: var(--bg-accent);
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
      color: var(--text-secondary);
    }}
    .toast-banner {{
      position: fixed;
      bottom: 14px;
      right: 14px;
      background: #0f172a;
      color: #fff;
      padding: 8px 14px;
      border-radius: var(--radius-sm);
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
            <span class="mcp-badge">⏱️ MCP App • ui://google-patents/prior-art-timeline</span>
            <span class="pub-badge" id="hdrPubNum">Loading...</span>
            <span class="status-pill" id="hdrStatusBadge">ACTIVE</span>
          </div>
          <h1 class="patent-title" id="hdrTitle">Prior Art Timeline, Legal Lifespan & INPADOC Family Map</h1>
          <div style="font-size:12.5px;color:var(--text-muted);margin-top:2px" id="hdrAssignee"></div>
        </div>
        <div class="loader-bar">
          <input type="text" class="input-box" id="patentInput" placeholder="e.g. US8000000B2" />
          <button class="btn btn-primary" id="loadBtn" onclick="loadTimelineFromInput()">🔍 Load Timeline</button>
          <button class="btn" onclick="askAiPriorArtCutoff()">✨ Ask AI Prior Art Strategy</button>
        </div>
      </div>

      <div class="kpi-strip">
        <div class="kpi-box">
          <span class="kpi-label">🚨 Priority Cutoff Date</span>
          <span class="kpi-value" id="kpiPriority" style="color:var(--brand-red)">—</span>
        </div>
        <div class="kpi-box">
          <span class="kpi-label">📅 Filing Date</span>
          <span class="kpi-value" id="kpiFiling">—</span>
        </div>
        <div class="kpi-box">
          <span class="kpi-label">🏛️ Grant Date</span>
          <span class="kpi-value" id="kpiGrant" style="color:var(--brand-green)">—</span>
        </div>
        <div class="kpi-box">
          <span class="kpi-label">⏳ Est. 20-Yr Expiration</span>
          <span class="kpi-value" id="kpiExpiry">—</span>
        </div>
        <div class="kpi-box">
          <span class="kpi-label">🌐 INPADOC Family Size</span>
          <span class="kpi-value" id="kpiFamilyCount">0</span>
        </div>
        <div class="kpi-box">
          <span class="kpi-label">📚 Scholar NPL Citations</span>
          <span class="kpi-value" id="kpiNplCount">0</span>
        </div>
      </div>
    </div>

    <div class="tabs-bar">
      <button class="tab-btn active" data-tab="timeline" onclick="switchTab('timeline')">
        ⏱️ 1. Priority Cutoff & Chronological Timeline
      </button>
      <button class="tab-btn" data-tab="family" onclick="switchTab('family')">
        🌍 2. Worldwide INPADOC Family Map & Jurisdictions
      </button>
      <button class="tab-btn" data-tab="npl" onclick="switchTab('npl')">
        📚 3. Non-Patent Literature (NPL) Prior Art
      </button>
    </div>

    <!-- TAB 1: Priority Cutoff & Chronological Swimlane -->
    <div id="tab-timeline">
      <div class="panel-card" style="margin-bottom:12px">
        <div class="panel-header">
          <span class="panel-title">Key Statutory Lifespan Stages (35 U.S.C. § 102 Priority Cutoff & 20-Year Term)</span>
        </div>
        <div class="lifespan-track" id="lifespanTrack"></div>
      </div>

      <div class="panel-card">
        <div class="panel-header">
          <span class="panel-title">Chronological Prosecution & Family Event Swimlane</span>
          <div style="display:flex;gap:6px">
            <button class="btn btn-sm" id="btnFilterEvents" onclick="toggleKeyEventsOnly()">Filter: All Events</button>
          </div>
        </div>
        <div class="swimlane-list" id="swimlaneList"></div>
      </div>
    </div>

    <!-- TAB 2: Worldwide INPADOC Family Map -->
    <div id="tab-family" style="display:none">
      <div class="panel-card" style="margin-bottom:12px">
        <div class="panel-header">
          <span class="panel-title">Global INPADOC Patent Family Coverage by Jurisdiction (Click to Filter)</span>
          <button class="btn btn-sm" onclick="selectJurisdiction('')">Show All Jurisdictions</button>
        </div>
        <div class="jur-grid" id="jurGrid"></div>
      </div>

      <div class="panel-card">
        <div class="panel-header">
          <span class="panel-title" id="familyTableTitle">INPADOC Family Member Publications</span>
        </div>
        <div style="overflow-x:auto" id="familyTableContainer"></div>
      </div>
    </div>

    <!-- TAB 3: Non-Patent Literature (NPL) -->
    <div id="tab-npl" style="display:none">
      <div class="panel-card">
        <div class="panel-header">
          <span class="panel-title">Google Scholar & Scientific Non-Patent Literature (NPL) Citations</span>
          <input type="search" class="input-box" id="nplSearch" placeholder="Filter NPL references..." oninput="renderNplTab()" />
        </div>
        <div style="padding:14px" id="nplContainer"></div>
      </div>
    </div>
  </div>

  <div class="toast-banner" id="toastBanner"></div>

  <script>
    const INITIAL_DATA = {initial_json};
    const SERVER_BASE = {server_base_json} || ((window.location.origin && window.location.origin.startsWith("http") && !window.location.origin.includes("usercontent")) ? window.location.origin : "");
    const state = {{
      data: INITIAL_DATA && INITIAL_DATA.publication_number ? INITIAL_DATA : null,
      activeTab: "timeline",
      keyEventsOnly: false,
      selectedCountry: "",
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
        if (params.structuredContent.publication_number || params.structuredContent.key_dates) {{
          return params.structuredContent;
        }}
      }}
      if (Array.isArray(params.content)) {{
        for (const c of params.content) {{
          if (c?.type === "text" && c.text) {{
            try {{
              const p = JSON.parse(c.text);
              if (p && (p.publication_number || p.key_dates)) return p;
            }} catch (_) {{}}
          }}
        }}
      }}
      return params.publication_number ? params : null;
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
          state.data = p;
          renderAll();
          showToast(`Loaded timeline for ${{p.publication_number}}`);
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
            appInfo: {{ name: "Google Patents Prior Art Timeline", version: "1.0.0" }},
            appCapabilities: {{}},
          }});
          if (res?.hostContext?.theme) document.documentElement.setAttribute("data-theme", res.hostContext.theme);
        }} catch (_) {{}}
        window.parent.postMessage({{ jsonrpc: "2.0", method: "ui/notifications/initialized", params: {{}} }}, "*");
      }}
    }}

    async function fetchTimeline(patentId) {{
      const clean = (patentId || "").trim();
      if (!clean) return;
      const btn = document.getElementById("loadBtn");
      btn.textContent = "⏳ Loading...";
      try {{
        if (window.parent && window.parent !== window) {{
          const rpc = await sendMcpRequest("tools/call", {{
            name: "get_prior_art_timeline",
            arguments: {{ patent_id: clean }},
          }});
          const p = extractPayload(rpc);
          if (p) {{
            state.data = p;
            renderAll();
            btn.textContent = "🔍 Load Timeline";
            return;
          }}
        }}
      }} catch (_) {{}}
      try {{
        const r = await fetch(`${{SERVER_BASE}}/apps/api/timeline?patent_id=${{encodeURIComponent(clean)}}`);
        if (r.ok) {{
          state.data = await r.json();
          renderAll();
        }}
      }} catch (_) {{}}
      btn.textContent = "🔍 Load Timeline";
    }}

    function loadTimelineFromInput() {{
      fetchTimeline(document.getElementById("patentInput").value);
    }}

    function switchTab(t) {{
      state.activeTab = t;
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.toggle("active", b.getAttribute("data-tab") === t));
      ["timeline", "family", "npl"].forEach((id) => {{
        document.getElementById(`tab-${{id}}`).style.display = id === t ? "block" : "none";
      }});
    }}

    function toggleKeyEventsOnly() {{
      state.keyEventsOnly = !state.keyEventsOnly;
      document.getElementById("btnFilterEvents").textContent = state.keyEventsOnly ? "Filter: Key Milestones Only" : "Filter: All Events";
      renderSwimlane();
    }}

    function selectJurisdiction(cc) {{
      state.selectedCountry = cc;
      renderFamilyTab();
    }}

    function renderAll() {{
      const d = state.data;
      if (!d) return;
      const kd = d.key_dates || {{}};
      document.getElementById("hdrPubNum").textContent = d.publication_number || "PATENT";
      document.getElementById("patentInput").value = d.publication_number || "";
      document.getElementById("hdrTitle").textContent = d.title || "Patent Prior Art Timeline & INPADOC Family";
      const st = d.legal_status_estimate || "ACTIVE";
      const stEl = document.getElementById("hdrStatusBadge");
      stEl.textContent = st;
      stEl.className = "status-pill" + (st.includes("EXPIRED") ? " expired" : "");
      document.getElementById("hdrAssignee").textContent =
        `🏢 Assignees: ${{(d.assignees || []).join(", ") || "—"}} • INPADOC Family ID: ${{d.family_id || "—"}}`;

      document.getElementById("kpiPriority").textContent = kd.priority_date || "—";
      document.getElementById("kpiFiling").textContent = kd.filing_date || "—";
      document.getElementById("kpiGrant").textContent = kd.grant_date || "—";
      document.getElementById("kpiExpiry").textContent =
        kd.estimated_expiration_date ? `${{kd.estimated_expiration_date}} (${{d.years_remaining ?? 0}}y left)` : "—";
      document.getElementById("kpiFamilyCount").textContent =
        `${{d.inpadoc_family_members_count || (d.inpadoc_family_members || []).length}} (${{d.jurisdictions_count || 1}} countries)`;
      document.getElementById("kpiNplCount").textContent =
        d.non_patent_literature_prior_art_count || (d.non_patent_literature_prior_art || []).length;

      // Render Lifespan Track
      document.getElementById("lifespanTrack").innerHTML = `
        <div class="stage-node priority">
          <div style="font-size:11px;font-weight:700;color:var(--brand-red)">1. PRIORITY CUTOFF (§ 102)</div>
          <div style="font-size:16px;font-weight:700;margin:4px 0">${{escapeHtml(kd.priority_date || "—")}}</div>
          <div style="font-size:11.5px;color:var(--text-secondary)">Art published before this date is primary prior art.</div>
        </div>
        <div class="stage-node">
          <div style="font-size:11px;font-weight:700;color:var(--brand-blue)">2. APPLICATION FILING</div>
          <div style="font-size:16px;font-weight:700;margin:4px 0">${{escapeHtml(kd.filing_date || "—")}}</div>
          <div style="font-size:11.5px;color:var(--text-secondary)">Starts the 20-year statutory patent term clock.</div>
        </div>
        <div class="stage-node">
          <div style="font-size:11px;font-weight:700;color:var(--brand-blue)">3. PUBLICATION DATE</div>
          <div style="font-size:16px;font-weight:700;margin:4px 0">${{escapeHtml(kd.publication_date || "—")}}</div>
          <div style="font-size:11.5px;color:var(--text-secondary)">Enters public prior art corpus globally.</div>
        </div>
        <div class="stage-node grant">
          <div style="font-size:11px;font-weight:700;color:var(--brand-green)">4. PATENT GRANT</div>
          <div style="font-size:16px;font-weight:700;margin:4px 0">${{escapeHtml(kd.grant_date || "Pending")}}</div>
          <div style="font-size:11.5px;color:var(--text-secondary)">Enforceable exclusive rights granted.</div>
        </div>
        <div class="stage-node expiry">
          <div style="font-size:11px;font-weight:700;color:var(--brand-purple)">5. EST. 20-YR EXPIRATION</div>
          <div style="font-size:16px;font-weight:700;margin:4px 0">${{escapeHtml(kd.estimated_expiration_date || "—")}}</div>
          <div style="font-size:11.5px;color:var(--text-secondary)">Status: <strong>${{escapeHtml(st)}}</strong></div>
        </div>
      `;

      renderSwimlane();
      renderFamilyTab();
      renderNplTab();
    }}

    function renderSwimlane() {{
      const d = state.data;
      if (!d) return;
      let events = d.chronological_milestones || [];
      if (state.keyEventsOnly) {{
        events = events.filter((e) => e.type !== "FAMILY_MEMBER");
      }}
      document.getElementById("swimlaneList").innerHTML = events
        .map((ev) => {{
          const cls = (ev.type || "").toLowerCase();
          const btnHtml = ev.publication_number
            ? `<button class="btn btn-sm" onclick="fetchTimeline('${{ev.publication_number}}')">Inspect</button>`
            : "";
          return `
            <div class="milestone-row ${{cls}}">
              <span style="font-family:var(--font-mono);font-weight:700">${{escapeHtml(ev.date || "—")}}</span>
              <span style="font-size:11px;font-weight:700;color:var(--brand-blue)">${{escapeHtml(ev.badge || ev.type)}}</span>
              <div>
                <div style="font-weight:700">${{escapeHtml(ev.label)}}</div>
                <div style="font-size:12px;color:var(--text-muted)">${{escapeHtml(ev.detail || "")}}</div>
              </div>
              <div>${{btnHtml}}</div>
            </div>
          `;
        }})
        .join("");
    }}

    function renderFamilyTab() {{
      const d = state.data;
      if (!d) return;
      const jurs = d.jurisdictions_summary || [];
      document.getElementById("jurGrid").innerHTML = jurs
        .map(
          (j) => `
          <div class="jur-card ${{state.selectedCountry === j.country_code ? "active" : ""}}" onclick="selectJurisdiction('${{j.country_code}}')">
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span style="font-size:18px">${{j.flag}} <strong>${{escapeHtml(j.country_code)}}</strong></span>
              <span class="pub-badge">${{j.count}} filings</span>
            </div>
            <div style="font-size:12px;color:var(--text-secondary);margin-top:4px">${{escapeHtml(j.country_name)}}</div>
            <div style="font-size:11px;color:var(--text-muted);margin-top:4px">
              Grants: <strong>${{j.grants}}</strong> • Apps: <strong>${{j.applications}}</strong>
            </div>
          </div>
        `
        )
        .join("");

      let members = d.inpadoc_family_members || [];
      if (state.selectedCountry) {{
        members = members.filter((m) => m.country_code === state.selectedCountry);
      }}
      document.getElementById("familyTableTitle").textContent =
        `INPADOC Family Member Publications (${{members.length}}${{state.selectedCountry ? " in " + state.selectedCountry : ""}})`;

      document.getElementById("familyTableContainer").innerHTML = `
        <table class="data-table">
          <thead>
            <tr>
              <th>Publication Number</th>
              <th>Jurisdiction</th>
              <th>Kind</th>
              <th>Publication Date</th>
              <th>Title</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            ${{members
              .map(
                (m) => `
              <tr>
                <td style="font-family:var(--font-mono);font-weight:700;color:var(--brand-blue)">${{escapeHtml(m.publication_number)}}</td>
                <td>${{escapeHtml(m.country_code)}}</td>
                <td><span class="status-pill">${{escapeHtml(m.kind_code)}}</span></td>
                <td style="font-family:var(--font-mono)">${{escapeHtml(m.publication_date || "—")}}</td>
                <td>${{escapeHtml(m.title || "—")}}</td>
                <td>
                  <button class="btn btn-sm" onclick="fetchTimeline('${{m.publication_number}}')">⏱️ Timeline</button>
                </td>
              </tr>
            `
              )
              .join("")}}
          </tbody>
        </table>
      `;
    }}

    function renderNplTab() {{
      const d = state.data;
      if (!d) return;
      const kw = (document.getElementById("nplSearch")?.value || "").toLowerCase();
      const npls = (d.non_patent_literature_prior_art || []).filter(
        (n) => !kw || (n.literature_text || "").toLowerCase().includes(kw)
      );
      if (!npls.length) {{
        document.getElementById("nplContainer").innerHTML = `<div style="color:var(--text-muted)">No Non-Patent Literature citations found for this patent.</div>`;
        return;
      }}
      document.getElementById("nplContainer").innerHTML = npls
        .map(
          (n, i) => `
          <div class="milestone-row" style="grid-template-columns:50px 1fr auto;margin-bottom:8px">
            <span style="font-family:var(--font-mono);font-weight:700;color:var(--brand-blue)">[NPL ${{(i + 1)}}]</span>
            <div>
              <div style="font-size:13px">${{escapeHtml(n.literature_text)}}</div>
              <div style="font-size:11px;color:var(--text-muted);margin-top:2px">Category: ${{escapeHtml(n.category || "cited")}} • ${{escapeHtml(n.source || "Scholar")}}</div>
            </div>
            <button class="btn btn-sm" onclick="askAiAboutNpl(${{i}})">✨ Ask AI</button>
          </div>
        `
        )
        .join("");
    }}

    function askAiPriorArtCutoff() {{
      const d = state.data;
      if (!d) return;
      const kd = d.key_dates || {{}};
      sendMcpRequest("ui/message", {{
        role: "user",
        content: [{{
          type: "text",
          text: `For patent ${{d.publication_number}} ("${{d.title}}") with priority date ${{kd.priority_date}} and ${{d.inpadoc_family_members_count}} INPADOC family members across ${{d.jurisdictions_count}} jurisdictions, summarize its global protection footprint, statutory expiration status (${{kd.estimated_expiration_date}}), and prior-art search strategy prior to ${{kd.priority_date}}.`,
        }}],
      }}).catch(() => {{}});
      showToast("Sent prior-art & family strategy prompt to AI host");
    }}

    function askAiAboutNpl(idx) {{
      const d = state.data;
      const npl = d?.non_patent_literature_prior_art?.[idx];
      if (!npl) return;
      sendMcpRequest("ui/message", {{
        role: "user",
        content: [{{
          type: "text",
          text: `Analyze this Non-Patent Literature (NPL) reference cited in ${{d.publication_number}} (Priority Date: ${{d.key_dates?.priority_date}}):\\n\\n"${{npl.literature_text}}"\\n\\nWhat technical teaching does this reference likely disclose?`,
        }}],
      }}).catch(() => {{}});
      showToast("Sent NPL analysis prompt to AI host");
    }}

    window.addEventListener("DOMContentLoaded", () => {{
      initBridge();
      if (state.data) renderAll();
    }});
  </script>
</body>
</html>"""
