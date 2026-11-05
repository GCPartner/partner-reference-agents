"""MCP App 3: D&B Corporate Family Tree & Upward Linkage Explorer (`ui://dnb/corporate-family-tree`).

Transforms D&B's 649-line / 535-node ASCII hierarchy (`OwnershipTool`) into an interactive,
filterable corporate tree with "Hide 196 Local Branches" enabled by default.
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

FAMILY_TREE_RESOURCE_URI = "ui://dnb/corporate-family-tree"

FAMILY_TREE_APP_TOOL_META: Dict[str, Any] = {
    "ui": {
        "resourceUri": FAMILY_TREE_RESOURCE_URI,
        "visibility": ["model", "app"],
    },
    "ui/resourceUri": FAMILY_TREE_RESOURCE_URI,
}

FAMILY_TREE_APP_RESOURCE_META: Dict[str, Any] = {
    "ui": {
        "prefersBorder": True,
        "csp": {
            "connectDomains": [DEFAULT_PUBLIC_API_BASE_URL, "https://plus.dnb.com", "*"],
            "resourceDomains": [DEFAULT_PUBLIC_API_BASE_URL, "*"],
            "frameDomains": [DEFAULT_PUBLIC_API_BASE_URL, "*"],
        },
    }
}

_LAST_FAMILY_TREE_PAYLOAD: Optional[Dict[str, Any]] = None


def set_cached_family_tree_payload(payload: Dict[str, Any]) -> None:
    global _LAST_FAMILY_TREE_PAYLOAD
    if isinstance(payload, dict):
        _LAST_FAMILY_TREE_PAYLOAD = payload


def get_cached_family_tree_payload() -> Optional[Dict[str, Any]]:
    return _LAST_FAMILY_TREE_PAYLOAD


def build_family_tree_html(
    initial_payload: Optional[Dict[str, Any]] = None,
    api_base_url: str = DEFAULT_PUBLIC_API_BASE_URL,
    include_suite_templates: bool = True,
) -> str:
    """Renders the self-contained `dnb.ai`-styled HTML for `ui://dnb/corporate-family-tree`."""
    effective_payload = (initial_payload or _LAST_FAMILY_TREE_PAYLOAD) if include_suite_templates else initial_payload
    serialized_payload = (
        json.dumps(effective_payload, ensure_ascii=False).replace("</", "<\\/")
        if effective_payload
        else "null"
    )
    shared_css = build_dnb_shared_css()
    bg_svg = build_dnb_network_canvas_svg()
    bridge_js = build_dnb_bridge_js(
        "D&B Corporate Family Tree Explorer",
        api_base_url=api_base_url,
        include_suite_templates=include_suite_templates,
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>D&amp;B Corporate Family Tree &amp; Upward Linkage Explorer</title>
  <style>
    {shared_css}

    .lineage-chain {{
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      padding: 12px 16px;
      border-radius: 12px;
      background: linear-gradient(90deg, #F2F8F9 0%, #E5EEF1 100%);
      border: 1.5px solid var(--primary-light-blue);
      margin-bottom: 16px;
    }}

    .lineage-step {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 6px 12px;
      border-radius: 9px;
      background: var(--white);
      border: 1px solid var(--primary-light-blue-40);
      font-size: 12.5px;
      font-weight: 700;
      color: var(--primary-dark-blue-3);
      cursor: pointer;
    }}

    .lineage-step.gu {{
      background: var(--primary-dark-blue-1);
      color: var(--white);
      border-color: var(--primary-dark-blue-3);
    }}

    .country-pills-bar {{
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
      margin-bottom: 12px;
    }}

    .country-pill {{
      padding: 5px 11px;
      border-radius: 999px;
      border: 1px solid var(--primary-light-blue-40);
      background: var(--primary-light-blue-10);
      color: var(--primary-dark-blue-1);
      font-family: var(--font-sans);
      font-size: 11.5px;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.14s ease;
    }}

    .country-pill.active {{
      background: var(--primary-dark-blue-1);
      color: var(--white);
      border-color: var(--primary-dark-blue-1);
    }}

    .tree-split-layout {{
      display: grid;
      grid-template-columns: 1.65fr 1fr;
      gap: 16px;
      align-items: start;
    }}

    @media (max-width: 860px) {{
      .tree-split-layout {{
        grid-template-columns: 1fr;
      }}
    }}

    .tree-scroll-box {{
      max-height: 460px;
      overflow-y: auto;
      padding: 10px;
      border-radius: 12px;
      background: var(--primary-light-blue-10);
      border: 1px solid var(--primary-light-blue-40);
    }}

    .tree-row {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      padding: 8px 11px;
      margin-bottom: 5px;
      border-radius: 9px;
      background: var(--white);
      border: 1px solid var(--border-gray);
      cursor: pointer;
      transition: all 0.12s ease;
    }}

    .tree-row:hover {{
      border-color: var(--primary-light-blue);
      background: #FAFCFD;
    }}

    .tree-row.selected {{
      border: 1.5px solid var(--primary-dark-blue-1);
      background: #E5EEF1;
      box-shadow: 0 3px 10px rgba(0, 81, 114, 0.12);
    }}

    .tree-row.gu-row {{
      background: linear-gradient(90deg, #002737 0%, #005172 100%);
      color: var(--white);
      border-color: var(--primary-light-blue);
    }}

    .tree-expand-btn {{
      width: 22px;
      height: 22px;
      border-radius: 6px;
      border: 1px solid var(--primary-light-blue-40);
      background: var(--primary-light-blue-10);
      color: var(--primary-dark-blue-1);
      font-size: 11px;
      font-weight: 800;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      flex-shrink: 0;
    }}

    .inspector-card {{
      padding: 18px;
      border-radius: 12px;
      background: linear-gradient(180deg, #F2F8F9 0%, #E5EEF1 100%);
      border: 1.5px solid var(--primary-light-blue);
      position: sticky;
      top: 12px;
    }}

    .toggle-switch-label {{
      display: inline-flex;
      align-items: center;
      gap: 7px;
      padding: 5px 12px;
      border-radius: 999px;
      background: var(--primary-light-blue-10);
      border: 1px solid var(--primary-light-blue);
      font-size: 12px;
      font-weight: 700;
      color: var(--primary-dark-blue-1);
      cursor: pointer;
      user-select: none;
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
          <span class="dnb-topbar-title">Corporate Family Tree &amp; Upward Linkage Explorer</span>
        </div>
        <div class="dnb-topbar-controls">
          <button id="backToMatcherTreeBtn" type="button" class="btn btn-ghost-light" title="Open Entity Matcher">← Entity Search</button>
          <input id="dunsTreeInput" class="dnb-input" type="text" placeholder="D-U-N-S or Company (e.g. 079942718, IBM)" value="079942718" style="width:190px;font-family:var(--font-mono);" />
          <select id="presetTreeSelect" class="dnb-select">
            <option value="079942718">Alphabet Inc. (07-994-2718)</option>
            <option value="060902413">Google LLC (06-090-2413)</option>
            <option value="001368083">IBM Corp. (00-136-8083)</option>
          </select>
          <button id="loadTreeBtn" type="button" class="btn btn-cyan">Load Family Tree</button>
        </div>
      </div>

      <!-- Main Body -->
      <div class="dnb-body">
        <!-- Upward Lineage Breadcrumb Banner -->
        <div class="lineage-chain" id="lineageChainContainer"></div>

        <!-- 3 KPI Tiles Row -->
        <div class="kpi-grid-3">
          <div class="kpi-card kpi-card-clickable" id="kpiCardTotalMembers" title="Click to open Global Ultimate 360° Snapshot">
            <span class="kpi-label">Total Corporate Family ↗</span>
            <span id="kpiTotalMembers" class="kpi-value">535 Members</span>
            <span id="kpiHqSub" class="kpi-sub">92 Regional &amp; Operating Headquarters (HQs)</span>
          </div>
          <div class="kpi-card kpi-card-clickable" id="kpiCardSubsidiaries" title="Click to toggle Local Branches visibility">
            <span class="kpi-label">Legal Subsidiaries vs. Branches ⇄</span>
            <span id="kpiSubsidiaries" class="kpi-value">339 Subsidiaries</span>
            <span id="kpiBranchesSub" class="kpi-sub">196 Local Branches (Hidden by Default to Reduce Noise)</span>
          </div>
          <div class="kpi-card kpi-card-clickable" id="kpiCardCountries" title="Click to show All Countries">
            <span class="kpi-label">Global Reach ⇣</span>
            <span id="kpiCountries" class="kpi-value">61 Countries</span>
            <span id="kpiDomesticUltSub" class="kpi-sub">227 Domestic Ultimate Parent Entities</span>
          </div>
        </div>

        <!-- Controls & Tree Section -->
        <div class="section-card">
          <div class="section-header">
            <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
              <input id="treeSearchInput" class="dnb-input" type="text" placeholder="Search entities by name, D-U-N-S, or country..." style="width:290px;height:32px;font-size:12.5px;" />
              <label class="toggle-switch-label">
                <input id="hideBranchesCheckbox" type="checkbox" checked style="accent-color:var(--primary-dark-blue-1);" />
                <span id="hideBranchesLabel">Hide 196 Local Branches (Subsidiaries Only)</span>
              </label>
            </div>
            <div style="display:flex;gap:6px;">
              <button id="expandAllBtn" type="button" class="btn btn-outline" style="height:30px;padding:0 10px;font-size:11.5px;">Expand All</button>
              <button id="collapseL1Btn" type="button" class="btn btn-outline" style="height:30px;padding:0 10px;font-size:11.5px;">Level 1 Only</button>
            </div>
          </div>

          <!-- Country Filter Pills -->
          <div id="countryPillsBar" class="country-pills-bar"></div>

          <!-- Split View: Hierarchy Tree (Left) + Selected Entity Inspector (Right) -->
          <div class="tree-split-layout">
            <div>
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;font-size:12px;color:var(--text-gray);font-weight:700;">
                <span id="visibleCountLabel">Showing 339 Legal Subsidiaries</span>
                <span>Click any node to inspect linkage &amp; actions</span>
              </div>
              <div id="treeListContainer" class="tree-scroll-box"></div>
            </div>

            <!-- Selected Node Inspector Drawer -->
            <div id="nodeInspectorCard" class="inspector-card"></div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="dnb-footer">
        <div>
          <span class="status-dot"></span>
          <span id="statusText">Synchronized with D&amp;B OwnershipTool (`hierarchyconnections_L1` &amp; `/v1/familyTree`)</span>
        </div>
        <div style="font-family:var(--font-mono);font-size:11px;">ui://dnb/corporate-family-tree</div>
      </div>
    </div>
  </div>

  <script>
  (function() {{
    const INITIAL_PAYLOAD = {serialized_payload};
    let currentPayload = null;
    let activeCountry = "ALL";
    let hideBranches = true;
    let expandedDuns = new Set(["079942718"]);
    let selectedNodeDuns = "079942718";

    {bridge_js}

    function renderLineageBanner() {{
      const gu = currentPayload?.global_ultimate || {{ name: "Alphabet Inc.", duns: "079942718", country: "US" }};
      const subj = currentPayload?.subject_company || {{ primary_name: "Alphabet Inc.", duns: "079942718" }};
      const nodesByDuns = new Map((currentPayload?.nodes || []).map((n) => [n.duns, n]));
      const selNode = nodesByDuns.get(selectedNodeDuns) || nodesByDuns.get(gu.duns) || (currentPayload?.nodes || [])[0] || {{
        name: subj.primary_name,
        duns: subj.duns,
        country: "US",
        roles_label: "Global Ultimate",
      }};

      // Trace path from Global Ultimate to currently selected node
      const path = [];
      let cur = selNode;
      const seen = new Set();
      while (cur && !seen.has(cur.duns)) {{
        seen.add(cur.duns);
        path.push(cur);
        cur = cur.parent_duns ? nodesByDuns.get(cur.parent_duns) : null;
      }}
      path.reverse();

      const stepsHtml = path.map((node, idx) => {{
        const isGu = idx === 0;
        const badgeTxt = isGu ? "GLOBAL ULTIMATE HQ" : (node.is_domestic_ultimate ? "DOMESTIC ULTIMATE" : (node.is_branch ? "BRANCH" : "SUBSIDIARY"));
        return `
          <div class="lineage-step ${{isGu ? "gu" : ""}}" data-focus-duns="${{escapeHtml(node.duns)}}">
            <span>${{isGu ? "🌐" : "🏢"}} ${{escapeHtml(node.name)}}</span>
            <span style="font-family:var(--font-mono);font-size:11px;opacity:0.85;">(${{escapeHtml(node.duns)}})</span>
            <span class="badge ${{isGu ? "badge-cyan" : "badge-teal"}}" style="font-size:10px;padding:1px 6px;">${{escapeHtml(badgeTxt)}}</span>
          </div>
        `;
      }}).join(`<span style="color:var(--primary-light-blue);font-weight:900;">➔</span>`);

      document.getElementById("lineageChainContainer").innerHTML = `
        <span style="font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:0.05em;color:var(--primary-dark-blue-1);">
          Upward Corporate Lineage:
        </span>
        ${{stepsHtml}}
      `;

      document.querySelectorAll("[data-focus-duns]").forEach((el) => {{
        el.onclick = () => {{
          selectedNodeDuns = el.getAttribute("data-focus-duns");
          renderLineageBanner();
          renderTree();
          renderInspector();
        }};
      }});
    }}

    function renderCountryPills() {{
      const dist = (currentPayload?.country_distribution || []).slice(0, 9);
      const totalCountries = currentPayload?.statistics?.countries_count || (currentPayload?.country_distribution || []).length;
      let html = `<button type="button" class="country-pill ${{activeCountry === "ALL" ? "active" : ""}}" data-country="ALL">All Countries (${{totalCountries}})</button>`;
      for (const c of dist) {{
        const countVal = hideBranches ? c.subsidiaries_count : c.total_count;
        if (countVal <= 0) continue;
        html += `<button type="button" class="country-pill ${{activeCountry === c.country ? "active" : ""}}" data-country="${{escapeHtml(c.country)}}">${{escapeHtml(c.country)}} (${{countVal}})</button>`;
      }}
      document.getElementById("countryPillsBar").innerHTML = html;
      document.querySelectorAll("#countryPillsBar .country-pill").forEach((btn) => {{
        btn.onclick = () => {{
          activeCountry = btn.getAttribute("data-country");
          renderCountryPills();
          renderTree();
        }};
      }});
    }}

    function areAllAncestorsExpanded(node, nodesByDuns) {{
      let pDuns = node.parent_duns;
      const visited = new Set();
      while (pDuns && !visited.has(pDuns)) {{
        visited.add(pDuns);
        if (!expandedDuns.has(pDuns)) return false;
        const parentNode = nodesByDuns.get(pDuns);
        pDuns = parentNode ? parentNode.parent_duns : null;
      }}
      return true;
    }}

    function renderTree() {{
      const allNodes = currentPayload?.nodes || [];
      const nodesByDuns = new Map(allNodes.map((n) => [n.duns, n]));
      const query = (document.getElementById("treeSearchInput")?.value || "").trim().toLowerCase();
      const isFiltering = Boolean(query || activeCountry !== "ALL");

      const visibleNodes = allNodes.filter((n) => {{
        if (hideBranches && n.is_branch && !n.is_global_ultimate) return false;
        if (activeCountry !== "ALL" && n.country !== activeCountry && !n.is_global_ultimate) return false;
        if (query) {{
          const hay = `${{n.name}} ${{n.duns}} ${{n.country}} ${{n.roles_label}}`.toLowerCase();
          return hay.includes(query);
        }}
        if (n.depth === 0) return true;
        return areAllAncestorsExpanded(n, nodesByDuns);
      }});

      document.getElementById("visibleCountLabel").textContent =
        `Showing ${{visibleNodes.length}} ${{hideBranches ? "Legal Subsidiaries" : "Family Tree Entities"}}`;

      let html = "";
      for (const n of visibleNodes.slice(0, 220)) {{
        const indentPx = isFiltering ? Math.min(n.depth, 2) * 14 : n.depth * 20;
        const kidCount = hideBranches ? n.subsidiary_children_count : n.children_count;
        const isExpanded = expandedDuns.has(n.duns);
        const isSel = n.duns === selectedNodeDuns;

        const expandBtnHtml = kidCount > 0 && !isFiltering
          ? `<span class="tree-expand-btn" data-toggle-expand="${{escapeHtml(n.duns)}}">${{isExpanded ? "−" : "+"}}</span>`
          : `<span style="display:inline-block;width:22px;text-align:center;color:var(--primary-light-blue);">•</span>`;

        const roleBadge = n.is_global_ultimate
          ? `<span class="badge badge-cyan" style="font-size:10px;padding:2px 7px;">GLOBAL ULTIMATE HQ</span>`
          : n.is_hq
          ? `<span class="badge badge-teal" style="font-size:10px;padding:2px 7px;">HQ • ${{kidCount}} Subs</span>`
          : n.is_domestic_ultimate
          ? `<span class="badge badge-cyan" style="font-size:10px;padding:2px 7px;">DOMESTIC ULTIMATE</span>`
          : n.is_branch
          ? `<span class="badge badge-warning" style="font-size:10px;padding:2px 7px;">BRANCH</span>`
          : `<span class="badge badge-success" style="font-size:10px;padding:2px 7px;">SUBSIDIARY</span>`;

        html += `
          <div class="tree-row ${{n.is_global_ultimate ? "gu-row" : ""}} ${{isSel ? "selected" : ""}}" style="margin-left:${{indentPx}}px;" data-select-node="${{escapeHtml(n.duns)}}">
            <div style="display:flex;align-items:center;gap:8px;min-width:0;">
              ${{expandBtnHtml}}
              <div style="min-width:0;">
                <div style="font-size:13px;font-weight:800;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                  ${{escapeHtml(n.name)}}
                </div>
                <div style="font-size:11px;opacity:0.82;font-family:var(--font-mono);">
                  D-U-N-S ${{escapeHtml(n.duns_formatted || n.duns)}} • Country: ${{escapeHtml(n.country)}}
                </div>
              </div>
            </div>
            <div style="display:flex;align-items:center;gap:6px;flex-shrink:0;">
              ${{roleBadge}}
            </div>
          </div>
        `;
      }}

      document.getElementById("treeListContainer").innerHTML = html || `<div style="padding:14px;color:var(--text-gray);">No corporate family members match your filter.</div>`;

      document.querySelectorAll("[data-toggle-expand]").forEach((btn) => {{
        btn.onclick = (e) => {{
          e.stopPropagation();
          const d = btn.getAttribute("data-toggle-expand");
          if (expandedDuns.has(d)) expandedDuns.delete(d);
          else expandedDuns.add(d);
          renderTree();
        }};
      }});

      document.querySelectorAll("[data-select-node]").forEach((row) => {{
        row.onclick = () => {{
          selectedNodeDuns = row.getAttribute("data-select-node");
          renderLineageBanner();
          renderTree();
          renderInspector();
        }};
      }});
    }}

    function renderInspector() {{
      const allNodes = currentPayload?.nodes || [];
      const node = allNodes.find((n) => n.duns === selectedNodeDuns) || allNodes[0];
      if (!node) return;
      const directSubs = allNodes.filter((n) => n.parent_duns === node.duns && !n.is_branch);

      const directSubsListHtml = directSubs.length
        ? `<div style="margin-top:10px;max-height:135px;overflow-y:auto;display:flex;flex-direction:column;gap:5px;">
            ${{directSubs.slice(0, 8).map((s) => `
              <div style="padding:6px 9px;border-radius:7px;background:var(--white);border:1px solid var(--border-gray);font-size:11.5px;display:flex;justify-content:space-between;cursor:pointer;" data-jump-sub="${{escapeHtml(s.duns)}}">
                <span style="font-weight:700;color:var(--primary-dark-blue-3);">${{escapeHtml(s.name)}}</span>
                <span style="font-family:var(--font-mono);color:var(--primary-dark-blue-1);">${{escapeHtml(s.country)}} • ${{escapeHtml(s.duns)}}</span>
              </div>
            `).join("")}}
          </div>`
        : `<div style="margin-top:6px;font-size:12px;color:var(--text-gray);">Leaf operating entity (0 direct child subsidiaries).</div>`;

      document.getElementById("nodeInspectorCard").innerHTML = `
        <div style="font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:0.05em;color:var(--primary-dark-blue-1);margin-bottom:6px;">
          ✦ Selected Entity Linkage Inspector
        </div>
        <div style="font-size:18px;font-weight:800;color:var(--primary-dark-blue-3);line-height:1.25;">
          ${{escapeHtml(node.name)}}
        </div>
        <div style="margin-top:8px;display:flex;gap:6px;flex-wrap:wrap;">
          <span class="duns-pill" id="inspCopyDuns">D-U-N-S® ${{escapeHtml(node.duns_formatted || node.duns)}} 📋</span>
          <span class="badge badge-cyan">Country: ${{escapeHtml(node.country)}}</span>
          <span class="badge badge-teal">Hierarchy Level ${{node.depth}}</span>
        </div>

        <div style="margin-top:14px;padding:12px;border-radius:10px;background:var(--white);border:1px solid var(--primary-light-blue-40);font-size:12.5px;line-height:1.55;">
          <div><strong>Family Tree Roles:</strong> ${{escapeHtml(node.roles_label)}}</div>
          <div style="margin-top:4px;"><strong>Immediate Parent:</strong> ${{escapeHtml(node.parent_name || "Top of Global Corporate Hierarchy")}} ${{node.parent_duns ? `(${{escapeHtml(node.parent_duns)}})` : ""}}</div>
          <div style="margin-top:4px;"><strong>Direct Subordinates:</strong> ${{node.subsidiary_children_count}} Subsidiaries • ${{node.branch_children_count}} Branches</div>
        </div>

        <div style="margin-top:12px;">
          <div style="font-size:11.5px;font-weight:800;text-transform:uppercase;color:var(--primary-dark-blue-2);">
            Direct Child Subsidiaries (${{directSubs.length}})
          </div>
          ${{directSubsListHtml}}
        </div>

        <div style="margin-top:14px;display:flex;flex-direction:column;gap:8px;">
          <button type="button" class="btn btn-primary" id="inspOpen360Btn" style="width:100%;">
            Open 360° Executive Snapshot for ${{escapeHtml(node.duns)}} →
          </button>
          <button type="button" class="btn btn-outline" id="inspOpenRiskBtn" style="width:100%;">
            Run Supplier Risk &amp; Credit Scorecard
          </button>
        </div>
      `;

      document.getElementById("inspCopyDuns").onclick = (e) => copyDunsToClipboard(node.duns, e.currentTarget);
      document.getElementById("inspOpen360Btn").onclick = (e) => {{
        switchToMcpApp(
          "open_company_360_app",
          {{ duns: node.duns }},
          `/apps/raw/company-360?duns=${{encodeURIComponent(node.duns)}}`,
          e.currentTarget
        );
      }};
      document.getElementById("inspOpenRiskBtn").onclick = (e) => {{
        switchToMcpApp(
          "open_supplier_risk_scorecard_app",
          {{ duns: node.duns }},
          `/apps/raw/supplier-risk?duns=${{encodeURIComponent(node.duns)}}`,
          e.currentTarget
        );
      }};
      document.querySelectorAll("[data-jump-sub]").forEach((el) => {{
        el.onclick = () => {{
          const childDuns = el.getAttribute("data-jump-sub");
          expandedDuns.add(node.duns);
          selectedNodeDuns = childDuns;
          renderLineageBanner();
          renderTree();
          renderInspector();
        }};
      }});
    }}

    function hydratePayload(payload) {{
      if (!payload || typeof payload !== "object") return;
      registerPayloadInSuiteBundle(payload);
      currentPayload = payload;
      const stats = payload.statistics || {{}};
      const gu = payload.global_ultimate || {{ duns: "079942718", name: "Alphabet Inc." }};
      const curDuns = payload.duns || gu.duns || "079942718";
      selectedNodeDuns = curDuns;
      expandedDuns = new Set([gu.duns || "079942718", curDuns]);

      // Also expand ancestors of selectedNodeDuns
      for (const item of payload.upward_lineage || []) {{
        if (item.duns) expandedDuns.add(item.duns);
      }}
      const nodesByDuns = new Map((payload.nodes || []).map((n) => [n.duns, n]));
      let curNode = nodesByDuns.get(curDuns);
      const seen = new Set();
      while (curNode && curNode.parent_duns && !seen.has(curNode.parent_duns)) {{
        seen.add(curNode.parent_duns);
        expandedDuns.add(curNode.parent_duns);
        curNode = nodesByDuns.get(curNode.parent_duns);
      }}

      document.getElementById("dunsTreeInput").value = curDuns;
      const presetSel = document.getElementById("presetTreeSelect");
      if (presetSel) {{
        let hasOpt = Array.from(presetSel.options).some((o) => o.value === curDuns);
        if (!hasOpt && payload.subject_company?.primary_name) {{
          const opt = document.createElement("option");
          opt.value = curDuns;
          opt.textContent = `${{payload.subject_company.primary_name}} (${{curDuns}})`;
          presetSel.appendChild(opt);
        }}
        presetSel.value = curDuns;
      }}

      document.getElementById("kpiTotalMembers").textContent = `${{(stats.total_members || 535).toLocaleString()}} Members`;
      document.getElementById("kpiHqSub").textContent = `${{stats.hq_count || 92}} Regional & Operating Headquarters (HQs)`;
      document.getElementById("kpiSubsidiaries").textContent = `${{(stats.subsidiaries_count || 339).toLocaleString()}} Subsidiaries`;
      document.getElementById("kpiBranchesSub").textContent = `${{(stats.branches_count || 196).toLocaleString()}} Local Branches (Hidden by Default to Reduce Noise)`;
      document.getElementById("kpiCountries").textContent = `${{stats.countries_count || 61}} Countries`;
      document.getElementById("kpiDomesticUltSub").textContent = `${{stats.domestic_ultimates_count || 227}} Domestic Ultimate Parent Entities`;
      document.getElementById("hideBranchesLabel").textContent =
        `Hide ${{(stats.branches_count || 196).toLocaleString()}} Local Branches (Subsidiaries Only)`;

      renderLineageBanner();
      renderCountryPills();
      renderTree();
      renderInspector();

      if (payload.data_source) {{
        const statusEl = document.getElementById("statusText");
        if (statusEl) statusEl.textContent = `Source: ${{payload.data_source}} • Loaded ${{(payload.nodes || []).length}} hierarchy nodes under ${{gu.name || curDuns}}`;
      }}
    }}

    document.getElementById("hideBranchesCheckbox").addEventListener("change", (e) => {{
      hideBranches = e.target.checked;
      renderCountryPills();
      renderTree();
    }});

    document.getElementById("kpiCardTotalMembers").addEventListener("click", () => {{
      const guDuns = currentPayload?.global_ultimate?.duns || selectedNodeDuns || "079942718";
      switchToMcpApp("open_company_360_app", {{ duns: guDuns }}, `/apps/raw/company-360?duns=${{encodeURIComponent(guDuns)}}`);
    }});

    document.getElementById("kpiCardSubsidiaries").addEventListener("click", () => {{
      const cb = document.getElementById("hideBranchesCheckbox");
      cb.checked = !cb.checked;
      hideBranches = cb.checked;
      renderCountryPills();
      renderTree();
    }});

    document.getElementById("kpiCardCountries").addEventListener("click", () => {{
      activeCountry = "ALL";
      renderCountryPills();
      renderTree();
      document.getElementById("countryPillsBar")?.scrollIntoView({{ behavior: "smooth", block: "center" }});
    }});

    document.getElementById("backToMatcherTreeBtn").addEventListener("click", (e) => {{
      const qName = currentPayload?.subject_company?.primary_name || currentPayload?.global_ultimate?.name || "Google";
      switchToMcpApp("open_entity_matcher_app", {{ name: qName, country_code: "US" }}, `/apps/raw/entity-matcher?name=${{encodeURIComponent(qName)}}&country=US`, e.currentTarget);
    }});

    document.getElementById("presetTreeSelect").addEventListener("change", (e) => {{
      document.getElementById("dunsTreeInput").value = e.target.value;
      document.getElementById("loadTreeBtn").click();
    }});

    document.getElementById("treeSearchInput").addEventListener("input", () => {{
      renderTree();
    }});

    document.getElementById("expandAllBtn").addEventListener("click", () => {{
      for (const n of currentPayload?.nodes || []) {{
        if (n.children_count > 0) expandedDuns.add(n.duns);
      }}
      renderTree();
    }});

    document.getElementById("collapseL1Btn").addEventListener("click", () => {{
      const guDuns = currentPayload?.global_ultimate?.duns || (currentPayload?.nodes && currentPayload.nodes[0]?.duns) || "079942718";
      expandedDuns = new Set([guDuns]);
      renderTree();
    }});

    document.getElementById("loadTreeBtn").addEventListener("click", async () => {{
      const btn = document.getElementById("loadTreeBtn");
      const duns = document.getElementById("dunsTreeInput").value.trim() || "079942718";
      const origTxt = btn.innerHTML;
      btn.disabled = true;
      btn.classList.add("is-loading");
      btn.textContent = "⏳ Loading...";
      try {{
        const data = await callMcpToolWithFallback("open_corporate_family_tree_app", {{ duns }});
        if (data) {{
          hydratePayload(data);
          const resolvedDuns = data.duns || duns;
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
              window.history.replaceState({{}}, "", `/apps/raw/family-tree?duns=${{encodeURIComponent(resolvedDuns)}}`);
            }} catch (_) {{}}
          }}
        }}
      }} finally {{
        btn.disabled = false;
        btn.classList.remove("is-loading");
        btn.innerHTML = origTxt;
      }}
    }});

    document.getElementById("dunsTreeInput").addEventListener("keydown", (e) => {{
      if (e.key === "Enter") {{
        e.preventDefault();
        document.getElementById("loadTreeBtn").click();
      }}
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
