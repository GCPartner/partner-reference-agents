"""MCP App 1: Executive 360° SEC EDGAR Financial Statement, Ratio & 10-K Filing Workbench.

Resource URI: `ui://sec-edgar/financial-dossier-workbench`
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

DOSSIER_RESOURCE_URI = "ui://sec-edgar/financial-dossier-workbench"

DOSSIER_APP_TOOL_META: Dict[str, Any] = {
    "ui": {
        "resourceUri": DOSSIER_RESOURCE_URI,
        "visibility": ["model", "app"],
    },
    "ui/resourceUri": DOSSIER_RESOURCE_URI,
}

DOSSIER_APP_RESOURCE_META: Dict[str, Any] = {
    "ui": {
        "prefersBorder": True,
        "csp": {
            "connectDomains": [d for d in [DEFAULT_PUBLIC_API_BASE_URL, "https://data.sec.gov", "https://www.sec.gov", "*"] if d],
            "resourceDomains": [d for d in [DEFAULT_PUBLIC_API_BASE_URL, "*"] if d],
            "frameDomains": [d for d in [DEFAULT_PUBLIC_API_BASE_URL, "*"] if d],
        },
    }
}

_LAST_DOSSIER_PAYLOAD: Optional[Dict[str, Any]] = None


def set_cached_dossier_payload(payload: Dict[str, Any]) -> None:
    """Stores the most recent enriched dossier payload for `resources/read` pre-hydration."""
    global _LAST_DOSSIER_PAYLOAD
    if isinstance(payload, dict):
        _LAST_DOSSIER_PAYLOAD = payload


def get_cached_dossier_payload() -> Optional[Dict[str, Any]]:
    """Returns the most recent enriched dossier payload."""
    return _LAST_DOSSIER_PAYLOAD


def _compute_dupont_by_period(
    income_rows: List[Dict[str, Any]],
    balance_rows: List[Dict[str, Any]],
    ratio_rows: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Computes 3-Step DuPont ROE decomposition (Net Margin % x Asset Turnover x Equity Multiplier) per period."""
    inc_by_p = {r.get("period_end"): r for r in (income_rows or []) if isinstance(r, dict)}
    bal_by_p = {r.get("period_end"): r for r in (balance_rows or []) if isinstance(r, dict)}
    rat_by_p = {r.get("period_end"): r for r in (ratio_rows or []) if isinstance(r, dict)}

    periods = [r.get("period_end") for r in (income_rows or []) if isinstance(r, dict) and r.get("period_end")]
    out: List[Dict[str, Any]] = []
    for p in periods:
        inc = inc_by_p.get(p, {})
        bal = bal_by_p.get(p, {})
        rat = rat_by_p.get(p, {})

        rev = inc.get("revenue")
        ni = inc.get("net_income")
        assets = bal.get("total_assets")
        equity = bal.get("stockholders_equity")

        net_margin_pct = rat.get("net_margin_pct")
        if net_margin_pct is None and rev and ni is not None and rev != 0:
            net_margin_pct = round((ni / rev) * 100.0, 2)

        asset_turnover = None
        if rev is not None and assets and assets > 0:
            asset_turnover = round(rev / assets, 2)

        equity_multiplier = None
        if assets is not None and equity and equity != 0:
            equity_multiplier = round(assets / equity, 2)

        roe_pct = rat.get("roe_pct")
        if roe_pct is None and ni is not None and equity and equity > 0:
            roe_pct = round((ni / equity) * 100.0, 2)

        out.append({
            "period_end": p,
            "net_profit_margin_pct": net_margin_pct,
            "asset_turnover": asset_turnover,
            "equity_multiplier": equity_multiplier,
            "roe_pct": roe_pct,
        })
    return out


def _flatten_period_rows(rows: List[Dict[str, Any]], nested_key: str) -> List[Dict[str, Any]]:
    """Flattens `{"period_end": "...", nested_key: {...}}` into a flat period dictionary."""
    out: List[Dict[str, Any]] = []
    for r in rows or []:
        if not isinstance(r, dict):
            continue
        nested = r.get(nested_key)
        if isinstance(nested, dict):
            merged = {**nested, **{k: v for k, v in r.items() if k != nested_key}}
            out.append(merged)
        else:
            out.append(dict(r))
    return out


def _extract_filings_from_dict_group(group: Any) -> List[Dict[str, Any]]:
    """Extracts flat filing dicts from `key_sec_filings` or `recent_filings_dossier` structures."""
    if not isinstance(group, dict):
        return []
    extracted: List[Dict[str, Any]] = []
    for val in group.values():
        if isinstance(val, dict):
            if val.get("accession_number") or val.get("form"):
                extracted.append(val)
            else:
                for sub_val in val.values():
                    if isinstance(sub_val, dict) and (sub_val.get("accession_number") or sub_val.get("form")):
                        extracted.append(sub_val)
                    elif isinstance(sub_val, list):
                        for item in sub_val:
                            if isinstance(item, dict) and (item.get("accession_number") or item.get("form")):
                                extracted.append(item)
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, dict) and (item.get("accession_number") or item.get("form")):
                    extracted.append(item)
    return extracted


def _normalize_and_merge_filings(*filing_lists: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicates filings by accession_number, normalizes description/8-K item fields, and sorts newest first."""
    merged: List[Dict[str, Any]] = []
    seen_keys: set[str] = set()
    for flist in filing_lists:
        for f in flist or []:
            if not isinstance(f, dict):
                continue
            acc = str(f.get("accession_number") or "").strip()
            f_date = str(f.get("filing_date") or "").strip()
            form = str(f.get("form") or "").strip()
            if not (acc or form):
                continue
            dedup_key = acc or f"{form}:{f_date}:{f.get('document_url', '')}"
            if dedup_key in seen_keys:
                continue
            seen_keys.add(dedup_key)

            f_copy = dict(f)
            desc = f_copy.get("description") or f_copy.get("primary_doc_description") or form or "SEC Filing"
            f_copy["description"] = desc
            f_copy["primary_doc_description"] = desc
            items_8k = f_copy.get("items_8k") or f_copy.get("items_8k_descriptions") or []
            if isinstance(items_8k, list) and items_8k:
                f_copy["items_8k"] = items_8k
                f_copy["items_8k_descriptions"] = items_8k
            merged.append(f_copy)

    merged.sort(key=lambda x: str(x.get("filing_date") or ""), reverse=True)
    return merged


def enrich_dossier_workbench_payload(
    raw_data: Dict[str, Any],
    statements_data: Optional[Dict[str, Any]] = None,
    filings_data: Optional[Dict[str, Any]] = None,
    concept_history_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Combines and enriches SEC EDGAR outputs into a unified payload for `ui://sec-edgar/financial-dossier-workbench`."""
    if not isinstance(raw_data, dict):
        return {"status": "error", "message": "Invalid dossier payload"}

    cached = _LAST_DOSSIER_PAYLOAD or {}
    raw_profile = raw_data.get("company_profile") if isinstance(raw_data.get("company_profile"), dict) else {}
    raw_comp = raw_data.get("company") if isinstance(raw_data.get("company"), dict) else {}
    stmt_comp = (statements_data or {}).get("company") if isinstance((statements_data or {}).get("company"), dict) else {}
    filings_comp = (filings_data or {}).get("company") if isinstance((filings_data or {}).get("company"), dict) else {}
    concept_comp = (concept_history_data or {}).get("company") if isinstance((concept_history_data or {}).get("company"), dict) else {}

    company: Dict[str, Any] = {
        **concept_comp,
        **filings_comp,
        **stmt_comp,
        **raw_comp,
        **raw_profile,
    }
    if not company:
        company = dict(cached.get("company") or {})

    cached_comp = cached.get("company") if isinstance(cached.get("company"), dict) else {}
    same_cik = bool(
        (company.get("cik") and cached_comp.get("cik") and str(company.get("cik")) == str(cached_comp.get("cik")))
        or (company.get("ticker") and cached_comp.get("ticker") and str(company.get("ticker")).upper() == str(cached_comp.get("ticker")).upper())
    )
    if same_cik:
        company = {**cached_comp, **company}

    # Determine statements source
    stmt_src = statements_data if isinstance(statements_data, dict) else (
        raw_data if "income_statement" in raw_data or "financial_ratios" in raw_data else (cached if same_cik else {})
    )
    income_statement = _flatten_period_rows(stmt_src.get("income_statement") or [], "line_items")
    balance_sheet = _flatten_period_rows(stmt_src.get("balance_sheet") or [], "line_items")
    cash_flow = _flatten_period_rows(stmt_src.get("cash_flow") or [], "line_items")
    financial_ratios = _flatten_period_rows(stmt_src.get("financial_ratios") or [], "ratios")

    # If only 360 dossier `headline_financials_by_period` or `financial_performance_by_period` was passed, synthesize statement rows
    perf_rows = (
        raw_data.get("headline_financials_by_period")
        or raw_data.get("financial_performance_by_period")
        or []
    )
    if perf_rows and not income_statement:
        for row in perf_rows:
            m = row.get("metrics") or {}
            yoy = row.get("yoy_or_qoq_growth_pct") or {}
            rat = row.get("ratios") or {}
            p_end = row.get("period_end")
            income_statement.append({
                "period_end": p_end,
                "revenue": m.get("revenue"),
                "revenue_growth_pct": yoy.get("revenue_growth_pct") or rat.get("yoy_revenue_growth_pct"),
                "gross_profit": m.get("gross_profit"),
                "r_and_d": m.get("r_and_d"),
                "sga": m.get("sga"),
                "operating_expenses": m.get("operating_expenses"),
                "operating_income": m.get("operating_income"),
                "operating_income_growth_pct": yoy.get("operating_income_growth_pct"),
                "interest_expense": m.get("interest_expense"),
                "pretax_income": m.get("pretax_income"),
                "income_tax": m.get("income_tax"),
                "net_income": m.get("net_income"),
                "net_income_growth_pct": yoy.get("net_income_growth_pct") or rat.get("yoy_net_income_growth_pct"),
                "eps_diluted": m.get("eps_diluted"),
            })
            balance_sheet.append({
                "period_end": p_end,
                "cash_and_equivalents": m.get("cash_and_equivalents"),
                "short_term_investments": m.get("short_term_investments"),
                "total_cash": m.get("total_cash"),
                "accounts_receivable": m.get("accounts_receivable"),
                "inventory": m.get("inventory"),
                "current_assets": m.get("current_assets"),
                "total_assets": m.get("total_assets"),
                "current_liabilities": m.get("current_liabilities"),
                "long_term_debt": m.get("long_term_debt"),
                "total_debt": m.get("total_debt"),
                "net_debt": m.get("net_debt") if m.get("net_debt") is not None else rat.get("net_debt"),
                "total_liabilities": m.get("total_liabilities"),
                "stockholders_equity": m.get("stockholders_equity"),
                "shares_outstanding": m.get("shares_outstanding"),
            })
            cash_flow.append({
                "period_end": p_end,
                "operating_cash_flow": m.get("operating_cash_flow"),
                "capex": m.get("capex"),
                "free_cash_flow": m.get("free_cash_flow"),
                "free_cash_flow_growth_pct": yoy.get("free_cash_flow_growth_pct"),
                "depreciation_amortization": m.get("depreciation_amortization"),
                "sbc": m.get("sbc") or m.get("share_based_compensation"),
                "dividends_paid": m.get("dividends_paid"),
                "share_repurchases": m.get("share_repurchases"),
            })
            financial_ratios.append({
                "period_end": p_end,
                **rat,
            })

    periods_analyzed = (
        stmt_src.get("periods_analyzed")
        or [r.get("period_end") for r in income_statement if r.get("period_end")]
    )
    cagr_summary = (
        stmt_src.get("multi_period_cagr_summary")
        or raw_data.get("multi_period_cagr_summary")
        or (cached.get("multi_period_cagr_summary") if same_cik else None)
        or {}
    )
    xbrl_tags_used = (
        stmt_src.get("xbrl_tags_used")
        or raw_data.get("xbrl_tags_used")
        or raw_data.get("xbrl_tag_provenance")
        or (cached.get("xbrl_tags_used") if same_cik else None)
        or {}
    )
    accounting_notes = (
        stmt_src.get("accounting_structure_notes")
        or raw_data.get("accounting_structure_notes")
        or (cached.get("accounting_structure_notes") if same_cik else None)
        or []
    )

    latest_inc = income_statement[0] if income_statement else {}
    latest_bal = balance_sheet[0] if balance_sheet else {}
    latest_cf = cash_flow[0] if cash_flow else {}
    latest_rat = financial_ratios[0] if financial_ratios else {}
    latest_hl = raw_data.get("latest_period_highlights") or {}

    yoy_rev = (
        latest_rat.get("yoy_revenue_growth_pct")
        if latest_rat.get("yoy_revenue_growth_pct") is not None
        else (latest_inc.get("revenue_growth_pct") if latest_inc.get("revenue_growth_pct") is not None else latest_hl.get("yoy_revenue_growth_pct"))
    )
    net_debt_val = (
        latest_rat.get("net_debt")
        if latest_rat.get("net_debt") is not None
        else (latest_bal.get("net_debt") if latest_bal.get("net_debt") is not None else latest_hl.get("net_debt"))
    )

    kpi_summary = {
        "latest_period": latest_inc.get("period_end") or latest_hl.get("period_end") or (periods_analyzed[0] if periods_analyzed else "N/A"),
        "revenue": latest_inc.get("revenue") if latest_inc.get("revenue") is not None else latest_hl.get("revenue"),
        "yoy_revenue_growth_pct": yoy_rev,
        "gross_margin_pct": latest_rat.get("gross_margin_pct") if latest_rat.get("gross_margin_pct") is not None else latest_hl.get("gross_margin_pct"),
        "operating_income": latest_inc.get("operating_income") if latest_inc.get("operating_income") is not None else latest_hl.get("operating_income"),
        "operating_margin_pct": latest_rat.get("operating_margin_pct") if latest_rat.get("operating_margin_pct") is not None else latest_hl.get("operating_margin_pct"),
        "net_income": latest_inc.get("net_income") if latest_inc.get("net_income") is not None else latest_hl.get("net_income"),
        "net_margin_pct": latest_rat.get("net_margin_pct") if latest_rat.get("net_margin_pct") is not None else latest_hl.get("net_margin_pct"),
        "eps_diluted": latest_inc.get("eps_diluted") if latest_inc.get("eps_diluted") is not None else latest_hl.get("eps_diluted"),
        "free_cash_flow": latest_cf.get("free_cash_flow") if latest_cf.get("free_cash_flow") is not None else latest_hl.get("free_cash_flow"),
        "fcf_margin_pct": latest_rat.get("fcf_margin_pct"),
        "total_cash": latest_bal.get("total_cash") if latest_bal.get("total_cash") is not None else latest_hl.get("total_cash"),
        "total_debt": latest_bal.get("total_debt") if latest_bal.get("total_debt") is not None else latest_hl.get("total_debt"),
        "net_debt": net_debt_val,
        "roe_pct": latest_rat.get("roe_pct") if latest_rat.get("roe_pct") is not None else latest_hl.get("roe_pct"),
        "current_ratio": latest_rat.get("current_ratio"),
    }

    # Filings dossier: combine all available filing sources + cached company filings so Tab 4 is never empty
    explicit_filings = filings_data.get("filings") if isinstance(filings_data, dict) and isinstance(filings_data.get("filings"), list) else []
    dossier_filings = raw_data.get("filings_dossier", {}).get("filings") if isinstance(raw_data.get("filings_dossier"), dict) else []
    top_filings = raw_data.get("filings") if isinstance(raw_data.get("filings"), list) else []
    key_sec_filings_list = _extract_filings_from_dict_group(raw_data.get("key_sec_filings"))
    recent_dossier_list = _extract_filings_from_dict_group(raw_data.get("recent_filings_dossier"))
    cached_filings_list = (cached.get("filings_dossier", {}).get("filings") or []) if same_cik else []

    merged_filings = _normalize_and_merge_filings(
        explicit_filings,
        dossier_filings,
        top_filings,
        key_sec_filings_list,
        recent_dossier_list,
        cached_filings_list,
    )
    key_by_type = (
        raw_data.get("key_sec_filings")
        or raw_data.get("recent_filings_dossier", {}).get("key_filings_by_type")
        or (cached.get("filings_dossier", {}).get("key_filings_by_type") if same_cik else None)
        or {}
    )
    filings_section: Dict[str, Any] = {
        "total_matched": len(merged_filings),
        "filings": merged_filings,
        "key_filings_by_type": key_by_type,
    }

    # Concept history section
    concept_section: Dict[str, Any] = {}
    if isinstance(concept_history_data, dict) and isinstance(concept_history_data.get("time_series"), list) and concept_history_data.get("time_series"):
        concept_section = dict(concept_history_data)
    elif isinstance(raw_data.get("initial_concept_history"), dict) and raw_data["initial_concept_history"].get("time_series"):
        concept_section = dict(raw_data["initial_concept_history"])
    elif "time_series" in raw_data and isinstance(raw_data.get("time_series"), list) and raw_data["time_series"]:
        concept_section = dict(raw_data)
    elif same_cik and cached.get("initial_concept_history", {}).get("time_series"):
        concept_section = dict(cached["initial_concept_history"])

    # Fallback synthesis: if concept_section is still empty and we have income_statement rows,
    # synthesize a multi-period revenue concept history so Tab 3 is always populated on load.
    if not concept_section.get("time_series") and income_statement:
        rev_tag = xbrl_tags_used.get("revenue") or "us-gaap:Revenues"
        synth_series: List[Dict[str, Any]] = []
        for idx, row in enumerate(income_statement):
            val = row.get("revenue")
            if val is None:
                continue
            prev_val = income_statement[idx + 1].get("revenue") if (idx + 1) < len(income_statement) else None
            pct_chg = None
            if isinstance(val, (int, float)) and isinstance(prev_val, (int, float)) and prev_val != 0:
                pct_chg = round(((float(val) - float(prev_val)) / abs(float(prev_val))) * 100.0, 2)
            synth_series.append({
                "period_end": row.get("period_end"),
                "val": val,
                "value": val,
                "pct_change": pct_chg,
                "period_over_period_growth_pct": pct_chg,
                "form": "10-K" if (stmt_src.get("period_type") or raw_data.get("period_type") or "annual") == "annual" else "10-Q",
                "source_tag": rev_tag,
                "restatement_audit": {"was_restated": False, "initial_reported_value": None},
            })
        if synth_series:
            concept_section = {
                "concept_requested": "revenue",
                "concept_resolved": rev_tag,
                "cagr_pct": cagr_summary.get("revenue_cagr_pct"),
                "concept": {
                    "requested": "revenue",
                    "label": "Revenues",
                    "unit": "USD",
                    "tags_used": [rev_tag],
                },
                "summary_statistics": {
                    "cagr_pct": cagr_summary.get("revenue_cagr_pct"),
                },
                "time_series": synth_series,
            }

    # Normalize concept_section fields so JS can read either schema seamlessly
    if concept_section.get("time_series"):
        c_meta = concept_section.get("concept") if isinstance(concept_section.get("concept"), dict) else {}
        tags_list = c_meta.get("tags_used") if isinstance(c_meta.get("tags_used"), list) else []
        if not concept_section.get("concept_resolved"):
            concept_section["concept_resolved"] = (
                (tags_list[0] if tags_list else None)
                or c_meta.get("label")
                or c_meta.get("requested")
                or concept_section.get("concept_requested")
                or "revenue"
            )
        if concept_section.get("cagr_pct") is None:
            stats = concept_section.get("summary_statistics") if isinstance(concept_section.get("summary_statistics"), dict) else {}
            concept_section["cagr_pct"] = stats.get("cagr_pct")
        norm_ts: List[Dict[str, Any]] = []
        for pt in concept_section.get("time_series", []):
            if not isinstance(pt, dict):
                continue
            pt_copy = dict(pt)
            v = pt_copy.get("val") if pt_copy.get("val") is not None else pt_copy.get("value")
            g = pt_copy.get("pct_change") if pt_copy.get("pct_change") is not None else pt_copy.get("period_over_period_growth_pct")
            pt_copy["val"] = v
            pt_copy["value"] = v
            pt_copy["pct_change"] = g
            pt_copy["period_over_period_growth_pct"] = g
            if "restatement_audit" not in pt_copy:
                rh = pt_copy.get("restatement_history")
                pt_copy["restatement_audit"] = {
                    "was_restated": bool(rh),
                    "initial_reported_value": rh[-1].get("prior_val") if isinstance(rh, list) and rh else None,
                }
            norm_ts.append(pt_copy)
        concept_section["time_series"] = norm_ts

    dupont_roe_by_period = _compute_dupont_by_period(income_statement, balance_sheet, financial_ratios)

    enriched = {
        "status": "success",
        "app_resource_uri": DOSSIER_RESOURCE_URI,
        "company": company,
        "period_type": stmt_src.get("period_type") or raw_data.get("period_type") or "annual",
        "periods_analyzed": periods_analyzed,
        "multi_period_cagr_summary": cagr_summary,
        "kpi_summary": kpi_summary,
        "dupont_roe_by_period": dupont_roe_by_period,
        "income_statement": income_statement,
        "balance_sheet": balance_sheet,
        "cash_flow": cash_flow,
        "financial_ratios": financial_ratios,
        "xbrl_tags_used": xbrl_tags_used,
        "accounting_structure_notes": accounting_notes,
        "filings_dossier": filings_section,
        "initial_concept_history": concept_section,
    }
    set_cached_dossier_payload(enriched)
    return enriched


def build_dossier_workbench_html(
    initial_payload: Optional[Dict[str, Any]] = None,
    theme_overrides: Optional[Dict[str, str]] = None,
    api_base_url: Optional[str] = None,
) -> str:
    """Builds the self-contained HTML5/CSS/JS bundle for `ui://sec-edgar/financial-dossier-workbench`."""
    theme = {**APEX_BRAND_THEME, **(theme_overrides or {})}
    shared_css = build_shared_css(theme)
    safe_json = json.dumps(initial_payload or get_cached_dossier_payload() or None).replace("</", "<\\/")
    safe_api_base_url = json.dumps((api_base_url or DEFAULT_PUBLIC_API_BASE_URL).rstrip("/"))

    return f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Apex Capital Institutional Research - Executive 360 SEC EDGAR Financial Statement &amp; Ratio Workbench</title>
  <style>
    {shared_css}
    .split-grid {{
      display: grid;
      grid-template-columns: 1.25fr 1fr;
      gap: 12px;
    }}
    @media (max-width: 900px) {{
      .split-grid {{ grid-template-columns: 1fr; }}
    }}
    .dupont-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(185px, 1fr));
      gap: 10px;
      margin-bottom: 12px;
    }}
    .dupont-card {{
      background: var(--surface-alt);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 10px 12px;
    }}
    .chart-box {{
      width: 100%;
      min-height: 220px;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }}
    .clickable-row {{
      cursor: pointer;
    }}
    .yoy-cell {{
      display: inline-flex;
      align-items: center;
      gap: 7px;
      min-width: 120px;
      justify-content: flex-end;
    }}
    .yoy-bar-track {{
      width: 64px;
      height: 11px;
      background: transparent;
      display: inline-flex;
      align-items: center;
    }}
    .yoy-bar-fill {{
      height: 11px;
      border-radius: 2px;
    }}
  </style>
</head>
<body>
  <!-- Top Institutional Navy Bar (#0f172a) -->
  <header class="top-banner">
    <div class="brand-title">
      <span class="brand-logo">A</span>
      <span>{theme["brand_name"]} - Executive 360 SEC EDGAR Financial Statement &amp; Ratio Workbench</span>
    </div>
    <div class="control-group">
      <button id="themeToggleBtn" class="btn btn-icon-header" title="Toggle Light/Dark Theme">☀️ / 🌙</button>
    </div>
  </header>

  <!-- Inset Rounded Deep Institutional Navy Control Banner (#0f172a) matching Wireframe -->
  <section class="control-strip">
    <div class="entity-identity">
      <div class="entity-avatar" id="entityAvatarBadge">SEC</div>
      <div>
        <div class="entity-name" id="companyNameTitle">LOADING SEC ENTITY...</div>
        <div class="entity-sub" id="companySubMeta">(CIK — | SIC —)</div>
      </div>
    </div>

    <div class="control-group">
      <input id="tickerInput" class="input input-mono" type="text" value="NVDA" style="width:135px;" placeholder="Ticker Search..." />
      <select id="periodTypeSelect" class="select">
        <option value="annual">Annual 10-K</option>
        <option value="quarterly">Quarterly 10-Q</option>
      </select>
      <select id="periodsSelect" class="select">
        <option value="4">4 Periods</option>
        <option value="5" selected>5 Periods</option>
        <option value="8">8 Periods</option>
      </select>
      <button id="loadDossierBtn" class="btn btn-neutral">Load Dossier</button>
    </div>

    <div class="control-group">
      <button id="askAiCfoBtn" class="btn btn-gold">Ask AI: CFO Executive Summary</button>
      <button id="askAiDupontBtn" class="btn btn-gold">Ask AI: DuPont ROE Bridge</button>
    </div>
  </section>

  <main class="workspace">
    <!-- 6-Card Centered KPI Strip (#ffffff surface) -->
    <section class="kpi-grid" id="kpiStrip"></section>

    <!-- Clean Underline Navigation Tabs -->
    <nav class="tabs-bar">
      <button class="tab-btn active" data-tab="statements">1. Financial Statements &amp; Charts</button>
      <button class="tab-btn" data-tab="ratios">2. Ratios &amp; DuPont ROE</button>
      <button class="tab-btn" data-tab="xbrl">3. XBRL Concept &amp; Restatements</button>
      <button class="tab-btn" data-tab="filings">4. SEC Filings 10-K/8-K</button>
    </nav>

    <!-- TAB 1: Full-Width 4-Series Grouped Bar Chart + US-GAAP Financial Statement Table -->
    <section id="tab-statements" class="tab-pane">
      <!-- Top Full-Width Panel: 4-Series Grouped Bar Chart matching Wireframe -->
      <div class="panel">
        <div class="panel-header">
          <span class="panel-title" id="chartTitle">Multi-Period Financial Trajectory (Revenue • Gross Profit • Operating Income • Net Income)</span>
          <span class="badge badge-navy" id="selectedMetricBadge" style="cursor:pointer;">Click any statement row below to isolate</span>
        </div>
        <div class="chart-box" id="mainComboChart"></div>
      </div>

      <!-- Middle Full-Width Panel: US-GAAP Harmonized Statement Table with YoY Bar & XBRL Tag Column -->
      <div class="panel">
        <div class="panel-header">
          <span class="panel-title" id="stmtTableTitle">US-GAAP Income Statement</span>
          <div class="pill-group" id="stmtSwitcher">
            <button class="pill active" data-stmt="income_statement">Income Statement</button>
            <button class="pill" data-stmt="balance_sheet">Balance Sheet</button>
            <button class="pill" data-stmt="cash_flow">Cash Flow</button>
          </div>
        </div>
        <div class="table-wrap" id="stmtTableContainer"></div>
        <div id="accountingNotesContainer"></div>
      </div>

      <!-- Bottom Panel: Profitability Margin Progression -->
      <div class="panel">
        <div class="panel-header">
          <span class="panel-title">Profitability Margin Progression (Gross Margin % • Operating Margin % • Net Margin % • FCF Margin %)</span>
        </div>
        <div class="chart-box" id="marginTrendChart"></div>
      </div>
    </section>

    <!-- TAB 2: Financial Ratios & DuPont 3-Step ROE -->
    <section id="tab-ratios" class="tab-pane" style="display:none;">
      <div class="panel">
        <div class="panel-header">
          <span class="panel-title">DuPont 3-Step Return on Equity (ROE) Decomposition (Net Margin × Asset Turnover × Equity Multiplier)</span>
        </div>
        <div class="dupont-grid" id="dupontContainer"></div>
      </div>
      <div class="panel">
        <div class="panel-header">
          <span class="panel-title">Multi-Period Institutional Ratio Matrix (Profitability • Liquidity • Leverage • Efficiency)</span>
        </div>
        <div class="table-wrap" id="ratiosTableContainer"></div>
      </div>
    </section>

    <!-- TAB 3: XBRL Concept Time-Series & Restatement Audit -->
    <section id="tab-xbrl" class="tab-pane" style="display:none;">
      <div class="panel">
        <div class="panel-header">
          <span class="panel-title">Live XBRL Concept Time-Series &amp; Restatement Audit Inspector</span>
          <div class="control-group">
            <div class="pill-group" id="conceptPills">
              <button class="pill active" data-concept="revenue">revenue</button>
              <button class="pill" data-concept="operating_income">operating_income</button>
              <button class="pill" data-concept="net_income">net_income</button>
              <button class="pill" data-concept="free_cash_flow">free_cash_flow</button>
              <button class="pill" data-concept="r_and_d">r_and_d</button>
              <button class="pill" data-concept="sbc">sbc</button>
              <button class="pill" data-concept="capex">capex</button>
              <button class="pill" data-concept="total_assets">total_assets</button>
              <button class="pill" data-concept="total_debt">total_debt</button>
            </div>
            <input id="customConceptInput" class="input input-mono" type="text" placeholder="Custom XBRL tag..." style="width:165px;" />
            <button id="traceConceptBtn" class="btn btn-primary">Trace XBRL Tag</button>
          </div>
        </div>
        <div class="split-grid">
          <div class="chart-box" id="conceptHistoryChart"></div>
          <div class="table-wrap" id="conceptHistoryTable"></div>
        </div>
      </div>
    </section>

    <!-- TAB 4: SEC Filings Explorer -->
    <section id="tab-filings" class="tab-pane" style="display:none;">
      <div class="panel">
        <div class="panel-header">
          <span class="panel-title">SEC EDGAR Archive Filings Explorer (10-K, 10-Q, 8-K, DEF 14A)</span>
          <div class="control-group">
            <div class="pill-group" id="filingFormPills">
              <button class="pill active" data-form="ALL">All Forms</button>
              <button class="pill" data-form="10-K">10-K Annual</button>
              <button class="pill" data-form="10-Q">10-Q Quarterly</button>
              <button class="pill" data-form="8-K">8-K Material Events</button>
              <button class="pill" data-form="DEF 14A">DEF 14A Proxy</button>
            </div>
            <input id="item8kInput" class="input" type="text" placeholder="8-K Item (e.g. 2.02, 5.02)" style="width:155px;" />
            <button id="searchFilingsBtn" class="btn btn-primary">Filter SEC Filings</button>
          </div>
        </div>
        <div class="table-wrap" id="filingsTableContainer"></div>
      </div>
    </section>
  </main>

  <footer class="footer-bar">
    <span id="statusText">SEC EDGAR Live XBRL Harmonization Engine Ready</span>
    <span>Resource: <code>{DOSSIER_RESOURCE_URI}</code> • MIME: <code>{MCP_APP_MIME_TYPE}</code></span>
  </footer>

  <script>
    const INITIAL_PAYLOAD = {safe_json};
    const API_BASE_URL = {safe_api_base_url};
    // Lock to the approved Light Mode institutional theme from mcp_apps_ux_design.md
    const LOCK_DESIGN_THEME = true;
    let currentPayload = null;
    let activeTab = "statements";
    let activeStmtType = "income_statement";
    let selectedPlotMetric = null;
    let activeFilingFormFilter = "ALL";
    let activeConcept = "revenue";
    let traceRequestSeq = 0;

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
        raw.company ||
        Array.isArray(raw.time_series) ||
        Array.isArray(raw.income_statement) ||
        Array.isArray(raw.filings) ||
        raw.filings_dossier ||
        raw.initial_concept_history
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
        const idf = msg.params.arguments.identifier;
        if (idf) document.getElementById("tickerInput").value = String(idf).toUpperCase();
        const reqConcept = msg.params.arguments.concept_or_tag;
        if (reqConcept) {{
          activeConcept = String(reqConcept).trim().toLowerCase();
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
            appInfo: {{ name: "Apex Capital 360 Financial Workbench", version: "1.0.0" }},
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
      if (abs >= 1e9) return `${{sign}}$${{(abs / 1e9).toFixed(2)}}B`;
      if (abs >= 1e6) return `${{sign}}$${{(abs / 1e6).toFixed(1)}}M`;
      if (abs >= 1e3) return `${{sign}}$${{(abs / 1e3).toFixed(1)}}K`;
      return `${{sign}}$${{abs.toFixed(2)}}`;
    }}

    function fmtTableVal(v, isPerShare = false, isShares = false) {{
      if (v === null || v === undefined || Number.isNaN(Number(v))) return "—";
      const n = Number(v);
      if (isPerShare) return `$${{n.toFixed(2)}}`;
      if (isShares) return `${{(n / 1e6).toFixed(1)}}M`;
      return fmtUsdCompact(n);
    }}

    function fmtPct(v, includePlus = true) {{
      if (v === null || v === undefined || Number.isNaN(Number(v))) return "—";
      const n = Number(v);
      const prefix = includePlus && n > 0 ? "+" : "";
      return `${{prefix}}${{n.toFixed(2)}}%`;
    }}

    function fmtPeriodHeader(periodEnd, idx, total) {{
      if (!periodEnd) return `P${{idx + 1}}`;
      const yr = String(periodEnd).slice(0, 4);
      const pType = currentPayload?.period_type || "annual";
      if (pType === "annual") return `FY${{yr}}`;
      return String(periodEnd).slice(0, 7);
    }}

    function deltaBadge(v, suffix = "%") {{
      if (v === null || v === undefined || Number.isNaN(Number(v))) return `<span class="badge">—</span>`;
      const n = Number(v);
      const cls = n >= 0 ? "badge-emerald" : "badge-crimson";
      const sign = n > 0 ? "+" : "";
      return `<span class="badge ${{cls}}">${{sign}}${{n.toFixed(1)}}${{suffix}}</span>`;
    }}

    // =========================================================================
    // 3. Payload Hydration & Multi-Tab Rendering
    // =========================================================================
    function extractFilingsFromGroup(group) {{
      if (!group || typeof group !== "object") return [];
      const out = [];
      for (const val of Object.values(group)) {{
        if (!val) continue;
        if (Array.isArray(val)) {{
          for (const item of val) {{
            if (item && typeof item === "object" && (item.accession_number || item.form)) out.push(item);
          }}
        }} else if (typeof val === "object") {{
          if (val.accession_number || val.form) {{
            out.push(val);
          }} else {{
            for (const subVal of Object.values(val)) {{
              if (Array.isArray(subVal)) {{
                for (const item of subVal) {{
                  if (item && typeof item === "object" && (item.accession_number || item.form)) out.push(item);
                }}
              }} else if (subVal && typeof subVal === "object" && (subVal.accession_number || subVal.form)) {{
                out.push(subVal);
              }}
            }}
          }}
        }}
      }}
      return out;
    }}

    function mergeAndDedupeFilings(...filingArrays) {{
      const merged = [];
      const seen = new Set();
      for (const arr of filingArrays) {{
        if (!Array.isArray(arr)) continue;
        for (const f of arr) {{
          if (!f || typeof f !== "object") continue;
          const acc = String(f.accession_number || "").trim();
          const form = String(f.form || "").trim();
          const fdate = String(f.filing_date || "").trim();
          if (!acc && !form) continue;
          const key = acc || `${{form}}:${{fdate}}:${{f.document_url || ""}}`;
          if (seen.has(key)) continue;
          seen.add(key);
          const desc = f.description || f.primary_doc_description || form || "SEC Filing";
          const items8k =
            Array.isArray(f.items_8k_descriptions) && f.items_8k_descriptions.length
              ? f.items_8k_descriptions
              : Array.isArray(f.items_8k)
              ? f.items_8k
              : [];
          merged.push({{
            ...f,
            description: desc,
            primary_doc_description: desc,
            items_8k: items8k,
            items_8k_descriptions: items8k,
          }});
        }}
      }}
      merged.sort((a, b) => String(b.filing_date || "").localeCompare(String(a.filing_date || "")));
      return merged;
    }}

    function hydratePayload(raw) {{
      if (!raw || typeof raw !== "object") return;

      const prev = currentPayload && typeof currentPayload === "object" ? currentPayload : {{}};
      const prevComp = prev.company || {{}};
      const rawComp = {{ ...(raw.company || {{}}), ...(raw.company_profile || {{}}) }};
      const sameCompany =
        Boolean(prevComp.cik && rawComp.cik && String(prevComp.cik) === String(rawComp.cik)) ||
        Boolean(prevComp.ticker && rawComp.ticker && String(prevComp.ticker).toUpperCase() === String(rawComp.ticker).toUpperCase()) ||
        (!rawComp.cik && !rawComp.ticker);

      if (!sameCompany) {{
        activeConcept = "revenue";
      }}

      const nextPayload = sameCompany ? {{ ...prev }} : {{}};
      nextPayload.company = sameCompany
        ? {{
            ...prevComp,
            ...rawComp,
            sic: rawComp.sic || prevComp.sic || "",
            sic_description: rawComp.sic_description || prevComp.sic_description || "",
          }}
        : rawComp;

      if (raw.period_type) nextPayload.period_type = raw.period_type;
      if (Array.isArray(raw.periods_analyzed) && raw.periods_analyzed.length) nextPayload.periods_analyzed = raw.periods_analyzed;
      if (raw.multi_period_cagr_summary && Object.keys(raw.multi_period_cagr_summary).length) {{
        nextPayload.multi_period_cagr_summary = raw.multi_period_cagr_summary;
      }}
      if (raw.kpi_summary && Object.keys(raw.kpi_summary).some((k) => k !== "latest_period" && raw.kpi_summary[k] != null)) {{
        nextPayload.kpi_summary = raw.kpi_summary;
      }}
      if (Array.isArray(raw.dupont_roe_by_period) && raw.dupont_roe_by_period.length) {{
        nextPayload.dupont_roe_by_period = raw.dupont_roe_by_period;
      }}
      if (Array.isArray(raw.income_statement) && raw.income_statement.length) {{
        nextPayload.income_statement = raw.income_statement;
      }}
      if (Array.isArray(raw.balance_sheet) && raw.balance_sheet.length) {{
        nextPayload.balance_sheet = raw.balance_sheet;
      }}
      if (Array.isArray(raw.cash_flow) && raw.cash_flow.length) {{
        nextPayload.cash_flow = raw.cash_flow;
      }}
      if (Array.isArray(raw.financial_ratios) && raw.financial_ratios.length) {{
        nextPayload.financial_ratios = raw.financial_ratios;
      }}
      if (raw.xbrl_tags_used && Object.keys(raw.xbrl_tags_used).length) {{
        nextPayload.xbrl_tags_used = raw.xbrl_tags_used;
      }} else if (raw.xbrl_tag_provenance && Object.keys(raw.xbrl_tag_provenance).length) {{
        nextPayload.xbrl_tags_used = raw.xbrl_tag_provenance;
      }}
      if (Array.isArray(raw.accounting_structure_notes) && raw.accounting_structure_notes.length) {{
        nextPayload.accounting_structure_notes = raw.accounting_structure_notes;
      }}

      // Merge XBRL Concept History (Tab 3):
      // Prioritize direct top-level `raw.time_series` (from `trace_xbrl_metric_history`)
      if (Array.isArray(raw.time_series) && raw.time_series.length) {{
        nextPayload.initial_concept_history = raw;
      }} else if (raw.initial_concept_history && Array.isArray(raw.initial_concept_history.time_series) && raw.initial_concept_history.time_series.length) {{
        const incomingReq = String(
          raw.initial_concept_history.concept_requested ||
          raw.initial_concept_history.concept?.requested ||
          "revenue"
        ).toLowerCase();
        // Do not overwrite a user-selected non-revenue concept with a default "revenue" dossier payload
        const preserveActive =
          sameCompany &&
          activeConcept &&
          activeConcept !== "revenue" &&
          incomingReq === "revenue" &&
          prev.initial_concept_history &&
          Array.isArray(prev.initial_concept_history.time_series) &&
          prev.initial_concept_history.time_series.length > 0;
        if (!preserveActive) {{
          nextPayload.initial_concept_history = raw.initial_concept_history;
        }}
      }}

      // Merge SEC Filings (Tab 4) from all incoming sources + preserve existing company filings
      const incomingFilings = mergeAndDedupeFilings(
        Array.isArray(raw.filings) ? raw.filings : [],
        Array.isArray(raw.filings_dossier?.filings) ? raw.filings_dossier.filings : [],
        extractFilingsFromGroup(raw.key_sec_filings),
        extractFilingsFromGroup(raw.recent_filings_dossier),
        sameCompany && Array.isArray(prev.filings_dossier?.filings) ? prev.filings_dossier.filings : []
      );
      if (incomingFilings.length) {{
        nextPayload.filings_dossier = {{
          total_matched: incomingFilings.length,
          filings: incomingFilings,
          key_filings_by_type:
            raw.key_sec_filings ||
            raw.filings_dossier?.key_filings_by_type ||
            raw.recent_filings_dossier?.key_filings_by_type ||
            (sameCompany ? prev.filings_dossier?.key_filings_by_type : {{}}) ||
            {{}},
        }};
      }}

      currentPayload = nextPayload;
      const comp = currentPayload.company || {{}};
      if (comp.ticker) {{
        document.getElementById("tickerInput").value = comp.ticker;
      }}
      if (currentPayload.period_type) {{
        document.getElementById("periodTypeSelect").value = currentPayload.period_type;
      }}

      const tickerStr = (comp.ticker || "SEC").toUpperCase();
      document.getElementById("entityAvatarBadge").textContent = tickerStr.slice(0, 4);
      document.getElementById("companyNameTitle").textContent = (comp.name || tickerStr || "SEC EDGAR ENTITY").toUpperCase();
      document.getElementById("companySubMeta").textContent = `(${{tickerStr}} | CIK ${{comp.cik || "—"}} | SIC ${{comp.sic || "—"}} ${{comp.sic_description || ""}})`;

      renderKpiStrip();
      renderStatementsTab();
      renderRatiosTab();
      renderXbrlTab();
      renderFilingsTab();
    }}

    function renderKpiStrip() {{
      const k = currentPayload?.kpi_summary || {{}};
      const cagr = currentPayload?.multi_period_cagr_summary || {{}};
      const yoyRev = k.yoy_revenue_growth_pct;
      const yoyCls = yoyRev != null && Number(yoyRev) < 0 ? "text-crimson" : "text-emerald";
      const netDebtVal = Number(k.net_debt || 0);
      const isNetCash = netDebtVal < 0;

      const cards = [
        {{
          label: "Revenue",
          val: fmtUsdCompact(k.revenue),
          sub: yoyRev != null
            ? `<span class="${{yoyCls}}">${{fmtPct(yoyRev)}} YoY</span>`
            : `<span class="text-muted-mono">${{escapeHtml(k.latest_period || "Latest")}}</span>`,
        }},
        {{
          label: "Gross Margin",
          val: fmtPct(k.gross_margin_pct, false),
          sub: `<span class="text-emerald">US-GAAP Harmonized</span>`,
        }},
        {{
          label: "Operating Income",
          val: fmtUsdCompact(k.operating_income),
          sub: `<span class="text-muted-mono">OPM ${{fmtPct(k.operating_margin_pct, false)}}</span>`,
        }},
        {{
          label: "Net Income",
          val: fmtUsdCompact(k.net_income),
          sub: `<span class="text-emerald">EPS ${{k.eps_diluted != null ? "$" + Number(k.eps_diluted).toFixed(2) : "—"}}</span>`,
        }},
        {{
          label: "Free Cash Flow",
          val: fmtUsdCompact(k.free_cash_flow),
          sub: `<span class="text-emerald">FCF Margin ${{fmtPct(k.fcf_margin_pct, false)}}</span>`,
        }},
        {{
          label: isNetCash ? "Net Cash" : "Net Debt",
          val: fmtUsdCompact(Math.abs(netDebtVal)),
          sub: `<span class="text-muted-mono">Cash ${{fmtUsdCompact(k.total_cash)}} • CR ${{k.current_ratio != null ? Number(k.current_ratio).toFixed(2) + "x" : "—"}}</span>`,
        }},
      ];
      document.getElementById("kpiStrip").innerHTML = cards
        .map(
          (c) => `
        <div class="kpi-card">
          <div class="kpi-label">${{escapeHtml(c.label)}}</div>
          <div class="kpi-val">${{escapeHtml(c.val)}}</div>
          <div class="kpi-sub">${{c.sub}}</div>
        </div>`
        )
        .join("");
    }}

    const STMT_ROW_DEFS = {{
      income_statement: [
        {{ key: "revenue", label: "Revenues", defaultTag: "us-gaap:Revenues", cagrKey: "revenue_cagr_pct", highlight: true }},
        {{ key: "cost_of_revenue", label: "Cost of Revenue", defaultTag: "us-gaap:CostOfGoodsAndServicesSold" }},
        {{ key: "gross_profit", label: "Gross Profit", defaultTag: "us-gaap:GrossProfit", highlight: true }},
        {{ key: "r_and_d", label: "Research & Development", defaultTag: "us-gaap:ResearchAndDevelopmentExpense" }},
        {{ key: "sga", label: "Selling, General & Admin", defaultTag: "us-gaap:SellingGeneralAndAdministrativeExpense" }},
        {{ key: "operating_expenses", label: "Operating Expenses", defaultTag: "us-gaap:OperatingExpenses" }},
        {{ key: "operating_income", label: "Operating IncomeLoss", defaultTag: "us-gaap:OperatingIncomeLoss", cagrKey: "operating_income_cagr_pct", highlight: true }},
        {{ key: "interest_expense", label: "Interest Expense", defaultTag: "us-gaap:InterestExpense" }},
        {{ key: "pretax_income", label: "Pretax Income (EBT)", defaultTag: "us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest" }},
        {{ key: "income_tax", label: "Income Tax Provision", defaultTag: "us-gaap:IncomeTaxExpenseBenefit" }},
        {{ key: "net_income", label: "Net Income", defaultTag: "us-gaap:NetIncomeLoss", cagrKey: "net_income_cagr_pct", highlight: true }},
        {{ key: "eps_diluted", label: "Diluted EPS ($/sh)", defaultTag: "us-gaap:EarningsPerShareDiluted", isPerShare: true }},
      ],
      balance_sheet: [
        {{ key: "cash_and_equivalents", label: "Cash & Cash Equivalents", defaultTag: "us-gaap:CashAndCashEquivalentsAtCarryingValue" }},
        {{ key: "short_term_investments", label: "Short-Term Marketable Securities", defaultTag: "us-gaap:MarketableSecuritiesCurrent" }},
        {{ key: "total_cash", label: "Total Cash & ST Investments", defaultTag: "Derived:Cash+STInvestments", highlight: true }},
        {{ key: "accounts_receivable", label: "Accounts Receivable, Net", defaultTag: "us-gaap:AccountsReceivableNetCurrent" }},
        {{ key: "inventory", label: "Inventories", defaultTag: "us-gaap:InventoryNet" }},
        {{ key: "current_assets", label: "Total Current Assets", defaultTag: "us-gaap:AssetsCurrent", highlight: true }},
        {{ key: "ppe_net", label: "Property, Plant & Equipment, Net", defaultTag: "us-gaap:PropertyPlantAndEquipmentNet" }},
        {{ key: "goodwill", label: "Goodwill & Intangibles", defaultTag: "us-gaap:Goodwill" }},
        {{ key: "total_assets", label: "Total Assets", defaultTag: "us-gaap:Assets", highlight: true }},
        {{ key: "accounts_payable", label: "Accounts Payable", defaultTag: "us-gaap:AccountsPayableCurrent" }},
        {{ key: "current_liabilities", label: "Total Current Liabilities", defaultTag: "us-gaap:LiabilitiesCurrent" }},
        {{ key: "long_term_debt", label: "Long-Term Debt", defaultTag: "us-gaap:LongTermDebtNoncurrent" }},
        {{ key: "total_debt", label: "Total Debt (Short + Long-Term)", defaultTag: "Derived:ShortTerm+LongTermDebt", highlight: true }},
        {{ key: "net_debt", label: "Net Debt (Total Debt - Cash)", defaultTag: "Derived:TotalDebt-TotalCash" }},
        {{ key: "total_liabilities", label: "Total Liabilities", defaultTag: "us-gaap:Liabilities" }},
        {{ key: "stockholders_equity", label: "Total Stockholders' Equity", defaultTag: "us-gaap:StockholdersEquity", highlight: true }},
        {{ key: "shares_outstanding", label: "Common Shares Outstanding", defaultTag: "us-gaap:CommonStockSharesOutstanding", isShares: true }},
      ],
      cash_flow: [
        {{ key: "operating_cash_flow", label: "Operating Cash Flow (OCF)", defaultTag: "us-gaap:NetCashProvidedByUsedInOperatingActivities", highlight: true }},
        {{ key: "capex", label: "Capital Expenditures (CapEx)", defaultTag: "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment" }},
        {{ key: "free_cash_flow", label: "Free Cash Flow (OCF - CapEx)", defaultTag: "Derived:OCF-CapEx", cagrKey: "fcf_cagr_pct", highlight: true }},
        {{ key: "depreciation_amortization", label: "Depreciation & Amortization", defaultTag: "us-gaap:DepreciationDepletionAndAmortization" }},
        {{ key: "sbc", label: "Stock-Based Compensation", defaultTag: "us-gaap:ShareBasedCompensation" }},
        {{ key: "investing_cash_flow", label: "Net Cash Used in Investing", defaultTag: "us-gaap:NetCashProvidedByUsedInInvestingActivities" }},
        {{ key: "financing_cash_flow", label: "Net Cash Used in Financing", defaultTag: "us-gaap:NetCashProvidedByUsedInFinancingActivities" }},
        {{ key: "dividends_paid", label: "Common Dividends Paid", defaultTag: "us-gaap:PaymentsOfDividendsCommonStock" }},
        {{ key: "share_repurchases", label: "Share Repurchases (Buybacks)", defaultTag: "us-gaap:PaymentsForRepurchaseOfCommonStock" }},
      ],
    }};

    const STMT_TITLES = {{
      income_statement: "US-GAAP Income Statement",
      balance_sheet: "US-GAAP Balance Sheet",
      cash_flow: "US-GAAP Cash Flow Statement",
    }};

    function renderStatementsTab() {{
      // Display chronological order (FY2021 -> FY2025) matching the wireframe table & chart
      const rawRows = currentPayload?.[activeStmtType] || [];
      const chronRows = rawRows.slice().reverse();
      const tagsUsed = currentPayload?.xbrl_tags_used || {{}};
      const defs = STMT_ROW_DEFS[activeStmtType] || [];

      document.getElementById("stmtTableTitle").textContent = STMT_TITLES[activeStmtType] || "US-GAAP Financial Statement";

      if (!chronRows.length) {{
        document.getElementById("stmtTableContainer").innerHTML = `<div style="padding:14px;color:var(--text-muted)">No statement rows available.</div>`;
        return;
      }}

      let html = `<table class="fin-table"><thead><tr><th>Name</th>`;
      chronRows.forEach((r, idx) => {{
        html += `<th>${{escapeHtml(fmtPeriodHeader(r.period_end, idx, chronRows.length))}}</th>`;
      }});
      html += `<th>YoY</th><th style="text-align:left;">XBRL tag</th></tr></thead><tbody>`;

      for (const d of defs) {{
        const vals = chronRows.map((r) => r[d.key]);
        if (vals.every((v) => v === null || v === undefined)) continue;

        const rowCls = d.highlight ? "row-highlight clickable-row" : "clickable-row";
        html += `<tr class="${{rowCls}}" data-plot-key="${{escapeHtml(d.key)}}" data-plot-label="${{escapeHtml(d.label)}}">`;
        html += `<td>${{escapeHtml(d.label)}}</td>`;
        for (const v of vals) {{
          html += `<td>${{fmtTableVal(v, d.isPerShare, d.isShares)}}</td>`;
        }}

        // Latest YoY change (last two chronological periods) with inline bar matching wireframe
        let yoyCell = "—";
        const latestVal = vals[vals.length - 1];
        const prevVal = vals.length >= 2 ? vals[vals.length - 2] : null;
        if (latestVal != null && prevVal != null && Number(prevVal) !== 0) {{
          const yoy = ((Number(latestVal) - Number(prevVal)) / Math.abs(Number(prevVal))) * 100.0;
          const sign = yoy > 0 ? "+" : "";
          const textCls = yoy >= 0 ? "text-emerald" : "text-crimson";
          const barColor = yoy >= 0 ? "var(--emerald)" : "var(--gold)";
          const barW = Math.min(64, Math.max(6, Math.round((Math.min(Math.abs(yoy), 150) / 150) * 64)));
          yoyCell = `
            <div class="yoy-cell">
              <span class="${{textCls}}">${{sign}}${{yoy.toFixed(0)}}%</span>
              <span class="yoy-bar-track"><span class="yoy-bar-fill" style="width:${{barW}}px;background:${{barColor}};"></span></span>
            </div>`;
        }}

        const rawTag = tagsUsed[d.key] || d.defaultTag || `us-gaap:${{d.key}}`;
        const formattedTag = rawTag.includes(":") ? rawTag : `us-gaap:${{rawTag}}`;
        html += `<td>${{yoyCell}}</td>`;
        html += `<td style="text-align:left;"><span class="xbrl-pill">${{escapeHtml(formattedTag)}}</span></td></tr>`;
      }}
      html += `</tbody></table>`;
      document.getElementById("stmtTableContainer").innerHTML = html;

      document.querySelectorAll("[data-plot-key]").forEach((tr) => {{
        tr.addEventListener("click", () => {{
          selectedPlotMetric = {{
            key: tr.getAttribute("data-plot-key"),
            label: tr.getAttribute("data-plot-label"),
          }};
          renderMainComboChart();
        }});
      }});

      const notes = currentPayload?.accounting_structure_notes || [];
      document.getElementById("accountingNotesContainer").innerHTML = notes.length
        ? `<div class="note-banner"><strong>Accounting &amp; XBRL Reconciliation Note:</strong> ${{notes.map(escapeHtml).join(" • ")}}</div>`
        : "";

      renderMainComboChart();
      renderMarginTrendChart();
    }}

    function renderMainComboChart() {{
      const inc = (currentPayload?.income_statement || []).slice().reverse();
      const stmtRows = (currentPayload?.[activeStmtType] || []).slice().reverse();
      if (!inc.length && !stmtRows.length) return;

      const w = 920;
      const h = 235;
      const padL = 68;
      const padR = 24;
      const padT = 20;
      const padB = 34;
      const plotW = w - padL - padR;
      const plotH = h - padT - padB;

      // Gridlines helper
      function buildGridlines(maxVal) {{
        let g = "";
        const steps = 4;
        for (let i = 0; i <= steps; i++) {{
          const ratio = i / steps;
          const y = padT + plotH - ratio * (plotH - 12);
          const labelVal = ratio * maxVal;
          g += `<line x1="${{padL}}" y1="${{y.toFixed(1)}}" x2="${{w - padR}}" y2="${{y.toFixed(1)}}" stroke="var(--border-subtle)" stroke-width="1" />`;
          g += `<text x="${{padL - 8}}" y="${{(y + 3.5).toFixed(1)}}" text-anchor="end" font-size="10.5" font-family="var(--font-mono)" fill="var(--text-muted)">${{i === 0 ? "$0" : fmtUsdCompact(labelVal)}}</text>`;
        }}
        return g;
      }}

      if (selectedPlotMetric && stmtRows.length) {{
        const key = selectedPlotMetric.key;
        document.getElementById("chartTitle").textContent = `${{selectedPlotMetric.label}} — Multi-Period Trajectory`;
        document.getElementById("selectedMetricBadge").textContent = `${{key}} (Click to reset to 4-series view)`;
        const vals = stmtRows.map((r) => Number(r[key] || 0));
        const maxVal = Math.max(1, ...vals.map((v) => Math.abs(v)));
        const n = stmtRows.length;
        const barW = Math.min(64, Math.floor(plotW / Math.max(1, n * 1.8)));

        let barsSvg = buildGridlines(maxVal);
        stmtRows.forEach((r, idx) => {{
          const v = Number(r[key] || 0);
          const x = padL + (idx + 0.5) * (plotW / n) - barW / 2;
          const bh = Math.max(4, Math.round((Math.abs(v) / maxVal) * (plotH - 12)));
          const y = padT + plotH - bh;
          const fill = v >= 0 ? "var(--navy-bar)" : "var(--crimson)";
          barsSvg += `<rect x="${{x}}" y="${{y}}" width="${{barW}}" height="${{bh}}" rx="2" fill="${{fill}}" />`;
          barsSvg += `<text x="${{x + barW / 2}}" y="${{y - 5}}" text-anchor="middle" font-size="10.5" font-family="var(--font-mono)" fill="var(--text)">${{fmtUsdCompact(v)}}</text>`;
          barsSvg += `<text x="${{x + barW / 2}}" y="${{h - 10}}" text-anchor="middle" font-size="11" font-family="var(--font-sans)" font-weight="600" fill="var(--text)">${{escapeHtml(fmtPeriodHeader(r.period_end, idx, n))}}</text>`;
        }});

        document.getElementById("mainComboChart").innerHTML = `
          <svg viewBox="0 0 ${{w}} ${{h}}" width="100%" height="225">
            <line x1="${{padL}}" y1="${{padT + plotH}}" x2="${{w - padR}}" y2="${{padT + plotH}}" stroke="var(--border)" />
            ${{barsSvg}}
          </svg>`;
        return;
      }}

      // Default 4-Series Grouped Bar Chart matching Wireframe:
      // Revenue (#0f172a Deep Navy), Gross Profit (#059669 Emerald), Operating Income (#047857 Deep Emerald), Net Income (#d97706 Slate Gold)
      document.getElementById("chartTitle").textContent = "Multi-Period Financial Trajectory (Revenue • Gross Profit • Operating Income • Net Income)";
      document.getElementById("selectedMetricBadge").textContent = "Click any statement row below to isolate";
      const allVals = [];
      inc.forEach((r) => {{
        const rev = Number(r.revenue || 0);
        const gp = r.gross_profit != null ? Number(r.gross_profit) : Math.max(0, rev - Number(r.cost_of_revenue || 0));
        allVals.push(Math.abs(rev), Math.abs(gp), Math.abs(Number(r.operating_income || 0)), Math.abs(Number(r.net_income || 0)));
      }});
      const maxV = Math.max(1, ...allVals);
      const n = inc.length;
      const groupW = plotW / Math.max(1, n);
      const barW = Math.min(26, Math.floor((groupW - 28) / 4));

      let svgContent = buildGridlines(maxV);
      inc.forEach((r, idx) => {{
        const rev = Number(r.revenue || 0);
        const gp = r.gross_profit != null ? Number(r.gross_profit) : Math.max(0, rev - Number(r.cost_of_revenue || 0));
        const opInc = Number(r.operating_income || 0);
        const netInc = Number(r.net_income || 0);

        const totalBarsW = barW * 4 + 3 * 4;
        const gx = padL + idx * groupW + (groupW - totalBarsW) / 2;
        const series = [
          {{ val: rev, color: "var(--navy-bar)", label: "Revenue" }},
          {{ val: gp, color: "var(--emerald)", label: "Gross Profit" }},
          {{ val: opInc, color: "var(--emerald-dark)", label: "Operating Income" }},
          {{ val: netInc, color: "var(--gold)", label: "Net Income" }},
        ];
        series.forEach((s, sIdx) => {{
          const bh = Math.max(3, Math.round((Math.abs(s.val) / maxV) * (plotH - 12)));
          const x = gx + sIdx * (barW + 4);
          const y = padT + plotH - bh;
          svgContent += `<rect x="${{x}}" y="${{y}}" width="${{barW}}" height="${{bh}}" rx="1.5" fill="${{s.color}}"><title>${{s.label}}: ${{fmtUsdCompact(s.val)}}</title></rect>`;
        }});
        const cx = padL + (idx + 0.5) * groupW;
        svgContent += `<text x="${{cx}}" y="${{h - 10}}" text-anchor="middle" font-size="11" font-family="var(--font-sans)" font-weight="600" fill="var(--text)">${{escapeHtml(fmtPeriodHeader(r.period_end, idx, n))}}</text>`;
      }});

      document.getElementById("mainComboChart").innerHTML = `
        <div style="display:flex;gap:18px;font-size:11.5px;font-weight:600;margin-bottom:6px;justify-content:center;align-items:center;">
          <span style="display:inline-flex;align-items:center;gap:6px;"><span style="display:inline-block;width:16px;height:10px;background:var(--navy-bar);border-radius:2px;"></span> Revenue</span>
          <span style="display:inline-flex;align-items:center;gap:6px;"><span style="display:inline-block;width:16px;height:10px;background:var(--emerald);border-radius:2px;"></span> Gross Profit</span>
          <span style="display:inline-flex;align-items:center;gap:6px;"><span style="display:inline-block;width:16px;height:10px;background:var(--emerald-dark);border-radius:2px;"></span> Operating Income</span>
          <span style="display:inline-flex;align-items:center;gap:6px;"><span style="display:inline-block;width:16px;height:10px;background:var(--gold);border-radius:2px;"></span> Net Income</span>
        </div>
        <svg viewBox="0 0 ${{w}} ${{h}}" width="100%" height="220">
          <line x1="${{padL}}" y1="${{padT + plotH}}" x2="${{w - padR}}" y2="${{padT + plotH}}" stroke="var(--border)" />
          ${{svgContent}}
        </svg>`;
    }}

    function renderMarginTrendChart() {{
      const rats = (currentPayload?.financial_ratios || []).slice().reverse();
      if (!rats.length) return;
      const w = 920;
      const h = 175;
      const padL = 56;
      const padR = 24;
      const padT = 16;
      const padB = 28;
      const plotW = w - padL - padR;
      const plotH = h - padT - padB;

      const vals = [];
      rats.forEach((r) => {{
        [r.gross_margin_pct, r.operating_margin_pct, r.net_margin_pct, r.fcf_margin_pct].forEach((v) => {{
          if (v !== null && v !== undefined) vals.push(Number(v));
        }});
      }});
      const minV = Math.min(0, ...vals);
      const maxV = Math.max(20, ...vals);
      const span = Math.max(1, maxV - minV);

      const xFor = (i) => padL + (rats.length === 1 ? plotW / 2 : (i / (rats.length - 1)) * plotW);
      const yFor = (v) => padT + plotH - ((Number(v || 0) - minV) / span) * plotH;

      const lines = [
        {{ key: "gross_margin_pct", color: "var(--navy-bar)", label: "Gross Margin %" }},
        {{ key: "operating_margin_pct", color: "var(--emerald)", label: "Operating Margin %" }},
        {{ key: "net_margin_pct", color: "var(--gold)", label: "Net Margin %" }},
      ];

      let paths = "";
      lines.forEach((ln) => {{
        const pts = rats
          .map((r, idx) => (r[ln.key] != null ? `${{xFor(idx).toFixed(1)}},${{yFor(r[ln.key]).toFixed(1)}}` : null))
          .filter(Boolean);
        if (pts.length >= 2) {{
          paths += `<polyline fill="none" stroke="${{ln.color}}" stroke-width="2.4" points="${{pts.join(" ")}}" />`;
        }}
        rats.forEach((r, idx) => {{
          if (r[ln.key] != null) {{
            const cx = xFor(idx);
            const cy = yFor(r[ln.key]);
            paths += `<circle cx="${{cx}}" cy="${{cy}}" r="4" fill="${{ln.color}}" />`;
          }}
        }});
      }});

      let labels = "";
      rats.forEach((r, idx) => {{
        labels += `<text x="${{xFor(idx)}}" y="${{h - 8}}" text-anchor="middle" font-size="11" font-family="var(--font-sans)" font-weight="600" fill="var(--text-muted)">${{escapeHtml(fmtPeriodHeader(r.period_end, idx, rats.length))}}</text>`;
      }});

      document.getElementById("marginTrendChart").innerHTML = `
        <div style="display:flex;gap:18px;font-size:11.5px;font-weight:600;margin-bottom:4px;justify-content:center;">
          <span style="display:inline-flex;align-items:center;gap:6px;"><span style="display:inline-block;width:10px;height:10px;background:var(--navy-bar);border-radius:50%;"></span> Gross Margin %</span>
          <span style="display:inline-flex;align-items:center;gap:6px;"><span style="display:inline-block;width:10px;height:10px;background:var(--emerald);border-radius:50%;"></span> Operating Margin %</span>
          <span style="display:inline-flex;align-items:center;gap:6px;"><span style="display:inline-block;width:10px;height:10px;background:var(--gold);border-radius:50%;"></span> Net Margin %</span>
        </div>
        <svg viewBox="0 0 ${{w}} ${{h}}" width="100%" height="165">
          <line x1="${{padL}}" y1="${{padT + plotH}}" x2="${{w - padR}}" y2="${{padT + plotH}}" stroke="var(--border)" />
          ${{paths}}
          ${{labels}}
        </svg>`;
    }}

    function renderRatiosTab() {{
      const dupont = currentPayload?.dupont_roe_by_period || [];
      document.getElementById("dupontContainer").innerHTML = dupont.length
        ? dupont
            .map(
              (d) => `
          <div class="dupont-card">
            <div style="font-size:11px;font-weight:700;color:var(--text-muted);margin-bottom:4px;">PERIOD ${{escapeHtml(d.period_end)}}</div>
            <div style="font-family:var(--font-mono);font-size:16px;font-weight:800;color:var(--primary);margin-bottom:6px;">
              ROE: ${{fmtPct(d.roe_pct, false)}}
            </div>
            <div style="font-size:11.5px;display:flex;flex-direction:column;gap:3px;font-family:var(--font-mono);">
              <span>Net Margin: <strong>${{fmtPct(d.net_profit_margin_pct, false)}}</strong></span>
              <span>× Asset Turnover: <strong>${{d.asset_turnover != null ? d.asset_turnover.toFixed(2) + "x" : "—"}}</strong></span>
              <span>× Equity Multiplier: <strong>${{d.equity_multiplier != null ? d.equity_multiplier.toFixed(2) + "x" : "—"}}</strong></span>
            </div>
          </div>`
            )
            .join("")
        : `<div style="color:var(--text-muted)">No DuPont ROE data available.</div>`;

      const rats = (currentPayload?.financial_ratios || []).slice().reverse();
      if (!rats.length) {{
        document.getElementById("ratiosTableContainer").innerHTML = "";
        return;
      }}
      const ratioDefs = [
        {{ key: "yoy_revenue_growth_pct", label: "YoY Revenue Growth Rate (%)", suffix: "%" }},
        {{ key: "yoy_net_income_growth_pct", label: "YoY Net Income Growth Rate (%)", suffix: "%" }},
        {{ key: "gross_margin_pct", label: "Gross Profit Margin (%)", suffix: "%" }},
        {{ key: "operating_margin_pct", label: "Operating Margin (EBIT %)", suffix: "%" }},
        {{ key: "net_margin_pct", label: "Net Profit Margin (%)", suffix: "%" }},
        {{ key: "fcf_margin_pct", label: "Free Cash Flow Margin (%)", suffix: "%" }},
        {{ key: "roe_pct", label: "Return on Stockholders' Equity (ROE %)", suffix: "%" }},
        {{ key: "roa_pct", label: "Return on Total Assets (ROA %)", suffix: "%" }},
        {{ key: "current_ratio", label: "Current Liquidity Ratio (x)", suffix: "x" }},
        {{ key: "quick_ratio", label: "Quick / Acid-Test Ratio (x)", suffix: "x" }},
        {{ key: "debt_to_equity", label: "Debt-to-Equity Leverage (x)", suffix: "x" }},
        {{ key: "rd_pct_of_revenue", label: "R&D Intensity (% of Revenue)", suffix: "%" }},
      ];

      let html = `<table class="fin-table"><thead><tr><th>Financial Ratio / Institutional Metric</th>`;
      rats.forEach((r, idx) => {{
        html += `<th>${{escapeHtml(fmtPeriodHeader(r.period_end, idx, rats.length))}}</th>`;
      }});
      html += `</tr></thead><tbody>`;
      for (const rd of ratioDefs) {{
        const vals = rats.map((r) => r[rd.key]);
        if (vals.every((v) => v === null || v === undefined)) continue;
        html += `<tr><td>${{escapeHtml(rd.label)}}</td>`;
        for (const v of vals) {{
          html += `<td>${{v !== null && v !== undefined ? Number(v).toFixed(2) + rd.suffix : "—"}}</td>`;
        }}
        html += `</tr>`;
      }}
      html += `</tbody></table>`;
      document.getElementById("ratiosTableContainer").innerHTML = html;
    }}

    const LOCAL_CONCEPT_ALIASES = {{
      revenue: "revenue",
      revenues: "revenue",
      total_revenue: "revenue",
      sales: "revenue",
      salesrevenuenet: "revenue",
      revenuefromcontractwithcustomerexcludingassessedtax: "revenue",
      revenuefromcontractwithcustomerincludingassessedtax: "revenue",
      cost_of_revenue: "cost_of_revenue",
      cost_of_goods_sold: "cost_of_revenue",
      cogs: "cost_of_revenue",
      costofgoodsandservicessold: "cost_of_revenue",
      costofrevenue: "cost_of_revenue",
      gross_profit: "gross_profit",
      grossprofit: "gross_profit",
      r_and_d: "r_and_d",
      rd: "r_and_d",
      research_and_development: "r_and_d",
      researchanddevelopmentexpense: "r_and_d",
      sga: "sga",
      sellinggeneralandadministrativeexpense: "sga",
      operating_expenses: "operating_expenses",
      operatingexpenses: "operating_expenses",
      costsandexpenses: "operating_expenses",
      operating_income: "operating_income",
      operatingincomeloss: "operating_income",
      operating_profit: "operating_income",
      ebit: "operating_income",
      interest_expense: "interest_expense",
      interestexpense: "interest_expense",
      pretax_income: "pretax_income",
      incomelossfromcontinuingoperationsbeforeincometaxesextraordinaryitemsnoncontrollinginterest: "pretax_income",
      income_tax: "income_tax",
      incometaxexpensebenefit: "income_tax",
      net_income: "net_income",
      netincomeloss: "net_income",
      profitloss: "net_income",
      earnings: "net_income",
      eps_diluted: "eps_diluted",
      eps: "eps_diluted",
      earningspersharediluted: "eps_diluted",
      cash_and_equivalents: "cash_and_equivalents",
      cashandcashequivalentsatcarryingvalue: "cash_and_equivalents",
      short_term_investments: "short_term_investments",
      marketablesecuritiescurrent: "short_term_investments",
      total_cash: "total_cash",
      cash: "total_cash",
      accounts_receivable: "accounts_receivable",
      accountsreceivablenetcurrent: "accounts_receivable",
      inventory: "inventory",
      inventorynet: "inventory",
      current_assets: "current_assets",
      assetscurrent: "current_assets",
      ppe_net: "ppe_net",
      propertyplantandequipmentnet: "ppe_net",
      goodwill: "goodwill",
      total_assets: "total_assets",
      assets: "total_assets",
      accounts_payable: "accounts_payable",
      accountspayablecurrent: "accounts_payable",
      current_liabilities: "current_liabilities",
      liabilitiescurrent: "current_liabilities",
      long_term_debt: "long_term_debt",
      longtermdebt: "long_term_debt",
      longtermdebtnoncurrent: "long_term_debt",
      total_debt: "total_debt",
      debt: "total_debt",
      net_debt: "net_debt",
      total_liabilities: "total_liabilities",
      liabilities: "total_liabilities",
      stockholders_equity: "stockholders_equity",
      stockholdersequity: "stockholders_equity",
      equity: "stockholders_equity",
      shares_outstanding: "shares_outstanding",
      shares: "shares_outstanding",
      commonstocksharesoutstanding: "shares_outstanding",
      entitycommonstocksharesoutstanding: "shares_outstanding",
      operating_cash_flow: "operating_cash_flow",
      ocf: "operating_cash_flow",
      netcashprovidedbyusedinoperatingactivities: "operating_cash_flow",
      capex: "capex",
      capital_expenditures: "capex",
      paymentstoacquirepropertyplantandequipment: "capex",
      free_cash_flow: "free_cash_flow",
      fcf: "free_cash_flow",
      freecashflow: "free_cash_flow",
      depreciation_amortization: "depreciation_amortization",
      depreciationdepletionandamortization: "depreciation_amortization",
      sbc: "sbc",
      share_based_compensation: "sbc",
      stock_based_compensation: "sbc",
      sharebasedcompensation: "sbc",
      allocatedsharebasedcompensationexpense: "sbc",
      investing_cash_flow: "investing_cash_flow",
      netcashprovidedbyusedininvestingactivities: "investing_cash_flow",
      financing_cash_flow: "financing_cash_flow",
      netcashprovidedbyusedinfinancingactivities: "financing_cash_flow",
      dividends_paid: "dividends_paid",
      paymentsofdividendscommonstock: "dividends_paid",
      share_repurchases: "share_repurchases",
      buybacks: "share_repurchases",
      paymentsforrepurchaseofcommonstock: "share_repurchases",
    }};

    function resolveCanonicalConceptKey(rawInput) {{
      let clean = String(rawInput || "").trim();
      if (clean.includes(":")) {{
        clean = clean.split(":").pop().trim();
      }}
      const lower = clean.toLowerCase();
      if (LOCAL_CONCEPT_ALIASES[lower]) return LOCAL_CONCEPT_ALIASES[lower];
      const compact = lower.replace(/[^a-z0-9]/g, "");
      if (LOCAL_CONCEPT_ALIASES[compact]) return LOCAL_CONCEPT_ALIASES[compact];
      for (const stmtType of ["income_statement", "balance_sheet", "cash_flow"]) {{
        for (const d of STMT_ROW_DEFS[stmtType] || []) {{
          if (d.key.toLowerCase() === lower || d.label.toLowerCase() === lower) return d.key;
          const defTagClean = String(d.defaultTag || "").split(":").pop().toLowerCase();
          if (defTagClean && defTagClean === compact) return d.key;
        }}
      }}
      return null;
    }}

    function buildLocalConceptHistory(conceptQuery, payload) {{
      const p = payload || currentPayload;
      if (!p) return null;
      const canonicalKey = resolveCanonicalConceptKey(conceptQuery);
      if (!canonicalKey) return null;

      let matchedDef = null;
      let matchedStmtType = null;
      for (const stmtType of ["income_statement", "balance_sheet", "cash_flow"]) {{
        for (const d of STMT_ROW_DEFS[stmtType] || []) {{
          if (d.key === canonicalKey) {{
            matchedDef = d;
            matchedStmtType = stmtType;
            break;
          }}
        }}
        if (matchedDef) break;
      }}
      if (!matchedDef || !matchedStmtType) return null;

      const rows = Array.isArray(p[matchedStmtType]) ? p[matchedStmtType] : [];
      if (!rows.length) return null;

      const rawTag = p.xbrl_tags_used?.[canonicalKey] || matchedDef.defaultTag || `us-gaap:${{canonicalKey}}`;
      const resolvedTag = rawTag.includes(":") ? rawTag : `us-gaap:${{rawTag}}`;
      const formLabel = (p.period_type || "annual") === "quarterly" ? "10-Q" : "10-K";

      const synthSeries = [];
      for (let i = 0; i < rows.length; i++) {{
        const val = rows[i]?.[canonicalKey];
        if (val === null || val === undefined || Number.isNaN(Number(val))) continue;
        const prevVal = i + 1 < rows.length ? rows[i + 1]?.[canonicalKey] : null;
        let pctChange = null;
        if (prevVal !== null && prevVal !== undefined && Number(prevVal) !== 0) {{
          pctChange = Number((((Number(val) - Number(prevVal)) / Math.abs(Number(prevVal))) * 100.0).toFixed(2));
        }}
        synthSeries.push({{
          period_end: rows[i].period_end,
          val: Number(val),
          value: Number(val),
          pct_change: pctChange,
          period_over_period_growth_pct: pctChange,
          form: formLabel,
          source_tag: resolvedTag,
          restatement_audit: {{ was_restated: false, initial_reported_value: null }},
        }});
      }}
      if (!synthSeries.length) return null;

      let cagrVal = matchedDef.cagrKey ? p.multi_period_cagr_summary?.[matchedDef.cagrKey] : null;
      if ((cagrVal === null || cagrVal === undefined) && synthSeries.length >= 2) {{
        const latestV = Number(synthSeries[0].val);
        const oldestV = Number(synthSeries[synthSeries.length - 1].val);
        const nPeriods = synthSeries.length - 1;
        if (latestV > 0 && oldestV > 0 && nPeriods > 0) {{
          cagrVal = Number(((Math.pow(latestV / oldestV, 1.0 / nPeriods) - 1.0) * 100.0).toFixed(2));
        }}
      }}

      return {{
        concept_requested: canonicalKey,
        concept_resolved: resolvedTag,
        cagr_pct: cagrVal,
        concept: {{
          requested: canonicalKey,
          label: matchedDef.label,
          unit: matchedDef.isPerShare ? "USD/shares" : matchedDef.isShares ? "shares" : "USD",
          tags_used: [resolvedTag],
        }},
        summary_statistics: {{
          cagr_pct: cagrVal,
        }},
        time_series: synthSeries,
      }};
    }}

    function renderXbrlTab() {{
      const ch = currentPayload?.initial_concept_history || {{}};
      const series = (ch.time_series || []).slice();
      if (!series.length) {{
        document.getElementById("conceptHistoryChart").innerHTML = `<div style="padding:14px;color:var(--text-muted)">Select any XBRL concept pill above to trace its historical SEC time-series &amp; restatement audit trail.</div>`;
        document.getElementById("conceptHistoryTable").innerHTML = "";
        return;
      }}

      const getVal = (r) => (r.val !== undefined && r.val !== null ? r.val : r.value);
      const getGrowth = (r) => (r.pct_change !== undefined && r.pct_change !== null ? r.pct_change : r.period_over_period_growth_pct);
      const conceptName =
        ch.concept_resolved ||
        (Array.isArray(ch.concept?.tags_used) && ch.concept.tags_used[0]) ||
        ch.concept?.label ||
        ch.concept?.requested ||
        ch.concept_requested ||
        "revenue";
      const unitStr = String(ch.concept?.unit || "USD").toLowerCase();
      const isPerShare = unitStr.includes("/share") || conceptName.toLowerCase().includes("pershare");
      const isShares = !isPerShare && (unitStr === "shares" || conceptName.toLowerCase().includes("sharesoutstanding"));
      const fmtValFn = (v) => fmtTableVal(v, isPerShare, isShares);
      const cagrVal = ch.cagr_pct !== undefined && ch.cagr_pct !== null ? ch.cagr_pct : ch.summary_statistics?.cagr_pct;

      const chron = series.slice().reverse();
      const w = 440;
      const h = 210;
      const padL = 48;
      const padR = 16;
      const padT = 22;
      const padB = 34;
      const plotW = w - padL - padR;
      const plotH = h - padT - padB;
      const maxV = Math.max(1, ...chron.map((r) => Math.abs(Number(getVal(r) || 0))));
      const n = chron.length;
      const barW = Math.min(36, Math.floor(plotW / Math.max(1, n * 1.5)));

      let bars = "";
      chron.forEach((r, idx) => {{
        const v = Number(getVal(r) || 0);
        const x = padL + (idx + 0.5) * (plotW / n) - barW / 2;
        const bh = Math.max(4, Math.round((Math.abs(v) / maxV) * (plotH - 18)));
        const y = padT + plotH - bh;
        const fill = v >= 0 ? "var(--navy-bar)" : "var(--crimson)";
        bars += `<rect x="${{x}}" y="${{y}}" width="${{barW}}" height="${{bh}}" rx="3" fill="${{fill}}" />`;
        bars += `<text x="${{x + barW / 2}}" y="${{y - 5}}" text-anchor="middle" font-size="9" font-family="var(--font-mono)" fill="var(--text)">${{fmtValFn(v)}}</text>`;
        bars += `<text x="${{x + barW / 2}}" y="${{h - 10}}" text-anchor="middle" font-size="9.5" font-family="var(--font-mono)" fill="var(--text-muted)">${{escapeHtml((r.period_end || "").slice(0, 7))}}</text>`;
      }});

      document.getElementById("conceptHistoryChart").innerHTML = `
        <div style="font-size:11.5px;font-weight:700;margin-bottom:6px;">
          Concept: <code>${{escapeHtml(conceptName)}}</code>
          • CAGR: <span class="badge badge-gold">${{fmtPct(cagrVal)}}</span>
        </div>
        <svg viewBox="0 0 ${{w}} ${{h}}" width="100%" height="200">
          <line x1="${{padL}}" y1="${{padT + plotH}}" x2="${{w - padR}}" y2="${{padT + plotH}}" stroke="var(--border)" />
          ${{bars}}
        </svg>`;

      let tbl = `<table class="fin-table"><thead><tr><th>Period End</th><th>Value</th><th>YoY / QoQ %</th><th>Form</th><th>Audit</th><th style="text-align:left;">XBRL Tag</th></tr></thead><tbody>`;
      for (const r of series) {{
        const v = getVal(r);
        const g = getGrowth(r);
        const rest = r.restatement_audit;
        const restHist = Array.isArray(r.restatement_history) ? r.restatement_history : [];
        const wasRestated = Boolean(rest?.was_restated || restHist.length > 0);
        const initReported = rest?.initial_reported_value ?? (restHist.length ? restHist[restHist.length - 1]?.prior_val : null);
        const restBadge = wasRestated
          ? `<span class="badge badge-gold">Restated (Init: ${{fmtValFn(initReported)}})</span>`
          : `<span class="badge badge-emerald">Unchanged</span>`;
        const rawSourceTag = String(r.source_tag || conceptName || "Revenues");
        const formattedSourceTag = rawSourceTag.includes(":") ? rawSourceTag : `us-gaap:${{rawSourceTag}}`;
        tbl += `<tr>
          <td>${{escapeHtml(r.period_end)}}</td>
          <td>${{fmtValFn(v)}}</td>
          <td>${{deltaBadge(g, "%")}}</td>
          <td><span class="badge badge-navy">${{escapeHtml(r.form || "10-K")}}</span></td>
          <td>${{restBadge}}</td>
          <td style="text-align:left;white-space:normal;word-break:break-word;"><span class="xbrl-pill" style="white-space:normal;word-break:break-all;">${{escapeHtml(formattedSourceTag)}}</span></td>
        </tr>`;
      }}
      tbl += `</tbody></table>`;
      document.getElementById("conceptHistoryTable").innerHTML = tbl;
    }}

    function renderFilingsTab() {{
      const allFilings = currentPayload?.filings_dossier?.filings || [];
      const itemQuery = (document.getElementById("item8kInput")?.value || "").trim().toLowerCase();
      const filtered = allFilings.filter((f) => {{
        const formStr = String(f.form || "").toUpperCase();
        const formMatch =
          activeFilingFormFilter === "ALL" ||
          formStr.startsWith(activeFilingFormFilter) ||
          (activeFilingFormFilter === "10-K" && formStr.startsWith("20-F"));
        if (!formMatch) return false;
        if (!itemQuery) return true;
        const itemsArr = Array.isArray(f.items_8k) ? f.items_8k.join(" ") : "";
        const descArr = Array.isArray(f.items_8k_descriptions) ? f.items_8k_descriptions.join(" ") : "";
        const hay = `${{f.form || ""}} ${{f.description || ""}} ${{f.primary_doc_description || ""}} ${{itemsArr}} ${{descArr}}`.toLowerCase();
        return hay.includes(itemQuery);
      }});

      if (!filtered.length) {{
        document.getElementById("filingsTableContainer").innerHTML = `<div style="padding:14px;color:var(--text-muted)">No matching SEC filings in current view. Click "Filter SEC Filings" to query SEC EDGAR.</div>`;
        return 0;
      }}

      let html = `<table class="fin-table"><thead><tr><th>Form</th><th>Filing Date</th><th>Report Period</th><th style="text-align:left;">Description / 8-K Items</th><th>SEC EDGAR Archive Link</th><th>AI Action</th></tr></thead><tbody>`;
      for (const f of filtered) {{
        const itemsList =
          Array.isArray(f.items_8k_descriptions) && f.items_8k_descriptions.length
            ? f.items_8k_descriptions
            : Array.isArray(f.items_8k) && f.items_8k.length
            ? f.items_8k
            : [];
        const itemsStr = itemsList.length
          ? itemsList.join("; ")
          : (f.description || f.primary_doc_description || f.form || "SEC Filing");
        const docUrl = f.document_url || f.filing_index_url || "#";
        html += `<tr>
          <td><span class="badge badge-gold">${{escapeHtml(f.form)}}</span></td>
          <td>${{escapeHtml(f.filing_date)}}</td>
          <td>${{escapeHtml(f.report_date || "—")}}</td>
          <td style="font-family:var(--font-sans);text-align:left;max-width:340px;overflow:hidden;text-overflow:ellipsis;">${{escapeHtml(itemsStr)}}</td>
          <td><a class="ext-link" href="${{escapeHtml(docUrl)}}" target="_blank" rel="noopener noreferrer">Open SEC Filing ↗</a></td>
          <td><button class="btn btn-gold" style="height:26px;padding:2px 8px;font-size:11px;" data-ask-filing="${{escapeHtml(f.form)}}|${{escapeHtml(f.filing_date)}}|${{escapeHtml(docUrl)}}">Ask AI</button></td>
        </tr>`;
      }}
      html += `</tbody></table>`;
      document.getElementById("filingsTableContainer").innerHTML = html;

      document.querySelectorAll("[data-ask-filing]").forEach((btn) => {{
        btn.addEventListener("click", () => {{
          const [form, fdate, url] = btn.getAttribute("data-ask-filing").split("|");
          const comp = currentPayload?.company || {{}};
          sendMcpNotification("ui/message", {{
            role: "user",
            content: [{{
              type: "text",
              text: `Please summarize the key financial takeaways and risk disclosures for ${{comp.name || comp.ticker}} from its Form ${{form}} filed on ${{fdate}} (SEC Archive reference: ${{url}}) using the SEC EDGAR MCP tools.`
            }}],
          }});
          document.getElementById("statusText").textContent = `Sent Form ${{form}} (${{fdate}}) analysis request to AI chat`;
        }});
      }});
      return filtered.length;
    }}

    // =========================================================================
    // 4. Interactive Event Listeners
    // =========================================================================
    document.getElementById("themeToggleBtn").addEventListener("click", () => {{
      const cur = document.documentElement.getAttribute("data-theme") || "light";
      document.documentElement.setAttribute("data-theme", cur === "dark" ? "light" : "dark");
    }});

    document.getElementById("selectedMetricBadge").addEventListener("click", () => {{
      selectedPlotMetric = null;
      renderMainComboChart();
    }});

    document.querySelectorAll(".tab-btn").forEach((btn) => {{
      btn.addEventListener("click", async () => {{
        document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        activeTab = btn.getAttribute("data-tab");
        document.querySelectorAll(".tab-pane").forEach((p) => (p.style.display = "none"));
        document.getElementById(`tab-${{activeTab}}`).style.display = "block";
        if (activeTab === "filings") {{
          const count = renderFilingsTab();
          if (count === 0) {{
            await runFilingsSearch(activeFilingFormFilter);
          }}
        }}
      }});
    }});

    document.querySelectorAll("#stmtSwitcher .pill").forEach((pill) => {{
      pill.addEventListener("click", () => {{
        document.querySelectorAll("#stmtSwitcher .pill").forEach((p) => p.classList.remove("active"));
        pill.classList.add("active");
        activeStmtType = pill.getAttribute("data-stmt");
        selectedPlotMetric = null;
        renderStatementsTab();
      }});
    }});

    document.getElementById("loadDossierBtn").addEventListener("click", async () => {{
      const identifier = document.getElementById("tickerInput").value.trim() || "NVDA";
      const period_type = document.getElementById("periodTypeSelect").value;
      const periods = Number(document.getElementById("periodsSelect").value || 5);
      const data = await callMcpToolWithFallback("open_financial_dossier_workbench_app", {{
        identifier,
        period_type,
        periods,
      }});
      if (data) hydratePayload(data);
    }});

    document.getElementById("tickerInput").addEventListener("keydown", (e) => {{
      if (e.key === "Enter") {{
        e.preventDefault();
        document.getElementById("loadDossierBtn").click();
      }}
    }});

    document.querySelectorAll("#conceptPills .pill").forEach((pill) => {{
      pill.addEventListener("click", async () => {{
        document.querySelectorAll("#conceptPills .pill").forEach((p) => p.classList.remove("active"));
        pill.classList.add("active");
        const concept = pill.getAttribute("data-concept");
        document.getElementById("customConceptInput").value = concept;
        await runConceptTrace(concept);
      }});
    }});

    document.getElementById("traceConceptBtn").addEventListener("click", async () => {{
      const concept = document.getElementById("customConceptInput").value.trim() || "revenue";
      await runConceptTrace(concept);
    }});

    document.getElementById("customConceptInput").addEventListener("keydown", (e) => {{
      if (e.key === "Enter") {{
        e.preventDefault();
        document.getElementById("traceConceptBtn").click();
      }}
    }});

    async function runConceptTrace(concept) {{
      const mySeq = ++traceRequestSeq;
      const canonical = resolveCanonicalConceptKey(concept);
      activeConcept = canonical || String(concept || "revenue").trim().toLowerCase();

      // Sync pill active state if the requested concept matches one of the 9 pills
      document.querySelectorAll("#conceptPills .pill").forEach((p) => {{
        p.classList.toggle("active", p.getAttribute("data-concept") === activeConcept);
      }});

      // Step 1: Instant (<1ms) client-side concept synthesis from already-loaded statement rows
      const localHistory = buildLocalConceptHistory(concept, currentPayload);
      if (localHistory && currentPayload) {{
        currentPayload.initial_concept_history = localHistory;
        renderXbrlTab();
        document.getElementById("statusText").textContent = `Switched to ${{localHistory.concept_resolved}} (fetching 10-period SEC EDGAR restatement audit...)`;
      }}

      // Step 2: Live 10-period SEC EDGAR XBRL concept & restatement audit fetch
      const identifier = document.getElementById("tickerInput").value.trim() || "NVDA";
      const period_type = document.getElementById("periodTypeSelect").value;
      const data = await callMcpToolWithFallback("trace_xbrl_metric_history", {{
        identifier,
        concept_or_tag: canonical || concept,
        period_type,
        periods: 10,
        include_restatement_audit: true,
      }});
      if (mySeq === traceRequestSeq && data) {{
        hydratePayload(data);
      }}
    }}

    async function runFilingsSearch(formFilterOverride) {{
      const effectiveFilter = formFilterOverride || activeFilingFormFilter || "ALL";
      const identifier = document.getElementById("tickerInput").value.trim() || "NVDA";
      const item_8k_filter = document.getElementById("item8kInput").value.trim() || null;
      const form_types = effectiveFilter === "ALL" ? ["10-K", "10-Q", "8-K", "DEF 14A"] : [effectiveFilter];
      const data = await callMcpToolWithFallback("search_and_inspect_sec_filings", {{
        identifier,
        form_types,
        item_8k_filter,
        limit: 25,
      }});
      if (data) {{
        hydratePayload(data);
      }}
    }}

    document.querySelectorAll("#filingFormPills .pill").forEach((pill) => {{
      pill.addEventListener("click", async () => {{
        document.querySelectorAll("#filingFormPills .pill").forEach((p) => p.classList.remove("active"));
        pill.classList.add("active");
        activeFilingFormFilter = pill.getAttribute("data-form");
        const count = renderFilingsTab();
        if (count === 0) {{
          await runFilingsSearch(activeFilingFormFilter);
        }}
      }});
    }});

    document.getElementById("item8kInput").addEventListener("input", () => {{
      renderFilingsTab();
    }});

    document.getElementById("item8kInput").addEventListener("keydown", (e) => {{
      if (e.key === "Enter") {{
        e.preventDefault();
        document.getElementById("searchFilingsBtn").click();
      }}
    }});

    document.getElementById("searchFilingsBtn").addEventListener("click", async () => {{
      renderFilingsTab();
      await runFilingsSearch(activeFilingFormFilter);
    }});

    document.getElementById("askAiCfoBtn").addEventListener("click", () => {{
      const comp = currentPayload?.company || {{}};
      const k = currentPayload?.kpi_summary || {{}};
      const cagr = currentPayload?.multi_period_cagr_summary || {{}};
      sendMcpNotification("ui/message", {{
        role: "user",
        content: [{{
          type: "text",
          text: `Please write an institutional CFO Executive Briefing for ${{comp.name || comp.ticker}} (${{comp.ticker}}, CIK ${{comp.cik}}) based on our SEC EDGAR Financial Workbench:\\n- Latest Period (${{k.latest_period}}): Revenue ${{fmtUsdCompact(k.revenue)}} (${{fmtPct(k.yoy_revenue_growth_pct)}} YoY, Multi-Period CAGR ${{fmtPct(cagr.revenue_cagr_pct)}}), Gross Margin ${{fmtPct(k.gross_margin_pct, false)}}, Operating Income ${{fmtUsdCompact(k.operating_income)}} (OPM ${{fmtPct(k.operating_margin_pct, false)}}), Net Income ${{fmtUsdCompact(k.net_income)}} (Diluted EPS $${{k.eps_diluted}}), Free Cash Flow ${{fmtUsdCompact(k.free_cash_flow)}} (FCF Margin ${{fmtPct(k.fcf_margin_pct, false)}}), Net Debt ${{fmtUsdCompact(k.net_debt)}}.`
        }}],
      }});
      document.getElementById("statusText").textContent = "Sent CFO Executive Briefing prompt to AI host";
    }});

    document.getElementById("askAiDupontBtn").addEventListener("click", () => {{
      const comp = currentPayload?.company || {{}};
      const d = (currentPayload?.dupont_roe_by_period || [])[0] || {{}};
      sendMcpNotification("ui/message", {{
        role: "user",
        content: [{{
          type: "text",
          text: `Please analyze the DuPont 3-Step Return on Equity (ROE) decomposition and operating leverage bridge for ${{comp.name || comp.ticker}} (Latest Period ${{d.period_end}}: ROE ${{fmtPct(d.roe_pct, false)}} = Net Profit Margin ${{fmtPct(d.net_profit_margin_pct, false)}} × Asset Turnover ${{d.asset_turnover}}x × Equity Multiplier ${{d.equity_multiplier}}x).`
        }}],
      }});
      document.getElementById("statusText").textContent = "Sent DuPont ROE & Margin Bridge prompt to AI host";
    }});

    initBridge();
    if (INITIAL_PAYLOAD) hydratePayload(INITIAL_PAYLOAD);
  </script>
</body>
</html>"""
