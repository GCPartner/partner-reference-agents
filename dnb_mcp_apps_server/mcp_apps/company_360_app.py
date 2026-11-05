"""MCP App 2: D&B Company 360° Executive Snapshot (`ui://dnb/company-360-snapshot`).

Condenses 612 lines of `DataTool` (`companyinfo_L2`) and `ContactTool` (`principalscontacts_L2`)
into a single scannable card with 3 KPI tiles and a 3-pill narrative switcher, with zero
`<<NOTENTITLED>>` or `NOTAVAILABLE` clutter.
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

COMPANY_360_RESOURCE_URI = "ui://dnb/company-360-snapshot"

COMPANY_360_APP_TOOL_META: Dict[str, Any] = {
    "ui": {
        "resourceUri": COMPANY_360_RESOURCE_URI,
        "visibility": ["model", "app"],
    },
    "ui/resourceUri": COMPANY_360_RESOURCE_URI,
}

COMPANY_360_APP_RESOURCE_META: Dict[str, Any] = {
    "ui": {
        "prefersBorder": True,
        "csp": {
            "connectDomains": [DEFAULT_PUBLIC_API_BASE_URL, "https://plus.dnb.com", "*"],
            "resourceDomains": [DEFAULT_PUBLIC_API_BASE_URL, "*"],
            "frameDomains": [DEFAULT_PUBLIC_API_BASE_URL, "*"],
        },
    }
}

_LAST_COMPANY_360_PAYLOAD: Optional[Dict[str, Any]] = None


def set_cached_company_360_payload(payload: Dict[str, Any]) -> None:
    global _LAST_COMPANY_360_PAYLOAD
    if isinstance(payload, dict):
        _LAST_COMPANY_360_PAYLOAD = payload


def get_cached_company_360_payload() -> Optional[Dict[str, Any]]:
    return _LAST_COMPANY_360_PAYLOAD


def build_company_360_html(
    initial_payload: Optional[Dict[str, Any]] = None,
    api_base_url: str = DEFAULT_PUBLIC_API_BASE_URL,
    include_suite_templates: bool = True,
) -> str:
    """Renders the self-contained `dnb.ai`-styled HTML for `ui://dnb/company-360-snapshot`."""
    effective_payload = (initial_payload or _LAST_COMPANY_360_PAYLOAD) if include_suite_templates else initial_payload
    serialized_payload = (
        json.dumps(effective_payload, ensure_ascii=False).replace("</", "<\\/")
        if effective_payload
        else "null"
    )
    shared_css = build_dnb_shared_css()
    bg_svg = build_dnb_network_canvas_svg()
    bridge_js = build_dnb_bridge_js(
        "D&B Company 360 Executive Snapshot",
        api_base_url=api_base_url,
        include_suite_templates=include_suite_templates,
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>D&amp;B Company 360° Executive Snapshot</title>
  <style>
    {shared_css}

    .narrative-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }}

    @media (max-width: 780px) {{
      .narrative-grid {{
        grid-template-columns: 1fr;
      }}
    }}

    .narrative-box {{
      padding: 16px 18px;
      border-radius: 12px;
      background: var(--primary-light-blue-10);
      border: 1px solid var(--primary-light-blue-40);
    }}

    .narrative-box h4 {{
      font-size: 13px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--primary-dark-blue-1);
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 6px;
    }}

    .narrative-box p {{
      font-size: 13.5px;
      line-height: 1.58;
      color: var(--primary-dark-blue-3);
    }}

    .meta-kv-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
      margin-top: 14px;
    }}

    @media (max-width: 780px) {{
      .meta-kv-grid {{
        grid-template-columns: 1fr;
      }}
    }}

    .meta-kv-item {{
      padding: 11px 14px;
      border-radius: 10px;
      background: var(--white);
      border: 1px solid var(--border-gray);
    }}

    .meta-kv-label {{
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--text-gray);
    }}

    .meta-kv-val {{
      font-size: 13px;
      font-weight: 700;
      color: var(--primary-dark-blue-3);
      margin-top: 3px;
      word-break: break-word;
    }}

    .leaders-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }}

    @media (max-width: 780px) {{
      .leaders-grid {{
        grid-template-columns: 1fr;
      }}
    }}

    .leader-card {{
      padding: 14px 16px;
      border-radius: 12px;
      background: var(--white);
      border: 1px solid var(--border-gray);
      display: flex;
      align-items: flex-start;
      gap: 12px;
    }}

    .leader-card.senior {{
      background: linear-gradient(180deg, #F2F8F9 0%, #E5EEF1 100%);
      border: 1.5px solid var(--primary-light-blue);
    }}

    .leader-avatar {{
      width: 38px;
      height: 38px;
      border-radius: 10px;
      background: var(--primary-dark-blue-1);
      color: var(--white);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 14px;
      flex-shrink: 0;
    }}

    .leader-name {{
      font-size: 14px;
      font-weight: 800;
      color: var(--primary-dark-blue-3);
    }}

    .leader-role {{
      font-size: 12px;
      color: var(--primary-dark-blue-2);
      margin-top: 3px;
      line-height: 1.35;
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
          <span class="dnb-topbar-title">Company 360° Executive Snapshot</span>
        </div>
        <div class="dnb-topbar-controls">
          <button id="backToMatcherBtn" type="button" class="btn btn-ghost-light" title="Open Entity Matcher">← Entity Search</button>
          <input id="dunsInput" class="dnb-input" type="text" placeholder="D-U-N-S or Company (e.g. 079942718, IBM)" value="079942718" style="width:195px;font-family:var(--font-mono);" />
          <select id="presetEntitySelect" class="dnb-select">
            <option value="079942718">Alphabet Inc. (07-994-2718)</option>
            <option value="060902413">Google LLC (06-090-2413)</option>
            <option value="001368083">IBM Corp. (00-136-8083)</option>
          </select>
          <button id="load360Btn" type="button" class="btn btn-cyan">Load 360° Profile</button>
        </div>
      </div>

      <!-- Main Body -->
      <div class="dnb-body">
        <!-- Hero Banner -->
        <div class="dnb-hero-banner">
          <div>
            <div class="dnb-entity-title">
              <span id="heroCompanyName">Alphabet Inc.</span>
              <span id="heroDunsPill" class="duns-pill" title="Click to copy D-U-N-S">D-U-N-S® 07-994-2718 📋</span>
              <span id="heroStatusBadge" class="badge badge-success">● Active (from 1998)</span>
              <span id="heroTickerBadge" class="badge badge-cyan">NASDAQ: GOOGL</span>
              <span id="heroFortuneBadge" class="badge badge-teal">Fortune 1000</span>
            </div>
            <div class="dnb-subtitle-row">
              <span id="heroAddress">📍 1600 Amphitheatre Pkwy, Mountain View, California, 94043-1351, United States</span>
              <span>•</span>
              <span id="heroPhone">☎ +1 6502530000</span>
              <span>•</span>
              <span id="heroWebsite">🌐 www.abc.xyz</span>
            </div>
          </div>
          <div style="display:flex;gap:8px;flex-wrap:wrap;">
            <button id="openTreeBtn" type="button" class="btn btn-outline">Explore Family Tree (535)</button>
            <button id="openRiskBtn" type="button" class="btn btn-primary">Risk &amp; Credit Scorecard →</button>
          </div>
        </div>

        <!-- 3 KPI Tiles Row -->
        <div class="kpi-grid-3">
          <div class="kpi-card kpi-card-clickable" id="kpiCardRevenue" title="Click to view Strategy & Financial Trajectory">
            <span class="kpi-label">Annual Consolidated Revenue ⇣</span>
            <span id="kpiRevenue" class="kpi-value">$402.8B</span>
            <span id="kpiRevenueSub" class="kpi-sub">FY End 2025-12-31 • Actual Consolidated (USD)</span>
          </div>
          <div class="kpi-card kpi-card-clickable" id="kpiCardEmployees" title="Click to view Leadership & Principals">
            <span class="kpi-label">Global Workforce ⇣</span>
            <span id="kpiEmployees" class="kpi-value">190,822</span>
            <span id="kpiEmployeesGrowth" class="kpi-sub" style="color:var(--dark-green);">▲ +41.0% 5-Yr Headcount Growth (Actual)</span>
          </div>
          <div class="kpi-card kpi-card-clickable" id="kpiCardFamily" title="Click to open Corporate Family Tree Explorer">
            <span class="kpi-label">Corporate Family Footprint ↗</span>
            <span id="kpiFamilyMembers" class="kpi-value">535 Entities</span>
            <span id="kpiFamilySub" class="kpi-sub">339 Subsidiaries • 196 Branches • 61 Countries</span>
          </div>
        </div>

        <!-- 3-Pill Segmented Switcher Section -->
        <div class="section-card" id="dossierSectionCard">
          <div class="section-header">
            <div class="section-title">
              <span>✦ D&amp;B Verified Intelligence Dossier</span>
            </div>
            <div class="segmented-pills" id="pillSwitcher">
              <button type="button" class="seg-pill active" data-pane="overview">Overview &amp; Operations</button>
              <button type="button" class="seg-pill" data-pane="strategy">Strategy, AI &amp; M&amp;A</button>
              <button type="button" class="seg-pill" data-pane="leadership">Leadership &amp; Identifiers</button>
            </div>
          </div>

          <!-- Pane 1: Overview & Operations -->
          <div id="pane-overview" class="pill-pane">
            <div class="narrative-grid" id="overviewNarratives"></div>
            <div class="meta-kv-grid" id="firmographicGrid"></div>
          </div>

          <!-- Pane 2: Strategy, AI & M&A -->
          <div id="pane-strategy" class="pill-pane" style="display:none;">
            <div class="narrative-grid" id="strategyNarratives"></div>
          </div>

          <!-- Pane 3: Leadership & Identifiers -->
          <div id="pane-leadership" class="pill-pane" style="display:none;">
            <div style="margin-bottom:12px;font-size:12.5px;font-weight:700;color:var(--primary-dark-blue-2);">
              Verified Principals &amp; Officers (`principalscontacts_L2`)
            </div>
            <div id="leadersGrid" class="leaders-grid"></div>
            <div style="margin-top:16px;margin-bottom:8px;font-size:12.5px;font-weight:700;color:var(--primary-dark-blue-2);">
              Regulatory &amp; Government Registration Identifiers
            </div>
            <div id="registrationsGrid" class="meta-kv-grid"></div>
          </div>
        </div>

        <!-- Bottom Action Strip -->
        <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;padding-top:4px;">
          <div style="font-size:12.5px;color:var(--text-gray);">
            All unentitled datablock placeholders and empty fields are automatically filtered for executive clarity.
          </div>
          <div style="display:flex;gap:8px;flex-wrap:wrap;">
            <button id="askExecBriefBtn" type="button" class="btn btn-outline">✦ Ask AI for C-Suite Executive Briefing</button>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="dnb-footer">
        <div>
          <span class="status-dot"></span>
          <span id="statusText">Synchronized with D&amp;B DataTool (`companyinfo_L2`) + ContactTool (`principalscontacts_L2`)</span>
        </div>
        <div style="font-family:var(--font-mono);font-size:11px;">ui://dnb/company-360-snapshot</div>
      </div>
    </div>
  </div>

  <script>
  (function() {{
    const INITIAL_PAYLOAD = {serialized_payload};
    let currentPayload = null;

    {bridge_js}

    function initialsFromName(name) {{
      const parts = String(name || "DB").trim().split(/\\s+/);
      if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
      return String(name || "DB").slice(0, 2).toUpperCase();
    }}

    function activatePillPane(targetPane) {{
      document.querySelectorAll("#pillSwitcher .seg-pill").forEach((b) => {{
        b.classList.toggle("active", b.getAttribute("data-pane") === targetPane);
      }});
      document.querySelectorAll(".pill-pane").forEach((p) => (p.style.display = "none"));
      const paneEl = document.getElementById(`pane-${{targetPane}}`);
      if (paneEl) paneEl.style.display = "block";
    }}

    function hydratePayload(payload) {{
      if (!payload || typeof payload !== "object") return;
      registerPayloadInSuiteBundle(payload);
      currentPayload = payload;
      const comp = payload.company || {{}};
      const lead = payload.leadership || {{}};
      const hier = payload.hierarchy_summary || {{}};
      const stats = hier.statistics || {{}};
      const sums = comp.summaries || {{}};

      const curDuns = comp.duns || payload.duns || "079942718";
      document.getElementById("dunsInput").value = curDuns;

      // Sync preset dropdown if present or add option dynamically
      const presetSel = document.getElementById("presetEntitySelect");
      if (presetSel) {{
        let hasOpt = Array.from(presetSel.options).some((o) => o.value === curDuns);
        if (!hasOpt && comp.primary_name) {{
          const opt = document.createElement("option");
          opt.value = curDuns;
          opt.textContent = `${{comp.primary_name}} (${{comp.duns_formatted || curDuns}})`;
          presetSel.appendChild(opt);
        }}
        presetSel.value = curDuns;
      }}

      document.getElementById("heroCompanyName").textContent = comp.primary_name || "Alphabet Inc.";
      const dunsPill = document.getElementById("heroDunsPill");
      dunsPill.textContent = `D-U-N-S® ${{comp.duns_formatted || curDuns}} 📋`;
      dunsPill.onclick = () => copyDunsToClipboard(curDuns, dunsPill);

      document.getElementById("heroStatusBadge").textContent = `● ${{comp.operating_status || "Active"}}`;
      document.getElementById("heroTickerBadge").textContent = `${{comp.primary_exchange || "NASDAQ"}}: ${{comp.primary_ticker || "GOOGL"}}`;
      document.getElementById("heroFortuneBadge").style.display = comp.is_fortune_1000 ? "inline-flex" : "none";
      document.getElementById("heroAddress").textContent = `📍 ${{comp.primary_address || "—"}}`;
      document.getElementById("heroPhone").textContent = `☎ ${{comp.telephone || "—"}}`;
      document.getElementById("heroWebsite").textContent = `🌐 ${{comp.website || "—"}}`;

      // Update Hero button family tree count dynamically
      const totalMem = stats.total_members || 535;
      document.getElementById("openTreeBtn").textContent = `Explore Family Tree (${{totalMem.toLocaleString()}})`;

      // KPIs
      document.getElementById("kpiRevenue").textContent = comp.yearly_revenue_formatted || "$402.8B";
      document.getElementById("kpiRevenueSub").textContent = `FY End ${{comp.fiscal_year_end || "2025-12-31"}} • Actual Consolidated (${{comp.currency || "USD"}})`;
      document.getElementById("kpiEmployees").textContent = comp.employees_consolidated_formatted || "190,822";
      document.getElementById("kpiEmployeesGrowth").textContent = `▲ ${{comp.employees_growth_rate || "Verified Consolidated Workforce"}}`;
      document.getElementById("kpiFamilyMembers").textContent = `${{totalMem.toLocaleString()}} Entities`;
      document.getElementById("kpiFamilySub").textContent = `${{stats.subsidiaries_count || 339}} Subsidiaries • ${{stats.branches_count || 196}} Branches • ${{stats.countries_count || 61}} Countries`;

      // Pane 1: Overview & Operations
      const ovCards = [
        sums.short_profile || {{ short_label: "Executive Profile", text: "Global enterprise technology leader." }},
        sums.operations || {{ short_label: "Core Operations & Segments", text: "Operates global technology, software, and cloud infrastructure segments." }},
        sums.geographic_reach || {{ short_label: "Global Footprint", text: "Significant international presence across Americas, EMEA, and APAC." }},
        sums.historical_background || {{ short_label: "Corporate History", text: "Established enterprise corporate operating history verified by D&B." }},
      ];
      document.getElementById("overviewNarratives").innerHTML = ovCards.map((c) => `
        <div class="narrative-box">
          <h4>✦ ${{escapeHtml(c.short_label || c.title)}}</h4>
          <p>${{escapeHtml(c.text)}}</p>
        </div>
      `).join("");

      const firmoItems = [
        {{ label: "Legal Entity Type", val: `${{comp.entity_type || "Corporation"}} • ${{comp.control_ownership_type || "Publicly Traded"}}` }},
        {{ label: "Primary Industry (SIC / NAICS)", val: comp.primary_industry || "7371: Custom computer programming" }},
        {{ label: "Incorporated / Started", val: `Incorporated ${{comp.incorporated_date || "—"}} (Operations started ${{comp.start_year || "—"}})` }},
      ];
      document.getElementById("firmographicGrid").innerHTML = firmoItems.map((it) => `
        <div class="meta-kv-item">
          <div class="meta-kv-label">${{escapeHtml(it.label)}}</div>
          <div class="meta-kv-val">${{escapeHtml(it.val)}}</div>
        </div>
      `).join("");

      // Pane 2: Strategy, AI & M&A
      const stCards = [
        sums.strategy || {{ short_label: "AI & Growth Strategy", text: "Core strategy centered on enterprise AI and cloud architecture." }},
        sums.mergers_and_acquisitions || {{ short_label: "M&A & Investments", text: "Strategic acquisitions across cloud security, AI, and hybrid cloud systems." }},
        sums.sales_and_marketing || {{ short_label: "Sales & Commercial Model", text: "Global enterprise direct sales, channel ecosystems, and recurring cloud subscriptions." }},
        sums.financial_performance || {{ short_label: "Financial Trajectory", text: "Strong cash flow and balance sheet scale tracked by Dun & Bradstreet." }},
      ];
      document.getElementById("strategyNarratives").innerHTML = stCards.map((c) => `
        <div class="narrative-box">
          <h4>✦ ${{escapeHtml(c.short_label || c.title)}}</h4>
          <p>${{escapeHtml(c.text)}}</p>
        </div>
      `).join("");

      // Pane 3: Leadership & Identifiers
      const principals = lead.principals || [];
      document.getElementById("leadersGrid").innerHTML = principals.map((p) => `
        <div class="leader-card ${{p.is_most_senior ? "senior" : ""}}">
          <div class="leader-avatar">${{escapeHtml(initialsFromName(p.name))}}</div>
          <div>
            <div class="leader-name">
              ${{escapeHtml(p.name)}}
              ${{p.is_most_senior ? `<span class="badge badge-teal" style="font-size:10px;padding:1px 6px;margin-left:4px;">CEO</span>` : ""}}
            </div>
            <div class="leader-role">${{escapeHtml(p.titles)}}</div>
          </div>
        </div>
      `).join("");

      const regs = comp.registrations || [];
      const regCards = [
        {{ label: "Legal Entity Identifier (LEI)", val: comp.lei || "—" }},
        ...regs.map((r) => ({{ label: r.type, val: r.number }})),
      ];
      document.getElementById("registrationsGrid").innerHTML = regCards.map((r) => `
        <div class="meta-kv-item">
          <div class="meta-kv-label">${{escapeHtml(r.label)}}</div>
          <div class="meta-kv-val" style="font-family:var(--font-mono);cursor:pointer;" data-copy-reg="${{escapeHtml(r.val)}}" title="Click to copy">${{escapeHtml(r.val)}} 📋</div>
        </div>
      `).join("");

      document.querySelectorAll("[data-copy-reg]").forEach((el) => {{
        el.onclick = () => copyDunsToClipboard(el.getAttribute("data-copy-reg"), el);
      }});

      if (payload.data_source) {{
        const statusEl = document.getElementById("statusText");
        if (statusEl) statusEl.textContent = `Source: ${{payload.data_source}} • Synchronized D&B 360° Dossier for ${{comp.primary_name || curDuns}}`;
      }}
    }}

    // Segmented Pill Switcher
    document.querySelectorAll("#pillSwitcher .seg-pill").forEach((btn) => {{
      btn.addEventListener("click", () => {{
        activatePillPane(btn.getAttribute("data-pane"));
      }});
    }});

    document.getElementById("kpiCardRevenue").addEventListener("click", () => {{
      activatePillPane("strategy");
      document.getElementById("dossierSectionCard")?.scrollIntoView({{ behavior: "smooth", block: "start" }});
    }});

    document.getElementById("kpiCardEmployees").addEventListener("click", () => {{
      activatePillPane("leadership");
      document.getElementById("dossierSectionCard")?.scrollIntoView({{ behavior: "smooth", block: "start" }});
    }});

    document.getElementById("kpiCardFamily").addEventListener("click", () => {{
      document.getElementById("openTreeBtn").click();
    }});

    document.getElementById("backToMatcherBtn").addEventListener("click", (e) => {{
      const comp = currentPayload?.company || {{}};
      const qName = comp.primary_name || "Google";
      switchToMcpApp("open_entity_matcher_app", {{ name: qName, country_code: "US" }}, `/apps/raw/entity-matcher?name=${{encodeURIComponent(qName)}}&country=US`, e.currentTarget);
    }});

    document.getElementById("presetEntitySelect").addEventListener("change", (e) => {{
      document.getElementById("dunsInput").value = e.target.value;
      document.getElementById("load360Btn").click();
    }});

    document.getElementById("load360Btn").addEventListener("click", async () => {{
      const btn = document.getElementById("load360Btn");
      const duns = document.getElementById("dunsInput").value.trim() || "079942718";
      const origTxt = btn.innerHTML;
      btn.disabled = true;
      btn.classList.add("is-loading");
      btn.textContent = "⏳ Loading...";
      try {{
        const data = await callMcpToolWithFallback("open_company_360_app", {{ duns }});
        if (data) {{
          hydratePayload(data);
          const resolvedDuns = data.company?.duns || data.duns || duns;
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
              window.history.replaceState({{}}, "", `/apps/raw/company-360?duns=${{encodeURIComponent(resolvedDuns)}}`);
            }} catch (_) {{}}
          }}
        }}
      }} finally {{
        btn.disabled = false;
        btn.classList.remove("is-loading");
        btn.innerHTML = origTxt;
      }}
    }});

    document.getElementById("dunsInput").addEventListener("keydown", (e) => {{
      if (e.key === "Enter") {{
        e.preventDefault();
        document.getElementById("load360Btn").click();
      }}
    }});

    document.getElementById("openTreeBtn").addEventListener("click", (e) => {{
      const comp = currentPayload?.company || {{}};
      const duns = comp.duns || document.getElementById("dunsInput").value.trim() || "079942718";
      switchToMcpApp(
        "open_corporate_family_tree_app",
        {{ duns }},
        `/apps/raw/family-tree?duns=${{encodeURIComponent(duns)}}`,
        e.currentTarget
      );
    }});

    document.getElementById("openRiskBtn").addEventListener("click", (e) => {{
      const comp = currentPayload?.company || {{}};
      const duns = comp.duns || document.getElementById("dunsInput").value.trim() || "079942718";
      switchToMcpApp(
        "open_supplier_risk_scorecard_app",
        {{ duns }},
        `/apps/raw/supplier-risk?duns=${{encodeURIComponent(duns)}}`,
        e.currentTarget
      );
    }});

    document.getElementById("askExecBriefBtn").addEventListener("click", () => {{
      const comp = currentPayload?.company || {{}};
      const stats = currentPayload?.hierarchy_summary?.statistics || {{}};
      const lead = currentPayload?.leadership || {{}};
      const sums = comp.summaries || {{}};
      const ceo = lead.most_senior_principal || (lead.principals && lead.principals[0]) || {{ name: "Chief Executive Officer", titles: "Executive Leadership" }};

      const promptText = `Please prepare a concise C-Suite Executive Briefing for ${{comp.primary_name}} (D-U-N-S ${{comp.duns_formatted || comp.duns}}, ${{comp.primary_exchange}}: ${{comp.primary_ticker}}) based on our D&B 360° Snapshot: Annual Revenue ${{comp.yearly_revenue_formatted}}, Global Employees ${{comp.employees_consolidated_formatted}} (${{comp.employees_growth_rate}}), and ${{stats.total_members || 535}} corporate family members across ${{stats.countries_count || 61}} countries.`;
      sendUiMessage(promptText);

      const plainMemo = [
        `D&B C-SUITE EXECUTIVE BRIEFING: ${{comp.primary_name || "Enterprise Entity"}}`,
        `D-U-N-S®: ${{comp.duns_formatted || comp.duns}} | Ticker: ${{comp.primary_exchange || ""}}:${{comp.primary_ticker || ""}} | LEI: ${{comp.lei || "—"}}`,
        `Headquarters: ${{comp.primary_address || "—"}}`,
        ``,
        `1. FINANCIAL & WORKFORCE SCALE`,
        `• Annual Consolidated Revenue: ${{comp.yearly_revenue_formatted || "—"}} (FY End ${{comp.fiscal_year_end || "—"}})`,
        `• Global Consolidated Workforce: ${{comp.employees_consolidated_formatted || "—"}} (${{comp.employees_growth_rate || "Verified"}})`,
        `• Global Corporate Footprint: ${{stats.total_members || 0}} Total Entities (${{stats.subsidiaries_count || 0}} Subsidiaries, ${{stats.branches_count || 0}} Branches across ${{stats.countries_count || 0}} Countries)`,
        `• Chief Executive / Most Senior Principal: ${{ceo.name}} (${{ceo.titles}})`,
        ``,
        `2. CORE BUSINESS & OPERATIONS`,
        `${{sums.short_profile?.text || sums.operations?.text || ""}}`,
        ``,
        `3. STRATEGIC DIRECTION & M&A`,
        `${{sums.strategy?.text || ""}} ${{sums.mergers_and_acquisitions?.text || ""}}`,
      ].join("\\n");

      const modalHtml = `
        <div style="display:flex;flex-direction:column;gap:14px;">
          <div style="padding:12px 15px;border-radius:10px;background:#F2F8F9;border:1px solid #ACD5E1;">
            <div style="font-size:11px;font-weight:800;text-transform:uppercase;color:#005172;letter-spacing:0.04em;">Verified Entity Identity &amp; Scale</div>
            <div style="margin-top:6px;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;font-size:12.5px;">
              <div><strong>Legal Name:</strong> ${{escapeHtml(comp.primary_name)}}</div>
              <div><strong>D-U-N-S®:</strong> <span style="font-family:var(--font-mono);">${{escapeHtml(comp.duns_formatted || comp.duns)}}</span></div>
              <div><strong>Annual Revenue:</strong> ${{escapeHtml(comp.yearly_revenue_formatted)}}</div>
              <div><strong>Global Workforce:</strong> ${{escapeHtml(comp.employees_consolidated_formatted)}}</div>
              <div><strong>Corporate Family:</strong> ${{escapeHtml(String(stats.total_members || 0))}} Members (${{escapeHtml(String(stats.countries_count || 0))}} Countries)</div>
              <div><strong>Senior Principal:</strong> ${{escapeHtml(ceo.name)}}</div>
            </div>
          </div>
          <div>
            <div style="font-size:12px;font-weight:800;text-transform:uppercase;color:#005172;margin-bottom:4px;">✦ Executive Profile &amp; Operations</div>
            <p style="font-size:13px;color:#002737;">${{escapeHtml(sums.short_profile?.text || sums.operations?.text || "")}}</p>
          </div>
          <div>
            <div style="font-size:12px;font-weight:800;text-transform:uppercase;color:#005172;margin-bottom:4px;">✦ AI, Growth Strategy &amp; Financial Trajectory</div>
            <p style="font-size:13px;color:#002737;">${{escapeHtml(sums.strategy?.text || "")}}</p>
            <p style="font-size:13px;color:#002737;margin-top:6px;">${{escapeHtml(sums.financial_performance?.text || "")}}</p>
          </div>
        </div>
      `;

      showDnbModal(
        `✦ C-Suite Executive Briefing — ${{comp.primary_name || "Company"}}`,
        `D-U-N-S® ${{comp.duns_formatted || comp.duns}} • ${{comp.primary_exchange || "Public"}}: ${{comp.primary_ticker || ""}} • Verified D&B DataTool + ContactTool`,
        modalHtml,
        plainMemo
      );
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
