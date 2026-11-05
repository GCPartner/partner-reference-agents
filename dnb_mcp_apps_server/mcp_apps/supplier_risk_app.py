"""MCP App 4: D&B Supplier Risk, Credit & Procurement Scorecard (`ui://dnb/supplier-risk-scorecard`).

Consolidates `RiskTool`, `PaymentTool`, `BusinessEventsTool`, `ESGTool`, and `DiversityTool`
plus `DataTool` government/procurement registrations (LEI, CAGE, GSA UEI) into a clean,
traffic-light vendor onboarding scorecard.
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

SUPPLIER_RISK_RESOURCE_URI = "ui://dnb/supplier-risk-scorecard"

SUPPLIER_RISK_APP_TOOL_META: Dict[str, Any] = {
    "ui": {
        "resourceUri": SUPPLIER_RISK_RESOURCE_URI,
        "visibility": ["model", "app"],
    },
    "ui/resourceUri": SUPPLIER_RISK_RESOURCE_URI,
}

SUPPLIER_RISK_APP_RESOURCE_META: Dict[str, Any] = {
    "ui": {
        "prefersBorder": True,
        "csp": {
            "connectDomains": [DEFAULT_PUBLIC_API_BASE_URL, "https://plus.dnb.com", "*"],
            "resourceDomains": [DEFAULT_PUBLIC_API_BASE_URL, "*"],
            "frameDomains": [DEFAULT_PUBLIC_API_BASE_URL, "*"],
        },
    }
}

_LAST_SUPPLIER_RISK_PAYLOAD: Optional[Dict[str, Any]] = None


def set_cached_supplier_risk_payload(payload: Dict[str, Any]) -> None:
    global _LAST_SUPPLIER_RISK_PAYLOAD
    if isinstance(payload, dict):
        _LAST_SUPPLIER_RISK_PAYLOAD = payload


def get_cached_supplier_risk_payload() -> Optional[Dict[str, Any]]:
    return _LAST_SUPPLIER_RISK_PAYLOAD


def build_supplier_risk_html(
    initial_payload: Optional[Dict[str, Any]] = None,
    api_base_url: str = DEFAULT_PUBLIC_API_BASE_URL,
    include_suite_templates: bool = True,
) -> str:
    """Renders the self-contained `dnb.ai`-styled HTML for `ui://dnb/supplier-risk-scorecard`."""
    effective_payload = (initial_payload or _LAST_SUPPLIER_RISK_PAYLOAD) if include_suite_templates else initial_payload
    serialized_payload = (
        json.dumps(effective_payload, ensure_ascii=False).replace("</", "<\\/")
        if effective_payload
        else "null"
    )
    shared_css = build_dnb_shared_css()
    bg_svg = build_dnb_network_canvas_svg()
    bridge_js = build_dnb_bridge_js(
        "D&B Supplier Risk & Procurement Scorecard",
        api_base_url=api_base_url,
        include_suite_templates=include_suite_templates,
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>D&amp;B Supplier Risk, Credit &amp; Procurement Scorecard</title>
  <style>
    {shared_css}

    .gauge-card {{
      padding: 16px 18px;
      border-radius: 12px;
      background: var(--primary-light-blue-10);
      border: 1px solid var(--primary-light-blue-40);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 10px;
    }}

    .gauge-top {{
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 8px;
    }}

    .gauge-score {{
      font-size: 28px;
      font-weight: 800;
      color: var(--primary-dark-blue-3);
      letter-spacing: -0.02em;
      font-variant-numeric: tabular-nums;
    }}

    .gauge-track {{
      position: relative;
      height: 10px;
      border-radius: 999px;
      background: var(--primary-blue-10);
      overflow: hidden;
      border: 1px solid rgba(48, 149, 180, 0.35);
    }}

    .gauge-fill {{
      height: 100%;
      border-radius: 999px;
      background: linear-gradient(90deg, #3095B4 0%, #00B2A9 55%, #046A38 100%);
      transition: width 0.35s ease;
    }}

    .risk-split-grid {{
      display: grid;
      grid-template-columns: 1.35fr 1fr;
      gap: 16px;
    }}

    @media (max-width: 820px) {{
      .risk-split-grid {{
        grid-template-columns: 1fr;
      }}
    }}

    .checklist-row {{
      padding: 12px 14px;
      border-radius: 10px;
      background: var(--primary-light-blue-10);
      border: 1px solid var(--primary-light-blue-40);
      margin-bottom: 9px;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }}

    .checklist-head {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      flex-wrap: wrap;
    }}

    .checklist-title {{
      font-size: 13px;
      font-weight: 800;
      color: var(--primary-dark-blue-3);
    }}

    .checklist-detail {{
      font-size: 12px;
      color: var(--primary-dark-blue-2);
      line-height: 1.45;
    }}

    .proc-id-row {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      padding: 9px 12px;
      border-radius: 9px;
      background: var(--white);
      border: 1px solid var(--border-gray);
      margin-bottom: 7px;
      font-size: 12.5px;
    }}

    .proc-id-label {{
      font-weight: 700;
      color: var(--text-gray);
      font-size: 11.5px;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }}

    .proc-id-val {{
      font-family: var(--font-mono);
      font-weight: 700;
      color: var(--primary-dark-blue-1);
      cursor: pointer;
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
          <span class="dnb-topbar-title">Supplier Risk, Credit &amp; Procurement Scorecard</span>
        </div>
        <div class="dnb-topbar-controls">
          <button id="backToMatcherRiskBtn" type="button" class="btn btn-ghost-light" title="Open Entity Matcher">← Entity Search</button>
          <input id="dunsRiskInput" class="dnb-input" type="text" placeholder="D-U-N-S or Company (e.g. 079942718, IBM)" value="079942718" style="width:190px;font-family:var(--font-mono);" />
          <select id="presetRiskSelect" class="dnb-select">
            <option value="079942718">Alphabet Inc. (07-994-2718)</option>
            <option value="060902413">Google LLC (06-090-2413)</option>
            <option value="001368083">IBM Corp. (00-136-8083)</option>
          </select>
          <button id="loadRiskBtn" type="button" class="btn btn-cyan">Run Risk Scorecard</button>
        </div>
      </div>

      <!-- Main Body -->
      <div class="dnb-body">
        <!-- Hero Banner -->
        <div class="dnb-hero-banner">
          <div>
            <div class="dnb-entity-title">
              <span id="riskCompanyName">Alphabet Inc.</span>
              <span id="riskDunsPill" class="duns-pill">D-U-N-S® 07-994-2718 📋</span>
              <span id="overallRiskBadge" class="badge badge-success" style="font-size:12.5px;padding:5px 12px;">✓ LOW RISK • APPROVED VENDOR</span>
              <span id="viabilityBadge" class="badge badge-teal">D&amp;B Viability Rating: 1A1</span>
            </div>
            <div class="dnb-subtitle-row">
              <span id="riskSubtitle">📍 1600 Amphitheatre Pkwy, Mountain View, CA • Annual Revenue: $402.8B • Recommended Credit Guideline: $25.0M</span>
            </div>
          </div>
          <div style="display:flex;gap:8px;flex-wrap:wrap;">
            <button id="switch360Btn" type="button" class="btn btn-outline">360° Company Snapshot</button>
            <button id="switchTreeBtn" type="button" class="btn btn-outline">Explore Family Tree</button>
            <button id="approveMemoBtn" type="button" class="btn btn-primary">✦ Generate Vendor Approval Memo</button>
          </div>
        </div>

        <!-- 3 Horizontal Risk Gauges Row -->
        <div class="kpi-grid-3">
          <!-- Gauge 1: Financial Stability / Failure Risk Percentile -->
          <div class="gauge-card">
            <div>
              <div class="kpi-label">Financial Stability Percentile</div>
              <div class="gauge-top" style="margin-top:4px;">
                <span id="failureScoreVal" class="gauge-score">94<span style="font-size:15px;color:var(--text-gray);"> / 100</span></span>
                <span id="failureTierBadge" class="badge badge-success">Class 1 • Minimal Risk</span>
              </div>
            </div>
            <div class="gauge-track">
              <div id="failureBarFill" class="gauge-fill" style="width: 94%;"></div>
            </div>
            <div id="failureDesc" class="kpi-sub">0.04% 12-Mo Default Incidence (vs. 1.15% Industry Avg)</div>
          </div>

          <!-- Gauge 2: Commercial Delinquency Risk -->
          <div class="gauge-card">
            <div>
              <div class="kpi-label">Delinquency Credit Score</div>
              <div class="gauge-top" style="margin-top:4px;">
                <span id="delinqScoreVal" class="gauge-score">91<span style="font-size:15px;color:var(--text-gray);"> / 100</span></span>
                <span id="delinqTierBadge" class="badge badge-success">Class 1 • Very Low</span>
              </div>
            </div>
            <div class="gauge-track">
              <div id="delinqBarFill" class="gauge-fill" style="width: 91%;"></div>
            </div>
            <div id="delinqDesc" class="kpi-sub">Strong liquidity &amp; $402.8B revenue scale support prompt settlement</div>
          </div>

          <!-- Gauge 3: D&B PAYDEX Score -->
          <div class="gauge-card">
            <div>
              <div class="kpi-label">D&amp;B PAYDEX® Trade Payment Score</div>
              <div class="gauge-top" style="margin-top:4px;">
                <span id="paydexScoreVal" class="gauge-score">84<span style="font-size:15px;color:var(--text-gray);"> / 100</span></span>
                <span id="paydexTierBadge" class="badge badge-teal">Prompt (Ahead of Terms)</span>
              </div>
            </div>
            <div class="gauge-track">
              <div id="paydexBarFill" class="gauge-fill" style="width: 84%;"></div>
            </div>
            <div id="paydexDesc" class="kpi-sub">Pays 4 Days Ahead of 30-Day Invoice Terms (Benchmark Prompt = 80)</div>
          </div>
        </div>

        <!-- 2-Column Split: Traffic-Light Compliance Checklist (Left) + Procurement Identifiers (Right) -->
        <div class="risk-split-grid">
          <div class="section-card" style="margin-bottom:0;">
            <div class="section-header">
              <div class="section-title">
                <span>🛡️ KYB Compliance, Legal Events &amp; Watchlist Screening</span>
              </div>
            </div>
            <div id="complianceChecklistContainer"></div>
          </div>

          <div class="section-card" style="margin-bottom:0;background:var(--primary-light-blue-10);border-color:var(--primary-light-blue-40);">
            <div class="section-header">
              <div class="section-title">
                <span>📋 ERP &amp; Procurement Registration Keys</span>
              </div>
              <span class="badge badge-cyan" style="font-size:10.5px;">Click value to copy</span>
            </div>
            <div id="procurementIdsContainer"></div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="dnb-footer">
        <div>
          <span class="status-dot"></span>
          <span id="statusText">D&amp;B Supplier Risk &amp; Procurement Verification Ready</span>
        </div>
        <div style="font-family:var(--font-mono);font-size:11px;">ui://dnb/supplier-risk-scorecard</div>
      </div>
    </div>
  </div>

  <script>
  (function() {{
    const INITIAL_PAYLOAD = {serialized_payload};
    let currentPayload = null;

    {bridge_js}

    function hydratePayload(payload) {{
      if (!payload || typeof payload !== "object") return;
      registerPayloadInSuiteBundle(payload);
      currentPayload = payload;
      const comp = payload.company || {{}};
      const rg = payload.risk_gauges || {{}};
      const fr = rg.failure_risk || {{}};
      const dr = rg.delinquency_risk || {{}};
      const px = rg.paydex || {{}};
      const proc = payload.procurement_identifiers || {{}};

      const curDuns = comp.duns || payload.duns || "079942718";
      document.getElementById("dunsRiskInput").value = curDuns;
      const presetSel = document.getElementById("presetRiskSelect");
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

      document.getElementById("riskCompanyName").textContent = comp.primary_name || "Alphabet Inc.";
      const dunsPill = document.getElementById("riskDunsPill");
      dunsPill.textContent = `D-U-N-S® ${{comp.duns_formatted || curDuns}} 📋`;
      dunsPill.onclick = () => copyDunsToClipboard(curDuns, dunsPill);

      document.getElementById("overallRiskBadge").textContent = `✓ ${{rg.overall_risk_badge || "LOW RISK"}} • APPROVED VENDOR`;
      document.getElementById("viabilityBadge").textContent = `D&B Viability Rating: ${{rg.viability_rating || "1A1"}}`;
      document.getElementById("riskSubtitle").textContent =
        `📍 ${{comp.primary_address || "Mountain View, CA"}} • Revenue: ${{comp.yearly_revenue_formatted || "$402.8B"}} • Recommended Credit Limit: ${{rg.recommended_credit_limit_formatted || "$25.0M"}}`;

      // Gauges
      const fScore = Number(fr.percentile || 94);
      document.getElementById("failureScoreVal").innerHTML = `${{fScore}}<span style="font-size:15px;color:var(--text-gray);"> / 100</span>`;
      document.getElementById("failureBarFill").style.width = `${{Math.min(100, Math.max(10, fScore))}}%`;
      document.getElementById("failureDesc").textContent = fr.description || "Minimal likelihood of financial stress.";

      const dScore = Number(dr.score || 91);
      document.getElementById("delinqScoreVal").innerHTML = `${{dScore}}<span style="font-size:15px;color:var(--text-gray);"> / 100</span>`;
      document.getElementById("delinqBarFill").style.width = `${{Math.min(100, Math.max(10, dScore))}}%`;
      document.getElementById("delinqDesc").textContent = dr.description || "Low probability of severe commercial delinquency.";

      const pScore = Number(px.score || 84);
      document.getElementById("paydexScoreVal").innerHTML = `${{pScore}}<span style="font-size:15px;color:var(--text-gray);"> / 100</span>`;
      document.getElementById("paydexBarFill").style.width = `${{Math.min(100, Math.max(10, pScore))}}%`;
      document.getElementById("paydexDesc").textContent = px.payment_behavior || "Pays 4 Days Ahead of 30-Day Invoice Terms";

      // Checklist
      const checks = payload.compliance_checklist || [];
      document.getElementById("complianceChecklistContainer").innerHTML = checks.map((c) => {{
        const bClass = c.badge_tone === "warning" ? "badge-warning" : (c.badge_tone === "danger" ? "badge-danger" : "badge-success");
        const icon = c.badge_tone === "warning" ? "⚠️" : "✓";
        return `
          <div class="checklist-row">
            <div class="checklist-head">
              <span class="checklist-title">${{escapeHtml(c.category)}}</span>
              <span class="badge ${{bClass}}">${{icon}} ${{escapeHtml(c.status)}}</span>
            </div>
            <div class="checklist-detail">${{escapeHtml(c.detail)}}</div>
          </div>
        `;
      }}).join("");

      // Procurement IDs
      const idItems = [
        {{ label: "D-U-N-S® Number", val: proc.duns_formatted || curDuns }},
        {{ label: "Legal Entity Identifier (LEI)", val: proc.lei || "—" }},
        {{ label: "US DoD CAGE Code", val: proc.cage_code || "—" }},
        {{ label: "GSA SAM.gov UEI", val: proc.gsa_uei || "—" }},
        {{ label: "Corporate Registry #", val: proc.state_reg_number || "—" }},
        {{ label: "Primary US SIC", val: proc.sic_code || "—" }},
        {{ label: "Primary NAICS", val: proc.naics_code || "—" }},
      ];
      document.getElementById("procurementIdsContainer").innerHTML = idItems.map((it) => `
        <div class="proc-id-row">
          <span class="proc-id-label">${{escapeHtml(it.label)}}</span>
          <span class="proc-id-val" data-copy-id="${{escapeHtml(it.val)}}" title="Click to copy">${{escapeHtml(it.val)}} 📋</span>
        </div>
      `).join("");

      document.querySelectorAll("[data-copy-id]").forEach((el) => {{
        el.onclick = () => copyDunsToClipboard(el.getAttribute("data-copy-id"), el);
      }});

      if (payload.entitlement_mode) {{
        document.getElementById("statusText").textContent = `Source: ${{payload.entitlement_mode}}`;
      }}
    }}

    document.getElementById("backToMatcherRiskBtn").addEventListener("click", (e) => {{
      const comp = currentPayload?.company || {{}};
      const qName = comp.primary_name || "Google";
      switchToMcpApp("open_entity_matcher_app", {{ name: qName, country_code: "US" }}, `/apps/raw/entity-matcher?name=${{encodeURIComponent(qName)}}&country=US`, e.currentTarget);
    }});

    document.getElementById("presetRiskSelect").addEventListener("change", (e) => {{
      document.getElementById("dunsRiskInput").value = e.target.value;
      document.getElementById("loadRiskBtn").click();
    }});

    document.getElementById("loadRiskBtn").addEventListener("click", async () => {{
      const btn = document.getElementById("loadRiskBtn");
      const duns = document.getElementById("dunsRiskInput").value.trim() || "079942718";
      const origTxt = btn.innerHTML;
      btn.disabled = true;
      btn.classList.add("is-loading");
      btn.textContent = "⏳ Loading...";
      try {{
        const data = await callMcpToolWithFallback("open_supplier_risk_scorecard_app", {{ duns }});
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
              window.history.replaceState({{}}, "", `/apps/raw/supplier-risk?duns=${{encodeURIComponent(resolvedDuns)}}`);
            }} catch (_) {{}}
          }}
        }}
      }} finally {{
        btn.disabled = false;
        btn.classList.remove("is-loading");
        btn.innerHTML = origTxt;
      }}
    }});

    document.getElementById("dunsRiskInput").addEventListener("keydown", (e) => {{
      if (e.key === "Enter") {{
        e.preventDefault();
        document.getElementById("loadRiskBtn").click();
      }}
    }});

    document.getElementById("switch360Btn").addEventListener("click", (e) => {{
      const comp = currentPayload?.company || {{}};
      const duns = comp.duns || document.getElementById("dunsRiskInput").value.trim() || "079942718";
      switchToMcpApp(
        "open_company_360_app",
        {{ duns }},
        `/apps/raw/company-360?duns=${{encodeURIComponent(duns)}}`,
        e.currentTarget
      );
    }});

    document.getElementById("switchTreeBtn").addEventListener("click", (e) => {{
      const comp = currentPayload?.company || {{}};
      const duns = comp.duns || document.getElementById("dunsRiskInput").value.trim() || "079942718";
      switchToMcpApp(
        "open_corporate_family_tree_app",
        {{ duns }},
        `/apps/raw/family-tree?duns=${{encodeURIComponent(duns)}}`,
        e.currentTarget
      );
    }});

    document.getElementById("approveMemoBtn").addEventListener("click", () => {{
      const comp = currentPayload?.company || {{}};
      const rg = currentPayload?.risk_gauges || {{}};
      const proc = currentPayload?.procurement_identifiers || {{}};
      const checks = currentPayload?.compliance_checklist || [];

      const promptText = `Please draft a formal Procurement & Vendor Risk Onboarding Approval Memo for ${{comp.primary_name}} (D-U-N-S ${{comp.duns_formatted || comp.duns}}, LEI ${{proc.lei}}, CAGE ${{proc.cage_code}}, GSA UEI ${{proc.gsa_uei}}) citing its D&B Viability Rating (${{rg.viability_rating}}), Financial Stability Percentile (${{rg.failure_risk?.percentile}}/100), Delinquency Score (${{rg.delinquency_risk?.score}}/100), PAYDEX (${{rg.paydex?.score}}/100), and Recommended Credit Limit (${{rg.recommended_credit_limit_formatted}}).`;
      sendUiMessage(promptText);

      const plainMemo = [
        `PROCUREMENT & THIRD-PARTY RISK ONBOARDING APPROVAL MEMO`,
        `Vendor Legal Name: ${{comp.primary_name || "Enterprise Vendor"}}`,
        `Decision Status: APPROVED (${{rg.overall_risk_badge || "LOW RISK"}} • D&B Viability Rating ${{rg.viability_rating || "1A1"}})`,
        `Recommended Commercial Credit Guideline: ${{rg.recommended_credit_limit_formatted || "$25.0M"}}`,
        ``,
        `1. ERP & GOVERNMENT REGISTRATION IDENTIFIERS`,
        `• D-U-N-S® Number: ${{proc.duns_formatted || comp.duns}}`,
        `• Legal Entity Identifier (LEI): ${{proc.lei || "—"}}`,
        `• US DoD CAGE Code: ${{proc.cage_code || "—"}}`,
        `• GSA SAM.gov UEI: ${{proc.gsa_uei || "—"}}`,
        `• Primary SIC / NAICS: ${{proc.sic_code || "—"}} | ${{proc.naics_code || "—"}}`,
        ``,
        `2. D&B CREDIT & RISK SCORECARD`,
        `• Financial Stability Percentile: ${{rg.failure_risk?.percentile || 94}} / 100 (${{rg.failure_risk?.tier || "Class 1 • Minimal Risk"}})`,
        `• Commercial Delinquency Score: ${{rg.delinquency_risk?.score || 91}} / 100 (${{rg.delinquency_risk?.tier || "Class 1 • Very Low"}})`,
        `• D&B PAYDEX® Trade Score: ${{rg.paydex?.score || 84}} / 100 (${{rg.paydex?.payment_behavior || "Prompt"}})`,
        ``,
        `3. KYB COMPLIANCE & WATCHLIST SCREENING`,
        ...checks.map((c) => `• ${{c.category}}: ${{c.status}} — ${{c.detail}}`),
      ].join("\\n");

      const modalHtml = `
        <div style="display:flex;flex-direction:column;gap:14px;">
          <div style="padding:12px 15px;border-radius:10px;background:rgba(4,106,56,0.08);border:1.5px solid #74AA4E;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">
            <div>
              <div style="font-size:11px;font-weight:800;text-transform:uppercase;color:#046A38;letter-spacing:0.04em;">Onboarding Recommendation</div>
              <div style="font-size:15px;font-weight:800;color:#002737;margin-top:2px;">✓ APPROVED FOR ENTERPRISE PROCUREMENT (${{escapeHtml(rg.overall_risk_badge || "LOW RISK")}})</div>
            </div>
            <span class="badge badge-success" style="font-size:12px;padding:5px 12px;">Credit Limit: ${{escapeHtml(rg.recommended_credit_limit_formatted || "$25.0M")}}</span>
          </div>

          <div style="padding:12px 15px;border-radius:10px;background:#F2F8F9;border:1px solid #ACD5E1;">
            <div style="font-size:11px;font-weight:800;text-transform:uppercase;color:#005172;letter-spacing:0.04em;">ERP Master Data &amp; Regulatory Keys</div>
            <div style="margin-top:6px;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px;font-size:12.5px;">
              <div><strong>D-U-N-S®:</strong> <span style="font-family:var(--font-mono);">${{escapeHtml(proc.duns_formatted || comp.duns)}}</span></div>
              <div><strong>LEI:</strong> <span style="font-family:var(--font-mono);">${{escapeHtml(proc.lei || "—")}}</span></div>
              <div><strong>DoD CAGE:</strong> <span style="font-family:var(--font-mono);">${{escapeHtml(proc.cage_code || "—")}}</span></div>
              <div><strong>SAM.gov UEI:</strong> <span style="font-family:var(--font-mono);">${{escapeHtml(proc.gsa_uei || "—")}}</span></div>
              <div><strong>Viability Rating:</strong> ${{escapeHtml(rg.viability_rating || "1A1")}}</div>
              <div><strong>PAYDEX® Score:</strong> ${{escapeHtml(String(rg.paydex?.score || 84))}} / 100 (Prompt)</div>
            </div>
          </div>

          <div>
            <div style="font-size:11.5px;font-weight:800;text-transform:uppercase;color:#005172;margin-bottom:6px;">KYB &amp; Watchlist Attestation Summary</div>
            <div style="display:flex;flex-direction:column;gap:6px;">
              ${{checks.map((c) => `
                <div style="padding:8px 11px;border-radius:8px;background:#FFFFFF;border:1px solid #D6D6D6;font-size:12px;">
                  <strong>${{escapeHtml(c.category)}} — ${{escapeHtml(c.status)}}:</strong> ${{escapeHtml(c.detail)}}
                </div>
              `).join("")}}
            </div>
          </div>
        </div>
      `;

      showDnbModal(
        `✦ Vendor Risk Onboarding Approval Memo — ${{comp.primary_name || "Vendor"}}`,
        `D-U-N-S® ${{proc.duns_formatted || comp.duns}} • Viability ${{rg.viability_rating || "1A1"}} • Recommended Credit Limit ${{rg.recommended_credit_limit_formatted || "$25.0M"}}`,
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
