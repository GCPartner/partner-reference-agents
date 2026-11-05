"""MCP App 1: D&B Entity Resolution & D-U-N-S Matcher (`ui://dnb/entity-matcher`).

Solves the mandatory first step of every Dun & Bradstreet workflow (`MatchTool`) by separating
the Global Ultimate HQ from operating subsidiaries and collapsing unrelated standalone homonyms.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from .brand_theme import (
    DEFAULT_PUBLIC_API_BASE_URL,
    build_dnb_bridge_js,
    build_dnb_network_canvas_svg,
    build_dnb_shared_css,
)

ENTITY_MATCHER_RESOURCE_URI = "ui://dnb/entity-matcher"

ENTITY_MATCHER_APP_TOOL_META: Dict[str, Any] = {
    "ui": {
        "resourceUri": ENTITY_MATCHER_RESOURCE_URI,
        "visibility": ["model", "app"],
    },
    "ui/resourceUri": ENTITY_MATCHER_RESOURCE_URI,
}

ENTITY_MATCHER_APP_RESOURCE_META: Dict[str, Any] = {
    "ui": {
        "prefersBorder": True,
        "csp": {
            "connectDomains": [DEFAULT_PUBLIC_API_BASE_URL, "https://plus.dnb.com", "*"],
            "resourceDomains": [DEFAULT_PUBLIC_API_BASE_URL, "*"],
            "frameDomains": [DEFAULT_PUBLIC_API_BASE_URL, "*"],
        },
    }
}

_LAST_MATCHER_PAYLOAD: Optional[Dict[str, Any]] = None


def set_cached_matcher_payload(payload: Dict[str, Any]) -> None:
    global _LAST_MATCHER_PAYLOAD
    if isinstance(payload, dict):
        _LAST_MATCHER_PAYLOAD = payload


def get_cached_matcher_payload() -> Optional[Dict[str, Any]]:
    return _LAST_MATCHER_PAYLOAD


def build_entity_matcher_html(
    initial_payload: Optional[Dict[str, Any]] = None,
    api_base_url: str = DEFAULT_PUBLIC_API_BASE_URL,
    include_suite_templates: bool = True,
) -> str:
    """Renders the self-contained `dnb.ai`-styled HTML for `ui://dnb/entity-matcher`."""
    effective_payload = (initial_payload or _LAST_MATCHER_PAYLOAD) if include_suite_templates else initial_payload
    serialized_payload = (
        json.dumps(effective_payload, ensure_ascii=False).replace("</", "<\\/")
        if effective_payload
        else "null"
    )
    shared_css = build_dnb_shared_css()
    bg_svg = build_dnb_network_canvas_svg()
    bridge_js = build_dnb_bridge_js(
        "D&B Entity Resolution & DUNS Matcher",
        api_base_url=api_base_url,
        include_suite_templates=include_suite_templates,
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>D&amp;B Entity Resolution &amp; D-U-N-S Matcher</title>
  <style>
    {shared_css}

    .spotlight-card {{
      position: relative;
      padding: 20px 22px;
      border-radius: 14px;
      background: linear-gradient(180deg, #F2F8F9 0%, #E5EEF1 100%);
      border: 2px solid var(--primary-light-blue);
      box-shadow: 0 8px 22px rgba(0, 81, 114, 0.10);
      margin-bottom: 18px;
    }}

    .spotlight-kicker {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--primary-dark-blue-1);
      background: var(--white);
      border: 1px solid var(--primary-light-blue-40);
      padding: 4px 10px;
      border-radius: 999px;
      margin-bottom: 10px;
    }}

    .spotlight-grid {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 16px;
      flex-wrap: wrap;
    }}

    .spotlight-actions {{
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      margin-top: 14px;
      padding-top: 12px;
      border-top: 1px solid rgba(48, 149, 180, 0.25);
    }}

    .sub-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }}

    @media (max-width: 760px) {{
      .sub-grid {{
        grid-template-columns: 1fr;
      }}
    }}

    .candidate-card {{
      padding: 14px 16px;
      border-radius: 12px;
      background: var(--white);
      border: 1px solid var(--border-gray);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 10px;
      transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }}

    .candidate-card:hover {{
      border-color: var(--primary-light-blue);
      box-shadow: 0 6px 16px rgba(0, 81, 114, 0.08);
    }}

    .candidate-name {{
      font-size: 15px;
      font-weight: 800;
      color: var(--primary-dark-blue-3);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }}

    .candidate-meta {{
      font-size: 12px;
      color: var(--text-gray);
      line-height: 1.45;
    }}

    .candidate-footer {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      flex-wrap: wrap;
      padding-top: 8px;
      border-top: 1px solid var(--primary-blue-10);
    }}

    .accordion-toggle {{
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 11px 16px;
      border-radius: 10px;
      background: var(--primary-light-blue-10);
      border: 1px solid var(--primary-light-blue-40);
      color: var(--primary-dark-blue-1);
      font-family: var(--font-sans);
      font-size: 13px;
      font-weight: 700;
      cursor: pointer;
    }}

    .accordion-toggle:hover {{
      background: var(--primary-blue-10);
    }}
  </style>
</head>
<body>
  <div class="dnb-outer-stage">
    {bg_svg}
    <div class="dnb-app-shell">
      <!-- Top Brand Bar -->
      <div class="dnb-topbar">
        <div class="dnb-brand-group">
          <div class="dnb-logo-badge">
            <span>dun<span class="dnb-logo-amp">&amp;</span>bradstreet</span>
            <span class="dnb-ai-pill">AI ✦</span>
          </div>
          <span class="dnb-topbar-title">Entity Resolution &amp; D-U-N-S® Disambiguation</span>
        </div>
        <div class="dnb-topbar-controls">
          <input id="companySearchInput" class="dnb-input" type="text" placeholder="Company name (e.g., Google, Alphabet)..." value="Google" style="width:210px;" />
          <select id="countrySelect" class="dnb-select">
            <option value="US" selected>US (United States)</option>
            <option value="GB">GB (United Kingdom)</option>
            <option value="DE">DE (Germany)</option>
            <option value="CA">CA (Canada)</option>
            <option value="IE">IE (Ireland)</option>
            <option value="IN">IN (India)</option>
            <option value="JP">JP (Japan)</option>
            <option value="SG">SG (Singapore)</option>
          </select>
          <button id="runMatchBtn" class="btn btn-cyan">Search D&amp;B Match</button>
        </div>
      </div>

      <!-- Main Body -->
      <div class="dnb-body">
        <!-- 3 KPI Summary Tiles -->
        <div class="kpi-grid-3">
          <div class="kpi-card kpi-card-clickable" id="kpiCardRecommended" title="Click to open 360° Executive Snapshot">
            <span class="kpi-label">Recommended Ultimate HQ ↗</span>
            <span id="kpiRecommendedName" class="kpi-value" style="font-size:20px;">Alphabet Inc.</span>
            <span id="kpiRecommendedDuns" class="kpi-sub">D-U-N-S® 07-994-2718 • Global Ultimate</span>
          </div>
          <div class="kpi-card kpi-card-clickable" id="kpiCardSubsidiaries" title="Click to jump to Linked Operating Units">
            <span class="kpi-label">Linked Operating Units ⇣</span>
            <span id="kpiSubsidiariesCount" class="kpi-value">13</span>
            <span class="kpi-sub">Verified Subsidiaries &amp; Divisions in Family Tree</span>
          </div>
          <div class="kpi-card kpi-card-clickable" id="kpiCardOther" title="Click to toggle Unlinked Name Homonyms">
            <span class="kpi-label">Unlinked Name Homonyms ⇣</span>
            <span id="kpiOtherCount" class="kpi-value">11</span>
            <span class="kpi-sub">Standalone Records (Auto-Collapsed Below)</span>
          </div>
        </div>

        <!-- Spotlight Recommended Global Ultimate Card -->
        <div id="spotlightContainer"></div>

        <!-- Operating Subsidiaries Section -->
        <div class="section-card" id="subsidiariesSectionCard">
          <div class="section-header">
            <div class="section-title">
              <span>🏢 Linked Operating Subsidiaries &amp; Headquarters</span>
              <span id="subCountBadge" class="badge badge-cyan">13 Entities</span>
            </div>
            <input id="filterCandidateInput" class="dnb-input" type="text" placeholder="Filter by subsidiary name, city, or trade style..." style="width:280px;height:32px;font-size:12px;" />
          </div>
          <div id="subsidiariesGrid" class="sub-grid"></div>
        </div>

        <!-- Collapsed Unlinked / Standalone Entities -->
        <div style="margin-top: 12px;" id="otherMatchesSection">
          <button id="toggleOtherBtn" type="button" class="accordion-toggle">
            <span id="toggleOtherLabel">Show 11 Unlinked / Standalone Name Matches (Filtered Out to Prevent Noise)</span>
            <span id="toggleOtherArrow">▾</span>
          </button>
          <div id="otherMatchesContainer" style="display:none; margin-top: 12px;" class="sub-grid"></div>
        </div>
      </div>

      <!-- Footer -->
      <div class="dnb-footer">
        <div>
          <span class="status-dot"></span>
          <span id="statusText">Verified via D&amp;B MatchTool (/v1/search/criteria) • Select a verified D-U-N-S® before running deep dossier calls</span>
        </div>
        <div style="font-family:var(--font-mono);font-size:11px;">ui://dnb/entity-matcher</div>
      </div>
    </div>
  </div>

  <script>
  (function() {{
    const INITIAL_PAYLOAD = {serialized_payload};
    let currentPayload = null;
    let showOtherMatches = false;

    {bridge_js}

    function renderSpotlight(rec) {{
      const container = document.getElementById("spotlightContainer");
      if (!rec) {{
        container.innerHTML = `<div class="section-card">No matching D&B candidates found. Try broadening the company name.</div>`;
        return;
      }}
      const tradeStr = (rec.trade_styles && rec.trade_styles.length)
        ? `Trade Styles: <strong>${{escapeHtml(rec.trade_styles.join(", "))}}</strong> • `
        : "";
      container.innerHTML = `
        <div class="spotlight-card">
          <div class="spotlight-kicker">✦ Recommended Global Ultimate &amp; Parent Headquarters</div>
          <div class="spotlight-grid">
            <div>
              <div class="dnb-entity-title">
                <span>${{escapeHtml(rec.primary_name)}}</span>
                <span class="duns-pill" data-copy-duns="${{escapeHtml(rec.duns)}}" title="Click to copy 9-digit D-U-N-S">
                  D-U-N-S® ${{escapeHtml(rec.duns_formatted || rec.duns)}} 📋
                </span>
                <span class="badge badge-success">✓ ${{rec.confidence_pct || 99}}% Match Confidence</span>
                <span class="badge badge-teal">${{escapeHtml(rec.role_badge || "GLOBAL ULTIMATE")}}</span>
              </div>
              <div class="dnb-subtitle-row">
                <span>📍 ${{escapeHtml(rec.address)}}</span>
                <span>•</span>
                <span>${{tradeStr}}☎ ${{escapeHtml(rec.telephone || "—")}}</span>
              </div>
            </div>
          </div>
          <div class="spotlight-actions">
            <button type="button" class="btn btn-primary" data-select-action="360" data-duns="${{escapeHtml(rec.duns)}}" data-name="${{escapeHtml(rec.primary_name)}}">
              Open 360° Executive Snapshot →
            </button>
            <button type="button" class="btn btn-outline" data-select-action="tree" data-duns="${{escapeHtml(rec.duns)}}" data-name="${{escapeHtml(rec.primary_name)}}">
              Explore Corporate Family Tree
            </button>
            <button type="button" class="btn btn-outline" data-select-action="risk" data-duns="${{escapeHtml(rec.duns)}}" data-name="${{escapeHtml(rec.primary_name)}}">
              Run Supplier Risk &amp; Credit Scorecard
            </button>
          </div>
        </div>
      `;
    }}

    function renderCandidateCard(c) {{
      const tradePills = (c.trade_styles && c.trade_styles.length)
        ? `<div style="margin-top:4px;font-size:11.5px;color:var(--primary-dark-blue-1);">Trade Styles: <strong>${{escapeHtml(c.trade_styles.join(", "))}}</strong></div>`
        : "";
      const badgeClass = c.is_hq ? "badge-teal" : (c.tier === "other" ? "badge-warning" : "badge-cyan");
      return `
        <div class="candidate-card">
          <div>
            <div class="candidate-name">
              <span>${{escapeHtml(c.primary_name)}}</span>
              <span class="duns-pill" style="font-size:11px;padding:2px 8px;" data-copy-duns="${{escapeHtml(c.duns)}}">
                ${{escapeHtml(c.duns_formatted || c.duns)}}
              </span>
            </div>
            <div style="margin-top:5px;display:flex;gap:6px;flex-wrap:wrap;">
              <span class="badge ${{badgeClass}}" style="font-size:10.5px;padding:2px 8px;">${{escapeHtml(c.role_badge)}}</span>
              <span class="badge badge-success" style="font-size:10.5px;padding:2px 8px;">${{c.confidence_pct}}% Match</span>
            </div>
            <div class="candidate-meta" style="margin-top:8px;">
              📍 ${{escapeHtml(c.address)}}
              ${{tradePills}}
            </div>
          </div>
          <div class="candidate-footer">
            <span style="font-size:11.5px;color:var(--text-gray);">☎ ${{escapeHtml(c.telephone || "—")}}</span>
            <div style="display:flex;gap:5px;flex-wrap:wrap;">
              <button type="button" class="btn btn-outline" style="height:28px;padding:0 9px;font-size:11.5px;" data-select-action="360" data-duns="${{escapeHtml(c.duns)}}" data-name="${{escapeHtml(c.primary_name)}}">
                Select 360° Profile
              </button>
              <button type="button" class="btn btn-outline" style="height:28px;padding:0 9px;font-size:11.5px;" data-select-action="tree" data-duns="${{escapeHtml(c.duns)}}" data-name="${{escapeHtml(c.primary_name)}}">
                Family Tree
              </button>
              <button type="button" class="btn btn-outline" style="height:28px;padding:0 9px;font-size:11.5px;" data-select-action="risk" data-duns="${{escapeHtml(c.duns)}}" data-name="${{escapeHtml(c.primary_name)}}">
                Risk Check
              </button>
            </div>
          </div>
        </div>
      `;
    }}

    function renderLists() {{
      if (!currentPayload) return;
      const q = (document.getElementById("filterCandidateInput")?.value || "").trim().toLowerCase();
      const subs = (currentPayload.operating_subsidiaries || []).filter((c) => {{
        if (!q) return true;
        const hay = `${{c.primary_name}} ${{c.duns}} ${{c.address}} ${{(c.trade_styles || []).join(" ")}} ${{c.family_tree_role}}`.toLowerCase();
        return hay.includes(q);
      }});
      const others = (currentPayload.other_matches || []).filter((c) => {{
        if (!q) return true;
        const hay = `${{c.primary_name}} ${{c.duns}} ${{c.address}} ${{(c.trade_styles || []).join(" ")}}`.toLowerCase();
        return hay.includes(q);
      }});

      document.getElementById("subCountBadge").textContent = `${{subs.length}} Entities`;
      document.getElementById("subsidiariesGrid").innerHTML = subs.length
        ? subs.map(renderCandidateCard).join("")
        : `<div style="padding:12px;color:var(--text-gray);font-size:13px;">No linked subsidiaries match your filter.</div>`;

      document.getElementById("otherMatchesContainer").innerHTML = others.map(renderCandidateCard).join("");
      document.getElementById("toggleOtherLabel").textContent =
        `${{showOtherMatches ? "Hide" : "Show"}} ${{others.length}} Unlinked / Standalone Name Matches (Filtered Out to Prevent Noise)`;

      bindActionButtons();
    }}

    function bindActionButtons() {{
      document.querySelectorAll("[data-copy-duns]").forEach((el) => {{
        el.onclick = () => copyDunsToClipboard(el.getAttribute("data-copy-duns"), el);
      }});

      document.querySelectorAll("[data-select-action]").forEach((btn) => {{
        btn.onclick = () => {{
          const action = btn.getAttribute("data-select-action");
          const duns = btn.getAttribute("data-duns");
          if (action === "360") {{
            switchToMcpApp("open_company_360_app", {{ duns }}, `/apps/raw/company-360?duns=${{encodeURIComponent(duns)}}`, btn);
          }} else if (action === "tree") {{
            switchToMcpApp("open_corporate_family_tree_app", {{ duns }}, `/apps/raw/family-tree?duns=${{encodeURIComponent(duns)}}`, btn);
          }} else if (action === "risk") {{
            switchToMcpApp("open_supplier_risk_scorecard_app", {{ duns }}, `/apps/raw/supplier-risk?duns=${{encodeURIComponent(duns)}}`, btn);
          }}
        }};
      }});
    }}

    function hydratePayload(payload) {{
      if (!payload || typeof payload !== "object") return;
      registerPayloadInSuiteBundle(payload);
      currentPayload = payload;
      if (payload.query?.name) {{
        document.getElementById("companySearchInput").value = payload.query.name;
      }}
      if (payload.query?.country) {{
        document.getElementById("countrySelect").value = payload.query.country;
      }}
      const rec = payload.recommended_candidate;
      document.getElementById("kpiRecommendedName").textContent = rec ? rec.primary_name : "—";
      document.getElementById("kpiRecommendedDuns").textContent = rec
        ? `D-U-N-S® ${{rec.duns_formatted || rec.duns}} • ${{rec.role_badge}}`
        : "No candidate found";
      document.getElementById("kpiSubsidiariesCount").textContent = String((payload.operating_subsidiaries || []).length);
      document.getElementById("kpiOtherCount").textContent = String((payload.other_matches || []).length);

      renderSpotlight(rec);
      renderLists();

      if (payload.data_source) {{
        const statusEl = document.getElementById("statusText");
        if (statusEl) statusEl.textContent = `Source: ${{payload.data_source}} • Matched ${{(payload.candidates || []).length}} records for "${{payload.query?.name || ""}}" (${{payload.query?.country || "US"}})`;
      }}
    }}

    async function runEntitySearch() {{
      const btn = document.getElementById("runMatchBtn");
      const name = document.getElementById("companySearchInput").value.trim() || "Google";
      const country = document.getElementById("countrySelect").value || "US";
      const origTxt = btn.innerHTML;
      btn.disabled = true;
      btn.classList.add("is-loading");
      btn.textContent = "⏳ Searching...";
      try {{
        const data = await callMcpToolWithFallback("open_entity_matcher_app", {{
          name,
          country_code: country,
        }});
        if (data) {{
          hydratePayload(data);
          if (
            typeof window !== "undefined" &&
            window.location &&
            window.location.protocol &&
            window.location.protocol.startsWith("http") &&
            (window.location.pathname.startsWith("/apps/") ||
              window.location.hostname === "127.0.0.1" ||
              window.location.hostname === "localhost") &&
            window.history &&
            window.history.replaceState
          ) {{
            try {{
              window.history.replaceState({{}}, "", `/apps/raw/entity-matcher?name=${{encodeURIComponent(name)}}&country=${{encodeURIComponent(country)}}`);
            }} catch (_) {{}}
          }}
        }}
      }} finally {{
        btn.disabled = false;
        btn.classList.remove("is-loading");
        btn.innerHTML = origTxt;
      }}
    }}

    document.getElementById("runMatchBtn").addEventListener("click", runEntitySearch);

    document.getElementById("countrySelect").addEventListener("change", () => {{
      if (document.getElementById("companySearchInput").value.trim()) {{
        runEntitySearch();
      }}
    }});

    document.getElementById("companySearchInput").addEventListener("keydown", (e) => {{
      if (e.key === "Enter") {{
        e.preventDefault();
        runEntitySearch();
      }}
    }});

    document.getElementById("filterCandidateInput").addEventListener("input", () => {{
      renderLists();
    }});

    document.getElementById("toggleOtherBtn").addEventListener("click", () => {{
      showOtherMatches = !showOtherMatches;
      document.getElementById("otherMatchesContainer").style.display = showOtherMatches ? "grid" : "none";
      document.getElementById("toggleOtherArrow").textContent = showOtherMatches ? "▴" : "▾";
      renderLists();
    }});

    document.getElementById("kpiCardRecommended").addEventListener("click", () => {{
      const rec = currentPayload?.recommended_candidate;
      if (rec && rec.duns) {{
        switchToMcpApp("open_company_360_app", {{ duns: rec.duns }}, `/apps/raw/company-360?duns=${{encodeURIComponent(rec.duns)}}`);
      }}
    }});

    document.getElementById("kpiCardSubsidiaries").addEventListener("click", () => {{
      document.getElementById("subsidiariesSectionCard")?.scrollIntoView({{ behavior: "smooth", block: "start" }});
    }});

    document.getElementById("kpiCardOther").addEventListener("click", () => {{
      if (!showOtherMatches) {{
        document.getElementById("toggleOtherBtn").click();
      }}
      document.getElementById("otherMatchesSection")?.scrollIntoView({{ behavior: "smooth", block: "start" }});
    }});

    initBridge();
    const startPayload = window.__DNB_ACTIVE_PAYLOAD__ || INITIAL_PAYLOAD;
    window.__DNB_ACTIVE_PAYLOAD__ = null;
    window.__dnbCurrentHydratePayload = hydratePayload;
    if (startPayload) hydratePayload(startPayload);
  }})();
  </script>
</body>
</html>"""
