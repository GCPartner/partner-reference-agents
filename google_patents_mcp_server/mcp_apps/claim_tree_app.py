"""View 1: Interactive Patent Claim Tree, Scope Inspector & Side-by-Side Comparator MCP App.

Implements the official MCP Apps extension (`ui://google-patents/claim-tree`,
`mimeType="text/html;profile=mcp-app"`) with:
1. Server-side Claim Dependency Parser & Limitation Decomposer (`parse_claim_dependency_tree`).
2. Full JSON-RPC 2.0 over `window.parent.postMessage` bridge (`ui/initialize`,
   `ui/notifications/initialized`, `ui/notifications/tool-input`, `ui/notifications/tool-result`,
   `ui/notifications/host-context-changed`, `ui/notifications/size-changed`, `tools/call`,
   `ui/message`, `ui/open-link`).
3. Interactive 4-Tab Workbench:
   - Tab 1: Collapsible Claim Dependency Tree + Merged Inherited Scope & Limitation Breakdown
   - Tab 2: Live Side-by-Side Claim Comparator (calls `get_patent_details` via MCP `tools/call`)
   - Tab 3: Interactive Claim Construction & Element Chart Matrix (with Markdown/CSV export)
   - Tab 4: Patent Dossier & Key Legal Metadata
"""

from __future__ import annotations

import html
import json
import re
from typing import Any, Dict, List, Optional

import os

MCP_APP_MIME_TYPE = "text/html;profile=mcp-app"
CLAIM_TREE_RESOURCE_URI = "ui://google-patents/claim-tree"
DEFAULT_PUBLIC_API_BASE_URL = os.environ.get("MCP_PUBLIC_BASE_URL", "").rstrip("/")

CLAIM_TREE_TOOL_META: Dict[str, Any] = {
    "ui": {
        "resourceUri": CLAIM_TREE_RESOURCE_URI,
        "visibility": ["model", "app"],
    },
    "ui/resourceUri": CLAIM_TREE_RESOURCE_URI,
}

CLAIM_TREE_RESOURCE_META: Dict[str, Any] = {
    "ui": {
        "prefersBorder": True,
        "csp": {
            "connectDomains": [
                d for d in [
                    "https://patentimages.storage.googleapis.com",
                    DEFAULT_PUBLIC_API_BASE_URL,
                    "https://patents.google.com",
                ] if d
            ],
            "resourceDomains": [
                d for d in [
                    "https://patentimages.storage.googleapis.com",
                    DEFAULT_PUBLIC_API_BASE_URL,
                    "https://patents.google.com",
                ] if d
            ],
            "frameDomains": [
                d for d in [
                    "https://patentimages.storage.googleapis.com",
                    DEFAULT_PUBLIC_API_BASE_URL,
                ] if d
            ],
        },
    }
}

# In-memory cache of recently fetched patent payloads so `resources/read` on
# `ui://google-patents/claim-tree` or `ui://google-patents/claim-tree/{patent_id}`
# can pre-hydrate the initial UI state even before `ui/notifications/tool-result` arrives.
_PATENT_PAYLOAD_CACHE: Dict[str, Dict[str, Any]] = {}
_LAST_PATENT_KEY: Optional[str] = None


def set_cached_patent_payload(patent_id: str, payload: Dict[str, Any]) -> None:
    """Stores a structured patent payload in the in-memory cache."""
    global _LAST_PATENT_KEY
    if not patent_id or not isinstance(payload, dict):
        return
    clean_key = patent_id.replace("-", "").strip().upper()
    _PATENT_PAYLOAD_CACHE[clean_key] = payload
    _PATENT_PAYLOAD_CACHE[patent_id.strip().upper()] = payload
    _LAST_PATENT_KEY = clean_key


def get_cached_patent_payload(patent_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieves a cached patent payload by ID, or the most recently loaded patent payload."""
    if patent_id:
        clean_key = patent_id.replace("-", "").strip().upper()
        if clean_key in _PATENT_PAYLOAD_CACHE:
            return _PATENT_PAYLOAD_CACHE[clean_key]
        if patent_id.strip().upper() in _PATENT_PAYLOAD_CACHE:
            return _PATENT_PAYLOAD_CACHE[patent_id.strip().upper()]
    if _LAST_PATENT_KEY and _LAST_PATENT_KEY in _PATENT_PAYLOAD_CACHE:
        return _PATENT_PAYLOAD_CACHE[_LAST_PATENT_KEY]
    return None


# ==============================================================================
# 1. Server-Side Patent Claim Dependency Parser & Limitation Decomposer
# ==============================================================================

_PARENT_REF_PATTERNS = [
    re.compile(r"\bclaims?\s+(\d+)\s*(?:to|through|-|–)\s*(\d+)\b", re.IGNORECASE),
    re.compile(r"\bclaims?\s+(\d+)\s+(?:or|and)\s+(\d+)\b", re.IGNORECASE),
    re.compile(r"\bclaim\s+(\d+)\b", re.IGNORECASE),
]


def _clean_claim_text(raw: str) -> str:
    """Unescapes HTML entities, removes stray XML/HTML tags, and normalizes whitespace."""
    text = html.unescape(raw or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()


def _split_raw_claims(claims_input: Any) -> List[Dict[str, Any]]:
    """Splits raw claims string or list into numbered claim dicts `[{'number': int, 'text': str}]`."""
    if not claims_input:
        return []

    if isinstance(claims_input, list):
        items: List[Dict[str, Any]] = []
        for idx, item in enumerate(claims_input, start=1):
            cleaned = _clean_claim_text(str(item))
            if not cleaned:
                continue
            m = re.match(r"^(\d+)\s*[\.\)]\s*(.+)$", cleaned, flags=re.DOTALL)
            if m:
                items.append({"number": int(m.group(1)), "text": m.group(2).strip()})
            else:
                items.append({"number": idx, "text": cleaned})
        return items

    text = _clean_claim_text(str(claims_input))
    text = re.sub(
        r"^(?:The invention claimed is|What is claimed is|We claim|I claim)\s*:?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()

    # Split on numbered claim boundaries (`1. `, `2. `, etc.)
    pattern = re.compile(r"(?:^|\n)\s*(\d{1,3})\s*[\.\)]\s+(?=[A-ZTheAnInA])", re.MULTILINE)
    matches = list(pattern.finditer(text))

    if not matches:
        # Fallback broader numeric split
        pattern_broad = re.compile(r"(?:^|\s+)(\d{1,3})\s*\.\s+(?=[A-Z])")
        matches = list(pattern_broad.finditer(text))

    if not matches:
        return [{"number": 1, "text": text}] if text else []

    parsed: List[Dict[str, Any]] = []
    seen_numbers = set()
    for i, match in enumerate(matches):
        claim_num = int(match.group(1))
        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start_pos:end_pos].strip()
        if not body:
            continue
        # Guard against out-of-sequence numbers inside body text
        if parsed and claim_num <= parsed[-1]["number"] and claim_num in seen_numbers:
            parsed[-1]["text"] += " " + match.group(0).strip() + " " + body
            continue
        seen_numbers.add(claim_num)
        parsed.append({"number": claim_num, "text": body})

    return parsed


def _extract_parent_claims(claim_text: str, self_num: int, valid_numbers: set[int]) -> List[int]:
    """Extracts parent claim numbers referenced by a dependent claim."""
    parents: List[int] = []

    # Range references: e.g., "claims 1 to 4"
    for m in _PARENT_REF_PATTERNS[0].finditer(claim_text):
        start_n, end_n = int(m.group(1)), int(m.group(2))
        if 1 <= start_n <= end_n and (end_n - start_n) <= 25:
            for n in range(start_n, end_n + 1):
                if n != self_num and n in valid_numbers and n not in parents:
                    parents.append(n)

    # Pair references: e.g., "claim 1 or 2"
    for m in _PARENT_REF_PATTERNS[1].finditer(claim_text):
        for grp in (1, 2):
            n = int(m.group(grp))
            if n != self_num and n in valid_numbers and n not in parents:
                parents.append(n)

    # Single claim references: e.g., "of claim 1"
    for m in _PARENT_REF_PATTERNS[2].finditer(claim_text):
        n = int(m.group(1))
        if n != self_num and n in valid_numbers and n not in parents:
            parents.append(n)

    return parents


def _classify_claim_category(text: str) -> str:
    """Classifies a claim into Method/Process, System/Apparatus, CRM, or Composition."""
    head = text[:220].lower()
    if any(w in head for w in ("method", "process", "step of", "performing")):
        return "Method / Process"
    if any(w in head for w in ("computer-readable", "non-transitory", "storage medium", "program product")):
        return "Computer-Readable Medium"
    if any(w in head for w in ("composition", "compound", "electrolyte", "molecule", "formulation", "polymer")):
        return "Composition / Material"
    return "System / Apparatus"


def _decompose_claim_limitations(claim_num: int, text: str) -> Dict[str, Any]:
    """Splits a claim into its preamble, transitional phrase, and individual element limitations."""
    clean = re.sub(r"\s+", " ", text).strip()

    trans_match = re.search(
        r"\b(comprising|consisting essentially of|consisting of|including|characterized by|wherein)\s*:?\s*",
        clean,
        flags=re.IGNORECASE,
    )

    if trans_match and trans_match.start() < 260:
        preamble = clean[: trans_match.end()].strip()
        transitional = trans_match.group(1).lower()
        remainder = clean[trans_match.end() :].strip()
    elif ":" in clean[:220]:
        colon_idx = clean.index(":")
        preamble = clean[: colon_idx + 1].strip()
        transitional = "colon"
        remainder = clean[colon_idx + 1 :].strip()
    else:
        preamble = ""
        transitional = ""
        remainder = clean

    raw_clauses = [c.strip() for c in re.split(r";\s*|\.\s+(?=[A-Z])", remainder) if c.strip()]
    limitations: List[Dict[str, str]] = []

    if preamble:
        limitations.append({
            "id": f"{claim_num}.pre",
            "label": f"[{claim_num}.pre]",
            "type": "preamble",
            "text": preamble,
        })

    if len(raw_clauses) <= 1 and "," in remainder and len(remainder) > 140:
        # Try splitting on ", wherein " or ", and " for single-sentence dependent claims
        sub_clauses = [
            s.strip()
            for s in re.split(r",\s*(?=(?:wherein|whereby|further comprising|and wherein)\b)", remainder, flags=re.IGNORECASE)
            if s.strip()
        ]
        if len(sub_clauses) > 1:
            raw_clauses = sub_clauses

    for idx, clause in enumerate(raw_clauses):
        suffix = chr(ord("a") + idx) if idx < 26 else f"el{idx + 1}"
        clause_text = clause if clause.endswith((".", ";")) else f"{clause};"
        limitations.append({
            "id": f"{claim_num}.{suffix}",
            "label": f"[{claim_num}.{suffix}]",
            "type": "limitation",
            "text": clause_text,
        })

    return {
        "preamble": preamble or (clean[:140] + ("..." if len(clean) > 140 else "")),
        "transitional_phrase": transitional,
        "limitations": limitations,
    }


def parse_claim_dependency_tree(claims_raw: Any) -> Dict[str, Any]:
    """Parses raw patent claims into a structured dependency tree and limitation breakdown."""
    raw_items = _split_raw_claims(claims_raw)
    if not raw_items:
        return {
            "total_claims": 0,
            "independent_count": 0,
            "dependent_count": 0,
            "max_depth": 0,
            "claims": [],
            "root_claim_numbers": [],
        }

    valid_nums = {item["number"] for item in raw_items}
    nodes_by_num: Dict[int, Dict[str, Any]] = {}

    for item in raw_items:
        num = item["number"]
        txt = item["text"]
        parents = _extract_parent_claims(txt, num, valid_nums)
        is_indep = len(parents) == 0
        decomp = _decompose_claim_limitations(num, txt)
        category = _classify_claim_category(txt)

        nodes_by_num[num] = {
            "number": num,
            "text": txt,
            "is_independent": is_indep,
            "parent_claims": parents,
            "primary_parent": parents[0] if parents else None,
            "children": [],
            "category": category,
            "preamble": decomp["preamble"],
            "transitional_phrase": decomp["transitional_phrase"],
            "limitations": decomp["limitations"],
            "word_count": len(txt.split()),
            "depth": 0,
            "ancestor_chain": [num],
        }

    # Wire parent -> children links
    root_numbers: List[int] = []
    for num, node in nodes_by_num.items():
        primary_parent = node["primary_parent"]
        if primary_parent and primary_parent in nodes_by_num and primary_parent != num:
            nodes_by_num[primary_parent]["children"].append(num)
        else:
            root_numbers.append(num)

    # Compute depth and ancestor chain for each claim (with cycle guard)
    max_depth = 0
    for num, node in nodes_by_num.items():
        chain = [num]
        curr = node["primary_parent"]
        visited = {num}
        while curr and curr in nodes_by_num and curr not in visited:
            visited.add(curr)
            chain.append(curr)
            curr = nodes_by_num[curr]["primary_parent"]
        chain.reverse()
        node["ancestor_chain"] = chain
        node["depth"] = len(chain) - 1
        if node["depth"] > max_depth:
            max_depth = node["depth"]
        # Inherit root claim category for dependent claims if generic
        root_num = chain[0]
        if not node["is_independent"] and root_num in nodes_by_num:
            node["category"] = nodes_by_num[root_num]["category"]

    claims_list = [nodes_by_num[k] for k in sorted(nodes_by_num.keys())]
    indep_count = sum(1 for c in claims_list if c["is_independent"])
    dep_count = len(claims_list) - indep_count

    return {
        "total_claims": len(claims_list),
        "independent_count": indep_count,
        "dependent_count": dep_count,
        "max_depth": max_depth,
        "root_claim_numbers": sorted(root_numbers),
        "claims": claims_list,
    }


def enrich_patent_with_claim_tree(patent_data: Dict[str, Any]) -> Dict[str, Any]:
    """Enriches a patent details dict with `claims_tree` and caches it for MCP App hydration."""
    if not isinstance(patent_data, dict):
        return patent_data
    enriched = dict(patent_data)
    claims_tree = parse_claim_dependency_tree(enriched.get("claims"))
    enriched["claims_tree"] = claims_tree
    enriched["mcp_app"] = {
        "resource_uri": CLAIM_TREE_RESOURCE_URI,
        "mime_type": MCP_APP_MIME_TYPE,
        "view": "claim-tree",
    }
    pub_num = enriched.get("publication_number") or enriched.get("ucid") or ""
    if pub_num:
        set_cached_patent_payload(str(pub_num), enriched)
    return enriched


# ==============================================================================
# 2. Self-Contained Interactive MCP App HTML Bundle (`text/html;profile=mcp-app`)
# ==============================================================================

def build_claim_tree_app_html(
    initial_patent: Optional[Dict[str, Any]] = None,
    comparison_patent: Optional[Dict[str, Any]] = None,
) -> str:
    """Builds the self-contained HTML/CSS/JS bundle for `ui://google-patents/claim-tree`."""
    initial_state = {
        "primaryPatent": initial_patent,
        "comparisonPatent": comparison_patent,
        "serverBase": os.environ.get("MCP_PUBLIC_BASE_URL", "").rstrip("/"),
    }
    initial_json = json.dumps(initial_state).replace("</", "<\\/")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Google Patents — Claim Tree & Scope Inspector (MCP App)</title>
  <style>
    :root {{
      --bg-app: #f8fafc;
      --bg-surface: #ffffff;
      --bg-muted: #f1f5f9;
      --bg-accent: #eff6ff;
      --bg-indep: #ecfdf5;
      --bg-warn: #fffbeb;
      --text-main: #0f172a;
      --text-secondary: #334155;
      --text-muted: #64748b;
      --border-color: #e2e8f0;
      --border-strong: #cbd5e1;
      --brand-blue: #1a73e8;
      --brand-blue-dark: #1557b0;
      --brand-green: #059669;
      --brand-purple: #7c3aed;
      --brand-amber: #d97706;
      --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.05);
      --shadow-md: 0 4px 12px rgba(15, 23, 42, 0.08);
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
      --bg-indep: #064e3b;
      --bg-warn: #78350f;
      --text-main: #f8fafc;
      --text-secondary: #cbd5e1;
      --text-muted: #94a3b8;
      --border-color: #334155;
      --border-strong: #475569;
      --brand-blue: #60a5fa;
      --brand-blue-dark: #3b82f6;
      --brand-green: #34d399;
      --brand-purple: #a78bfa;
      --brand-amber: #fbbf24;
    }}

    * {{
      box-sizing: border-box;
    }}

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
      max-width: 1280px;
      margin: 0 auto;
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}

    /* Top Header Bar */
    .header-card {{
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-lg);
      padding: 14px 18px;
      box-shadow: var(--shadow-sm);
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}

    .header-top {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }}

    .brand-row {{
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }}

    .mcp-badge {{
      display: inline-flex;
      align-items: center;
      gap: 5px;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: 3px 8px;
      border-radius: 999px;
      background: var(--bg-accent);
      color: var(--brand-blue);
      border: 1px solid rgba(26, 115, 232, 0.25);
    }}

    .pub-badge {{
      font-family: var(--font-mono);
      font-size: 12.5px;
      font-weight: 700;
      padding: 3px 9px;
      border-radius: var(--radius-sm);
      background: var(--brand-blue);
      color: #ffffff;
    }}

    .status-pill {{
      font-size: 11px;
      font-weight: 600;
      padding: 2px 8px;
      border-radius: 999px;
      background: var(--bg-indep);
      color: var(--brand-green);
    }}

    .patent-title {{
      margin: 2px 0 0 0;
      font-size: 17px;
      font-weight: 700;
      color: var(--text-main);
      line-height: 1.3;
    }}

    .patent-subtitle {{
      font-size: 12.5px;
      color: var(--text-muted);
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      align-items: center;
    }}

    /* Quick Loader Bar */
    .loader-bar {{
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
    }}

    .input-box {{
      padding: 6px 10px;
      border: 1px solid var(--border-strong);
      border-radius: var(--radius-sm);
      background: var(--bg-surface);
      color: var(--text-main);
      font-size: 12.5px;
      font-family: var(--font-mono);
      min-width: 155px;
    }}

    .btn {{
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 6px 12px;
      border-radius: var(--radius-sm);
      font-size: 12.5px;
      font-weight: 600;
      cursor: pointer;
      border: 1px solid var(--border-strong);
      background: var(--bg-surface);
      color: var(--text-main);
      transition: all 0.15s ease;
    }}

    .btn:hover {{
      background: var(--bg-muted);
    }}

    .btn-primary {{
      background: var(--brand-blue);
      color: #ffffff;
      border-color: var(--brand-blue);
    }}

    .btn-primary:hover {{
      background: var(--brand-blue-dark);
    }}

    .btn-sm {{
      padding: 4px 8px;
      font-size: 11.5px;
    }}

    /* KPI Strip */
    .kpi-strip {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(135px, 1fr));
      gap: 8px;
      padding-top: 6px;
      border-top: 1px solid var(--border-color);
    }}

    .kpi-box {{
      background: var(--bg-muted);
      border-radius: var(--radius-sm);
      padding: 7px 11px;
      display: flex;
      flex-direction: column;
    }}

    .kpi-label {{
      font-size: 10.5px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--text-muted);
      font-weight: 600;
    }}

    .kpi-value {{
      font-size: 16px;
      font-weight: 700;
      color: var(--text-main);
    }}

    /* Navigation Tabs */
    .tabs-bar {{
      display: flex;
      gap: 6px;
      border-bottom: 1px solid var(--border-color);
      padding-bottom: 2px;
      overflow-x: auto;
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
      border-radius: var(--radius-sm) var(--radius-sm) 0 0;
      white-space: nowrap;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }}

    .tab-btn:hover {{
      color: var(--text-main);
      background: var(--bg-muted);
    }}

    .tab-btn.active {{
      color: var(--brand-blue);
      border-bottom-color: var(--brand-blue);
      background: var(--bg-surface);
    }}

    /* Tab 1: Split Tree + Inspector Layout */
    .workbench-grid {{
      display: grid;
      grid-template-columns: 370px 1fr;
      gap: 12px;
      align-items: start;
    }}

    @media (max-width: 840px) {{
      .workbench-grid {{
        grid-template-columns: 1fr;
      }}
    }}

    .panel-card {{
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      box-shadow: var(--shadow-sm);
      overflow: hidden;
    }}

    .panel-header {{
      padding: 10px 14px;
      border-bottom: 1px solid var(--border-color);
      background: var(--bg-muted);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      flex-wrap: wrap;
    }}

    .panel-title {{
      font-size: 12.5px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.03em;
      color: var(--text-secondary);
    }}

    .filter-toolbar {{
      padding: 8px 12px;
      border-bottom: 1px solid var(--border-color);
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
      align-items: center;
    }}

    .filter-toolbar input[type="search"] {{
      flex: 1;
      min-width: 130px;
      padding: 5px 9px;
      border: 1px solid var(--border-strong);
      border-radius: var(--radius-sm);
      font-size: 12px;
      background: var(--bg-surface);
      color: var(--text-main);
    }}

    /* Tree List */
    .tree-container {{
      max-height: 580px;
      overflow-y: auto;
      padding: 8px;
    }}

    .tree-node-wrapper {{
      display: flex;
      flex-direction: column;
    }}

    .tree-children {{
      margin-left: 16px;
      padding-left: 10px;
      border-left: 1.5px dashed var(--border-strong);
    }}

    .claim-node {{
      display: flex;
      flex-direction: column;
      gap: 3px;
      padding: 8px 10px;
      margin-bottom: 5px;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-color);
      background: var(--bg-surface);
      cursor: pointer;
      transition: all 0.12s ease;
    }}

    .claim-node:hover {{
      border-color: var(--brand-blue);
      background: var(--bg-accent);
    }}

    .claim-node.selected {{
      border-color: var(--brand-blue);
      border-width: 2px;
      background: var(--bg-accent);
    }}

    .claim-node.independent {{
      border-left: 4px solid var(--brand-green);
    }}

    .claim-node.dependent {{
      border-left: 4px solid var(--brand-blue);
    }}

    .claim-node-top {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 6px;
    }}

    .claim-num-label {{
      font-weight: 700;
      font-size: 12.5px;
      color: var(--text-main);
      display: inline-flex;
      align-items: center;
      gap: 5px;
    }}

    .badge {{
      font-size: 10px;
      font-weight: 700;
      padding: 1px 6px;
      border-radius: 999px;
      text-transform: uppercase;
    }}

    .badge-indep {{
      background: var(--bg-indep);
      color: var(--brand-green);
    }}

    .badge-dep {{
      background: var(--bg-accent);
      color: var(--brand-blue);
    }}

    .badge-cat {{
      background: var(--bg-muted);
      color: var(--text-secondary);
    }}

    .claim-preview-text {{
      font-size: 11.5px;
      color: var(--text-muted);
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }}

    /* Right Pane: Claim Scope Inspector */
    .inspector-body {{
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }}

    .chain-breadcrumbs {{
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 6px;
      padding: 10px 12px;
      background: var(--bg-muted);
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-color);
    }}

    .chain-step {{
      padding: 3px 9px;
      border-radius: var(--radius-sm);
      font-size: 12px;
      font-weight: 600;
      background: var(--bg-surface);
      border: 1px solid var(--border-strong);
      cursor: pointer;
    }}

    .chain-step.active {{
      background: var(--brand-blue);
      color: #ffffff;
      border-color: var(--brand-blue);
    }}

    .section-box {{
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}

    .section-heading {{
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--text-muted);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}

    .limitation-card {{
      padding: 10px 12px;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-color);
      background: var(--bg-surface);
      display: flex;
      gap: 10px;
      align-items: flex-start;
    }}

    .limitation-card.preamble {{
      background: var(--bg-muted);
      border-left: 3px solid var(--brand-purple);
    }}

    .limitation-card.limitation {{
      border-left: 3px solid var(--brand-blue);
    }}

    .lim-id {{
      font-family: var(--font-mono);
      font-size: 11.5px;
      font-weight: 700;
      color: var(--brand-blue);
      min-width: 48px;
      padding-top: 1px;
    }}

    .lim-text {{
      font-size: 13.5px;
      color: var(--text-main);
      flex: 1;
    }}

    .inherited-block {{
      padding: 10px 12px;
      border-radius: var(--radius-sm);
      border: 1px dashed var(--border-strong);
      background: var(--bg-muted);
      font-size: 12.5px;
      color: var(--text-secondary);
      margin-bottom: 6px;
    }}

    .inherited-block.current {{
      border: 1.5px solid var(--brand-blue);
      background: var(--bg-accent);
      color: var(--text-main);
      font-weight: 500;
    }}

    mark.hl {{
      background: #fef08a;
      color: #713f12;
      padding: 0 3px;
      border-radius: 3px;
      font-weight: 600;
    }}

    .kw-trans {{
      font-weight: 700;
      color: var(--brand-purple);
      text-decoration: underline;
      text-underline-offset: 2px;
    }}

    /* Tab 2: Side-by-Side Comparator */
    .compare-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }}

    @media (max-width: 780px) {{
      .compare-grid {{
        grid-template-columns: 1fr;
      }}
    }}

    .shared-terms-bar {{
      padding: 10px 14px;
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      align-items: center;
    }}

    .term-chip {{
      font-size: 11.5px;
      font-family: var(--font-mono);
      padding: 2px 8px;
      border-radius: 999px;
      background: var(--bg-indep);
      color: var(--brand-green);
      border: 1px solid rgba(5, 150, 105, 0.25);
      cursor: pointer;
    }}

    /* Tab 3: Claim Chart Matrix */
    .chart-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 12.5px;
    }}

    .chart-table th,
    .chart-table td {{
      border: 1px solid var(--border-color);
      padding: 8px 10px;
      text-align: left;
      vertical-align: top;
    }}

    .chart-table th {{
      background: var(--bg-muted);
      font-weight: 700;
      color: var(--text-secondary);
    }}

    .chart-note-input {{
      width: 100%;
      min-height: 44px;
      padding: 6px;
      border: 1px solid var(--border-strong);
      border-radius: 4px;
      font-family: var(--font-sans);
      font-size: 12px;
      background: var(--bg-surface);
      color: var(--text-main);
    }}

    /* Toast / Status Banner */
    .toast-banner {{
      position: fixed;
      bottom: 14px;
      right: 14px;
      background: #0f172a;
      color: #ffffff;
      padding: 8px 14px;
      border-radius: var(--radius-sm);
      font-size: 12px;
      box-shadow: var(--shadow-md);
      z-index: 1000;
      display: none;
    }}
  </style>
</head>
<body>
  <div class="app-shell" id="appRoot">
    <!-- Header Card -->
    <div class="header-card">
      <div class="header-top">
        <div>
          <div class="brand-row">
            <span class="mcp-badge">⚡ MCP App • ui://google-patents/claim-tree</span>
            <span class="pub-badge" id="hdrPubNum">Loading...</span>
            <span class="status-pill" id="hdrKindBadge">PATENT</span>
          </div>
          <h1 class="patent-title" id="hdrTitle">Google Patents Interactive Claim Tree & Scope Inspector</h1>
          <div class="patent-subtitle" id="hdrSubtitle">
            <span>Waiting for tool result or enter a patent publication number to inspect...</span>
          </div>
        </div>

        <div class="loader-bar">
          <input
            type="text"
            class="input-box"
            id="patentInput"
            placeholder="e.g. US8000000B2"
            title="Enter any Patent ID to fetch via MCP tools/call"
          />
          <button class="btn btn-primary" id="loadPatentBtn" onclick="loadPrimaryPatentFromInput()">
            🔍 Load Patent
          </button>
          <button class="btn" onclick="openGooglePatentsPage()" title="Open on patents.google.com">
            ↗ Google Patents
          </button>
        </div>
      </div>

      <!-- KPI Summary Strip -->
      <div class="kpi-strip">
        <div class="kpi-box">
          <span class="kpi-label">Total Claims</span>
          <span class="kpi-value" id="kpiTotalClaims">0</span>
        </div>
        <div class="kpi-box">
          <span class="kpi-label">Independent Claims</span>
          <span class="kpi-value" id="kpiIndepClaims" style="color: var(--brand-green)">0</span>
        </div>
        <div class="kpi-box">
          <span class="kpi-label">Dependent Claims</span>
          <span class="kpi-value" id="kpiDepClaims" style="color: var(--brand-blue)">0</span>
        </div>
        <div class="kpi-box">
          <span class="kpi-label">Max Chain Depth</span>
          <span class="kpi-value" id="kpiMaxDepth">0</span>
        </div>
        <div class="kpi-box">
          <span class="kpi-label">Priority / Filing Date</span>
          <span class="kpi-value" id="kpiPriorityDate" style="font-size: 13.5px">—</span>
        </div>
      </div>
    </div>

    <!-- Navigation Tabs -->
    <div class="tabs-bar">
      <button class="tab-btn active" data-tab="tree" onclick="switchTab('tree')">
        🌳 1. Claim Dependency Tree & Scope Inspector
      </button>
      <button class="tab-btn" data-tab="compare" onclick="switchTab('compare')">
        ⚖️ 2. Side-by-Side Claim Comparator
      </button>
      <button class="tab-btn" data-tab="chart" onclick="switchTab('chart')">
        📋 3. Claim Construction Chart Matrix
      </button>
      <button class="tab-btn" data-tab="dossier" onclick="switchTab('dossier')">
        📄 4. Patent Dossier & Metadata
      </button>
    </div>

    <!-- TAB 1: Dependency Tree & Scope Inspector -->
    <div id="tab-tree" class="tab-view">
      <div class="workbench-grid">
        <!-- Left Column: Interactive Dependency Tree -->
        <div class="panel-card">
          <div class="panel-header">
            <span class="panel-title">Claim Hierarchy</span>
            <div style="display: flex; gap: 4px">
              <button class="btn btn-sm" id="filterIndepBtn" onclick="toggleIndependentOnly()">
                Independent Only: OFF
              </button>
              <button class="btn btn-sm" onclick="expandCollapseAll()">
                Expand/Collapse
              </button>
            </div>
          </div>
          <div class="filter-toolbar">
            <input
              type="search"
              id="claimSearchInput"
              placeholder="Filter claims or highlight keywords (e.g. camera, telemetry)..."
              oninput="onSearchKeywordChange()"
            />
          </div>
          <div class="tree-container" id="claimTreeList"></div>
        </div>

        <!-- Right Column: Selected Claim Scope Inspector -->
        <div class="panel-card">
          <div class="panel-header">
            <span class="panel-title" id="inspectorHeaderTitle">Claim Inspector</span>
            <div style="display: flex; gap: 6px; flex-wrap: wrap">
              <button class="btn btn-sm" onclick="copySelectedClaimText()">📋 Copy Claim</button>
              <button class="btn btn-sm btn-primary" onclick="askAiAboutSelectedClaim()">
                ✨ Ask AI to Analyze Claim
              </button>
            </div>
          </div>
          <div class="inspector-body" id="claimInspectorBody"></div>
        </div>
      </div>
    </div>

    <!-- TAB 2: Side-by-Side Claim Comparator -->
    <div id="tab-compare" class="tab-view" style="display: none">
      <div class="panel-card" style="margin-bottom: 12px">
        <div class="panel-header">
          <span class="panel-title">Side-by-Side Patent Claim Comparison (FTO & Prior Art)</span>
          <div class="loader-bar">
            <input
              type="text"
              class="input-box"
              id="comparePatentInput"
              placeholder="Compare with (e.g. US10000000B2)"
              value="US10000000B2"
            />
            <button class="btn btn-primary btn-sm" onclick="loadComparisonPatent()">
              ⚡ Fetch & Compare via MCP
            </button>
            <button class="btn btn-sm" onclick="askAiToCompareClaims()">
              ✨ Ask AI for Claim Diff Analysis
            </button>
          </div>
        </div>
        <div class="shared-terms-bar" id="sharedTermsBar">
          <span style="font-size: 12px; color: var(--text-muted)">
            Load a comparison patent above to compute overlapping technical vocabulary and compare independent claims side-by-side.
          </span>
        </div>
      </div>

      <div class="compare-grid">
        <div class="panel-card">
          <div class="panel-header">
            <span class="panel-title" id="cmpLeftTitle">Primary Patent</span>
            <select id="cmpLeftClaimSelect" class="input-box" style="min-width: 110px" onchange="renderComparisonPane()"></select>
          </div>
          <div class="inspector-body" id="cmpLeftBody"></div>
        </div>

        <div class="panel-card">
          <div class="panel-header">
            <span class="panel-title" id="cmpRightTitle">Comparison Patent</span>
            <select id="cmpRightClaimSelect" class="input-box" style="min-width: 110px" onchange="renderComparisonPane()"></select>
          </div>
          <div class="inspector-body" id="cmpRightBody"></div>
        </div>
      </div>
    </div>

    <!-- TAB 3: Claim Construction & Element Chart Matrix -->
    <div id="tab-chart" class="tab-view" style="display: none">
      <div class="panel-card">
        <div class="panel-header">
          <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap">
            <span class="panel-title">Claim Element Chart</span>
            <select id="chartClaimSelect" class="input-box" onchange="renderClaimChartMatrix()"></select>
          </div>
          <div style="display: flex; gap: 6px">
            <button class="btn btn-sm" onclick="exportClaimChartMarkdown()">📋 Copy as Markdown Table</button>
            <button class="btn btn-sm btn-primary" onclick="sendClaimChartToAi()">
              ✨ Send Claim Chart to AI
            </button>
          </div>
        </div>
        <div style="padding: 14px; overflow-x: auto" id="claimChartContainer"></div>
      </div>
    </div>

    <!-- TAB 4: Patent Dossier & Metadata -->
    <div id="tab-dossier" class="tab-view" style="display: none">
      <div class="panel-card">
        <div class="panel-header">
          <span class="panel-title">Patent Bibliographic Dossier & Abstract</span>
        </div>
        <div class="inspector-body" id="dossierBody"></div>
      </div>
    </div>
  </div>

  <div class="toast-banner" id="toastBanner"></div>

  <script>
    // =========================================================================
    // 1. State & Initial Data Hydration
    // =========================================================================
    const INITIAL_BOOTSTRAP = {initial_json};

    const state = {{
      primaryPatent: INITIAL_BOOTSTRAP.primaryPatent || null,
      comparisonPatent: INITIAL_BOOTSTRAP.comparisonPatent || null,
      selectedClaimNumber: 1,
      activeTab: "tree",
      independentOnly: false,
      collapsedNodes: new Set(),
      searchKeyword: "",
      chartNotes: {{}},
      chartStatus: {{}},
      mcpInitialized: false,
      nextRpcId: 100,
      pendingRpc: new Map(),
    }};

    function showToast(msg) {{
      const el = document.getElementById("toastBanner");
      if (!el) return;
      el.textContent = msg;
      el.style.display = "block";
      clearTimeout(window.__toastTimer);
      window.__toastTimer = setTimeout(() => {{
        el.style.display = "none";
      }}, 3200);
    }}

    function escapeHtml(str) {{
      return String(str ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }}

    // =========================================================================
    // 2. Client-Side Claim Dependency Parser Fallback
    //    (If raw `get_patent_details` JSON arrives without pre-parsed `claims_tree`)
    // =========================================================================
    function ensureClaimsTree(patent) {{
      if (!patent || typeof patent !== "object") return null;
      if (patent.claims_tree && Array.isArray(patent.claims_tree.claims) && patent.claims_tree.claims.length > 0) {{
        return patent;
      }}
      const raw = patent.claims || "";
      const text = String(raw)
        .replace(/&#39;/g, "'")
        .replace(/&quot;/g, '"')
        .replace(/&amp;/g, "&")
        .replace(/^(?:The invention claimed is|What is claimed is|We claim|I claim)\\s*:?\\s*/i, "")
        .trim();

      if (!text) {{
        patent.claims_tree = {{
          total_claims: 0,
          independent_count: 0,
          dependent_count: 0,
          max_depth: 0,
          root_claim_numbers: [],
          claims: [],
        }};
        return patent;
      }}

      const parts = text.split(/(?:^|\\n)\\s*(\\d{{1,3}})\\s*[\\.\\)]\\s+/m);
      const rawClaims = [];
      if (parts.length >= 3) {{
        for (let i = 1; i < parts.length - 1; i += 2) {{
          const num = parseInt(parts[i], 10);
          const body = (parts[i + 1] || "").trim();
          if (!isNaN(num) && body) rawClaims.push({{ number: num, text: body }});
        }}
      }} else {{
        rawClaims.push({{ number: 1, text }});
      }}

      const validNums = new Set(rawClaims.map((c) => c.number));
      const nodesByNum = {{}};

      rawClaims.forEach((item) => {{
        const parents = [];
        const mRange = item.text.match(/\\bclaims?\\s+(\\d+)\\s*(?:to|through|-)\\s*(\\d+)\\b/i);
        if (mRange) {{
          const s = parseInt(mRange[1], 10), e = parseInt(mRange[2], 10);
          for (let n = s; n <= e && n - s <= 25; n++) {{
            if (n !== item.number && validNums.has(n)) parents.push(n);
          }}
        }}
        const reSingle = /\\bclaim\\s+(\\d+)\\b/gi;
        let m;
        while ((m = reSingle.exec(item.text)) !== null) {{
          const n = parseInt(m[1], 10);
          if (n !== item.number && validNums.has(n) && !parents.includes(n)) {{
            parents.push(n);
          }}
        }}

        const clauses = item.text.split(/;\\s*/).map((s) => s.trim()).filter(Boolean);
        const limitations = clauses.map((c, idx) => ({{
          id: `${{item.number}}.${{idx === 0 ? "pre" : String.fromCharCode(96 + idx)}}`,
          label: `[${{item.number}}.${{idx === 0 ? "pre" : String.fromCharCode(96 + idx)}}]`,
          type: idx === 0 ? "preamble" : "limitation",
          text: c.endsWith(".") || c.endsWith(";") ? c : c + ";",
        }}));

        const head = item.text.slice(0, 200).toLowerCase();
        const category = head.includes("method") || head.includes("process")
          ? "Method / Process"
          : head.includes("computer-readable") || head.includes("medium")
          ? "Computer-Readable Medium"
          : "System / Apparatus";

        nodesByNum[item.number] = {{
          number: item.number,
          text: item.text,
          is_independent: parents.length === 0,
          parent_claims: parents,
          primary_parent: parents[0] || null,
          children: [],
          category,
          preamble: clauses[0] || item.text.slice(0, 140),
          limitations,
          word_count: item.text.split(/\\s+/).length,
          depth: 0,
          ancestor_chain: [item.number],
        }};
      }});

      const roots = [];
      Object.values(nodesByNum).forEach((node) => {{
        if (node.primary_parent && nodesByNum[node.primary_parent]) {{
          nodesByNum[node.primary_parent].children.push(node.number);
        }} else {{
          roots.push(node.number);
        }}
      }});

      let maxDepth = 0;
      Object.values(nodesByNum).forEach((node) => {{
        const chain = [node.number];
        let curr = node.primary_parent;
        const seen = new Set([node.number]);
        while (curr && nodesByNum[curr] && !seen.has(curr)) {{
          seen.add(curr);
          chain.push(curr);
          curr = nodesByNum[curr].primary_parent;
        }}
        chain.reverse();
        node.ancestor_chain = chain;
        node.depth = chain.length - 1;
        if (node.depth > maxDepth) maxDepth = node.depth;
      }});

      const claimsArr = Object.keys(nodesByNum)
        .map((k) => nodesByNum[k])
        .sort((a, b) => a.number - b.number);
      const indepCount = claimsArr.filter((c) => c.is_independent).length;

      patent.claims_tree = {{
        total_claims: claimsArr.length,
        independent_count: indepCount,
        dependent_count: claimsArr.length - indepCount,
        max_depth: maxDepth,
        root_claim_numbers: roots,
        claims: claimsArr,
      }};
      return patent;
    }}

    // =========================================================================
    // 3. Official MCP Apps JSON-RPC 2.0 over postMessage Bridge
    // =========================================================================
    function sendMcpJsonRpcRequest(method, params) {{
      return new Promise((resolve, reject) => {{
        const id = ++state.nextRpcId;
        state.pendingRpc.set(id, {{ resolve, reject }});
        window.parent.postMessage({{ jsonrpc: "2.0", id, method, params }}, "*");
        setTimeout(() => {{
          if (state.pendingRpc.has(id)) {{
            state.pendingRpc.delete(id);
            reject(new Error(`MCP RPC timeout for ${{method}}`));
          }}
        }}, 12000);
      }});
    }}

    function sendMcpNotification(method, params = {{}}) {{
      if (window.parent && window.parent !== window) {{
        window.parent.postMessage({{ jsonrpc: "2.0", method, params }}, "*");
      }}
    }}

    function extractPatentPayloadFromToolResult(resultObj) {{
      if (!resultObj || typeof resultObj !== "object") return null;

      // 1. Check structuredContent first (standard MCP Apps)
      if (resultObj.structuredContent && typeof resultObj.structuredContent === "object") {{
        const sc = resultObj.structuredContent;
        if (sc.primaryPatent) return sc;
        if (sc.publication_number || sc.claims || sc.title) return sc;
        if (typeof sc.result === "string") {{
          try {{
            return JSON.parse(sc.result);
          }} catch (_) {{}}
        }}
      }}

      // 2. Check content[0].text JSON
      if (Array.isArray(resultObj.content)) {{
        for (const block of resultObj.content) {{
          if (block && block.type === "text" && typeof block.text === "string") {{
            try {{
              const parsed = JSON.parse(block.text);
              if (parsed && (parsed.publication_number || parsed.primaryPatent || parsed.claims || parsed.title)) {{
                return parsed;
              }}
            }} catch (_) {{}}
          }}
        }}
      }}

      // 3. Direct object fallback
      if (resultObj.publication_number || resultObj.primaryPatent || resultObj.claims) {{
        return resultObj;
      }}
      return null;
    }}

    window.addEventListener("message", (event) => {{
      const data = event.data;
      if (!data || typeof data !== "object" || data.jsonrpc !== "2.0") return;

      // Handle responses to our outbound requests (`ui/initialize`, `tools/call`, etc.)
      if (data.id !== undefined && state.pendingRpc.has(data.id)) {{
        const {{ resolve, reject }} = state.pendingRpc.get(data.id);
        state.pendingRpc.delete(data.id);
        if (data.error) reject(data.error);
        else resolve(data.result);
        return;
      }}

      // Handle incoming Host -> App notifications
      const method = data.method;
      const params = data.params || {{}};

      if (method === "ui/notifications/tool-input" || method === "ui/notifications/tool-input-partial") {{
        const args = params.arguments || {{}};
        const pid = args.patent_url_or_id || args.patent_id || "";
        if (pid) {{
          document.getElementById("patentInput").value = pid;
        }}
      }} else if (method === "ui/notifications/tool-result") {{
        const payload = extractPatentPayloadFromToolResult(params);
        if (payload) {{
          if (payload.primaryPatent) {{
            state.primaryPatent = ensureClaimsTree(payload.primaryPatent);
            if (payload.comparisonPatent) {{
              state.comparisonPatent = ensureClaimsTree(payload.comparisonPatent);
            }}
          }} else {{
            state.primaryPatent = ensureClaimsTree(payload);
          }}
          if (state.primaryPatent?.claims_tree?.claims?.length) {{
            state.selectedClaimNumber = state.primaryPatent.claims_tree.claims[0].number;
          }}
          renderAll();
          showToast(`Loaded ${{state.primaryPatent?.publication_number || "patent"}} via MCP tool-result`);
        }}
      }} else if (method === "ui/notifications/host-context-changed") {{
        if (params.theme === "dark" || params.theme === "light") {{
          document.documentElement.setAttribute("data-theme", params.theme);
        }}
      }}
    }});

    async function initMcpAppBridge() {{
      if (window.parent && window.parent !== window) {{
        try {{
          const initRes = await sendMcpJsonRpcRequest("ui/initialize", {{
            protocolVersion: "2025-06-18",
            appInfo: {{
              name: "Google Patents Claim Tree & Scope Inspector",
              version: "1.0.0",
            }},
            appCapabilities: {{}},
          }});
          state.mcpInitialized = true;
          if (initRes?.hostContext?.theme) {{
            document.documentElement.setAttribute("data-theme", initRes.hostContext.theme);
          }}
          sendMcpNotification("ui/notifications/initialized", {{}});
        }} catch (_) {{
          // Host may not require explicit handshake; still send initialized notification
          sendMcpNotification("ui/notifications/initialized", {{}});
        }}
      }}

      // Observe size changes and notify host
      if (typeof ResizeObserver !== "undefined") {{
        const ro = new ResizeObserver(() => {{
          sendMcpNotification("ui/notifications/size-changed", {{
            width: document.documentElement.scrollWidth,
            height: document.documentElement.scrollHeight,
          }});
        }});
        ro.observe(document.body);
      }}
    }}

    // Calls `get_patent_details` via MCP `tools/call` (with local HTTP fallback if standalone)
    async function fetchPatentViaMcpOrHttp(patentId) {{
      const cleanId = (patentId || "").trim();
      if (!cleanId) return null;

      // 1. Try official MCP Apps `tools/call` over postMessage
      if (window.parent && window.parent !== window) {{
        try {{
          const rpcRes = await sendMcpJsonRpcRequest("tools/call", {{
            name: "get_patent_details",
            arguments: {{
              patent_url_or_id: cleanId,
              include_claims: true,
              include_description: false,
            }},
          }});
          const extracted = extractPatentPayloadFromToolResult(rpcRes);
          if (extracted && !extracted.error) {{
            return ensureClaimsTree(extracted);
          }}
        }} catch (_) {{
          // Fall through to HTTP endpoint if host doesn't proxy tools/call
        }}
      }}

      // 2. Fallback to built-in HTTP helper endpoint `/apps/api/patent-details`
      try {{
        const apiBase = (window.location.origin && window.location.origin.startsWith("http") && !window.location.origin.includes("usercontent"))
          ? window.location.origin
          : (INITIAL_BOOTSTRAP.serverBase || "");
        const resp = await fetch(`${{apiBase}}/apps/api/patent-details?patent_id=${{encodeURIComponent(cleanId)}}`);
        if (resp.ok) {{
          const data = await resp.json();
          if (data && !data.error) return ensureClaimsTree(data);
        }}
      }} catch (_) {{}}

      return null;
    }}

    // =========================================================================
    // 4. UI Actions & Rendering
    // =========================================================================
    async function loadPrimaryPatentFromInput() {{
      const pid = document.getElementById("patentInput").value.trim();
      if (!pid) return;
      const btn = document.getElementById("loadPatentBtn");
      btn.textContent = "⏳ Loading...";
      const data = await fetchPatentViaMcpOrHttp(pid);
      btn.textContent = "🔍 Load Patent";
      if (data) {{
        state.primaryPatent = data;
        state.selectedClaimNumber = data.claims_tree?.claims?.[0]?.number || 1;
        renderAll();
        showToast(`Loaded ${{data.publication_number || pid}}`);
      }} else {{
        showToast(`Could not load patent ${{pid}}`);
      }}
    }}

    async function loadComparisonPatent() {{
      const pid = document.getElementById("comparePatentInput").value.trim();
      if (!pid) return;
      showToast(`Fetching comparison patent ${{pid}}...`);
      const data = await fetchPatentViaMcpOrHttp(pid);
      if (data) {{
        state.comparisonPatent = data;
        renderComparisonTab();
        showToast(`Compared with ${{data.publication_number || pid}}`);
      }} else {{
        showToast(`Could not load comparison patent ${{pid}}`);
      }}
    }}

    function switchTab(tabId) {{
      state.activeTab = tabId;
      document.querySelectorAll(".tab-btn").forEach((btn) => {{
        btn.classList.toggle("active", btn.getAttribute("data-tab") === tabId);
      }});
      ["tree", "compare", "chart", "dossier"].forEach((id) => {{
        const el = document.getElementById(`tab-${{id}}`);
        if (el) el.style.display = id === tabId ? "block" : "none";
      }});
      if (tabId === "compare") renderComparisonTab();
      if (tabId === "chart") renderClaimChartMatrix();
      if (tabId === "dossier") renderDossierTab();
    }}

    function toggleIndependentOnly() {{
      state.independentOnly = !state.independentOnly;
      const btn = document.getElementById("filterIndepBtn");
      btn.textContent = `Independent Only: ${{state.independentOnly ? "ON" : "OFF"}}`;
      renderClaimTreeList();
    }}

    function expandCollapseAll() {{
      const claims = state.primaryPatent?.claims_tree?.claims || [];
      if (state.collapsedNodes.size > 0) {{
        state.collapsedNodes.clear();
      }} else {{
        claims.forEach((c) => {{
          if (c.children && c.children.length > 0) state.collapsedNodes.add(c.number);
        }});
      }}
      renderClaimTreeList();
    }}

    function onSearchKeywordChange() {{
      state.searchKeyword = (document.getElementById("claimSearchInput").value || "").trim();
      renderClaimTreeList();
      renderClaimInspector();
    }}

    function highlightText(rawText, keyword) {{
      let htmlStr = escapeHtml(rawText);
      // Highlight transitional patent keywords
      htmlStr = htmlStr.replace(
        /\\b(comprising|wherein|configured to|consisting of|further comprising|whereby|plurality of)\\b/gi,
        '<span class="kw-trans">$1</span>'
      );
      if (keyword && keyword.length >= 2) {{
        const safeKw = keyword.replace(/[.*+?^${{}}()|[\\]\\\\]/g, "\\\\$&");
        const re = new RegExp(`(${{safeKw}})`, "gi");
        htmlStr = htmlStr.replace(re, '<mark class="hl">$1</mark>');
      }}
      return htmlStr;
    }}

    function renderHeader() {{
      const p = state.primaryPatent;
      if (!p) return;
      const tree = p.claims_tree || {{}};
      document.getElementById("hdrPubNum").textContent = p.publication_number || p.ucid || "PATENT";
      document.getElementById("hdrKindBadge").textContent = `${{p.country_code || "US"}} • ${{p.kind_code || "GRANT"}}`;
      document.getElementById("hdrTitle").textContent = p.title || "Untitled Patent";
      document.getElementById("patentInput").value = p.publication_number || p.ucid || "";

      const assignees = (p.assignees || []).join(", ") || "Unassigned";
      const inventors = (p.inventors || []).slice(0, 4).join(", ") || "—";
      document.getElementById("hdrSubtitle").innerHTML = `
        <span>🏢 <strong>Assignee:</strong> ${{escapeHtml(assignees)}}</span>
        <span>🔬 <strong>Inventors:</strong> ${{escapeHtml(inventors)}}</span>
        <span>📅 <strong>Granted/Pub:</strong> ${{escapeHtml(p.grant_date || p.publication_date || "—")}}</span>
      `;

      document.getElementById("kpiTotalClaims").textContent = tree.total_claims ?? 0;
      document.getElementById("kpiIndepClaims").textContent = tree.independent_count ?? 0;
      document.getElementById("kpiDepClaims").textContent = tree.dependent_count ?? 0;
      document.getElementById("kpiMaxDepth").textContent = tree.max_depth ?? 0;
      document.getElementById("kpiPriorityDate").textContent = p.priority_date || p.filing_date || "—";
    }}

    function selectClaim(claimNum) {{
      state.selectedClaimNumber = claimNum;
      renderClaimTreeList();
      renderClaimInspector();
    }}

    function toggleNodeCollapse(event, claimNum) {{
      event.stopPropagation();
      if (state.collapsedNodes.has(claimNum)) state.collapsedNodes.delete(claimNum);
      else state.collapsedNodes.add(claimNum);
      renderClaimTreeList();
    }}

    function renderClaimTreeList() {{
      const container = document.getElementById("claimTreeList");
      const p = state.primaryPatent;
      const claims = p?.claims_tree?.claims || [];
      if (!claims.length) {{
        container.innerHTML = `<div style="padding:16px;color:var(--text-muted)">No claims found for this patent.</div>`;
        return;
      }}

      const byNum = {{}};
      claims.forEach((c) => (byNum[c.number] = c));
      const kw = state.searchKeyword.toLowerCase();

      function matchesFilter(c) {{
        if (state.independentOnly && !c.is_independent) return false;
        if (kw && !c.text.toLowerCase().includes(kw) && !String(c.number).includes(kw)) return false;
        return true;
      }}

      function renderNodeRecursive(claimNum) {{
        const c = byNum[claimNum];
        if (!c) return "";
        const hasChildren = Array.isArray(c.children) && c.children.length > 0;
        const isCollapsed = state.collapsedNodes.has(c.number);
        const showSelf = matchesFilter(c);

        const childrenHtml = (!isCollapsed && hasChildren)
          ? c.children.map((ch) => renderNodeRecursive(ch)).join("")
          : "";

        if (!showSelf && !childrenHtml) return "";

        const isSelected = c.number === state.selectedClaimNumber;
        const typeClass = c.is_independent ? "independent" : "dependent";
        const badgeHtml = c.is_independent
          ? `<span class="badge badge-indep">Indep</span>`
          : `<span class="badge badge-dep">→ Claim ${{c.primary_parent}}</span>`;

        const collapseBtn = hasChildren
          ? `<button class="btn btn-sm" style="padding:0 5px;font-size:10px" onclick="toggleNodeCollapse(event, ${{c.number}})">${{isCollapsed ? "▶ +" + c.children.length : "▼"}}</button>`
          : "";

        return `
          <div class="tree-node-wrapper">
            <div class="claim-node ${{typeClass}} ${{isSelected ? "selected" : ""}}" onclick="selectClaim(${{c.number}})">
              <div class="claim-node-top">
                <span class="claim-num-label">
                  ${{collapseBtn}}
                  Claim ${{c.number}}
                  ${{badgeHtml}}
                </span>
                <span class="badge badge-cat">${{escapeHtml(c.category || "Claim")}}</span>
              </div>
              <div class="claim-preview-text">${{highlightText(c.text, state.searchKeyword)}}</div>
            </div>
            ${{childrenHtml ? `<div class="tree-children">${{childrenHtml}}</div>` : ""}}
          </div>
        `;
      }}

      const roots = p.claims_tree.root_claim_numbers || claims.filter((c) => c.is_independent).map((c) => c.number);
      const htmlOut = roots.map((r) => renderNodeRecursive(r)).join("");
      container.innerHTML = htmlOut || `<div style="padding:14px;color:var(--text-muted)">No claims match filter "${{escapeHtml(state.searchKeyword)}}".</div>`;
    }}

    function renderClaimInspector() {{
      const body = document.getElementById("claimInspectorBody");
      const claims = state.primaryPatent?.claims_tree?.claims || [];
      const byNum = {{}};
      claims.forEach((c) => (byNum[c.number] = c));
      const selected = byNum[state.selectedClaimNumber] || claims[0];

      if (!selected) {{
        body.innerHTML = `<div style="color:var(--text-muted)">Select a claim from the tree on the left to inspect its full inherited scope and limitations.</div>`;
        return;
      }}

      document.getElementById("inspectorHeaderTitle").textContent =
        `Claim ${{selected.number}} (${{selected.is_independent ? "Independent" : "Dependent on Claim " + selected.primary_parent}}) • ${{selected.category}}`;

      const chain = selected.ancestor_chain || [selected.number];
      const breadcrumbsHtml = chain
        .map((num, idx) => {{
          const node = byNum[num];
          const label = idx === 0 ? `Claim ${{num}} (Root Independent)` : `Claim ${{num}}`;
          return `
            <span class="chain-step ${{num === selected.number ? "active" : ""}}" onclick="selectClaim(${{num}})">
              ${{label}}
            </span>
            ${{idx < chain.length - 1 ? `<span style="color:var(--text-muted)">→</span>` : ""}}
          `;
        }})
        .join("");

      const limitations = selected.limitations || [];
      const limitationsHtml = limitations
        .map(
          (lim) => `
          <div class="limitation-card ${{lim.type}}">
            <span class="lim-id">${{escapeHtml(lim.label)}}</span>
            <div class="lim-text">${{highlightText(lim.text, state.searchKeyword)}}</div>
          </div>
        `
        )
        .join("");

      // Build combined inherited chain view if dependent claim
      let inheritedHtml = "";
      if (chain.length > 1) {{
        inheritedHtml = `
          <div class="section-box">
            <div class="section-heading">
              <span>🔗 Combined Inherited Claim Scope (${{chain.length}} Claims Merged)</span>
              <span style="font-size:11px;font-weight:500">Includes all parent limitations required for infringement/validity</span>
            </div>
            ${{chain
              .map((num) => {{
                const cNode = byNum[num];
                if (!cNode) return "";
                const isCurr = num === selected.number;
                return `
                  <div class="inherited-block ${{isCurr ? "current" : ""}}">
                    <div style="font-weight:700;margin-bottom:3px;font-size:11.5px;color:var(--brand-blue)">
                      ${{isCurr ? "★ Selected Claim " + num : "↑ Inherited from Parent Claim " + num}}
                    </div>
                    <div>${{highlightText(cNode.text, state.searchKeyword)}}</div>
                  </div>
                `;
              }})
              .join("")}}
          </div>
        `;
      }}

      const childrenLinks = (selected.children || [])
        .map(
          (chNum) =>
            `<button class="btn btn-sm" onclick="selectClaim(${{chNum}})">↓ Claim ${{chNum}}</button>`
        )
        .join(" ");

      body.innerHTML = `
        <div class="section-box">
          <div class="section-heading">
            <span>Dependency Lineage Path (Depth: ${{selected.depth}})</span>
            <span>${{selected.word_count}} words • ${{limitations.length}} clauses</span>
          </div>
          <div class="chain-breadcrumbs">${{breadcrumbsHtml}}</div>
        </div>

        <div class="section-box">
          <div class="section-heading">
            <span>🧩 Clause & Limitation Decomposition (Claim ${{selected.number}})</span>
          </div>
          ${{limitationsHtml}}
        </div>

        ${{inheritedHtml}}

        ${{
          childrenLinks
            ? `<div class="section-box">
                 <div class="section-heading"><span>Direct Dependent Child Claims (${{selected.children.length}})</span></div>
                 <div style="display:flex;gap:6px;flex-wrap:wrap">${{childrenLinks}}</div>
               </div>`
            : ""
        }}
      `;
    }}

    // =========================================================================
    // 5. Tab 2: Side-by-Side Claim Comparator
    // =========================================================================
    const STOP_WORDS = new Set([
      "the", "and", "for", "with", "that", "from", "wherein", "claim", "comprising",
      "configured", "based", "first", "second", "least", "one", "plurality", "system",
      "method", "apparatus", "device", "includes", "including", "having", "into",
      "each", "said", "associated", "when", "whereby", "further", "thereof", "which",
    ]);

    function extractTechnicalTerms(text) {{
      const words = String(text || "")
        .toLowerCase()
        .replace(/[^a-z0-9\\s-]/g, " ")
        .split(/\\s+/)
        .filter((w) => w.length >= 4 && !STOP_WORDS.has(w) && !/^\\d+$/.test(w));
      return new Set(words);
    }}

    function renderComparisonTab() {{
      const pLeft = state.primaryPatent;
      const pRight = state.comparisonPatent;

      const leftSel = document.getElementById("cmpLeftClaimSelect");
      const rightSel = document.getElementById("cmpRightClaimSelect");

      if (pLeft?.claims_tree?.claims) {{
        document.getElementById("cmpLeftTitle").textContent =
          `${{pLeft.publication_number || "Primary"}} (${{pLeft.claims_tree.total_claims}} claims)`;
        const prevLeft = leftSel.value;
        leftSel.innerHTML = pLeft.claims_tree.claims
          .map(
            (c) =>
              `<option value="${{c.number}}">Claim ${{c.number}} ${{c.is_independent ? "(Indep)" : "(Dep)"}}</option>`
          )
          .join("");
        if (prevLeft) leftSel.value = prevLeft;
      }}

      if (pRight?.claims_tree?.claims) {{
        document.getElementById("cmpRightTitle").textContent =
          `${{pRight.publication_number || "Comparison"}} (${{pRight.claims_tree.total_claims}} claims)`;
        const prevRight = rightSel.value;
        rightSel.innerHTML = pRight.claims_tree.claims
          .map(
            (c) =>
              `<option value="${{c.number}}">Claim ${{c.number}} ${{c.is_independent ? "(Indep)" : "(Dep)"}}</option>`
          )
          .join("");
        if (prevRight) rightSel.value = prevRight;
      }} else {{
        document.getElementById("cmpRightTitle").textContent = "Comparison Patent (Not Loaded)";
        rightSel.innerHTML = `<option value="">— Load patent above —</option>`;
      }}

      renderComparisonPane();
    }}

    function renderComparisonPane() {{
      const pLeft = state.primaryPatent;
      const pRight = state.comparisonPatent;
      const leftNum = parseInt(document.getElementById("cmpLeftClaimSelect").value || "1", 10);
      const rightNum = parseInt(document.getElementById("cmpRightClaimSelect").value || "1", 10);

      const leftClaim = (pLeft?.claims_tree?.claims || []).find((c) => c.number === leftNum) || pLeft?.claims_tree?.claims?.[0];
      const rightClaim = (pRight?.claims_tree?.claims || []).find((c) => c.number === rightNum) || pRight?.claims_tree?.claims?.[0];

      const leftTerms = leftClaim ? extractTechnicalTerms(leftClaim.text) : new Set();
      const rightTerms = rightClaim ? extractTechnicalTerms(rightClaim.text) : new Set();
      const shared = [...leftTerms].filter((t) => rightTerms.has(t)).slice(0, 24);

      const sharedBar = document.getElementById("sharedTermsBar");
      if (leftClaim && rightClaim) {{
        sharedBar.innerHTML = `
          <span style="font-size:12px;font-weight:700;color:var(--text-secondary)">
            🔗 Shared Technical Terms (${{shared.length}}):
          </span>
          ${{
            shared.length
              ? shared
                  .map(
                    (term) =>
                      `<span class="term-chip" onclick="highlightSharedTerm('${{term}}')">${{escapeHtml(term)}}</span>`
                  )
                  .join("")
              : `<span style="font-size:12px;color:var(--text-muted)">No overlapping technical terms in selected claims.</span>`
          }}
        `;
      }}

      function formatSideCard(patent, claimObj) {{
        if (!patent || !claimObj) {{
          return `<div style="color:var(--text-muted)">Click <strong>⚡ Fetch & Compare via MCP</strong> above to load a second patent for side-by-side comparison.</div>`;
        }}
        return `
          <div style="font-size:12px;color:var(--text-muted);margin-bottom:6px">
            <strong>${{escapeHtml(patent.title || "")}}</strong> • Assignee: ${{escapeHtml((patent.assignees || []).join(", ") || "—")}} • Priority: ${{escapeHtml(patent.priority_date || patent.filing_date || "—")}}
          </div>
          ${{(claimObj.limitations || [])
            .map(
              (lim) => `
              <div class="limitation-card ${{lim.type}}">
                <span class="lim-id">${{escapeHtml(lim.label)}}</span>
                <div class="lim-text">${{highlightText(lim.text, state.searchKeyword)}}</div>
              </div>
            `
            )
            .join("")}}
        `;
      }}

      document.getElementById("cmpLeftBody").innerHTML = formatSideCard(pLeft, leftClaim);
      document.getElementById("cmpRightBody").innerHTML = formatSideCard(pRight, rightClaim);
    }}

    function highlightSharedTerm(term) {{
      state.searchKeyword = term;
      document.getElementById("claimSearchInput").value = term;
      renderComparisonPane();
    }}

    // =========================================================================
    // 6. Tab 3: Claim Construction & Element Chart Matrix
    // =========================================================================
    function renderClaimChartMatrix() {{
      const p = state.primaryPatent;
      const claims = p?.claims_tree?.claims || [];
      const sel = document.getElementById("chartClaimSelect");
      if (!claims.length) return;

      if (!sel.options.length || sel.getAttribute("data-pub") !== p.publication_number) {{
        sel.setAttribute("data-pub", p.publication_number || "");
        sel.innerHTML = claims
          .map(
            (c) =>
              `<option value="${{c.number}}">Claim ${{c.number}} (${{c.is_independent ? "Independent" : "Dependent"}} - ${{c.limitations.length}} elements)</option>`
          )
          .join("");
        sel.value = String(state.selectedClaimNumber || claims[0].number);
      }}

      const chosenNum = parseInt(sel.value || "1", 10);
      const claim = claims.find((c) => c.number === chosenNum) || claims[0];
      const rowsHtml = (claim.limitations || [])
        .map((lim) => {{
          const key = `${{p.publication_number || "P"}}_${{lim.id}}`;
          const statusVal = state.chartStatus[key] || "Unmapped";
          const noteVal = state.chartNotes[key] || "";
          return `
            <tr>
              <td style="font-family:var(--font-mono);font-weight:700;width:85px;color:var(--brand-blue)">${{escapeHtml(lim.label)}}</td>
              <td>${{highlightText(lim.text, state.searchKeyword)}}</td>
              <td style="width:150px">
                <select class="input-box" style="min-width:130px" onchange="state.chartStatus['${{key}}']=this.value">
                  <option value="Unmapped" ${{statusVal === "Unmapped" ? "selected" : ""}}>⚪ Unmapped</option>
                  <option value="Disclosed / Present" ${{statusVal === "Disclosed / Present" ? "selected" : ""}}>🟢 Disclosed / Present</option>
                  <option value="Partial / Arguable" ${{statusVal === "Partial / Arguable" ? "selected" : ""}}>🟡 Partial / Arguable</option>
                  <option value="Missing / Novel" ${{statusVal === "Missing / Novel" ? "selected" : ""}}>🔴 Missing / Novel</option>
                </select>
              </td>
              <td style="width:260px">
                <textarea
                  class="chart-note-input"
                  placeholder="Prior art mapping or FTO notes..."
                  oninput="state.chartNotes['${{key}}']=this.value"
                >${{escapeHtml(noteVal)}}</textarea>
              </td>
            </tr>
          `;
        }})
        .join("");

      document.getElementById("claimChartContainer").innerHTML = `
        <table class="chart-table">
          <thead>
            <tr>
              <th>Element ID</th>
              <th>Patent Claim Limitation (${{escapeHtml(p.publication_number || "")}} — Claim ${{claim.number}})</th>
              <th>Assessment</th>
              <th>Analyst / Prior Art Mapping Notes</th>
            </tr>
          </thead>
          <tbody>${{rowsHtml}}</tbody>
        </table>
      `;
    }}

    function buildClaimChartMarkdown() {{
      const p = state.primaryPatent;
      const claims = p?.claims_tree?.claims || [];
      const chosenNum = parseInt(document.getElementById("chartClaimSelect").value || "1", 10);
      const claim = claims.find((c) => c.number === chosenNum) || claims[0];
      if (!claim) return "";

      const lines = [
        `### Claim Chart: ${{p.publication_number}} (${{p.title}}) — Claim ${{claim.number}}`,
        `| Element | Claim Limitation | Status | Analyst Notes |`,
        `| :--- | :--- | :--- | :--- |`,
      ];
      (claim.limitations || []).forEach((lim) => {{
        const key = `${{p.publication_number || "P"}}_${{lim.id}}`;
        const st = state.chartStatus[key] || "Unmapped";
        const nt = (state.chartNotes[key] || "—").replace(/\\n/g, " ");
        lines.push(`| **${{lim.label}}** | ${{lim.text.replace(/\\|/g, "\\\\|")}} | ${{st}} | ${{nt}} |`);
      }});
      return lines.join("\\n");
    }}

    function exportClaimChartMarkdown() {{
      const md = buildClaimChartMarkdown();
      if (!md) return;
      navigator.clipboard?.writeText(md);
      showToast("Copied Claim Chart Markdown table to clipboard!");
    }}

    function sendClaimChartToAi() {{
      const md = buildClaimChartMarkdown();
      if (!md) return;
      sendMcpJsonRpcRequest("ui/message", {{
        role: "user",
        content: [
          {{
            type: "text",
            text: `Please review this Claim Element Chart and provide a technical validity / FTO assessment:\\n\\n${{md}}`,
          }},
        ],
      }}).catch(() => {{}});
      showToast("Sent Claim Chart to AI chat host!");
    }}

    // =========================================================================
    // 7. Tab 4: Patent Dossier & Metadata
    // =========================================================================
    function renderDossierTab() {{
      const p = state.primaryPatent;
      const el = document.getElementById("dossierBody");
      if (!p) return;

      const cpcHtml = (p.cpc_codes || [])
        .map((c) => `<span class="term-chip" style="background:var(--bg-accent);color:var(--brand-blue)">${{escapeHtml(c)}}</span>`)
        .join(" ");

      el.innerHTML = `
        <div class="section-box">
          <div class="section-heading"><span>Abstract</span></div>
          <div style="padding:12px;background:var(--bg-muted);border-radius:var(--radius-sm);font-size:13.5px">
            ${{escapeHtml(p.abstract || "No abstract available.")}}
          </div>
        </div>
        <div class="section-box">
          <div class="section-heading"><span>Bibliographic & Legal Metadata</span></div>
          <div class="kpi-strip" style="border-top:none">
            <div class="kpi-box"><span class="kpi-label">Publication Number</span><span class="kpi-value" style="font-size:13.5px">${{escapeHtml(p.publication_number || "—")}}</span></div>
            <div class="kpi-box"><span class="kpi-label">Application Number</span><span class="kpi-value" style="font-size:13.5px">${{escapeHtml(p.application_number || "—")}}</span></div>
            <div class="kpi-box"><span class="kpi-label">Family ID</span><span class="kpi-value" style="font-size:13.5px">${{escapeHtml(p.family_id || "—")}}</span></div>
            <div class="kpi-box"><span class="kpi-label">Priority Date</span><span class="kpi-value" style="font-size:13.5px">${{escapeHtml(p.priority_date || "—")}}</span></div>
            <div class="kpi-box"><span class="kpi-label">Filing Date</span><span class="kpi-value" style="font-size:13.5px">${{escapeHtml(p.filing_date || "—")}}</span></div>
            <div class="kpi-box"><span class="kpi-label">Publication Date</span><span class="kpi-value" style="font-size:13.5px">${{escapeHtml(p.publication_date || "—")}}</span></div>
          </div>
        </div>
        <div class="section-box">
          <div class="section-heading"><span>CPC Classifications (${{(p.cpc_codes || []).length}})</span></div>
          <div style="display:flex;gap:6px;flex-wrap:wrap">${{cpcHtml || "—"}}</div>
        </div>
      `;
    }}

    // =========================================================================
    // 8. Helper Host Actions (`ui/message`, `ui/open-link`, Clipboard)
    // =========================================================================
    function copySelectedClaimText() {{
      const claims = state.primaryPatent?.claims_tree?.claims || [];
      const selected = claims.find((c) => c.number === state.selectedClaimNumber) || claims[0];
      if (!selected) return;
      navigator.clipboard?.writeText(`${{selected.number}}. ${{selected.text}}`);
      showToast(`Copied Claim ${{selected.number}} to clipboard`);
    }}

    function askAiAboutSelectedClaim() {{
      const p = state.primaryPatent;
      const claims = p?.claims_tree?.claims || [];
      const selected = claims.find((c) => c.number === state.selectedClaimNumber) || claims[0];
      if (!p || !selected) return;
      const prompt = `Analyze Claim ${{selected.number}} (${{selected.is_independent ? "Independent" : "Dependent"}}) of patent ${{p.publication_number}} ("${{p.title}}"). Identify its core inventive limitations, scope breadth, and potential design-around strategies:\\n\\nClaim ${{selected.number}}: ${{selected.text}}`;
      sendMcpJsonRpcRequest("ui/message", {{
        role: "user",
        content: [{{ type: "text", text: prompt }}],
      }}).catch(() => {{}});
      showToast(`Sent Claim ${{selected.number}} analysis prompt to AI host`);
    }}

    function askAiToCompareClaims() {{
      const p1 = state.primaryPatent;
      const p2 = state.comparisonPatent;
      if (!p1 || !p2) {{
        showToast("Load a comparison patent first!");
        return;
      }}
      const leftNum = parseInt(document.getElementById("cmpLeftClaimSelect").value || "1", 10);
      const rightNum = parseInt(document.getElementById("cmpRightClaimSelect").value || "1", 10);
      const prompt = `Compare Claim ${{leftNum}} of ${{p1.publication_number}} ("${{p1.title}}") against Claim ${{rightNum}} of ${{p2.publication_number}} ("${{p2.title}}"). Highlight overlapping limitations and key distinguishing elements.`;
      sendMcpJsonRpcRequest("ui/message", {{
        role: "user",
        content: [{{ type: "text", text: prompt }}],
      }}).catch(() => {{}});
      showToast("Sent Claim Comparison prompt to AI host");
    }}

    function openGooglePatentsPage() {{
      const pubId = (state.primaryPatent?.publication_number || state.primaryPatent?.ucid || "").replace(/-/g, "");
      if (!pubId) return;
      const apiBase = (window.location.origin && window.location.origin.startsWith("http") && !window.location.origin.includes("usercontent"))
        ? window.location.origin
        : (INITIAL_BOOTSTRAP.serverBase || "");
      const safeReaderUrl = (apiBase ? apiBase + "/apps/patent/" : "https://patents.google.com/patent/") + encodeURIComponent(pubId);
      window.open(safeReaderUrl, "_blank", "noopener,noreferrer");
    }}

    function renderAll() {{
      if (state.primaryPatent) {{
        state.primaryPatent = ensureClaimsTree(state.primaryPatent);
      }}
      if (state.comparisonPatent) {{
        state.comparisonPatent = ensureClaimsTree(state.comparisonPatent);
      }}
      renderHeader();
      renderClaimTreeList();
      renderClaimInspector();
      if (state.activeTab === "compare") renderComparisonTab();
      if (state.activeTab === "chart") renderClaimChartMatrix();
      if (state.activeTab === "dossier") renderDossierTab();
    }}

    // Boot
    window.addEventListener("DOMContentLoaded", () => {{
      initMcpAppBridge();
      if (state.primaryPatent) {{
        renderAll();
      }}
    }});
  </script>
</body>
</html>"""


def build_host_simulator_html(default_patent_id: str = "US8000000B2") -> str:
    """Builds a browser-based MCP Apps Host Simulator page at `/apps/claim-tree` for testing."""
    safe_pid = html.escape(default_patent_id)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>MCP Apps Host Simulator — Google Patents Claim Tree (ui://google-patents/claim-tree)</title>
  <style>
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #0f172a;
      color: #f8fafc;
      display: flex;
      flex-direction: column;
      height: 100vh;
    }}
    .host-bar {{
      padding: 10px 18px;
      background: #1e293b;
      border-bottom: 1px solid #334155;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }}
    .host-title {{
      font-size: 13px;
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .uri-pill {{
      font-family: monospace;
      background: #0f172a;
      color: #38bdf8;
      padding: 3px 8px;
      border-radius: 6px;
      font-size: 12px;
      border: 1px solid #334155;
    }}
    .host-controls {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .host-controls input {{
      padding: 5px 10px;
      border-radius: 6px;
      border: 1px solid #475569;
      background: #0f172a;
      color: #f8fafc;
      font-family: monospace;
    }}
    .host-controls button {{
      padding: 6px 12px;
      border-radius: 6px;
      border: none;
      background: #2563eb;
      color: white;
      font-weight: 600;
      cursor: pointer;
    }}
    .main-split {{
      flex: 1;
      display: grid;
      grid-template-columns: 1fr 340px;
      overflow: hidden;
    }}
    iframe {{
      width: 100%;
      height: 100%;
      border: none;
      background: #f8fafc;
    }}
    .rpc-log {{
      background: #020617;
      border-left: 1px solid #334155;
      padding: 10px;
      overflow-y: auto;
      font-family: monospace;
      font-size: 11.5px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}
    .log-entry {{
      padding: 6px 8px;
      border-radius: 6px;
      background: #0f172a;
      border-left: 3px solid #38bdf8;
      word-break: break-all;
    }}
    .log-entry.in {{ border-left-color: #34d399; }}
    .log-entry.out {{ border-left-color: #f59e0b; }}
  </style>
</head>
<body>
  <div class="host-bar">
    <div class="host-title">
      <span>🖥️ MCP Apps Host Sandbox Simulator</span>
      <span class="uri-pill">ui://google-patents/claim-tree</span>
      <span class="uri-pill">text/html;profile=mcp-app</span>
    </div>
    <div class="host-controls">
      <input id="simPatentId" value="{safe_pid}" placeholder="Patent ID" />
      <button onclick="simulateToolExecution()">Simulate MCP Tool Call & Push Result</button>
      <button style="background:#475569" onclick="toggleTheme()">Toggle Theme</button>
    </div>
  </div>
  <div class="main-split">
    <iframe id="mcpAppFrame" sandbox="allow-scripts allow-same-origin allow-forms" src="/apps/raw/claim-tree?patent_id={safe_pid}"></iframe>
    <div class="rpc-log" id="rpcLog">
      <div style="font-weight:700;color:#94a3b8;margin-bottom:4px">JSON-RPC postMessage Log (Host ↔ Guest UI)</div>
    </div>
  </div>
  <script>
    let currentTheme = "light";
    const frame = document.getElementById("mcpAppFrame");
    const logEl = document.getElementById("rpcLog");

    function appendLog(dir, method, payload) {{
      const div = document.createElement("div");
      div.className = "log-entry " + dir;
      div.innerHTML = `<strong>[${{dir.toUpperCase()}}] ${{method}}</strong><br/>` +
        JSON.stringify(payload).slice(0, 260);
      logEl.appendChild(div);
      logEl.scrollTop = logEl.scrollHeight;
    }}

    window.addEventListener("message", async (event) => {{
      const msg = event.data;
      if (!msg || msg.jsonrpc !== "2.0") return;

      if (msg.method === "ui/initialize") {{
        appendLog("in", "ui/initialize", msg.params);
        const resp = {{
          jsonrpc: "2.0",
          id: msg.id,
          result: {{
            protocolVersion: "2025-06-18",
            hostCapabilities: {{ tools: {{}}, messaging: {{}} }},
            hostContext: {{ theme: currentTheme }},
          }},
        }};
        frame.contentWindow.postMessage(resp, "*");
        appendLog("out", "ui/initialize (result)", resp.result);
      }} else if (msg.method === "ui/notifications/initialized") {{
        appendLog("in", "ui/notifications/initialized", msg.params);
        simulateToolExecution();
      }} else if (msg.method === "tools/call") {{
        appendLog("in", `tools/call (${{msg.params?.name}})`, msg.params?.arguments);
        const pid = msg.params?.arguments?.patent_url_or_id || msg.params?.arguments?.patent_id || "US8000000B2";
        const res = await fetch(`/apps/api/patent-details?patent_id=${{encodeURIComponent(pid)}}`);
        const data = await res.json();
        const rpcResp = {{
          jsonrpc: "2.0",
          id: msg.id,
          result: {{
            content: [{{ type: "text", text: JSON.stringify(data) }}],
            structuredContent: data,
          }},
        }};
        frame.contentWindow.postMessage(rpcResp, "*");
        appendLog("out", `tools/call result (${{pid}})`, {{ publication_number: data.publication_number }});
      }} else if (msg.method === "ui/message") {{
        appendLog("in", "ui/message (Chat Prompt)", msg.params);
        frame.contentWindow.postMessage({{ jsonrpc: "2.0", id: msg.id, result: {{ status: "delivered" }} }}, "*");
      }} else if (msg.method === "ui/open-link") {{
        appendLog("in", "ui/open-link", msg.params);
        window.open(msg.params.url, "_blank", "noopener,noreferrer");
        frame.contentWindow.postMessage({{ jsonrpc: "2.0", id: msg.id, result: {{ status: "opened" }} }}, "*");
      }} else if (msg.method === "ui/notifications/size-changed") {{
        // Silent or minimal log
      }}
    }});

    async function simulateToolExecution() {{
      const pid = document.getElementById("simPatentId").value.trim() || "US8000000B2";
      frame.contentWindow.postMessage({{
        jsonrpc: "2.0",
        method: "ui/notifications/tool-input",
        params: {{ arguments: {{ patent_url_or_id: pid }} }},
      }}, "*");
      appendLog("out", "ui/notifications/tool-input", {{ patent_url_or_id: pid }});

      const res = await fetch(`/apps/api/patent-details?patent_id=${{encodeURIComponent(pid)}}`);
      const data = await res.json();
      frame.contentWindow.postMessage({{
        jsonrpc: "2.0",
        method: "ui/notifications/tool-result",
        params: {{
          content: [{{ type: "text", text: JSON.stringify(data) }}],
          structuredContent: data,
        }},
      }}, "*");
      appendLog("out", "ui/notifications/tool-result", {{
        publication_number: data.publication_number,
        total_claims: data.claims_tree?.total_claims,
      }});
    }}

    function toggleTheme() {{
      currentTheme = currentTheme === "light" ? "dark" : "light";
      frame.contentWindow.postMessage({{
        jsonrpc: "2.0",
        method: "ui/notifications/host-context-changed",
        params: {{ theme: currentTheme }},
      }}, "*");
      appendLog("out", "ui/notifications/host-context-changed", {{ theme: currentTheme }});
    }}
  </script>
</body>
</html>"""
