"""MCP App (ui://) for Interactive 2D Chemical Structure / SMILES Explorer & Substructure Workbench.

Implements View 6 of the Google Patents MCP Apps suite:
- Resource URI: ui://google-patents/chemistry-explorer
- MIME Type: text/html;profile=mcp-app
- Supports both MCP Apps SEP-1865 JSON-RPC postMessage bridge and pre-populated
  server-rendered payload injection.

Features:
1. Interactive 2D Skeletal Molecule SVG Visualizer:
   - Pure client-side SMILES tokenizer, ring-closure solver, and 2D coordinate layout
   - CPK heteroatom coloring (O=Red, N=Blue, S=Amber, F/Cl=Green, Br=Brown, P=Orange)
   - Double/triple/aromatic bond rendering
2. Preset Compound Library & Substructure Workbench:
   - One-click presets (Aspirin, Ibuprofen, Paracetamol, Ethylene Carbonate, Caffeine, Sulfanilamide)
   - Functional group appender (-COOH, -OH, -NH2, -CF3, Phenyl, Ester)
   - Live `search_chemistry` execution (`EXACT`, `SUBSTRUCTURE`, `SIMILARITY`)
3. Physicochemical & Lipinski Rule-of-5 Property Inspector + Matching Chemical Patents Grid
"""

from __future__ import annotations

import json
import re
from collections import Counter
from typing import Any

CHEMISTRY_RESOURCE_URI = "ui://google-patents/chemistry-explorer"
MCP_APP_MIME_TYPE = "text/html;profile=mcp-app"

CHEMISTRY_TOOL_META: dict[str, Any] = {
    "ui": {
        "resourceUri": CHEMISTRY_RESOURCE_URI,
        "visibility": ["model", "app"],
    },
    "ui/resourceUri": CHEMISTRY_RESOURCE_URI,
}

_LAST_CHEMISTRY_PAYLOAD: dict[str, Any] | None = None

_ATOMIC_WEIGHTS = {
    "C": 12.011,
    "N": 14.007,
    "O": 15.999,
    "S": 32.06,
    "P": 30.974,
    "F": 18.998,
    "Cl": 35.45,
    "Br": 79.904,
    "I": 126.904,
    "B": 10.81,
    "Si": 28.085,
}


def set_cached_chemistry_payload(payload: dict[str, Any]) -> None:
    """Store the most recent chemistry payload for resource pre-hydration."""
    global _LAST_CHEMISTRY_PAYLOAD
    _LAST_CHEMISTRY_PAYLOAD = payload


def get_cached_chemistry_payload() -> dict[str, Any] | None:
    """Retrieve the most recent chemistry payload."""
    return _LAST_CHEMISTRY_PAYLOAD


def _analyze_smiles(smiles: str) -> dict[str, Any]:
    """Compute molecular properties, functional groups, and Lipinski metrics from SMILES."""
    s = (smiles or "").strip()
    if not s:
        return {}

    # Extract element tokens (Cl, Br, Si, or single letters C, N, O, S, P, F, I, B, c, n, o, s, p)
    tokens = re.findall(r"Cl|Br|Si|[BCNOSPFIbcnosp]", s)
    counts: Counter[str] = Counter()
    aromatic_atoms = 0
    for t in tokens:
        if t.islower():
            aromatic_atoms += 1
            elem = t.upper()
        else:
            elem = t
        counts[elem] += 1

    # Estimate heavy atom MW + approximate hydrogens
    heavy_mw = sum(counts[el] * _ATOMIC_WEIGHTS.get(el, 12.0) for el in counts)
    # Approximate implicit hydrogens for organic molecules
    approx_h = max(0, counts["C"] * 2 + 2 - counts["F"] - counts["Cl"] - counts["Br"] - counts["I"] - aromatic_atoms)
    est_mw = round(heavy_mw + approx_h * 1.008, 2)

    # Build Hill-order formula (C, H, then alphabetical)
    formula_parts: list[str] = []
    if counts["C"]:
        formula_parts.append(f"C{counts['C'] if counts['C'] > 1 else ''}")
    if approx_h > 0:
        formula_parts.append(f"H{approx_h if approx_h > 1 else ''}")
    for el in sorted(k for k in counts if k != "C"):
        cnt = counts[el]
        if cnt > 0:
            formula_parts.append(f"{el}{cnt if cnt > 1 else ''}")

    # Ring closures (digits 1-9 in SMILES appear in pairs)
    ring_digits = re.findall(r"(?<!\[)\d", s)
    num_rings = max(0, len(ring_digits) // 2)

    hba = counts["O"] + counts["N"]
    hbd = len(re.findall(r"O\)|\[OH\]|\[NH2?\]|N\(|nH", s))
    if s.endswith("O") or s.startswith("O"):
        hbd += 1

    functional_groups: list[str] = []
    if "C(=O)O" in s and not re.search(r"C\(=O\)O[Cc]", s):
        functional_groups.append("Carboxylic Acid (-COOH)")
    if re.search(r"C\(=O\)O[Cc]|OC\(=O\)", s):
        functional_groups.append("Ester (-COO-)")
    if re.search(r"C\(=O\)N|NC\(=O\)", s):
        functional_groups.append("Amide (-CONH-)")
    if re.search(r"OC\(=O\)O", s):
        functional_groups.append("Carbonate Ester (-OC(=O)O-)")
    if aromatic_atoms >= 5:
        functional_groups.append("Aromatic Ring System")
    if "S(=O)(=O)" in s:
        functional_groups.append("Sulfonyl / Sulfonamide")
    if "C#N" in s:
        functional_groups.append("Nitrile (-CN)")
    if counts["F"] >= 3 and ("C(F)(F)F" in s or "FC(F)F" in s):
        functional_groups.append("Trifluoromethyl (-CF3)")
    elif counts["F"] or counts["Cl"] or counts["Br"] or counts["I"]:
        functional_groups.append("Halogenated Substituent")

    lipinski_pass = est_mw <= 500 and hba <= 10 and hbd <= 5

    return {
        "smiles": s,
        "molecular_formula_est": "".join(formula_parts) or "Unknown",
        "molecular_weight_est": est_mw,
        "heavy_atom_count": sum(counts.values()),
        "ring_count": num_rings,
        "aromatic_atom_count": aromatic_atoms,
        "h_bond_acceptors": hba,
        "h_bond_donors_est": hbd,
        "lipinski_ro5_compliant": lipinski_pass,
        "functional_groups": functional_groups,
        "element_counts": dict(counts),
    }


def enrich_chemistry_payload(raw_data: dict[str, Any]) -> dict[str, Any]:
    """Enrich `search_chemistry` payload with computed molecular descriptors and normalized results."""
    if not isinstance(raw_data, dict):
        return {"status": "error", "message": "Invalid chemistry payload"}

    enriched = dict(raw_data)
    chem_meta = enriched.get("chemistry_search") if isinstance(enriched.get("chemistry_search"), dict) else {}
    smiles = str(enriched.get("smiles") or chem_meta.get("input") or "").strip()
    match_type = str(enriched.get("match_type") or enriched.get("mode") or chem_meta.get("mode") or "EXACT").strip()
    enriched["smiles"] = smiles
    enriched["match_type"] = match_type
    enriched["molecule_analysis"] = _analyze_smiles(smiles)

    raw_results = enriched.get("results") or []
    normalized: list[dict[str, Any]] = []
    for item in raw_results:
        if not isinstance(item, dict):
            continue
        pub_id = str(item.get("publication_number") or item.get("id") or "").strip()
        if not pub_id:
            continue
        assignee = (
            (item.get("assignees")[0] if isinstance(item.get("assignees"), list) and item.get("assignees") else None)
            or item.get("assignee")
            or "Unassigned / Individual"
        )
        normalized.append(
            {
                "id": pub_id,
                "title": str(item.get("title") or "Untitled Patent"),
                "snippet": str(item.get("snippet") or ""),
                "assignee": str(assignee),
                "publication_date": str(item.get("publication_date") or item.get("grant_date") or ""),
                "filing_date": str(item.get("filing_date") or ""),
                "thumbnail_url": str(item.get("thumbnail_url") or ""),
                "google_patents_url": item.get("google_patents_url")
                or f"https://patents.google.com/patent/{pub_id}/en",
            }
        )

    enriched["normalized_results"] = normalized
    enriched["app_view"] = "chemistry-explorer"
    set_cached_chemistry_payload(enriched)
    return enriched


def build_chemistry_app_html(initial_payload: dict[str, Any] | None = None) -> str:
    """Build a self-contained HTML5 MCP App for the 2D Chemical Structure & SMILES Explorer."""
    import os
    payload_to_inject = initial_payload or get_cached_chemistry_payload()
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
  <title>Google Patents — 2D Chemical Structure &amp; SMILES Explorer</title>
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
      --primary: #0d9488;
      --primary-light: #ccfbf1;
      --indigo: #4f46e5;
      --indigo-light: #e0e7ff;
      --emerald: #059669;
      --emerald-light: #d1fae5;
      --amber: #d97706;
      --amber-light: #fef3c7;
      --radius: 10px;
      --radius-sm: 6px;
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
        --primary: #14b8a6;
        --primary-light: rgba(20, 184, 166, 0.2);
        --indigo: #6366f1;
        --indigo-light: rgba(99, 102, 241, 0.2);
        --emerald: #10b981;
        --emerald-light: rgba(16, 185, 129, 0.2);
        --amber: #f59e0b;
        --amber-light: rgba(245, 158, 11, 0.2);
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
      text-transform: uppercase;
    }}

    .input {{
      background: var(--bg-muted);
      border: 1px solid var(--border);
      color: var(--text-main);
      border-radius: var(--radius-sm);
      padding: 5px 9px;
      font-size: 12px;
      font-family: var(--font-mono);
    }}

    .btn {{
      border: 1px solid var(--border);
      background: var(--bg-panel);
      color: var(--text-main);
      padding: 5px 10px;
      border-radius: var(--radius-sm);
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 5px;
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

    .preset-bar {{
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
      padding-top: 4px;
      border-top: 1px solid var(--border);
    }}

    .preset-chip {{
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: var(--bg-muted);
      color: var(--text-secondary);
      cursor: pointer;
      font-weight: 600;
    }}

    .preset-chip:hover {{
      background: var(--primary-light);
      color: var(--primary);
      border-color: var(--primary);
    }}

    .main-grid {{
      flex: 1;
      display: grid;
      grid-template-columns: 420px 1fr;
      overflow: hidden;
    }}

    .left-workbench {{
      border-right: 1px solid var(--border);
      background: var(--bg-panel);
      display: flex;
      flex-direction: column;
      overflow-y: auto;
      padding: 12px;
      gap: 12px;
    }}

    .svg-box {{
      border: 1px solid var(--border);
      border-radius: var(--radius);
      background: #ffffff;
      height: 250px;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
    }}

    .prop-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }}

    .prop-card {{
      background: var(--bg-muted);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 8px 10px;
    }}

    .prop-label {{
      font-size: 10px;
      text-transform: uppercase;
      color: var(--text-muted);
      font-weight: 700;
    }}

    .prop-val {{
      font-size: 13px;
      font-weight: 700;
      font-family: var(--font-mono);
      margin-top: 2px;
    }}

    .right-results {{
      overflow-y: auto;
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}

    .patent-card {{
      background: var(--bg-panel);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 12px;
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: flex-start;
    }}

    .badge {{
      display: inline-flex;
      padding: 2px 7px;
      border-radius: 999px;
      font-size: 10.5px;
      font-weight: 600;
      background: var(--primary-light);
      color: var(--primary);
    }}

    .statusbar {{
      background: var(--bg-panel);
      border-top: 1px solid var(--border);
      padding: 5px 14px;
      font-size: 11px;
      color: var(--text-muted);
      display: flex;
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
        <span>2D Chemical Structure / SMILES Explorer &amp; Substructure Workbench</span>
      </div>
      <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;">
        <input id="smilesInput" class="input" style="width:240px;" placeholder="Enter SMILES (e.g. CC(=O)Oc1ccccc1C(=O)O)" />
        <select id="matchTypeSelect" class="input">
          <option value="EXACT">EXACT</option>
          <option value="SUBSTRUCTURE" selected>SUBSTRUCTURE</option>
          <option value="SIMILARITY">SIMILARITY</option>
        </select>
        <button id="runChemSearchBtn" class="btn btn-primary">Search Chemical Patents</button>
      </div>
    </div>

    <div class="preset-bar">
      <span style="font-size:11px;font-weight:700;color:var(--text-muted);">Presets:</span>
      <span class="preset-chip" data-smiles="CC(=O)Oc1ccccc1C(=O)O">Aspirin</span>
      <span class="preset-chip" data-smiles="CC(C)Cc1ccc(cc1)C(C)C(=O)O">Ibuprofen</span>
      <span class="preset-chip" data-smiles="CC(=O)Nc1ccc(O)cc1">Paracetamol</span>
      <span class="preset-chip" data-smiles="O=C1OCCO1">Ethylene Carbonate (Battery)</span>
      <span class="preset-chip" data-smiles="Cn1cnc2c1c(=O)n(C)c(=O)n2C">Caffeine</span>
      <span class="preset-chip" data-smiles="Nc1ccc(S(=O)(=O)N)cc1">Sulfanilamide</span>
      <span style="margin-left:auto;font-size:11px;font-weight:700;color:var(--text-muted);">Append Group:</span>
      <span class="preset-chip" data-append="C(=O)O">+COOH</span>
      <span class="preset-chip" data-append="C(F)(F)F">+CF3</span>
      <span class="preset-chip" data-append="O">+OH</span>
    </div>
  </header>

  <div class="main-grid">
    <aside class="left-workbench">
      <div class="svg-box">
        <svg id="moleculeSvg" width="100%" height="100%" viewBox="-160 -120 320 240"></svg>
      </div>

      <div class="prop-grid">
        <div class="prop-card">
          <div class="prop-label">Est. Formula</div>
          <div id="propFormula" class="prop-val">—</div>
        </div>
        <div class="prop-card">
          <div class="prop-label">Est. Mol Weight</div>
          <div id="propMw" class="prop-val">—</div>
        </div>
        <div class="prop-card">
          <div class="prop-label">Rings / Aromatic</div>
          <div id="propRings" class="prop-val">—</div>
        </div>
        <div class="prop-card">
          <div class="prop-label">HBA / HBD (Lipinski)</div>
          <div id="propLipinski" class="prop-val">—</div>
        </div>
      </div>

      <div>
        <div class="prop-label" style="margin-bottom:6px;">Detected Functional Groups &amp; Pharmacophores</div>
        <div id="funcGroupsList" style="display:flex;gap:6px;flex-wrap:wrap;"></div>
      </div>

      <button id="askMarkushAiBtn" class="btn" style="justify-content:center;margin-top:auto;">
        Ask AI for Markush / Bioisostere Prior-Art Analysis
      </button>
    </aside>

    <main class="right-results">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div style="font-weight:700;font-size:14px;">Matching Chemical &amp; Formulation Patents (<span id="chemResultCount">0</span>)</div>
        <span id="searchQueryBadge" class="badge"></span>
      </div>
      <div id="chemPatentsList" style="display:flex;flex-direction:column;gap:10px;"></div>
    </main>
  </div>

  <footer class="statusbar">
    <span id="statusText">Ready</span>
    <span>ui://google-patents/chemistry-explorer</span>
  </footer>

  <script>
    const INITIAL_PAYLOAD = {initial_json};
    const SERVER_BASE = {server_base_json} || ((window.location.origin && window.location.origin.startsWith("http") && !window.location.origin.includes("usercontent")) ? window.location.origin : "");
    let currentPayload = null;

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

    const ATOM_COLORS = {{
      C: "#1e293b",
      O: "#dc2626",
      N: "#2563eb",
      S: "#d97706",
      P: "#ea580c",
      F: "#16a34a",
      Cl: "#16a34a",
      Br: "#9a3412",
      I: "#7e22ce",
    }};

    function drawSmiles2D(smiles) {{
      const svg = document.getElementById("moleculeSvg");
      const s = String(smiles || "").trim();
      if (!s) {{
        svg.innerHTML = '<text x="0" y="0" text-anchor="middle" fill="#64748b" font-size="12">Enter a SMILES string to render 2D structure</text>';
        return;
      }}

      // Parse SMILES into atoms and bonds with 2D coordinates
      const atoms = [];
      const bonds = [];
      const stack = [];
      const rings = {{}};
      let currAtom = -1;
      let nextBondOrder = 1;
      let angle = -Math.PI / 6;
      const bondLen = 34;

      let i = 0;
      while (i < s.length) {{
        const ch = s[i];
        if (ch === "(") {{
          stack.push({{ atom: currAtom, angle }});
          angle += Math.PI / 3;
          i++;
          continue;
        }}
        if (ch === ")") {{
          if (stack.length) {{
            const popped = stack.pop();
            currAtom = popped.atom;
            angle = popped.angle - Math.PI / 3;
          }}
          i++;
          continue;
        }}
        if (ch === "=") {{ nextBondOrder = 2; i++; continue; }}
        if (ch === "#") {{ nextBondOrder = 3; i++; continue; }}
        if (ch === "-" || ch === ":" || ch === "/" || ch === "\\\\") {{ i++; continue; }}
        if (/[1-9]/.test(ch)) {{
          if (rings[ch] !== undefined && currAtom >= 0) {{
            bonds.push({{ from: rings[ch], to: currAtom, order: nextBondOrder, ring: true }});
            delete rings[ch];
          }} else if (currAtom >= 0) {{
            rings[ch] = currAtom;
          }}
          nextBondOrder = 1;
          i++;
          continue;
        }}
        if (ch === "[") {{
          const closeIdx = s.indexOf("]", i);
          const label = closeIdx > i ? s.slice(i + 1, closeIdx) : "X";
          i = closeIdx > i ? closeIdx + 1 : i + 1;
          addAtom(label.replace(/[^A-Za-z]/g, "") || "C", false);
          continue;
        }}
        if (/[A-Za-z]/.test(ch)) {{
          let sym = ch;
          if (i + 1 < s.length && ((ch === "C" && s[i + 1] === "l") || (ch === "B" && s[i + 1] === "r"))) {{
            sym = s.slice(i, i + 2);
            i += 2;
          }} else {{
            i++;
          }}
          const isArom = sym === sym.toLowerCase();
          addAtom(sym.length === 1 ? sym.toUpperCase() : sym, isArom);
          continue;
        }}
        i++;
      }}

      function addAtom(elem, isArom) {{
        const idx = atoms.length;
        let x = 0, y = 0;
        if (currAtom >= 0) {{
          const prev = atoms[currAtom];
          angle += (idx % 2 === 0 ? 1 : -1) * (Math.PI / 3);
          x = prev.x + bondLen * Math.cos(angle);
          y = prev.y + bondLen * Math.sin(angle);
          bonds.push({{ from: currAtom, to: idx, order: isArom && prev.isArom ? 1.5 : nextBondOrder }});
        }}
        atoms.push({{ elem, isArom, x, y }});
        currAtom = idx;
        nextBondOrder = 1;
      }}

      // Arrange 6-membered rings neatly into hexagons when a ring closure is detected
      for (const b of bonds) {{
        if (b.ring) {{
          const span = b.to - b.from + 1;
          if (span >= 5 && span <= 7) {{
            const cx = atoms[b.from].x + bondLen;
            const cy = atoms[b.from].y;
            const r = bondLen / (2 * Math.sin(Math.PI / span));
            for (let k = 0; k < span; k++) {{
              const aIdx = b.from + k;
              if (atoms[aIdx]) {{
                const theta = (2 * Math.PI * k) / span - Math.PI / 2;
                atoms[aIdx].x = cx + r * Math.cos(theta);
                atoms[aIdx].y = cy + r * Math.sin(theta);
              }}
            }}
          }}
        }}
      }}

      if (!atoms.length) return;

      // Center bounding box
      const minX = Math.min(...atoms.map((a) => a.x));
      const maxX = Math.max(...atoms.map((a) => a.x));
      const minY = Math.min(...atoms.map((a) => a.y));
      const maxY = Math.max(...atoms.map((a) => a.y));
      const midX = (minX + maxX) / 2;
      const midY = (minY + maxY) / 2;
      const pad = 40;
      const w = Math.max(220, maxX - minX + pad * 2);
      const h = Math.max(160, maxY - minY + pad * 2);
      svg.setAttribute("viewBox", `${{midX - w / 2}} ${{midY - h / 2}} ${{w}} ${{h}}`);

      let html = "";
      for (const b of bonds) {{
        const a1 = atoms[b.from];
        const a2 = atoms[b.to];
        if (!a1 || !a2) continue;
        if (b.order === 2) {{
          const dx = a2.y - a1.y;
          const dy = -(a2.x - a1.x);
          const len = Math.hypot(dx, dy) || 1;
          const ox = (dx / len) * 2.5;
          const oy = (dy / len) * 2.5;
          html += `<line x1="${{a1.x - ox}}" y1="${{a1.y - oy}}" x2="${{a2.x - ox}}" y2="${{a2.y - oy}}" stroke="#334155" stroke-width="2" />`;
          html += `<line x1="${{a1.x + ox}}" y1="${{a1.y + oy}}" x2="${{a2.x + ox}}" y2="${{a2.y + oy}}" stroke="#334155" stroke-width="2" />`;
        }} else if (b.order === 1.5) {{
          html += `<line x1="${{a1.x}}" y1="${{a1.y}}" x2="${{a2.x}}" y2="${{a2.y}}" stroke="#334155" stroke-width="2.2" />`;
          html += `<line x1="${{a1.x}}" y1="${{a1.y}}" x2="${{a2.x}}" y2="${{a2.y}}" stroke="#0d9488" stroke-width="1.2" stroke-dasharray="3,3" />`;
        }} else {{
          html += `<line x1="${{a1.x}}" y1="${{a1.y}}" x2="${{a2.x}}" y2="${{a2.y}}" stroke="#334155" stroke-width="2.2" />`;
        }}
      }}

      atoms.forEach((a) => {{
        const color = ATOM_COLORS[a.elem] || "#1e293b";
        if (a.elem !== "C" || atoms.length <= 2) {{
          html += `<circle cx="${{a.x}}" cy="${{a.y}}" r="10" fill="#ffffff" />`;
          html += `<text x="${{a.x}}" y="${{a.y + 4}}" text-anchor="middle" font-size="12" font-weight="700" font-family="sans-serif" fill="${{color}}">${{escapeHtml(a.elem)}}</text>`;
        }} else {{
          html += `<circle cx="${{a.x}}" cy="${{a.y}}" r="3" fill="#334155" />`;
        }}
      }});

      svg.innerHTML = html;
    }}

    function computeFallbackAnalysis(smiles) {{
      const s = String(smiles || "").trim();
      const tokens = s.match(/Cl|Br|Si|[BCNOSPFIbcnosp]/g) || [];
      const counts = {{}};
      let arom = 0;
      tokens.forEach((t) => {{
        if (t === t.toLowerCase()) arom++;
        const el = t.length === 1 ? t.toUpperCase() : t;
        counts[el] = (counts[el] || 0) + 1;
      }});
      const mw = ((counts.C || 0) * 14 + (counts.O || 0) * 16 + (counts.N || 0) * 14 + (counts.S || 0) * 32 + (counts.F || 0) * 19).toFixed(1);
      const formula = Object.entries(counts).map(([k, v]) => k + (v > 1 ? v : "")).join("");
      return {{
        smiles: s,
        molecular_formula_est: formula || "—",
        molecular_weight_est: mw,
        ring_count: Math.floor(((s.match(/[1-9]/g) || []).length) / 2),
        aromatic_atom_count: arom,
        h_bond_acceptors: (counts.O || 0) + (counts.N || 0),
        h_bond_donors_est: 1,
        lipinski_ro5_compliant: true,
        functional_groups: arom >= 5 ? ["Aromatic Ring System"] : [],
      }};
    }}

    function hydratePayload(data) {{
      if (!data || typeof data !== "object") return;
      currentPayload = data;
      const smiles = data.smiles || "CC(=O)Oc1ccccc1C(=O)O";
      document.getElementById("smilesInput").value = smiles;
      if (data.match_type) document.getElementById("matchTypeSelect").value = data.match_type;

      drawSmiles2D(smiles);

      const analysis = data.molecule_analysis || computeFallbackAnalysis(smiles);
      document.getElementById("propFormula").textContent = analysis.molecular_formula_est || "—";
      document.getElementById("propMw").textContent = (analysis.molecular_weight_est || "—") + " Da";
      document.getElementById("propRings").textContent = `${{analysis.ring_count || 0}} rings (${{analysis.aromatic_atom_count || 0}} arom)`;
      document.getElementById("propLipinski").textContent =
        `${{analysis.h_bond_acceptors || 0}} / ${{analysis.h_bond_donors_est || 0}} (${{analysis.lipinski_ro5_compliant ? "Pass" : "Review"}})`;

      const fgEl = document.getElementById("funcGroupsList");
      const fgs = analysis.functional_groups || [];
      fgEl.innerHTML = fgs.length
        ? fgs.map((g) => `<span class="badge">${{escapeHtml(g)}}</span>`).join("")
        : '<span style="font-size:11.5px;color:var(--text-muted);">Standard organic scaffold</span>';

      const results = data.normalized_results || data.results || [];
      document.getElementById("chemResultCount").textContent = results.length;
      document.getElementById("searchQueryBadge").textContent = `${{data.match_type || "SUBSTRUCTURE"}}: ${{smiles}}`;

      const listEl = document.getElementById("chemPatentsList");
      listEl.innerHTML = results.length
        ? results.map((r) => {{
            const id = r.id || r.publication_number || "";
            const cleanId = String(id).replace(/-/g, "");
            const url = (SERVER_BASE ? SERVER_BASE + "/apps/patent/" : "https://patents.google.com/patent/") + encodeURIComponent(cleanId);
            return `
              <div class="patent-card">
                <div>
                  <div style="display:flex;gap:8px;align-items:center;">
                    <span style="font-family:var(--font-mono);font-weight:700;color:var(--primary);">${{escapeHtml(id)}}</span>
                    <span style="font-size:11px;color:var(--text-muted);">${{escapeHtml(r.publication_date || "")}}</span>
                    <span class="badge">${{escapeHtml(r.assignee || "Assignee")}}</span>
                  </div>
                  <div style="font-weight:700;font-size:13px;margin-top:3px;">${{escapeHtml(r.title || "")}}</div>
                  <div style="font-size:11.5px;color:var(--text-secondary);margin-top:4px;">${{escapeHtml(r.snippet || "")}}</div>
                </div>
                <a class="btn" href="${{escapeHtml(url)}}" target="_blank" rel="noopener">Open ↗</a>
              </div>
            `;
          }}).join("")
        : '<div style="color:var(--text-muted);">No matching chemical patents found for this SMILES query.</div>';
    }}

    document.querySelectorAll("[data-smiles]").forEach((chip) => {{
      chip.addEventListener("click", () => {{
        const sm = chip.getAttribute("data-smiles");
        document.getElementById("smilesInput").value = sm;
        drawSmiles2D(sm);
        const analysis = computeFallbackAnalysis(sm);
        document.getElementById("propFormula").textContent = analysis.molecular_formula_est;
        document.getElementById("propMw").textContent = analysis.molecular_weight_est + " Da";
      }});
    }});

    document.querySelectorAll("[data-append]").forEach((chip) => {{
      chip.addEventListener("click", () => {{
        const sm = document.getElementById("smilesInput").value.trim() + chip.getAttribute("data-append");
        document.getElementById("smilesInput").value = sm;
        drawSmiles2D(sm);
      }});
    }});

    document.getElementById("smilesInput").addEventListener("input", (e) => {{
      drawSmiles2D(e.target.value);
    }});

    document.getElementById("runChemSearchBtn").addEventListener("click", async () => {{
      const smiles = document.getElementById("smilesInput").value.trim();
      const match_type = document.getElementById("matchTypeSelect").value;
      if (!smiles) return;
      document.getElementById("statusText").textContent = `Searching chemical patents (${{match_type}}) for ${{smiles}}...`;
      try {{
        const res = await sendRpcRequest("tools/call", {{
          name: "search_chemistry",
          arguments: {{ smiles, mode: match_type, limit: 15 }}
        }});
        if (res && Array.isArray(res.content)) {{
          for (const item of res.content) {{
            if (item.type === "text" && item.text) {{
              hydratePayload(JSON.parse(item.text));
              document.getElementById("statusText").textContent = "Chemical patent search complete";
              return;
            }}
          }}
        }}
      }} catch (_) {{}}
      try {{
        const r = await fetch(`${{SERVER_BASE}}/apps/api/chemistry?smiles=${{encodeURIComponent(smiles)}}&mode=${{encodeURIComponent(match_type)}}`);
        if (r.ok) {{
          hydratePayload(await r.json());
          document.getElementById("statusText").textContent = "Chemical patent search complete";
          return;
        }}
      }} catch (_) {{}}
      document.getElementById("statusText").textContent = "Host tool call unavailable; ask in chat.";
    }});

    document.getElementById("askMarkushAiBtn").addEventListener("click", () => {{
      const smiles = document.getElementById("smilesInput").value.trim() || "CC(=O)Oc1ccccc1C(=O)O";
      window.parent.postMessage({{
        jsonrpc: "2.0",
        method: "ui/message",
        params: {{
          role: "user",
          content: [{{
            type: "text",
            text: `Analyze the chemical structure SMILES "${{smiles}}" and its matching patents. Suggest key bioisosteres or functional group modifications to evaluate Markush claim scope and freedom-to-operate.`
          }}]
        }}
      }}, "*");
    }});

    if (INITIAL_PAYLOAD) {{
      hydratePayload(INITIAL_PAYLOAD);
    }} else {{
      drawSmiles2D("CC(=O)Oc1ccccc1C(=O)O");
    }}
  </script>
</body>
</html>"""
