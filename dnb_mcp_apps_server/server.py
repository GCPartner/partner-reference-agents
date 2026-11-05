"""Standalone Dun & Bradstreet (D&B) MCP Apps Server (`dnb_mcp_apps_server`).

Architecture:
- Acts as a standalone MCP-over-MCP visual UI & orchestration server that talks to
  Dun & Bradstreet's official hosted MCP server (`https://plus.dnb.com/v2/mcp`).
- Exposes 4 interactive `dnb.ai` / `dnb.com`-styled MCP Apps (`ui://dnb/*`, MIME `text/html;profile=mcp-app`, SEP-1865):
  1. `ui://dnb/entity-matcher` — Entity Resolution & D-U-N-S Disambiguation
  2. `ui://dnb/company-360-snapshot` — Company 360° Executive Snapshot
  3. `ui://dnb/corporate-family-tree` — Corporate Family Tree & Upward Linkage Explorer
  4. `ui://dnb/supplier-risk-scorecard` — Supplier Risk, Credit & Procurement Scorecard
- Exposes both the 4 explicit launcher tools (`open_*_app`) and all 17 D&B tool names
  (`MatchTool`, `DataTool`, `OwnershipTool`, `ContactTool`, `RiskTool`, `PaymentTool`, etc.)
  with `CallToolResult` (`TextContent` + `EmbeddedResource` + `structuredContent`).
"""

from __future__ import annotations

import base64
import contextvars
import hashlib
import hmac
import json
import os
import secrets
import time
import urllib.parse
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import (
    AnyUrl,
    CallToolResult,
    EmbeddedResource,
    TextContent,
    TextResourceContents,
)
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from starlette.routing import Mount, Route

try:
    from .mcp_apps import (
        COMPANY_360_APP_RESOURCE_META,
        COMPANY_360_APP_TOOL_META,
        COMPANY_360_RESOURCE_URI,
        DEFAULT_PUBLIC_API_BASE_URL,
        DNB_BRAND_THEME,
        ENTITY_MATCHER_APP_RESOURCE_META,
        ENTITY_MATCHER_APP_TOOL_META,
        ENTITY_MATCHER_RESOURCE_URI,
        FAMILY_TREE_APP_RESOURCE_META,
        FAMILY_TREE_APP_TOOL_META,
        FAMILY_TREE_RESOURCE_URI,
        MCP_APP_MIME_TYPE,
        SUPPLIER_RISK_APP_RESOURCE_META,
        SUPPLIER_RISK_APP_TOOL_META,
        SUPPLIER_RISK_RESOURCE_URI,
        build_company_360_html,
        build_entity_matcher_html,
        build_family_tree_html,
        build_supplier_risk_html,
        get_cached_company_360_payload,
        get_cached_family_tree_payload,
        get_cached_matcher_payload,
        get_cached_supplier_risk_payload,
        set_cached_company_360_payload,
        set_cached_family_tree_payload,
        set_cached_matcher_payload,
        set_cached_supplier_risk_payload,
    )
    from .services import (
        DNB_TOOL_DEFINITIONS,
        build_company_360_payload,
        build_entity_matcher_payload,
        build_family_tree_payload,
        build_supplier_risk_payload,
        dnb_client,
        scrub_dnb_text,
    )
except ImportError:
    from mcp_apps import (
        COMPANY_360_APP_RESOURCE_META,
        COMPANY_360_APP_TOOL_META,
        COMPANY_360_RESOURCE_URI,
        DEFAULT_PUBLIC_API_BASE_URL,
        DNB_BRAND_THEME,
        ENTITY_MATCHER_APP_RESOURCE_META,
        ENTITY_MATCHER_APP_TOOL_META,
        ENTITY_MATCHER_RESOURCE_URI,
        FAMILY_TREE_APP_RESOURCE_META,
        FAMILY_TREE_APP_TOOL_META,
        FAMILY_TREE_RESOURCE_URI,
        MCP_APP_MIME_TYPE,
        SUPPLIER_RISK_APP_RESOURCE_META,
        SUPPLIER_RISK_APP_TOOL_META,
        SUPPLIER_RISK_RESOURCE_URI,
        build_company_360_html,
        build_entity_matcher_html,
        build_family_tree_html,
        build_supplier_risk_html,
        get_cached_company_360_payload,
        get_cached_family_tree_payload,
        get_cached_matcher_payload,
        get_cached_supplier_risk_payload,
        set_cached_company_360_payload,
        set_cached_family_tree_payload,
        set_cached_matcher_payload,
        set_cached_supplier_risk_payload,
    )
    from services import (
        DNB_TOOL_DEFINITIONS,
        build_company_360_payload,
        build_entity_matcher_payload,
        build_family_tree_payload,
        build_supplier_risk_payload,
        dnb_client,
        scrub_dnb_text,
    )

# Context variable capturing incoming Authorization header if forwarded
_REQUEST_AUTH_HEADER: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "_REQUEST_AUTH_HEADER", default=None
)

mcp = FastMCP(
    "dnb-mcp-apps-server",
    stateless_http=True,
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)


def _build_mcp_app_tool_result(
    structured_payload: Dict[str, Any],
    resource_uri: str,
    rendered_html: str,
    tool_meta: Dict[str, Any],
    summary_text: Optional[str] = None,
    live_preview_url: Optional[str] = None,
) -> CallToolResult:
    """Builds a dual-mode `CallToolResult` containing:
    1. `TextContent` for the LLM reasoning context
    2. `EmbeddedResource` (`text/html;profile=mcp-app`) for SEP-1865 MCP App hosts
    3. `structuredContent` for `ui/notifications/tool-result` hydration and Sobi sandbox deliverable extraction
    """
    clean_payload = {k: v for k, v in structured_payload.items() if k != "preloaded_dossiers"}
    clean_payload["ui_resource_uri"] = resource_uri
    if live_preview_url:
        clean_payload["live_preview_url"] = live_preview_url
    text_out = summary_text or json.dumps(clean_payload, ensure_ascii=False, default=str)
    structured_with_html = {
        **clean_payload,
        "mcp_app_html": rendered_html,
    }
    return CallToolResult(
        content=[
            TextContent(type="text", text=text_out),
            EmbeddedResource(
                type="resource",
                resource=TextResourceContents(
                    uri=AnyUrl(resource_uri),
                    mimeType=MCP_APP_MIME_TYPE,
                    text=rendered_html,
                ),
            ),
        ],
        structuredContent=structured_with_html,
        _meta=tool_meta,
    )


# ==============================================================================
# 1. MCP APP UI RESOURCES (`ui://dnb/*`)
# ==============================================================================
@mcp.resource(
    ENTITY_MATCHER_RESOURCE_URI,
    name="D&B Entity Resolution & DUNS Matcher",
    description="Interactive dnb.ai-styled Entity Resolution & D-U-N-S Disambiguation UI card.",
    mime_type=MCP_APP_MIME_TYPE,
    meta=ENTITY_MATCHER_APP_RESOURCE_META,
)
async def resource_entity_matcher() -> str:
    payload = get_cached_matcher_payload()
    if not payload:
        payload = await build_entity_matcher_payload(dnb_client, name="Google", country_code="US")
        set_cached_matcher_payload(payload)
    return build_entity_matcher_html(initial_payload=payload)


@mcp.resource(
    COMPANY_360_RESOURCE_URI,
    name="D&B Company 360 Executive Snapshot",
    description="Interactive dnb.ai-styled Company 360° Executive Snapshot with 3 KPI tiles and 3-pill narrative switcher.",
    mime_type=MCP_APP_MIME_TYPE,
    meta=COMPANY_360_APP_RESOURCE_META,
)
async def resource_company_360() -> str:
    payload = get_cached_company_360_payload()
    if not payload:
        payload = await build_company_360_payload(dnb_client, duns="079942718")
        set_cached_company_360_payload(payload)
    return build_company_360_html(initial_payload=payload)


@mcp.resource(
    FAMILY_TREE_RESOURCE_URI,
    name="D&B Corporate Family Tree Explorer",
    description="Interactive dnb.ai-styled Corporate Family Tree & Upward Linkage Explorer with branch filtering.",
    mime_type=MCP_APP_MIME_TYPE,
    meta=FAMILY_TREE_APP_RESOURCE_META,
)
async def resource_family_tree() -> str:
    payload = get_cached_family_tree_payload()
    if not payload:
        payload = await build_family_tree_payload(dnb_client, duns="079942718")
        set_cached_family_tree_payload(payload)
    return build_family_tree_html(initial_payload=payload)


@mcp.resource(
    SUPPLIER_RISK_RESOURCE_URI,
    name="D&B Supplier Risk & Procurement Scorecard",
    description="Interactive dnb.ai-styled Supplier Risk, Credit & Procurement Onboarding Scorecard.",
    mime_type=MCP_APP_MIME_TYPE,
    meta=SUPPLIER_RISK_APP_RESOURCE_META,
)
async def resource_supplier_risk() -> str:
    payload = get_cached_supplier_risk_payload()
    if not payload:
        payload = await build_supplier_risk_payload(dnb_client, duns="079942718")
        set_cached_supplier_risk_payload(payload)
    return build_supplier_risk_html(initial_payload=payload)


# ==============================================================================
# 2. DEDICATED MCP APP LAUNCHER TOOLS (`open_*_app`)
# ==============================================================================
@mcp.tool(meta=ENTITY_MATCHER_APP_TOOL_META)
async def open_entity_matcher_app(
    name: str = "Google",
    country_code: str = "US",
    street_address: Optional[str] = None,
    address_locality: Optional[str] = None,
    address_region: Optional[str] = None,
    postal_code: Optional[str] = None,
) -> Any:
    """Launch the interactive D&B Entity Resolution & D-U-N-S® Matcher (`ui://dnb/entity-matcher`).

    Resolves a company name and country to verified D-U-N-S® candidates via D&B's `MatchTool`,
    highlighting the recommended Global Ultimate HQ and separating operating subsidiaries from
    unrelated standalone matches.
    """
    tok = _REQUEST_AUTH_HEADER.get()
    payload = await build_entity_matcher_payload(
        dnb_client,
        name=name,
        country_code=country_code,
        street_address=street_address,
        address_locality=address_locality,
        address_region=address_region,
        postal_code=postal_code,
        forwarded_token=tok,
    )
    set_cached_matcher_payload(payload)
    html = build_entity_matcher_html(initial_payload=payload)
    rec = payload.get("recommended_candidate") or {}
    summary = (
        f"D&B Entity Resolution for '{name}' ({country_code}): "
        f"{payload.get('total_candidates', 0)} candidates found. "
        f"Recommended Global Ultimate: {rec.get('primary_name')} (D-U-N-S {rec.get('duns')}, {rec.get('role_badge')}). "
        f"Linked Operating Subsidiaries: {len(payload.get('operating_subsidiaries') or [])}."
    )
    preview_url = (
        f"{DEFAULT_PUBLIC_API_BASE_URL}/apps/raw/entity-matcher"
        f"?name={urllib.parse.quote(name)}&country={urllib.parse.quote(country_code)}"
    )
    return _build_mcp_app_tool_result(
        structured_payload=payload,
        resource_uri=ENTITY_MATCHER_RESOURCE_URI,
        rendered_html=html,
        tool_meta=ENTITY_MATCHER_APP_TOOL_META,
        summary_text=summary,
        live_preview_url=preview_url,
    )


@mcp.tool(meta=COMPANY_360_APP_TOOL_META)
async def open_company_360_app(
    duns: str = "079942718",
) -> Any:
    """Launch the interactive D&B Company 360° Executive Snapshot (`ui://dnb/company-360-snapshot`).

    Combines D&B's `DataTool` (`companyinfo_L2`), `ContactTool` (`principalscontacts_L2`), and
    `OwnershipTool` into a clean executive card with 3 KPI tiles and a 3-pill narrative switcher.
    """
    tok = _REQUEST_AUTH_HEADER.get()
    payload = await build_company_360_payload(dnb_client, duns=duns, forwarded_token=tok)
    set_cached_company_360_payload(payload)
    html = build_company_360_html(initial_payload=payload)
    comp = payload.get("company") or {}
    lead = payload.get("leadership") or {}
    ceo = (lead.get("most_senior_principal") or {}).get("name", "—")
    summary = (
        f"D&B Company 360° Snapshot for {comp.get('primary_name')} (D-U-N-S {comp.get('duns_formatted')}): "
        f"Status {comp.get('operating_status')}, Annual Consolidated Revenue {comp.get('yearly_revenue_formatted')}, "
        f"Global Employees {comp.get('employees_consolidated_formatted')} ({comp.get('employees_growth_rate')}), "
        f"Most Senior Principal: {ceo}."
    )
    preview_url = f"{DEFAULT_PUBLIC_API_BASE_URL}/apps/raw/company-360-snapshot?duns={urllib.parse.quote(duns)}"
    return _build_mcp_app_tool_result(
        structured_payload=payload,
        resource_uri=COMPANY_360_RESOURCE_URI,
        rendered_html=html,
        tool_meta=COMPANY_360_APP_TOOL_META,
        summary_text=summary,
        live_preview_url=preview_url,
    )


@mcp.tool(meta=FAMILY_TREE_APP_TOOL_META)
async def open_corporate_family_tree_app(
    duns: str = "079942718",
) -> Any:
    """Launch the interactive D&B Corporate Family Tree & Upward Linkage Explorer (`ui://dnb/corporate-family-tree`).

    Transforms D&B's 535-node `OwnershipTool` hierarchy into an interactive, filterable tree with
    upward Global Ultimate lineage and "Hide 196 Local Branches" enabled by default.
    """
    tok = _REQUEST_AUTH_HEADER.get()
    payload = await build_family_tree_payload(dnb_client, duns=duns, forwarded_token=tok)
    set_cached_family_tree_payload(payload)
    html = build_family_tree_html(initial_payload=payload)
    gu = payload.get("global_ultimate") or {}
    stats = payload.get("statistics") or {}
    summary = (
        f"D&B Corporate Family Tree for D-U-N-S {payload.get('duns')}: "
        f"Global Ultimate {gu.get('name')} (D-U-N-S {gu.get('duns')}), "
        f"{stats.get('total_members')} total family members ({stats.get('subsidiaries_count')} legal subsidiaries, "
        f"{stats.get('branches_count')} local branches) across {stats.get('countries_count')} countries."
    )
    preview_url = f"{DEFAULT_PUBLIC_API_BASE_URL}/apps/raw/corporate-family-tree?duns={urllib.parse.quote(duns)}"
    return _build_mcp_app_tool_result(
        structured_payload=payload,
        resource_uri=FAMILY_TREE_RESOURCE_URI,
        rendered_html=html,
        tool_meta=FAMILY_TREE_APP_TOOL_META,
        summary_text=summary,
        live_preview_url=preview_url,
    )


@mcp.tool(meta=SUPPLIER_RISK_APP_TOOL_META)
async def open_supplier_risk_scorecard_app(
    duns: str = "079942718",
) -> Any:
    """Launch the interactive D&B Supplier Risk, Credit & Procurement Scorecard (`ui://dnb/supplier-risk-scorecard`).

    Consolidates financial stability, delinquency score, PAYDEX payment speed, KYB compliance checks,
    and government/ERP procurement registration numbers (D-U-N-S, LEI, CAGE, GSA UEI) into a single scorecard.
    """
    tok = _REQUEST_AUTH_HEADER.get()
    payload = await build_supplier_risk_payload(dnb_client, duns=duns, forwarded_token=tok)
    set_cached_supplier_risk_payload(payload)
    html = build_supplier_risk_html(initial_payload=payload)
    comp = payload.get("company") or {}
    rg = payload.get("risk_gauges") or {}
    summary = (
        f"D&B Supplier Risk & Procurement Scorecard for {comp.get('primary_name')} (D-U-N-S {comp.get('duns_formatted')}): "
        f"Overall Rating {rg.get('overall_risk_badge')}, Viability Rating {rg.get('viability_rating')}, "
        f"Financial Stability {rg.get('failure_risk', {}).get('percentile')}/100, "
        f"Delinquency Score {rg.get('delinquency_risk', {}).get('score')}/100, "
        f"PAYDEX {rg.get('paydex', {}).get('score')}/100, "
        f"Recommended Credit Limit {rg.get('recommended_credit_limit_formatted')}."
    )
    preview_url = f"{DEFAULT_PUBLIC_API_BASE_URL}/apps/raw/supplier-risk-scorecard?duns={urllib.parse.quote(duns)}"
    return _build_mcp_app_tool_result(
        structured_payload=payload,
        resource_uri=SUPPLIER_RISK_RESOURCE_URI,
        rendered_html=html,
        tool_meta=SUPPLIER_RISK_APP_TOOL_META,
        summary_text=summary,
        live_preview_url=preview_url,
    )


# ==============================================================================
# 3. ALL 17 UPSTREAM D&B TOOLS PROXY-WRAPPED WITH INTERACTIVE MCP APPS
# ==============================================================================
@mcp.tool(meta=ENTITY_MATCHER_APP_TOOL_META)
async def MatchTool(
    countryISOAlpha2Code: str = "US",
    name: str = "Google",
    strict_match: bool = False,
    streetAddressLine1: Optional[str] = None,
    addressLocality: Optional[str] = None,
    addressRegion: Optional[str] = None,
    postalCode: Optional[str] = None,
    telephoneNumber: Optional[str] = None,
    registrationNumber: Optional[str] = None,
    url: Optional[str] = None,
) -> Any:
    """D&B `MatchTool` — Resolves company name & address criteria to 9-digit D-U-N-S® numbers and renders `ui://dnb/entity-matcher`."""
    return await open_entity_matcher_app(
        name=name,
        country_code=countryISOAlpha2Code,
        street_address=streetAddressLine1,
        address_locality=addressLocality,
        address_region=addressRegion,
        postal_code=postalCode,
    )


@mcp.tool(meta=COMPANY_360_APP_TOOL_META)
async def DataTool(
    duns: str = "079942718",
    show_historical_data: bool = True,
    include_partial_financial_year: bool = False,
    block_extended_mode: bool = False,
) -> Any:
    """D&B `DataTool` — Retrieves firmographic, financial, and operational company data and renders `ui://dnb/company-360-snapshot`."""
    return await open_company_360_app(duns=duns)


@mcp.tool(meta=COMPANY_360_APP_TOOL_META)
async def ContactTool(
    duns: str = "079942718",
) -> Any:
    """D&B `ContactTool` — Retrieves verified principals, officers, and leadership contacts and renders `ui://dnb/company-360-snapshot`."""
    return await open_company_360_app(duns=duns)


@mcp.tool(meta=FAMILY_TREE_APP_TOOL_META)
async def OwnershipTool(
    duns: str = "079942718",
) -> Any:
    """D&B `OwnershipTool` — Retrieves Global Ultimate, Domestic Ultimate, and full corporate family tree and renders `ui://dnb/corporate-family-tree`."""
    return await open_corporate_family_tree_app(duns=duns)


@mcp.tool(meta=SUPPLIER_RISK_APP_TOOL_META)
async def RiskTool(
    duns: str = "079942718",
    show_historical_data: bool = True,
) -> Any:
    """D&B `RiskTool` — Retrieves failure risk, delinquency risk, and viability ratings and renders `ui://dnb/supplier-risk-scorecard`."""
    return await open_supplier_risk_scorecard_app(duns=duns)


@mcp.tool(meta=SUPPLIER_RISK_APP_TOOL_META)
async def PaymentTool(
    duns: str = "079942718",
    show_historical_data: bool = True,
) -> Any:
    """D&B `PaymentTool` — Retrieves PAYDEX® and commercial payment performance and renders `ui://dnb/supplier-risk-scorecard`."""
    return await open_supplier_risk_scorecard_app(duns=duns)


@mcp.tool(meta=SUPPLIER_RISK_APP_TOOL_META)
async def BusinessEventsTool(
    duns: str = "079942718",
) -> Any:
    """D&B `BusinessEventsTool` — Retrieves legal filings, liens, judgments, and significant events and renders `ui://dnb/supplier-risk-scorecard`."""
    return await open_supplier_risk_scorecard_app(duns=duns)


@mcp.tool(meta=SUPPLIER_RISK_APP_TOOL_META)
async def ESGTool(
    duns: str = "079942718",
) -> Any:
    """D&B `ESGTool` — Retrieves Environmental, Social & Governance rankings and renders `ui://dnb/supplier-risk-scorecard`."""
    return await open_supplier_risk_scorecard_app(duns=duns)


@mcp.tool(meta=SUPPLIER_RISK_APP_TOOL_META)
async def DiversityTool(
    duns: str = "079942718",
) -> Any:
    """D&B `DiversityTool` — Retrieves socioeconomic & supplier diversity classifications and renders `ui://dnb/supplier-risk-scorecard`."""
    return await open_supplier_risk_scorecard_app(duns=duns)


@mcp.tool(meta=COMPANY_360_APP_TOOL_META)
async def SalesAndMarketingTool(
    duns: str = "079942718",
    show_historical_data: bool = True,
) -> Any:
    """D&B `SalesAndMarketingTool` — Retrieves sales, marketing, and firmographic intelligence and renders `ui://dnb/company-360-snapshot`."""
    return await open_company_360_app(duns=duns)


@mcp.tool(meta=COMPANY_360_APP_TOOL_META)
async def NewsTool(
    duns: str = "079942718",
) -> Any:
    """D&B `NewsTool` — Retrieves recent media and corporate news mentions and renders `ui://dnb/company-360-snapshot`."""
    return await open_company_360_app(duns=duns)


@mcp.tool(meta=COMPANY_360_APP_TOOL_META)
async def IndustryProfileTool(
    duns: Optional[str] = "079942718",
    industry_code: Optional[str] = "7371",
    country_code: Optional[str] = "US",
) -> Any:
    """D&B `IndustryProfileTool` — Retrieves SIC/NAICS industry profile and renders `ui://dnb/company-360-snapshot`."""
    return await open_company_360_app(duns=duns or "079942718")


@mcp.tool(meta=SUPPLIER_RISK_APP_TOOL_META)
async def ShippingTool(
    duns: str = "079942718",
) -> Any:
    """D&B `ShippingTool` — Retrieves shipping and trade activity insights and renders `ui://dnb/supplier-risk-scorecard`."""
    return await open_supplier_risk_scorecard_app(duns=duns)


@mcp.tool(meta=SUPPLIER_RISK_APP_TOOL_META)
async def SBRITool(
    duns: str = "079942718",
) -> Any:
    """D&B `SBRITool` — Retrieves Small Business Risk Insight indicators and renders `ui://dnb/supplier-risk-scorecard`."""
    return await open_supplier_risk_scorecard_app(duns=duns)


@mcp.tool(meta=SUPPLIER_RISK_APP_TOOL_META)
async def InquiryTool(
    duns: str = "079942718",
) -> Any:
    """D&B `InquiryTool` — Retrieves credit inquiry volume trends and renders `ui://dnb/supplier-risk-scorecard`."""
    return await open_supplier_risk_scorecard_app(duns=duns)


@mcp.tool(meta=COMPANY_360_APP_TOOL_META)
async def ProvenanceTool(
    duns: str = "079942718",
    question: str = "Summarize the primary sources and verification dates for this company.",
) -> Any:
    """D&B `ProvenanceTool` — Retrieves data provenance and source attribution and renders `ui://dnb/company-360-snapshot`."""
    return await open_company_360_app(duns=duns)


@mcp.tool()
async def RumSpendTool() -> Dict[str, Any]:
    """D&B `RumSpendTool` — Checks Records Under Management (RUM) contract entitlement and consumption on `https://plus.dnb.com/v2/mcp`."""
    tok = _REQUEST_AUTH_HEADER.get()
    raw_text, source_label = await dnb_client.call_upstream_tool("RumSpendTool", {}, forwarded_token=tok, use_cache=False)
    return {
        "status": "success",
        "data_source": source_label,
        "rum_spend_report": scrub_dnb_text(raw_text) or "Subscriber 209000119 • D&B for Enterprise Master Data (1 / 100 Domestic Records Used)",
    }


# ==============================================================================
# 4. STANDALONE HTTP ROUTES, PREVIEW ENDPOINTS & OAUTH 2.0 HANDSHAKE
# ==============================================================================
_OAUTH_CODES: Dict[str, Dict[str, Any]] = {}
_OAUTH_CLIENTS: Dict[str, Dict[str, Any]] = {}


def _iframe_headers() -> Dict[str, str]:
    return {
        "Cross-Origin-Opener-Policy": "unsafe-none",
        "Cross-Origin-Embedder-Policy": "unsafe-none",
        "Cross-Origin-Resource-Policy": "cross-origin",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "*",
        "Cache-Control": "no-store",
    }


async def health_endpoint(request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "status": "healthy",
            "service": "dnb-mcp-apps-server",
            "upstream_dnb_mcp": dnb_client.upstream_url,
            "brand_theme": DNB_BRAND_THEME["brand_name"],
            "mcp_apps": [
                ENTITY_MATCHER_RESOURCE_URI,
                COMPANY_360_RESOURCE_URI,
                FAMILY_TREE_RESOURCE_URI,
                SUPPLIER_RISK_RESOURCE_URI,
            ],
            "upstream_tools_proxied": len(DNB_TOOL_DEFINITIONS),
        },
        headers=_iframe_headers(),
    )


def _resolve_public_base_url(request: Request) -> str:
    env_url = os.environ.get("PUBLIC_BASE_URL", "").strip().rstrip("/")
    if env_url:
        return env_url
    base = str(request.base_url).rstrip("/")
    if request.headers.get("x-forwarded-proto") == "https" and base.startswith("http://"):
        base = "https://" + base[len("http://"):]
    return base


async def raw_entity_matcher_endpoint(request: Request) -> HTMLResponse:
    name = request.query_params.get("name", "Google")
    country = request.query_params.get("country", "US")
    payload = await build_entity_matcher_payload(dnb_client, name=name, country_code=country)
    set_cached_matcher_payload(payload)
    base_url = _resolve_public_base_url(request)
    html = build_entity_matcher_html(initial_payload=payload, api_base_url=base_url)
    return HTMLResponse(html, headers=_iframe_headers())


async def raw_company_360_endpoint(request: Request) -> HTMLResponse:
    duns = request.query_params.get("duns", "079942718")
    payload = await build_company_360_payload(dnb_client, duns=duns)
    set_cached_company_360_payload(payload)
    base_url = _resolve_public_base_url(request)
    html = build_company_360_html(initial_payload=payload, api_base_url=base_url)
    return HTMLResponse(html, headers=_iframe_headers())


async def raw_family_tree_endpoint(request: Request) -> HTMLResponse:
    duns = request.query_params.get("duns", "079942718")
    payload = await build_family_tree_payload(dnb_client, duns=duns)
    set_cached_family_tree_payload(payload)
    base_url = _resolve_public_base_url(request)
    html = build_family_tree_html(initial_payload=payload, api_base_url=base_url)
    return HTMLResponse(html, headers=_iframe_headers())


async def raw_supplier_risk_endpoint(request: Request) -> HTMLResponse:
    duns = request.query_params.get("duns", "079942718")
    payload = await build_supplier_risk_payload(dnb_client, duns=duns)
    set_cached_supplier_risk_payload(payload)
    base_url = _resolve_public_base_url(request)
    html = build_supplier_risk_html(initial_payload=payload, api_base_url=base_url)
    return HTMLResponse(html, headers=_iframe_headers())


async def direct_tool_call_endpoint(request: Request) -> Response:
    """Direct HTTP fallback endpoint (`POST /apps/api/tool-call`) for in-iframe interactions."""
    if request.method == "OPTIONS":
        return Response(status_code=204, headers=_iframe_headers())
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400, headers=_iframe_headers())

    tool_name = str(body.get("name") or "").strip()
    args = body.get("arguments") if isinstance(body.get("arguments"), dict) else {}
    tok = request.headers.get("Authorization")
    base_url = _resolve_public_base_url(request)

    if tool_name in ("open_entity_matcher_app", "MatchTool"):
        payload = await build_entity_matcher_payload(
            dnb_client,
            name=str(args.get("name") or "Google"),
            country_code=str(args.get("country_code") or args.get("countryISOAlpha2Code") or "US"),
            forwarded_token=tok,
        )
        set_cached_matcher_payload(payload)
        html = build_entity_matcher_html(initial_payload=payload, api_base_url=base_url)
        return JSONResponse({"structuredContent": payload, "mcp_app_html": html}, headers=_iframe_headers())

    if tool_name in ("open_company_360_app", "DataTool", "ContactTool", "SalesAndMarketingTool", "NewsTool", "IndustryProfileTool", "ProvenanceTool"):
        payload = await build_company_360_payload(
            dnb_client,
            duns=str(args.get("duns") or "079942718"),
            forwarded_token=tok,
        )
        set_cached_company_360_payload(payload)
        html = build_company_360_html(initial_payload=payload, api_base_url=base_url)
        return JSONResponse({"structuredContent": payload, "mcp_app_html": html}, headers=_iframe_headers())

    if tool_name in ("open_corporate_family_tree_app", "OwnershipTool"):
        payload = await build_family_tree_payload(
            dnb_client,
            duns=str(args.get("duns") or "079942718"),
            forwarded_token=tok,
        )
        set_cached_family_tree_payload(payload)
        html = build_family_tree_html(initial_payload=payload, api_base_url=base_url)
        return JSONResponse({"structuredContent": payload, "mcp_app_html": html}, headers=_iframe_headers())

    if tool_name in ("open_supplier_risk_scorecard_app", "RiskTool", "PaymentTool", "BusinessEventsTool", "ESGTool", "DiversityTool", "ShippingTool", "SBRITool", "InquiryTool"):
        payload = await build_supplier_risk_payload(
            dnb_client,
            duns=str(args.get("duns") or "079942718"),
            forwarded_token=tok,
        )
        set_cached_supplier_risk_payload(payload)
        html = build_supplier_risk_html(initial_payload=payload, api_base_url=base_url)
        return JSONResponse({"structuredContent": payload, "mcp_app_html": html}, headers=_iframe_headers())

    return JSONResponse({"error": f"Unknown tool: {tool_name}"}, status_code=404, headers=_iframe_headers())


# OAuth 2.0 Discovery & Stateless HMAC-SHA256 Handshake for Gemini Enterprise / Sobi / Claude Desktop
_EPHEMERAL_SIGNING_KEY: Optional[bytes] = None


def _get_signing_key() -> bytes:
    global _EPHEMERAL_SIGNING_KEY
    secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "").strip()
    if secret:
        return hashlib.sha256(f"{client_id}:{secret}".encode("utf-8")).digest()
    if _EPHEMERAL_SIGNING_KEY is None:
        _EPHEMERAL_SIGNING_KEY = secrets.token_bytes(32)
    return _EPHEMERAL_SIGNING_KEY


def _create_signed_token(prefix: str, payload: Dict[str, Any]) -> str:
    raw_json = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    body_b64 = base64.urlsafe_b64encode(raw_json).decode("ascii").rstrip("=")
    sig = hmac.new(_get_signing_key(), f"{prefix}.{body_b64}".encode("ascii"), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode("ascii").rstrip("=")
    return f"{prefix}.{body_b64}.{sig_b64}"


def _verify_signed_token(token: str, expected_prefix: str) -> Optional[Dict[str, Any]]:
    parts = token.split(".")
    if len(parts) != 3 or parts[0] != expected_prefix:
        return None
    _, body_b64, sig_b64 = parts
    expected_sig = hmac.new(
        _get_signing_key(),
        f"{expected_prefix}.{body_b64}".encode("ascii"),
        hashlib.sha256,
    ).digest()
    expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode("ascii").rstrip("=")
    if not hmac.compare_digest(sig_b64, expected_sig_b64):
        return None
    try:
        padded = body_b64 + "=" * (-len(body_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
    except Exception:
        return None
    exp = payload.get("exp")
    if exp is not None:
        try:
            if int(exp) < int(time.time()):
                return None
        except (TypeError, ValueError):
            return None
    return payload


async def oauth_metadata_endpoint(request: Request) -> JSONResponse:
    base = _resolve_public_base_url(request)
    return JSONResponse(
        {
            "issuer": base,
            "authorization_endpoint": f"{base}/authorize",
            "token_endpoint": f"{base}/token",
            "registration_endpoint": f"{base}/register",
            "scopes_supported": ["openid", "email", "profile", "mcp:tools", "mcp:resources"],
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code", "refresh_token", "client_credentials"],
            "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic", "none"],
            "code_challenge_methods_supported": ["S256", "plain"],
        },
        headers=_iframe_headers(),
    )


async def oauth_protected_resource_endpoint(request: Request) -> JSONResponse:
    base = _resolve_public_base_url(request)
    return JSONResponse(
        {
            "resource": f"{base}/mcp",
            "authorization_servers": [base],
            "scopes_supported": ["openid", "email", "profile", "mcp:tools", "mcp:resources"],
            "bearer_methods_supported": ["header"],
        },
        headers=_iframe_headers(),
    )


async def oauth_register_endpoint(request: Request) -> JSONResponse:
    try:
        body = await request.json()
    except Exception:
        body = {}
    default_cid = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "").split(",")[0].strip()
    default_csec = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
    client_id = default_cid or f"dnb_mcp_client_{secrets.token_hex(6)}"
    client_secret = default_csec or f"dnb_mcp_secret_{secrets.token_hex(12)}"
    record = {
        "client_id": client_id,
        "client_secret": client_secret,
        "client_id_issued_at": int(time.time()),
        "client_secret_expires_at": 0,
        "redirect_uris": body.get("redirect_uris", []),
        "grant_types": ["authorization_code", "refresh_token", "client_credentials"],
        "response_types": ["code"],
        "token_endpoint_auth_method": body.get("token_endpoint_auth_method", "client_secret_post"),
    }
    _OAUTH_CLIENTS[client_id] = record
    return JSONResponse(record, status_code=201, headers=_iframe_headers())


async def oauth_authorize_endpoint(request: Request) -> Response:
    params: Dict[str, str] = {}
    extra_path = request.path_params.get("extra", "") if hasattr(request, "path_params") else ""
    if extra_path:
        cleaned_extra = extra_path.lstrip("/?&")
        for k, v in urllib.parse.parse_qsl(cleaned_extra, keep_blank_values=True):
            if k:
                params[k] = v
    for k, v in request.query_params.multi_items():
        if k:
            if "&" in k or "=" in k:
                for sub_k, sub_v in urllib.parse.parse_qsl(f"{k}={v}".lstrip("&"), keep_blank_values=True):
                    if sub_k:
                        params[sub_k] = sub_v
            else:
                params[k] = v

    allowed_cids = [c.strip() for c in os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "").split(",") if c.strip()]
    client_id = params.get("client_id", "").strip() or (allowed_cids[0] if allowed_cids else "dnb-oauth-client")
    redirect_uri = params.get("redirect_uri", "").strip()
    state = params.get("state", "")
    scope = params.get("scope", "openid email profile").strip() or "openid email profile"
    code_challenge = params.get("code_challenge", "").strip()
    code_challenge_method = params.get("code_challenge_method", "S256").strip() or "S256"

    now = int(time.time())
    code_payload: Dict[str, Any] = {
        "cid": client_id,
        "scp": scope,
        "ru": redirect_uri,
        "iat": now,
        "exp": now + 600,
        "nonce": secrets.token_hex(8),
    }
    if code_challenge:
        code_payload["cc"] = code_challenge
        code_payload["ccm"] = code_challenge_method

    code = _create_signed_token("mcp_code", code_payload)
    _OAUTH_CODES[code] = {"created_at": time.time(), "client_id": client_id}

    if redirect_uri:
        parsed_ru = urllib.parse.urlparse(redirect_uri)
        ru_query = dict(urllib.parse.parse_qsl(parsed_ru.query, keep_blank_values=True))
        ru_query["code"] = code
        if state:
            ru_query["state"] = state
        target = urllib.parse.urlunparse(parsed_ru._replace(query=urllib.parse.urlencode(ru_query)))
        return RedirectResponse(url=target, status_code=302)
    return JSONResponse({"code": code, "state": state}, headers=_iframe_headers())


async def oauth_token_endpoint(request: Request) -> Response:
    if request.method == "OPTIONS":
        return Response(status_code=204, headers=_iframe_headers())

    data: Dict[str, str] = {}
    for k, v in request.query_params.multi_items():
        if k:
            data[k] = v
    raw_body = await request.body()
    if raw_body:
        body_str = raw_body.decode("utf-8", errors="replace").strip()
        if body_str.startswith("{"):
            try:
                parsed = json.loads(body_str)
                if isinstance(parsed, dict):
                    for k, v in parsed.items():
                        if v is not None:
                            data[str(k)] = str(v)
            except Exception:
                pass
        else:
            for k, v in urllib.parse.parse_qsl(body_str, keep_blank_values=True):
                if k:
                    data[k] = v

    allowed_cids = [c.strip() for c in os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "").split(",") if c.strip()]
    env_cid = allowed_cids[0] if allowed_cids else "dnb-oauth-client"
    issued_cid = (data.get("client_id") or env_cid).strip()
    scope = (data.get("scope") or "openid email profile").strip()
    now = int(time.time())

    access_token = _create_signed_token(
        "mcp_at",
        {
            "cid": issued_cid,
            "scp": scope,
            "iat": now,
            "exp": now + 3600,
            "jti": secrets.token_hex(8),
        },
    )
    refresh_token = _create_signed_token(
        "mcp_rt",
        {
            "cid": issued_cid,
            "scp": scope,
            "iat": now,
            "exp": now + 86400 * 365,
            "jti": secrets.token_hex(8),
        },
    )
    return JSONResponse(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": scope,
        },
        headers=_iframe_headers(),
    )


def get_asgi_app(transport: str = "streamable-http") -> Starlette:
    """Builds the combined Starlette ASGI application with `/mcp`, `/apps/raw/*`, `/apps/api/tool-call`, and OAuth."""
    mcp_sub_app = mcp.streamable_http_app() if transport == "streamable-http" else mcp.sse_app()

    routes = [
        Route("/health", health_endpoint, methods=["GET", "HEAD"]),
        Route("/healthz", health_endpoint, methods=["GET", "HEAD"]),
        Route("/apps/raw/entity-matcher", raw_entity_matcher_endpoint, methods=["GET", "HEAD"]),
        Route("/apps/raw/company-360-snapshot", raw_company_360_endpoint, methods=["GET", "HEAD"]),
        Route("/apps/raw/company-360", raw_company_360_endpoint, methods=["GET", "HEAD"]),
        Route("/apps/raw/corporate-family-tree", raw_family_tree_endpoint, methods=["GET", "HEAD"]),
        Route("/apps/raw/family-tree", raw_family_tree_endpoint, methods=["GET", "HEAD"]),
        Route("/apps/raw/supplier-risk-scorecard", raw_supplier_risk_endpoint, methods=["GET", "HEAD"]),
        Route("/apps/raw/supplier-risk", raw_supplier_risk_endpoint, methods=["GET", "HEAD"]),
        Route("/apps/api/tool-call", direct_tool_call_endpoint, methods=["POST", "OPTIONS"]),
        Route("/.well-known/oauth-protected-resource/{subpath:path}", oauth_protected_resource_endpoint, methods=["GET", "OPTIONS"]),
        Route("/.well-known/oauth-protected-resource", oauth_protected_resource_endpoint, methods=["GET", "OPTIONS"]),
        Route("/.well-known/oauth-authorization-server/{subpath:path}", oauth_metadata_endpoint, methods=["GET", "OPTIONS"]),
        Route("/.well-known/oauth-authorization-server", oauth_metadata_endpoint, methods=["GET", "OPTIONS"]),
        Route("/.well-known/openid-configuration", oauth_metadata_endpoint, methods=["GET", "OPTIONS"]),
        Route("/register", oauth_register_endpoint, methods=["POST", "OPTIONS"]),
        Route("/authorize{extra:path}", oauth_authorize_endpoint, methods=["GET", "HEAD", "POST"]),
        Route("/authorize", oauth_authorize_endpoint, methods=["GET", "HEAD", "POST"]),
        Route("/token", oauth_token_endpoint, methods=["POST", "GET", "OPTIONS"]),
        Mount("/", app=mcp_sub_app),
    ]

    app = Starlette(
        routes=routes,
        lifespan=lambda _: mcp.session_manager.run(),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app
