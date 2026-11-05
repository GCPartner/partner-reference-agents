"""SEC EDGAR Interactive MCP Apps Server (`ui://sec-edgar/*`, `text/html;profile=mcp-app`) for Google Cloud Run.

Built using the Cloud Run MCP Server Creator, API-to-MCP Wrapper, and MCP Apps Developer skills.
Enhances the 7 coarse-grained SEC EDGAR financial tools with 2 interactive Apex Capital Institutional Research MCP Apps:
1. `ui://sec-edgar/financial-dossier-workbench` (`open_financial_dossier_workbench_app`)
2. `ui://sec-edgar/peer-industry-comparator` (`open_peer_industry_comparator_app`)
"""

import asyncio
import base64
from contextvars import ContextVar
import hashlib
import hmac
import json
import logging
import os
import secrets
import time
import urllib.parse
from typing import Any, Dict, List, Literal, Optional

import httpx
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import TransportSecuritySettings
from mcp.types import (
    CallToolResult,
    EmbeddedResource,
    TextContent,
    TextResourceContents,
    ToolAnnotations,
)
from pydantic import AnyHttpUrl, AnyUrl
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from starlette.routing import Route

try:
    from services.sec_client import DownstreamApiClient, SecEdgarService, prune_payload_for_llm
    from mcp_apps import (
        DOSSIER_APP_RESOURCE_META,
        DOSSIER_APP_TOOL_META,
        DOSSIER_RESOURCE_URI,
        MCP_APP_MIME_TYPE,
        PEER_APP_RESOURCE_META,
        PEER_APP_TOOL_META,
        PEER_RESOURCE_URI,
        build_dossier_workbench_html,
        build_peer_comparator_html,
        enrich_dossier_workbench_payload,
        enrich_peer_comparator_payload,
        get_cached_dossier_payload,
        get_cached_peer_payload,
    )
except ImportError:
    from .services.sec_client import DownstreamApiClient, SecEdgarService, prune_payload_for_llm
    from .mcp_apps import (
        DOSSIER_APP_RESOURCE_META,
        DOSSIER_APP_TOOL_META,
        DOSSIER_RESOURCE_URI,
        MCP_APP_MIME_TYPE,
        PEER_APP_RESOURCE_META,
        PEER_APP_TOOL_META,
        PEER_RESOURCE_URI,
        build_dossier_workbench_html,
        build_peer_comparator_html,
        enrich_dossier_workbench_payload,
        enrich_peer_comparator_payload,
        get_cached_dossier_payload,
        get_cached_peer_payload,
    )

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
SERVICE_NAME = os.environ.get(
    "MCP_SERVER_NAME",
    "Apex Capital SEC EDGAR Interactive MCP Apps Server",
)
logger = logging.getLogger("sec-edgar-mcp-apps-server")


# ==============================================================================
# 0. Multi-Tenant Per-Request User Token Context (3-Legged OAuth Passthrough)
# ==============================================================================

_CURRENT_USER_TOKEN: ContextVar[Optional[str]] = ContextVar("_CURRENT_USER_TOKEN", default=None)
_CURRENT_USER_CLAIMS: ContextVar[Optional[Dict[str, Any]]] = ContextVar("_CURRENT_USER_CLAIMS", default=None)


def get_current_user_token() -> Optional[str]:
    """Returns the verified Bearer token of the currently authenticated MCP user."""
    return _CURRENT_USER_TOKEN.get()


def get_current_user_claims() -> Dict[str, Any]:
    """Returns the verified OAuth claims/metadata of the currently authenticated MCP user."""
    return _CURRENT_USER_CLAIMS.get() or {}


# ==============================================================================
# 1. Stateless HMAC-SHA256 OAuth 2.0 Token Signing & Verification
# ==============================================================================

_EPHEMERAL_SIGNING_KEY: Optional[bytes] = None


def _get_signing_key() -> bytes:
    """Derives a deterministic HMAC-SHA256 key from GOOGLE_OAUTH_CLIENT_ID & GOOGLE_OAUTH_CLIENT_SECRET."""
    global _EPHEMERAL_SIGNING_KEY
    secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "").strip()
    if secret:
        return hashlib.sha256(f"{client_id}:{secret}".encode("utf-8")).digest()
    if _EPHEMERAL_SIGNING_KEY is None:
        logger.warning("GOOGLE_OAUTH_CLIENT_SECRET not set; generating instance-local ephemeral signing key.")
        _EPHEMERAL_SIGNING_KEY = secrets.token_bytes(32)
    return _EPHEMERAL_SIGNING_KEY


def _create_signed_token(prefix: str, payload: Dict[str, Any]) -> str:
    """Creates a stateless HMAC-SHA256 signed token with the given prefix."""
    raw_json = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    body_b64 = base64.urlsafe_b64encode(raw_json).decode("ascii").rstrip("=")
    sig = hmac.new(_get_signing_key(), f"{prefix}.{body_b64}".encode("ascii"), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode("ascii").rstrip("=")
    return f"{prefix}.{body_b64}.{sig_b64}"


def _verify_signed_token(token: str, expected_prefix: str) -> Optional[Dict[str, Any]]:
    """Verifies an HMAC-SHA256 signed token and checks its expiration."""
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
        logger.warning("Rejected signed token with invalid HMAC signature (prefix=%s)", expected_prefix)
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
                logger.warning("Rejected expired signed token (prefix=%s)", expected_prefix)
                return None
        except (TypeError, ValueError):
            return None
    return payload


# ==============================================================================
# 2. Google Cloud & Stateless HMAC OAuth 2.0 Token Verifier
# ==============================================================================

class GoogleOAuthTokenVerifier(TokenVerifier):
    """Validates both server-signed HMAC tokens (mcp_at.*) and Google OAuth tokens (ya29... / eyJ...)."""

    TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"

    def __init__(
        self,
        expected_client_ids: Optional[List[str]] = None,
        allowed_domain: Optional[str] = None,
    ):
        self.expected_client_ids = [cid.strip() for cid in (expected_client_ids or []) if cid.strip()]
        self.allowed_domain = allowed_domain.strip().lower() if allowed_domain else None

    async def verify_token(self, token: str) -> Optional[AccessToken]:
        if not token or not token.strip():
            return None

        clean_token = token.strip()
        if clean_token.startswith("ge_rt_"):
            clean_token = clean_token[len("ge_rt_"):]

        # Fast-path: Verify stateless HMAC-SHA256 tokens issued by our /token endpoint
        if clean_token.startswith("mcp_at.") or clean_token.startswith("mcp_rt."):
            prefix = "mcp_at" if clean_token.startswith("mcp_at.") else "mcp_rt"
            payload = _verify_signed_token(clean_token, expected_prefix=prefix)
            if not payload:
                return None
            cid = str(payload.get("cid", "")).strip()
            if self.expected_client_ids and cid not in self.expected_client_ids:
                logger.warning("Rejected signed token: cid did not match GOOGLE_OAUTH_CLIENT_ID")
                return None
            raw_scopes = str(payload.get("scp", "openid email profile")).split()
            normalized = set(raw_scopes) | {"openid", "email", "profile"}
            _CURRENT_USER_TOKEN.set(clean_token)
            _CURRENT_USER_CLAIMS.set(payload)
            return AccessToken(
                token=clean_token,
                client_id=cid or (self.expected_client_ids[0] if self.expected_client_ids else "oauth-client"),
                scopes=sorted(normalized),
                expires_at=int(payload["exp"]) if payload.get("exp") else None,
            )

        # Fallback: Verify standard Google OAuth 2.0 access_token or OIDC id_token via tokeninfo
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    self.TOKENINFO_URL,
                    params={"access_token": clean_token},
                )
                if resp.status_code != 200 and clean_token.count(".") == 2:
                    resp = await client.get(
                        self.TOKENINFO_URL,
                        params={"id_token": clean_token},
                    )
                if resp.status_code != 200:
                    logger.warning("Google OAuth token verification failed with status %d", resp.status_code)
                    return None
                data = resp.json()
        except Exception:
            logger.exception("Error communicating with Google tokeninfo endpoint")
            return None

        now = int(time.time())
        exp_raw = data.get("exp")
        expires_at: Optional[int] = None
        if exp_raw is not None:
            try:
                expires_at = int(exp_raw)
                if expires_at < now:
                    return None
            except (TypeError, ValueError):
                return None

        aud = data.get("aud", "")
        azp = data.get("azp", "")
        if self.expected_client_ids:
            if aud not in self.expected_client_ids and azp not in self.expected_client_ids:
                logger.warning("Rejected Google OAuth token: aud/azp mismatch")
                return None

        if self.allowed_domain:
            email = (data.get("email") or "").lower()
            email_verified = str(data.get("email_verified", "")).lower() == "true"
            hd = (data.get("hd") or "").lower()
            if not email_verified or (not email.endswith(f"@{self.allowed_domain}") and hd != self.allowed_domain):
                logger.warning("Rejected Google OAuth token: user domain not in GOOGLE_ALLOWED_DOMAIN")
                return None

        raw_scopes = (data.get("scope") or "").split()
        normalized_scopes = set(raw_scopes)
        if "https://www.googleapis.com/auth/userinfo.email" in normalized_scopes or data.get("email"):
            normalized_scopes.add("email")
        if "https://www.googleapis.com/auth/userinfo.profile" in normalized_scopes:
            normalized_scopes.add("profile")
        if "https://www.googleapis.com/auth/plus.me" in normalized_scopes or "email" in normalized_scopes or data.get("sub"):
            normalized_scopes.add("openid")

        client_id = azp or aud or (self.expected_client_ids[0] if self.expected_client_ids else "google-oauth-client")
        _CURRENT_USER_TOKEN.set(clean_token)
        _CURRENT_USER_CLAIMS.set(data)
        return AccessToken(
            token=clean_token,
            client_id=client_id,
            scopes=sorted(normalized_scopes),
            expires_at=expires_at,
        )


def _build_auth_configuration() -> tuple[Optional[TokenVerifier], Optional[AuthSettings]]:
    """Builds FastMCP OAuth 2.0 TokenVerifier and AuthSettings from environment variables."""
    raw_client_ids = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "").strip()
    allowed_domain = os.environ.get("GOOGLE_ALLOWED_DOMAIN", "").strip() or None
    require_oauth_env = os.environ.get("REQUIRE_OAUTH", "").strip().lower()

    if require_oauth_env in ("false", "0", "no"):
        oauth_enabled = False
    elif require_oauth_env in ("true", "1", "yes") or bool(raw_client_ids):
        oauth_enabled = True
    else:
        oauth_enabled = False

    if not oauth_enabled:
        logger.info("OAuth 2.0 token verification is DISABLED (set GOOGLE_OAUTH_CLIENT_ID or REQUIRE_OAUTH=true to enable).")
        return None, None

    client_ids = [c.strip() for c in raw_client_ids.split(",") if c.strip()]
    raw_scopes = os.environ.get("OAUTH_REQUIRED_SCOPES", "openid email").strip()
    required_scopes = [s.strip() for s in raw_scopes.replace(",", " ").split() if s.strip()]
    resource_server_url_str = os.environ.get("MCP_RESOURCE_SERVER_URL", "").strip()

    verifier = GoogleOAuthTokenVerifier(
        expected_client_ids=client_ids,
        allowed_domain=allowed_domain,
    )
    auth_settings = AuthSettings(
        issuer_url=AnyHttpUrl("https://accounts.google.com"),
        required_scopes=required_scopes or None,
        resource_server_url=AnyHttpUrl(resource_server_url_str) if resource_server_url_str else None,
    )
    logger.info(
        "OAuth 2.0 token verification ENABLED (client_ids=%d, required_scopes=%s, allowed_domain=%s)",
        len(client_ids),
        required_scopes,
        allowed_domain,
    )
    return verifier, auth_settings


# ==============================================================================
# 3. FastMCP & Async SEC EDGAR Workflow Client Initialization
# ==============================================================================

transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=False,
    allowed_hosts=["*"],
    allowed_origins=["*"],
)

_token_verifier, _auth_settings = _build_auth_configuration()

READ_ONLY_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=True,
)

mcp = FastMCP(
    name=SERVICE_NAME,
    instructions=os.environ.get(
        "MCP_SERVER_INSTRUCTIONS",
        (
            "Apex Capital Institutional Research — SEC EDGAR Interactive MCP Apps Server (SEP-1865). "
            "Provides 7 coarse-grained SEC EDGAR financial & 10-K workflow tools plus 2 interactive visual MCP Apps: "
            "`open_financial_dossier_workbench_app` (ui://sec-edgar/financial-dossier-workbench) and "
            "`open_peer_industry_comparator_app` (ui://sec-edgar/peer-industry-comparator)."
        ),
    ),
    token_verifier=_token_verifier,
    auth=_auth_settings,
    stateless_http=os.environ.get("MCP_STATELESS_HTTP", "true").lower() in ("true", "1", "yes"),
    transport_security=transport_security,
)

sec_api_client = DownstreamApiClient(
    base_url=os.environ.get("DOWNSTREAM_API_BASE_URL", "https://data.sec.gov"),
    user_token_getter=get_current_user_token,
    timeout_sec=20.0,
    max_concurrency=6,
)
sec_service = SecEdgarService(sec_api_client)


def _serialize_for_llm(data: Dict[str, Any], max_bytes: int = 32768) -> str:
    """Serializes tool output to JSON while preserving all requested fiscal periods and filings."""
    pruned = prune_payload_for_llm(data, max_list_items=50, max_str_len=600)
    pretty = json.dumps(pruned, indent=2)
    if len(pretty.encode("utf-8")) <= max_bytes:
        return pretty

    return json.dumps(pruned, separators=(",", ":"))


# ==============================================================================
# 4. Registered SEP-1865 `ui://` MCP App Resources
# ==============================================================================

@mcp.resource(
    DOSSIER_RESOURCE_URI,
    mime_type=MCP_APP_MIME_TYPE,
    meta=DOSSIER_APP_RESOURCE_META,
)
def read_financial_dossier_workbench_resource() -> str:
    """Returns the interactive Apex Capital 360° SEC EDGAR Financial Statement, Ratio & Filing Workbench (`text/html;profile=mcp-app`)."""
    return build_dossier_workbench_html(get_cached_dossier_payload(), api_base_url=_get_public_base_url())


@mcp.resource(
    PEER_RESOURCE_URI,
    mime_type=MCP_APP_MIME_TYPE,
    meta=PEER_APP_RESOURCE_META,
)
def read_peer_industry_comparator_resource() -> str:
    """Returns the interactive Apex Capital Peer Group & SEC Industry XBRL Frame Comparator (`text/html;profile=mcp-app`)."""
    return build_peer_comparator_html(get_cached_peer_payload(), api_base_url=_get_public_base_url())


# ==============================================================================
# 5. Dedicated MCP App Launcher Tools (Returning CallToolResult + EmbeddedResource)
# ==============================================================================

@mcp.tool(annotations=READ_ONLY_ANNOTATIONS, meta=DOSSIER_APP_TOOL_META)
async def open_financial_dossier_workbench_app(
    identifier: str = "NVDA",
    period_type: Literal["annual", "quarterly"] = "annual",
    periods: int = 5,
) -> CallToolResult:
    """Opens the interactive Apex Capital 360° SEC EDGAR Financial Statement, DuPont Ratio & 10-K Filing Workbench (`ui://sec-edgar/financial-dossier-workbench`).

    Fans out concurrently across SEC EDGAR to retrieve the company's 360° financial dossier, multi-period harmonized
    Income Statement, Balance Sheet, Cash Flow Statement, 13 financial ratios, 3-step DuPont ROE decomposition,
    XBRL revenue history with restatement audit, and recent 10-K/10-Q/8-K/DEF 14A filings, rendering an interactive
    institutional visual workbench.

    Args:
        identifier: Stock ticker symbol (e.g., 'NVDA', 'AAPL', 'IBM'), company name, or CIK.
        period_type: 'annual' (10-K full fiscal years) or 'quarterly' (10-Q single quarters).
        periods: Number of historical periods to align side-by-side (2 to 10, default 5).
    """
    dossier_task = sec_service.get_company_360_financial_dossier(
        identifier=identifier,
        period_type=period_type,
        periods=periods,
        include_recent_filings=True,
    )
    statements_task = sec_service.analyze_financial_statements_and_ratios(
        identifier=identifier,
        statement_types=["income_statement", "balance_sheet", "cash_flow", "ratios"],
        period_type=period_type,
        periods=periods,
    )
    filings_task = sec_service.search_and_inspect_sec_filings(
        identifier=identifier,
        form_types=["10-K", "10-Q", "8-K", "DEF 14A"],
        limit=25,
    )
    concept_task = sec_service.trace_xbrl_metric_history(
        identifier=identifier,
        concept_or_tag="revenue",
        period_type=period_type,
        periods=min(10, max(5, periods)),
        include_restatement_audit=True,
    )
    dossier_res, stmt_res, filings_res, concept_res = await asyncio.gather(
        dossier_task,
        statements_task,
        filings_task,
        concept_task,
    )
    enriched = enrich_dossier_workbench_payload(
        raw_data=dossier_res,
        statements_data=stmt_res,
        filings_data=filings_res,
        concept_history_data=concept_res,
    )
    app_html = build_dossier_workbench_html(enriched, api_base_url=_get_public_base_url())
    summary_json = _serialize_for_llm(enriched)

    return CallToolResult(
        content=[
            TextContent(type="text", text=summary_json),
            EmbeddedResource(
                type="resource",
                resource=TextResourceContents(
                    uri=AnyUrl(DOSSIER_RESOURCE_URI),
                    mimeType=MCP_APP_MIME_TYPE,
                    text=app_html,
                    _meta=DOSSIER_APP_RESOURCE_META,
                ),
            ),
        ],
        structuredContent=enriched,
    )


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS, meta=PEER_APP_TOOL_META)
async def open_peer_industry_comparator_app(
    identifiers: List[str] = ["AAPL", "MSFT", "GOOGL", "NVDA"],
    period_type: Literal["annual", "quarterly"] = "annual",
    fiscal_year: Optional[int] = None,
    benchmark_concept: str = "revenue",
    calendar_year: int = 2024,
) -> CallToolResult:
    """Opens the interactive Apex Capital Peer Group & SEC Cross-Market XBRL Frame Comparator (`ui://sec-edgar/peer-industry-comparator`).

    Benchmarks 2 to 10 peer companies side-by-side with peer-group medians, outperformance/underperformance badges,
    and horizontal grouped metric bars, paired with the SEC Cross-Company XBRL Frame percentile distribution (`p10`-`p99`)
    and Top Market Reporters leaderboard.

    Args:
        identifiers: List of 2 to 10 peer tickers, names, or CIKs (e.g., ['AAPL', 'MSFT', 'GOOGL', 'NVDA']).
        period_type: 'annual' (latest 10-K) or 'quarterly' (latest 10-Q).
        fiscal_year: Optional target fiscal year to align all peers.
        benchmark_concept: XBRL concept for industry-wide SEC frame benchmarking ('revenue', 'operating_income', 'net_income', 'total_assets', 'total_cash', 'r_and_d').
        calendar_year: Calendar year for the SEC XBRL Frame distribution (e.g., 2024 or 2025).
    """
    highlight = identifiers[0] if identifiers else None
    peer_task = sec_service.compare_peer_group_financials(
        identifiers=identifiers,
        period_type=period_type,
        fiscal_year=fiscal_year,
    )
    frame_task = sec_service.benchmark_industry_xbrl_frame(
        concept_or_tag=benchmark_concept,
        calendar_year=calendar_year,
        highlight_identifier=highlight,
        top_n=15,
    )
    peer_res, frame_res = await asyncio.gather(peer_task, frame_task)
    enriched = enrich_peer_comparator_payload(peer_data=peer_res, frame_data=frame_res)
    app_html = build_peer_comparator_html(enriched, api_base_url=_get_public_base_url())
    summary_json = _serialize_for_llm(enriched)

    return CallToolResult(
        content=[
            TextContent(type="text", text=summary_json),
            EmbeddedResource(
                type="resource",
                resource=TextResourceContents(
                    uri=AnyUrl(PEER_RESOURCE_URI),
                    mimeType=MCP_APP_MIME_TYPE,
                    text=app_html,
                    _meta=PEER_APP_RESOURCE_META,
                ),
            ),
        ],
        structuredContent=enriched,
    )


# ==============================================================================
# 6. Coarse-Grained SEC EDGAR MCP Workflow Data Tools (7 Tools with APP_TOOL_META)
# ==============================================================================

@mcp.tool(annotations=READ_ONLY_ANNOTATIONS, meta=DOSSIER_APP_TOOL_META)
async def get_company_360_financial_dossier(
    identifier: str,
    period_type: Literal["annual", "quarterly"] = "annual",
    periods: int = 4,
    include_recent_filings: bool = True,
) -> str:
    """Generates a comprehensive 360-degree corporate and financial dossier for a U.S. public company in a single call.

    Accepts a stock ticker (e.g., 'AAPL', 'NVDA'), company name (e.g., 'Apple Inc'), or CIK. Automatically resolves
    the 10-digit zero-padded CIK and fans out in parallel across SEC `submissions` and `companyfacts` to return:
    corporate governance metadata, latest 10-K/10-Q/8-K/DEF 14A filing links, and harmonized multi-period headline
    financials (Revenue, Gross Profit, Operating Income, Net Income, EPS, R&D, Operating Cash Flow, Free Cash Flow,
    Cash, Total Assets, Total Debt, Stockholders' Equity) with computed YoY growth rates and profitability margins.

    Args:
        identifier: Stock ticker symbol (e.g., 'NVDA'), company name (e.g., 'NVIDIA'), or CIK.
        period_type: 'annual' (10-K full fiscal years) or 'quarterly' (10-Q single quarters).
        periods: Number of most recent fiscal periods to include (1 to 10, default 4).
        include_recent_filings: Whether to include direct SEC EDGAR Archive links to latest 10-K, 10-Q, DEF 14A, and 8-Ks.
    """
    dossier_task = sec_service.get_company_360_financial_dossier(
        identifier=identifier,
        period_type=period_type,
        periods=periods,
        include_recent_filings=include_recent_filings,
    )
    statements_task = sec_service.analyze_financial_statements_and_ratios(
        identifier=identifier,
        statement_types=["income_statement", "balance_sheet", "cash_flow", "ratios"],
        period_type=period_type,
        periods=periods,
    )
    filings_task = sec_service.search_and_inspect_sec_filings(
        identifier=identifier,
        form_types=["10-K", "10-Q", "8-K", "DEF 14A"],
        limit=25,
    )
    concept_task = sec_service.trace_xbrl_metric_history(
        identifier=identifier,
        concept_or_tag="revenue",
        period_type=period_type,
        periods=min(10, max(5, periods)),
        include_restatement_audit=True,
    )
    result, stmt_res, filings_res, concept_res = await asyncio.gather(
        dossier_task,
        statements_task,
        filings_task,
        concept_task,
    )
    enriched = enrich_dossier_workbench_payload(
        raw_data=result,
        statements_data=stmt_res,
        filings_data=filings_res,
        concept_history_data=concept_res,
    )
    if isinstance(result, dict) and "error" not in result:
        for ui_key in (
            "kpi_summary",
            "dupont_roe_by_period",
            "income_statement",
            "balance_sheet",
            "cash_flow",
            "financial_ratios",
            "filings_dossier",
            "initial_concept_history",
        ):
            if enriched.get(ui_key):
                result[ui_key] = enriched[ui_key]
    return _serialize_for_llm(result)


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS, meta=DOSSIER_APP_TOOL_META)
async def analyze_financial_statements_and_ratios(
    identifier: str,
    statement_types: Optional[List[str]] = None,
    period_type: Literal["annual", "quarterly"] = "annual",
    periods: int = 5,
) -> str:
    """Performs a structured multi-period financial statement and ratio analysis (Income Statement, Balance Sheet, Cash Flow, and Ratios).

    Automatically harmonizes changing US-GAAP/IFRS accounting tags across years, deduplicates restated comparative periods,
    and computes YoY/QoQ growth rates, multi-year CAGR, profitability margins (Gross, Operating, Net, FCF), liquidity
    ratios (Current Ratio, Quick Ratio), leverage metrics (Debt/Equity, Net Debt), and return metrics (ROE, ROA).

    Args:
        identifier: Company ticker ('MSFT'), name ('Microsoft'), or CIK.
        statement_types: Subset of ['income_statement', 'balance_sheet', 'cash_flow', 'ratios'] (defaults to all four).
        period_type: 'annual' (10-K full fiscal years) or 'quarterly' (10-Q single quarters).
        periods: Number of historical periods to align side-by-side (2 to 10, default 5).
    """
    stmt_task = sec_service.analyze_financial_statements_and_ratios(
        identifier=identifier,
        statement_types=statement_types,
        period_type=period_type,
        periods=periods,
    )
    dossier_task = sec_service.get_company_360_financial_dossier(
        identifier=identifier,
        period_type=period_type,
        periods=periods,
        include_recent_filings=True,
    )
    filings_task = sec_service.search_and_inspect_sec_filings(
        identifier=identifier,
        form_types=["10-K", "10-Q", "8-K", "DEF 14A"],
        limit=25,
    )
    concept_task = sec_service.trace_xbrl_metric_history(
        identifier=identifier,
        concept_or_tag="revenue",
        period_type=period_type,
        periods=min(10, max(5, periods)),
        include_restatement_audit=True,
    )
    result, dossier_res, filings_res, concept_res = await asyncio.gather(
        stmt_task,
        dossier_task,
        filings_task,
        concept_task,
    )
    enriched = enrich_dossier_workbench_payload(
        raw_data=dossier_res,
        statements_data=result,
        filings_data=filings_res,
        concept_history_data=concept_res,
    )
    if isinstance(result, dict) and "error" not in result:
        for ui_key in (
            "kpi_summary",
            "dupont_roe_by_period",
            "income_statement",
            "balance_sheet",
            "cash_flow",
            "financial_ratios",
            "filings_dossier",
            "initial_concept_history",
        ):
            if enriched.get(ui_key):
                result[ui_key] = enriched[ui_key]
    return _serialize_for_llm(result)


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS, meta=DOSSIER_APP_TOOL_META)
async def search_and_inspect_sec_filings(
    identifier: str,
    form_types: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    item_8k_filter: Optional[str] = None,
    include_amendments: bool = True,
    limit: int = 15,
) -> str:
    """Searches and filters a company's SEC EDGAR filing history with enriched metadata and direct clickable SEC Archive URLs.

    Supports filtering by form type ('10-K', '10-Q', '8-K', 'DEF 14A', 'S-1', '20-F', '4', '13F-HR'), filing date range,
    and specific Form 8-K Material Event Item codes (e.g., '2.02' for Earnings Releases, '1.01' for Material Agreements,
    '1.05' for Cybersecurity Incidents, '5.02' for Executive/Director Changes).

    Args:
        identifier: Company ticker, name, or CIK.
        form_types: List of SEC form types to include (defaults to ['10-K', '10-Q', '8-K', 'DEF 14A'] if omitted).
        start_date: Optional ISO start date ('YYYY-MM-DD') filter on filingDate.
        end_date: Optional ISO end date ('YYYY-MM-DD') filter on filingDate.
        item_8k_filter: Optional Form 8-K item number or keyword filter (e.g., '2.02', '5.02', 'Cybersecurity').
        include_amendments: Whether to include amended filings such as 10-K/A and 10-Q/A (default True).
        limit: Maximum number of matching filings to return (1 to 50, default 15).
    """
    effective_forms = form_types if form_types is not None else ["10-K", "10-Q", "8-K", "DEF 14A"]
    cached = get_cached_dossier_payload() or {}
    cached_ticker = str(cached.get("company", {}).get("ticker", "")).upper()
    need_backfill = not (cached_ticker and cached_ticker == identifier.strip().upper() and cached.get("income_statement"))

    if need_backfill:
        result, dossier_res, stmt_res = await asyncio.gather(
            sec_service.search_and_inspect_sec_filings(
                identifier=identifier,
                form_types=effective_forms,
                start_date=start_date,
                end_date=end_date,
                item_8k_filter=item_8k_filter,
                include_amendments=include_amendments,
                limit=limit,
            ),
            sec_service.get_company_360_financial_dossier(
                identifier=identifier,
                period_type="annual",
                periods=5,
                include_recent_filings=True,
            ),
            sec_service.analyze_financial_statements_and_ratios(
                identifier=identifier,
                statement_types=["income_statement", "balance_sheet", "cash_flow", "ratios"],
                period_type="annual",
                periods=5,
            ),
        )
        enriched = enrich_dossier_workbench_payload(
            raw_data=dossier_res,
            statements_data=stmt_res,
            filings_data=result,
        )
    else:
        result = await sec_service.search_and_inspect_sec_filings(
            identifier=identifier,
            form_types=effective_forms,
            start_date=start_date,
            end_date=end_date,
            item_8k_filter=item_8k_filter,
            include_amendments=include_amendments,
            limit=limit,
        )
        enriched = enrich_dossier_workbench_payload(raw_data=result, filings_data=result)

    if isinstance(result, dict) and "error" not in result:
        result["company"] = enriched.get("company", result.get("company"))
        for ui_key in (
            "kpi_summary",
            "dupont_roe_by_period",
            "income_statement",
            "balance_sheet",
            "cash_flow",
            "financial_ratios",
            "filings_dossier",
            "initial_concept_history",
        ):
            if enriched.get(ui_key):
                result[ui_key] = enriched[ui_key]
    return _serialize_for_llm(result)


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS, meta=DOSSIER_APP_TOOL_META)
async def trace_xbrl_metric_history(
    identifier: str,
    concept_or_tag: str,
    taxonomy: Literal["us-gaap", "dei", "ifrs-full"] = "us-gaap",
    period_type: Literal["annual", "quarterly", "all"] = "annual",
    periods: int = 10,
    include_restatement_audit: bool = False,
) -> str:
    """Retrieves the historical time-series, YoY/QoQ progression, CAGR, and restatement audit trail for a specific XBRL concept.

    Uses the lightweight SEC `companyconcept` endpoint (fanned out across US-GAAP alias tags when a canonical concept
    is requested) without downloading the full 15 MB companyfacts dataset.

    Args:
        identifier: Company ticker, name, or CIK.
        concept_or_tag: Exact XBRL tag (e.g., 'ResearchAndDevelopmentExpense', 'Goodwill', 'EntityCommonStockSharesOutstanding')
                        or canonical alias ('revenue', 'r_and_d', 'sbc', 'capex', 'operating_income', 'shares_outstanding').
        taxonomy: XBRL taxonomy namespace ('us-gaap', 'dei', or 'ifrs-full').
        period_type: 'annual' (10-K FY), 'quarterly' (10-Q single quarters), or 'all'.
        periods: Number of historical periods to return (1 to 25, default 10).
        include_restatement_audit: If True, includes prior restated values reported for the same fiscal period across subsequent filings.
    """
    cached = get_cached_dossier_payload() or {}
    cached_ticker = str(cached.get("company", {}).get("ticker", "")).upper()
    eff_pt: Literal["annual", "quarterly"] = "quarterly" if period_type == "quarterly" else "annual"
    need_backfill = not (
        cached_ticker
        and cached_ticker == identifier.strip().upper()
        and cached.get("income_statement")
        and cached.get("filings_dossier", {}).get("filings")
    )

    if need_backfill:
        result, dossier_res, stmt_res, filings_res = await asyncio.gather(
            sec_service.trace_xbrl_metric_history(
                identifier=identifier,
                concept_or_tag=concept_or_tag,
                taxonomy=taxonomy,
                period_type=period_type,
                periods=periods,
                include_restatement_audit=include_restatement_audit,
            ),
            sec_service.get_company_360_financial_dossier(
                identifier=identifier,
                period_type=eff_pt,
                periods=5,
                include_recent_filings=True,
            ),
            sec_service.analyze_financial_statements_and_ratios(
                identifier=identifier,
                statement_types=["income_statement", "balance_sheet", "cash_flow", "ratios"],
                period_type=eff_pt,
                periods=5,
            ),
            sec_service.search_and_inspect_sec_filings(
                identifier=identifier,
                form_types=["10-K", "10-Q", "8-K", "DEF 14A"],
                limit=25,
            ),
        )
        enriched = enrich_dossier_workbench_payload(
            raw_data=dossier_res,
            statements_data=stmt_res,
            filings_data=filings_res,
            concept_history_data=result,
        )
    else:
        result = await sec_service.trace_xbrl_metric_history(
            identifier=identifier,
            concept_or_tag=concept_or_tag,
            taxonomy=taxonomy,
            period_type=period_type,
            periods=periods,
            include_restatement_audit=include_restatement_audit,
        )
        enriched = enrich_dossier_workbench_payload(raw_data=result, concept_history_data=result)

    if isinstance(result, dict) and "error" not in result:
        result["company"] = enriched.get("company", result.get("company"))
        for ui_key in (
            "kpi_summary",
            "dupont_roe_by_period",
            "income_statement",
            "balance_sheet",
            "cash_flow",
            "financial_ratios",
            "filings_dossier",
            "initial_concept_history",
        ):
            if enriched.get(ui_key):
                result[ui_key] = enriched[ui_key]
    return _serialize_for_llm(result)


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS, meta=PEER_APP_TOOL_META)
async def compare_peer_group_financials(
    identifiers: List[str],
    metrics: Optional[List[str]] = None,
    period_type: Literal["annual", "quarterly"] = "annual",
    fiscal_year: Optional[int] = None,
) -> str:
    """Benchmarks 2 to 10 public peer companies side-by-side across standardized financial metrics, growth rates, and margins.

    Executes bounded parallel requests across all peer tickers, aligns figures to the most recent comparable fiscal period,
    and computes peer-group medians and means.

    Args:
        identifiers: List of 2 to 10 peer tickers, company names, or CIKs (e.g., ['NVDA', 'AMD', 'INTC']).
        metrics: Optional subset of metric keys to highlight.
        period_type: 'annual' (latest 10-K) or 'quarterly' (latest 10-Q).
        fiscal_year: Optional target year (e.g., 2024 or 2025) to align all peers.
    """
    cached_peer = get_cached_peer_payload() or {}
    if not cached_peer.get("industry_frame", {}).get("top_leaders"):
        result, frame_res = await asyncio.gather(
            sec_service.compare_peer_group_financials(
                identifiers=identifiers,
                metrics=metrics,
                period_type=period_type,
                fiscal_year=fiscal_year,
            ),
            sec_service.benchmark_industry_xbrl_frame(
                concept_or_tag="revenue",
                calendar_year=fiscal_year or 2024,
                highlight_identifier=identifiers[0] if identifiers else None,
                top_n=15,
            ),
        )
        enriched = enrich_peer_comparator_payload(peer_data=result, frame_data=frame_res)
    else:
        result = await sec_service.compare_peer_group_financials(
            identifiers=identifiers,
            metrics=metrics,
            period_type=period_type,
            fiscal_year=fiscal_year,
        )
        enriched = enrich_peer_comparator_payload(peer_data=result)
    if isinstance(result, dict) and "error" not in result:
        result["peer_comparison"] = enriched.get("peer_comparison")
        if enriched.get("industry_frame"):
            result["industry_frame"] = enriched.get("industry_frame")
    return _serialize_for_llm(result)


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS, meta=PEER_APP_TOOL_META)
async def benchmark_industry_xbrl_frame(
    concept_or_tag: str,
    calendar_year: int = 2024,
    calendar_quarter: Optional[int] = None,
    highlight_identifier: Optional[str] = None,
    unit: str = "USD",
    taxonomy: Literal["us-gaap", "dei", "ifrs-full"] = "us-gaap",
    top_n: int = 15,
) -> str:
    """Queries the SEC Cross-Company XBRL Frames API (`frames/{taxonomy}/{tag}/{unit}/CY{YYYY}[Q{Q}][I]`) to rank all reporting public companies.

    Automatically handles durational flow frames (`CY2024`, `CY2024Q3`) vs. instantaneous balance-sheet frames (`CY2024Q4I`),
    computes market-wide percentiles (`p10`, `p25`, `p50_median`, `p75`, `p90`, `p99`), returns the top N leaders,
    and calculates the exact rank and percentile of `highlight_identifier` if provided.

    Args:
        concept_or_tag: Canonical concept ('revenue', 'net_income', 'total_assets', 'total_cash', 'r_and_d') or exact XBRL tag ('Assets', 'Revenues').
        calendar_year: Standardized calendar year (e.g., 2024 or 2025).
        calendar_quarter: Optional quarter (1, 2, 3, or 4). Omit for full calendar year.
        highlight_identifier: Optional company ticker/name/CIK (e.g., 'AAPL') to locate and benchmark within the market distribution.
        unit: Unit of measure ('USD', 'shares', 'USD-per-shares').
        taxonomy: XBRL taxonomy ('us-gaap', 'dei', 'ifrs-full').
        top_n: Number of top-ranking companies to include (5 to 40, default 15).
    """
    cached_peer = get_cached_peer_payload() or {}
    if not cached_peer.get("peer_comparison", {}).get("peer_comparison_table"):
        default_peers = ["AAPL", "MSFT", "GOOGL", "NVDA"]
        if highlight_identifier and highlight_identifier.upper() not in default_peers:
            default_peers = [highlight_identifier.upper()] + default_peers[:3]
        result, peer_res = await asyncio.gather(
            sec_service.benchmark_industry_xbrl_frame(
                concept_or_tag=concept_or_tag,
                calendar_year=calendar_year,
                calendar_quarter=calendar_quarter,
                highlight_identifier=highlight_identifier,
                unit=unit,
                taxonomy=taxonomy,
                top_n=top_n,
            ),
            sec_service.compare_peer_group_financials(
                identifiers=default_peers,
                period_type="annual",
                fiscal_year=calendar_year,
            ),
        )
        enriched = enrich_peer_comparator_payload(peer_data=peer_res, frame_data=result)
    else:
        result = await sec_service.benchmark_industry_xbrl_frame(
            concept_or_tag=concept_or_tag,
            calendar_year=calendar_year,
            calendar_quarter=calendar_quarter,
            highlight_identifier=highlight_identifier,
            unit=unit,
            taxonomy=taxonomy,
            top_n=top_n,
        )
        enriched = enrich_peer_comparator_payload(frame_data=result)
    if isinstance(result, dict) and "error" not in result:
        result["industry_frame"] = enriched.get("industry_frame")
        if enriched.get("peer_comparison"):
            result["peer_comparison"] = enriched.get("peer_comparison")
    return _serialize_for_llm(result)


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS)
async def resolve_and_discover_sec_entities(
    company_query: str,
    xbrl_tag_keyword: Optional[str] = None,
    limit: int = 5,
) -> str:
    """Fuzzy-searches SEC-registered public companies by name/ticker/CIK and optionally discovers company-specific XBRL tags by keyword.

    Enriches top company matches in parallel with inline corporate metadata (SIC industry, exchange, fiscal year-end,
    state of incorporation). When `xbrl_tag_keyword` is provided, also searches the top matched company's reported
    XBRL concepts to return exact tag names, units, descriptions, and latest values.

    Args:
        company_query: Partial company name, ticker symbol, or CIK (e.g., 'Alphabet', 'Berkshire', 'GOOGL').
        xbrl_tag_keyword: Optional keyword (e.g., 'revenue', 'inventory', 'lease', 'research') to discover reported XBRL tags.
        limit: Maximum number of matching companies to enrich and return (1 to 15, default 5).
    """
    result = await sec_service.resolve_and_discover_sec_entities(
        company_query=company_query,
        xbrl_tag_keyword=xbrl_tag_keyword,
        limit=limit,
    )
    return _serialize_for_llm(result)


# ==============================================================================
# 7. Standalone Sandbox-Safe MCP App Preview & JSON API Routes
# ==============================================================================

SANDBOX_SAFE_HEADERS = {
    "Cross-Origin-Opener-Policy": "unsafe-none",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "*",
}


async def preview_financial_dossier_workbench(request) -> Response:
    """Standalone HTTP preview route `/apps/raw/financial-dossier-workbench`."""
    identifier = request.query_params.get("identifier", "NVDA").strip() or "NVDA"
    period_type_raw = request.query_params.get("period_type", "annual").strip().lower()
    period_type: Literal["annual", "quarterly"] = "quarterly" if period_type_raw == "quarterly" else "annual"
    try:
        periods = int(request.query_params.get("periods", "5"))
    except ValueError:
        periods = 5

    cached = get_cached_dossier_payload()
    if (
        cached
        and str(cached.get("company", {}).get("ticker", "")).upper() == identifier.upper()
        and cached.get("period_type") == period_type
        and cached.get("filings_dossier", {}).get("filings")
    ):
        html = build_dossier_workbench_html(cached, api_base_url=_get_public_base_url(request))
        return HTMLResponse(html, headers=SANDBOX_SAFE_HEADERS)

    dossier_res, stmt_res, filings_res, concept_res = await asyncio.gather(
        sec_service.get_company_360_financial_dossier(
            identifier=identifier,
            period_type=period_type,
            periods=periods,
            include_recent_filings=True,
        ),
        sec_service.analyze_financial_statements_and_ratios(
            identifier=identifier,
            statement_types=["income_statement", "balance_sheet", "cash_flow", "ratios"],
            period_type=period_type,
            periods=periods,
        ),
        sec_service.search_and_inspect_sec_filings(
            identifier=identifier,
            form_types=["10-K", "10-Q", "8-K", "DEF 14A"],
            limit=25,
        ),
        sec_service.trace_xbrl_metric_history(
            identifier=identifier,
            concept_or_tag="revenue",
            period_type=period_type,
            periods=min(10, max(5, periods)),
            include_restatement_audit=True,
        ),
    )
    enriched = enrich_dossier_workbench_payload(
        raw_data=dossier_res,
        statements_data=stmt_res,
        filings_data=filings_res,
        concept_history_data=concept_res,
    )
    html = build_dossier_workbench_html(enriched, api_base_url=_get_public_base_url(request))
    return HTMLResponse(html, headers=SANDBOX_SAFE_HEADERS)


async def preview_peer_industry_comparator(request) -> Response:
    """Standalone HTTP preview route `/apps/raw/peer-industry-comparator`."""
    raw_ids = request.query_params.get("identifiers", "AAPL,MSFT,GOOGL,NVDA")
    identifiers = [x.strip().upper() for x in raw_ids.split(",") if x.strip()][:10]
    if len(identifiers) < 2:
        identifiers = ["AAPL", "MSFT", "GOOGL", "NVDA"]
    concept = request.query_params.get("concept", "revenue").strip() or "revenue"
    try:
        year = int(request.query_params.get("year", "2024"))
    except ValueError:
        year = 2024

    peer_res, frame_res = await asyncio.gather(
        sec_service.compare_peer_group_financials(
            identifiers=identifiers,
            period_type="annual",
        ),
        sec_service.benchmark_industry_xbrl_frame(
            concept_or_tag=concept,
            calendar_year=year,
            highlight_identifier=identifiers[0],
            top_n=15,
        ),
    )
    enriched = enrich_peer_comparator_payload(peer_data=peer_res, frame_data=frame_res)
    html = build_peer_comparator_html(enriched, api_base_url=_get_public_base_url(request))
    return HTMLResponse(html, headers=SANDBOX_SAFE_HEADERS)


async def apps_api_tool_call(request) -> Response:
    """Helper endpoint `/apps/api/tool-call` allowing standalone browser previews to invoke live SEC tools."""
    if request.method == "OPTIONS":
        return Response(status_code=204, headers=SANDBOX_SAFE_HEADERS)
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400, headers=SANDBOX_SAFE_HEADERS)

    name = body.get("name", "")
    args = body.get("arguments") or {}

    if name == "open_financial_dossier_workbench_app":
        res = await open_financial_dossier_workbench_app(
            identifier=args.get("identifier", "NVDA"),
            period_type=args.get("period_type", "annual"),
            periods=int(args.get("periods", 5)),
        )
        return JSONResponse({"structuredContent": res.structuredContent}, headers=SANDBOX_SAFE_HEADERS)

    if name == "open_peer_industry_comparator_app":
        res = await open_peer_industry_comparator_app(
            identifiers=args.get("identifiers") or ["AAPL", "MSFT", "GOOGL", "NVDA"],
            period_type=args.get("period_type", "annual"),
            fiscal_year=args.get("fiscal_year"),
            benchmark_concept=args.get("benchmark_concept", "revenue"),
            calendar_year=int(args.get("calendar_year", 2024)),
        )
        return JSONResponse({"structuredContent": res.structuredContent}, headers=SANDBOX_SAFE_HEADERS)

    if name == "trace_xbrl_metric_history":
        await trace_xbrl_metric_history(
            identifier=args.get("identifier", "NVDA"),
            concept_or_tag=args.get("concept_or_tag", "revenue"),
            period_type=args.get("period_type", "annual"),
            periods=int(args.get("periods", 10)),
            include_restatement_audit=bool(args.get("include_restatement_audit", True)),
        )
        enriched = get_cached_dossier_payload() or {}
        return JSONResponse({"structuredContent": enriched, "result": enriched.get("initial_concept_history", {})}, headers=SANDBOX_SAFE_HEADERS)

    if name == "search_and_inspect_sec_filings":
        await search_and_inspect_sec_filings(
            identifier=args.get("identifier", "NVDA"),
            form_types=args.get("form_types"),
            item_8k_filter=args.get("item_8k_filter"),
            limit=int(args.get("limit", 25)),
        )
        enriched = get_cached_dossier_payload() or {}
        return JSONResponse({"structuredContent": enriched, "result": enriched.get("filings_dossier", {})}, headers=SANDBOX_SAFE_HEADERS)

    if name == "compare_peer_group_financials":
        raw = await sec_service.compare_peer_group_financials(
            identifiers=args.get("identifiers") or ["AAPL", "MSFT", "GOOGL", "NVDA"],
            period_type=args.get("period_type", "annual"),
            fiscal_year=args.get("fiscal_year"),
        )
        enriched = enrich_peer_comparator_payload(peer_data=raw)
        return JSONResponse({"structuredContent": enriched, "result": raw}, headers=SANDBOX_SAFE_HEADERS)

    if name == "benchmark_industry_xbrl_frame":
        raw = await sec_service.benchmark_industry_xbrl_frame(
            concept_or_tag=args.get("concept_or_tag", "revenue"),
            calendar_year=int(args.get("calendar_year", 2024)),
            calendar_quarter=args.get("calendar_quarter"),
            highlight_identifier=args.get("highlight_identifier"),
            top_n=int(args.get("top_n", 15)),
        )
        enriched = enrich_peer_comparator_payload(frame_data=raw)
        return JSONResponse({"structuredContent": enriched, "result": raw}, headers=SANDBOX_SAFE_HEADERS)

    return JSONResponse({"error": f"Unsupported tool: {name}"}, status_code=400, headers=SANDBOX_SAFE_HEADERS)


# ==============================================================================
# 8. Built-in OAuth 2.0 Discovery, DCR, /authorize & /token Endpoints
# ==============================================================================

GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
_last_authorize_redirect_uri: Optional[str] = None
_last_public_base_url: Optional[str] = None


def _is_valid_redirect_uri(uri: str) -> bool:
    """Validates redirect_uri to prevent open redirect / XSS."""
    if not uri:
        return False
    parsed = urllib.parse.urlparse(uri)
    if parsed.scheme == "https" and bool(parsed.netloc):
        return True
    if parsed.scheme == "http" and parsed.hostname in ("localhost", "127.0.0.1"):
        return True
    return False


def _get_public_base_url(request=None) -> str:
    """Determines the external HTTPS base URL of this MCP server."""
    global _last_public_base_url
    env_base = os.environ.get("MCP_PUBLIC_BASE_URL", "").strip().rstrip("/")
    if env_base:
        return env_base
    if request is not None and hasattr(request, "headers"):
        host = request.headers.get("x-forwarded-host") or request.headers.get("host")
        proto = request.headers.get("x-forwarded-proto") or "https"
        if host:
            if "localhost" in host or "127.0.0.1" in host:
                proto = "http"
            _last_public_base_url = f"{proto}://{host}".rstrip("/")
            return _last_public_base_url
    if _last_public_base_url:
        return _last_public_base_url
    return "http://localhost:8080"


async def oauth_protected_resource_metadata(request) -> Response:
    """RFC 9728 OAuth 2.0 Protected Resource Metadata endpoint required by modern MCP clients."""
    base_url = _get_public_base_url(request)
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "*",
        "Cache-Control": "no-store",
    }
    if request.method == "OPTIONS":
        return Response(status_code=204, headers=cors_headers)
    return JSONResponse(
        {
            "resource": f"{base_url}/mcp",
            "authorization_servers": [base_url],
            "scopes_supported": ["openid", "email", "profile"],
            "bearer_methods_supported": ["header"],
            "resource_documentation": f"{base_url}/",
        },
        headers=cors_headers,
    )


async def oauth_authorization_server_metadata(request) -> Response:
    """RFC 8414 OAuth 2.0 Authorization Server Metadata & OpenID Configuration endpoint."""
    base_url = _get_public_base_url(request)
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "*",
        "Cache-Control": "no-store",
    }
    if request.method == "OPTIONS":
        return Response(status_code=204, headers=cors_headers)
    return JSONResponse(
        {
            "issuer": base_url,
            "authorization_endpoint": f"{base_url}/authorize",
            "token_endpoint": f"{base_url}/token",
            "registration_endpoint": f"{base_url}/register",
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code", "refresh_token"],
            "token_endpoint_auth_methods_supported": [
                "client_secret_post",
                "client_secret_basic",
                "none",
            ],
            "code_challenge_methods_supported": ["S256", "plain"],
            "scopes_supported": ["openid", "email", "profile"],
        },
        headers=cors_headers,
    )


async def oauth_register_client(request) -> Response:
    """RFC 7591 OAuth 2.0 Dynamic Client Registration endpoint."""
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "*",
        "Cache-Control": "no-store",
    }
    if request.method == "OPTIONS":
        return Response(status_code=204, headers=cors_headers)

    body_data: Dict[str, Any] = {}
    try:
        raw = await request.body()
        if raw:
            body_data = json.loads(raw.decode("utf-8", errors="replace"))
    except Exception:
        body_data = {}

    allowed_cids = [
        c.strip() for c in os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "").split(",") if c.strip()
    ]
    default_cid = allowed_cids[0] if allowed_cids else "mcp-dynamic-client"
    default_csec = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()

    redirect_uris = body_data.get("redirect_uris") or ["https://vertexaisearch.cloud.google.com/oauth-redirect"]
    client_name = body_data.get("client_name") or "MCP Dynamic Client"
    auth_method = body_data.get("token_endpoint_auth_method") or (
        "client_secret_post" if default_csec else "none"
    )
    now = int(time.time())

    resp_payload: Dict[str, Any] = {
        "client_id": default_cid,
        "client_name": client_name,
        "client_id_issued_at": now,
        "redirect_uris": redirect_uris,
        "grant_types": body_data.get("grant_types") or ["authorization_code", "refresh_token"],
        "response_types": body_data.get("response_types") or ["code"],
        "token_endpoint_auth_method": auth_method,
        "scope": body_data.get("scope") or "openid email profile",
    }
    if default_csec:
        resp_payload["client_secret"] = default_csec
        resp_payload["client_secret_expires_at"] = 0

    logger.info("OAuth /register dynamically registered MCP client: name=%s, redirect_uris=%s", client_name, redirect_uris)
    return JSONResponse(resp_payload, status_code=201, headers=cors_headers)


async def oauth_authorize(request) -> Response:
    """OAuth 2.0 Authorization Endpoint that validates client_id/redirect_uri and issues a signed authorization code."""
    global _last_authorize_redirect_uri

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

    allowed_cids = [
        c.strip() for c in os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "").split(",") if c.strip()
    ]
    code_challenge = params.get("code_challenge", "").strip()
    client_id = params.get("client_id", "").strip() or (allowed_cids[0] if allowed_cids else "oauth-client")
    if allowed_cids and client_id not in allowed_cids and not code_challenge:
        logger.warning("Rejected /authorize request: client_id did not match GOOGLE_OAUTH_CLIENT_ID")
        return JSONResponse(
            {"error": "unauthorized_client", "error_description": "Invalid client_id"},
            status_code=400,
        )

    redirect_uri = params.get("redirect_uri", "").strip()
    if not redirect_uri or not _is_valid_redirect_uri(redirect_uri):
        logger.warning("Rejected invalid or missing redirect_uri in /authorize")
        return JSONResponse(
            {"error": "invalid_request", "error_description": "Invalid redirect_uri"},
            status_code=400,
        )
    _last_authorize_redirect_uri = redirect_uri

    scope = params.get("scope", "openid email profile").strip() or "openid email profile"
    state = params.get("state", "")
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

    signed_code = _create_signed_token("mcp_code", code_payload)

    parsed_ru = urllib.parse.urlparse(redirect_uri)
    ru_query = dict(urllib.parse.parse_qsl(parsed_ru.query, keep_blank_values=True))
    ru_query["code"] = signed_code
    if state:
        ru_query["state"] = state
    target_url = urllib.parse.urlunparse(
        parsed_ru._replace(query=urllib.parse.urlencode(ru_query))
    )

    logger.info(
        "OAuth /authorize issued signed code and redirecting to redirect_uri=%s (has_state=%s, has_pkce=%s)",
        redirect_uri,
        bool(state),
        bool(code_challenge),
    )
    return RedirectResponse(url=target_url, status_code=302)


def _extract_basic_auth(auth_header: str) -> tuple[str, str]:
    """Extracts client_id and client_secret from an HTTP Basic Authorization header."""
    if not auth_header or not auth_header.lower().startswith("basic "):
        return "", ""
    encoded = auth_header[6:].strip()
    try:
        decoded = base64.b64decode(encoded).decode("utf-8")
        if ":" not in decoded:
            return urllib.parse.unquote(decoded), ""
        cid, csec = decoded.split(":", 1)
        return urllib.parse.unquote(cid).strip(), urllib.parse.unquote(csec).strip()
    except Exception:
        logger.warning("Failed to decode HTTP Basic Authorization header on /token")
        return "", ""


async def oauth_token(request) -> Response:
    """OAuth 2.0 Token Endpoint exchanging signed authorization codes or refresh tokens for access + refresh tokens."""
    sec_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
        "Access-Control-Allow-Headers": "*",
        "Cache-Control": "no-store",
        "Pragma": "no-cache",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
    }
    if request.method == "OPTIONS":
        return Response(status_code=204, headers=sec_headers)

    data: Dict[str, str] = {}
    for k, v in request.query_params.multi_items():
        if k:
            data[k] = v

    raw_body = await request.body()
    if raw_body:
        body_str = raw_body.decode("utf-8", errors="replace").strip()
        if body_str.startswith("{"):
            try:
                parsed_json = json.loads(body_str)
                if isinstance(parsed_json, dict):
                    for k, v in parsed_json.items():
                        if v is not None:
                            data[str(k)] = str(v)
            except Exception:
                logger.warning("Failed to parse JSON body on /token")
        else:
            for k, v in urllib.parse.parse_qsl(body_str, keep_blank_values=True):
                if k:
                    data[k] = v

    basic_cid, basic_csec = _extract_basic_auth(request.headers.get("authorization", ""))
    allowed_cids = [
        c.strip() for c in os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "").split(",") if c.strip()
    ]
    env_cid = allowed_cids[0] if allowed_cids else ""
    env_csec = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()

    client_id = (data.get("client_id") or basic_cid or env_cid).strip()
    client_secret = (data.get("client_secret") or basic_csec or env_csec).strip()

    grant_type = data.get("grant_type", "").strip()
    if not grant_type:
        if "code" in data:
            grant_type = "authorization_code"
        elif "refresh_token" in data:
            grant_type = "refresh_token"

    incoming_code = data.get("code", "").strip()
    incoming_rt = data.get("refresh_token", "").strip()
    incoming_verifier = data.get("code_verifier", "").strip()

    # 1. Handle stateless HMAC-signed authorization_code (mcp_code.*) or refresh_token (mcp_rt.*)
    if incoming_code.startswith("mcp_code.") or incoming_rt.startswith("mcp_rt."):
        if incoming_code.startswith("mcp_code."):
            token_payload = _verify_signed_token(incoming_code, expected_prefix="mcp_code")
            if not token_payload:
                return JSONResponse(
                    {"error": "invalid_grant", "error_description": "Invalid or expired authorization code"},
                    status_code=400,
                    headers=sec_headers,
                )
            expected_cc = token_payload.get("cc")
            if expected_cc and incoming_verifier:
                ccm = token_payload.get("ccm", "S256").upper()
                if ccm == "S256":
                    computed_cc = (
                        base64.urlsafe_b64encode(hashlib.sha256(incoming_verifier.encode("ascii")).digest())
                        .decode("ascii")
                        .rstrip("=")
                    )
                else:
                    computed_cc = incoming_verifier
                if not hmac.compare_digest(computed_cc, str(expected_cc)):
                    return JSONResponse(
                        {"error": "invalid_grant", "error_description": "PKCE code_verifier mismatch"},
                        status_code=400,
                        headers=sec_headers,
                    )
            elif not expected_cc:
                if allowed_cids and client_id not in allowed_cids:
                    return JSONResponse(
                        {"error": "invalid_client", "error_description": "Client ID mismatch"},
                        status_code=401,
                        headers=sec_headers,
                    )
                if env_csec and client_secret and not hmac.compare_digest(client_secret, env_csec):
                    return JSONResponse(
                        {"error": "invalid_client", "error_description": "Client secret mismatch"},
                        status_code=401,
                        headers=sec_headers,
                    )
        else:
            token_payload = _verify_signed_token(incoming_rt, expected_prefix="mcp_rt")
            if not token_payload:
                return JSONResponse(
                    {"error": "invalid_grant", "error_description": "Invalid or expired refresh token"},
                    status_code=400,
                    headers=sec_headers,
                )

        now = int(time.time())
        scope = str(token_payload.get("scp", "openid email profile"))
        issued_cid = str(token_payload.get("cid") or client_id or env_cid)
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
        logger.info("OAuth /token issued signed access_token & refresh_token (grant_type=%s)", grant_type)
        return JSONResponse(
            {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_in": 3600,
                "scope": scope,
            },
            status_code=200,
            headers=sec_headers,
        )

    # 2. Fallback: Forward raw Google OAuth codes/tokens to https://oauth2.googleapis.com/token
    payload: Dict[str, str] = {
        "grant_type": grant_type,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    for field in ("code", "redirect_uri", "code_verifier", "refresh_token"):
        val = data.get(field, "").strip()
        if val:
            payload[field] = val

    if grant_type == "authorization_code" and not payload.get("redirect_uri") and _last_authorize_redirect_uri:
        payload["redirect_uri"] = _last_authorize_redirect_uri

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(GOOGLE_TOKEN_ENDPOINT, data=payload)
            resp_data = resp.json() if resp.content else {}
    except Exception:
        logger.exception("Error communicating with Google OAuth token endpoint")
        return JSONResponse(
            {"error": "server_error", "error_description": "Upstream token exchange failed"},
            status_code=502,
            headers=sec_headers,
        )

    if resp.status_code != 200:
        return JSONResponse(resp_data, status_code=resp.status_code, headers=sec_headers)

    if not resp_data.get("refresh_token"):
        if payload.get("refresh_token"):
            resp_data["refresh_token"] = payload["refresh_token"]
        elif resp_data.get("access_token"):
            resp_data["refresh_token"] = f"ge_rt_{resp_data['access_token']}"

    resp_data.setdefault("token_type", "Bearer")
    resp_data.setdefault("expires_in", 3599)
    return JSONResponse(resp_data, status_code=200, headers=sec_headers)


async def health(request) -> Response:
    """Health check endpoint for Cloud Run liveness/startup probes and readiness verification."""
    return JSONResponse({
        "status": "healthy",
        "service": SERVICE_NAME,
        "transports": ["streamable-http", "sse"],
        "mcp_apps": [
            DOSSIER_RESOURCE_URI,
            PEER_RESOURCE_URI,
        ],
        "endpoints": {
            "mcp": "/mcp",
            "sse": "/sse",
            "messages": "/messages/",
            "authorize": "/authorize",
            "token": "/token",
            "register": "/register",
            "health": "/health",
            "preview_dossier_workbench": "/apps/raw/financial-dossier-workbench",
            "preview_peer_comparator": "/apps/raw/peer-industry-comparator",
        },
        "oauth_enabled": _token_verifier is not None,
        "sec_circuit_breaker": sec_api_client.circuit_breaker.get_status(),
    })


class _OriginTrackerMiddleware:
    """Pure ASGI middleware that records the external HTTPS origin from incoming request headers."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        global _last_public_base_url
        if scope.get("type") == "http":
            headers = {
                k.decode("latin-1").lower(): v.decode("latin-1")
                for k, v in scope.get("headers", [])
            }
            host = headers.get("x-forwarded-host") or headers.get("host")
            proto = headers.get("x-forwarded-proto") or scope.get("scheme") or "https"
            if host:
                if "localhost" in host or "127.0.0.1" in host:
                    proto = "http"
                _last_public_base_url = f"{proto}://{host}".rstrip("/")
        await self.app(scope, receive, send)


def get_asgi_app(transport: Optional[str] = None):
    """Returns a unified Starlette ASGI app supporting StreamableHTTP (/mcp), SSE (/sse), MCP App Previews (/apps/raw/*), OAuth, and /health."""
    app = mcp.streamable_http_app()

    sse_starlette = mcp.sse_app()
    existing_paths = {getattr(r, "path", None) for r in app.routes}
    for route in sse_starlette.routes:
        if getattr(route, "path", None) not in existing_paths:
            app.routes.append(route)

    app.routes.insert(0, Route("/apps/api/tool-call", apps_api_tool_call, methods=["POST", "OPTIONS"]))
    app.routes.insert(0, Route("/apps/raw/peer-industry-comparator", preview_peer_industry_comparator, methods=["GET", "HEAD"]))
    app.routes.insert(0, Route("/apps/raw/financial-dossier-workbench", preview_financial_dossier_workbench, methods=["GET", "HEAD"]))
    app.routes.insert(0, Route("/.well-known/oauth-protected-resource/{subpath:path}", oauth_protected_resource_metadata, methods=["GET", "OPTIONS"]))
    app.routes.insert(0, Route("/.well-known/oauth-protected-resource", oauth_protected_resource_metadata, methods=["GET", "OPTIONS"]))
    app.routes.insert(0, Route("/.well-known/oauth-authorization-server/{subpath:path}", oauth_authorization_server_metadata, methods=["GET", "OPTIONS"]))
    app.routes.insert(0, Route("/.well-known/oauth-authorization-server", oauth_authorization_server_metadata, methods=["GET", "OPTIONS"]))
    app.routes.insert(0, Route("/.well-known/openid-configuration", oauth_authorization_server_metadata, methods=["GET", "OPTIONS"]))
    app.routes.insert(0, Route("/register", oauth_register_client, methods=["POST", "OPTIONS"]))
    app.routes.insert(0, Route("/token", oauth_token, methods=["POST", "GET", "OPTIONS"]))
    app.routes.insert(0, Route("/authorize{extra:path}", oauth_authorize, methods=["GET", "HEAD"]))
    app.routes.insert(0, Route("/authorize", oauth_authorize, methods=["GET", "HEAD"]))
    app.routes.insert(0, Route("/health", health, methods=["GET", "HEAD"]))
    app.routes.insert(0, Route("/healthz", health, methods=["GET", "HEAD"]))
    app.routes.insert(0, Route("/", health, methods=["GET", "HEAD"]))
    app.add_middleware(_OriginTrackerMiddleware)
    return app
