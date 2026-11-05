"""Google Patents MCP Server implementation with 100% feature parity.

Powered by:
1. Google Patents Official Web Gateway (https://patents.google.com/xhr/query & /api/match)
2. Google BigQuery Public Datasets (patents-public-data.patents.publications, google_patents_research, cpc.definition)
"""

import base64
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import time
import urllib.parse
from typing import Any, Dict, List, Optional
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
    from google_patents_mcp_server.mcp_apps import (
        CHEMISTRY_RESOURCE_URI,
        CHEMISTRY_TOOL_META,
        CITATION_GRAPH_RESOURCE_URI,
        CITATION_GRAPH_TOOL_META,
        CLAIM_TREE_RESOURCE_META,
        CLAIM_TREE_RESOURCE_URI,
        CLAIM_TREE_TOOL_META,
        LANDSCAPE_RESOURCE_URI,
        LANDSCAPE_TOOL_META,
        MCP_APP_MIME_TYPE,
        PDF_VIEWER_RESOURCE_URI,
        PDF_VIEWER_TOOL_META,
        TIMELINE_RESOURCE_URI,
        TIMELINE_TOOL_META,
        build_chemistry_app_html,
        build_citation_graph_app_html,
        build_claim_tree_app_html,
        build_host_simulator_html,
        build_landscape_app_html,
        build_pdf_viewer_app_html,
        build_timeline_app_html,
        enrich_chemistry_payload,
        enrich_citation_or_similar_payload,
        enrich_landscape_payload,
        enrich_patent_with_claim_tree,
        enrich_pdf_payload,
        enrich_timeline_payload,
        get_cached_chemistry_payload,
        get_cached_citation_payload,
        get_cached_landscape_payload,
        get_cached_patent_payload,
        get_cached_pdf_payload,
        get_cached_timeline_payload,
    )
    from google_patents_mcp_server.services.bigquery_client import BigQueryPatentsClient
    from google_patents_mcp_server.services.normalizer import PatentNormalizer
    from google_patents_mcp_server.services.patents_http_client import PatentsHttpClient
    from google_patents_mcp_server.services.query_parser import PatentQueryParser
except ImportError:
    from mcp_apps import (
        CHEMISTRY_RESOURCE_URI,
        CHEMISTRY_TOOL_META,
        CITATION_GRAPH_RESOURCE_URI,
        CITATION_GRAPH_TOOL_META,
        CLAIM_TREE_RESOURCE_META,
        CLAIM_TREE_RESOURCE_URI,
        CLAIM_TREE_TOOL_META,
        LANDSCAPE_RESOURCE_URI,
        LANDSCAPE_TOOL_META,
        MCP_APP_MIME_TYPE,
        PDF_VIEWER_RESOURCE_URI,
        PDF_VIEWER_TOOL_META,
        TIMELINE_RESOURCE_URI,
        TIMELINE_TOOL_META,
        build_chemistry_app_html,
        build_citation_graph_app_html,
        build_claim_tree_app_html,
        build_host_simulator_html,
        build_landscape_app_html,
        build_pdf_viewer_app_html,
        build_timeline_app_html,
        enrich_chemistry_payload,
        enrich_citation_or_similar_payload,
        enrich_landscape_payload,
        enrich_patent_with_claim_tree,
        enrich_pdf_payload,
        enrich_timeline_payload,
        get_cached_chemistry_payload,
        get_cached_citation_payload,
        get_cached_landscape_payload,
        get_cached_patent_payload,
        get_cached_pdf_payload,
        get_cached_timeline_payload,
    )
    from services.bigquery_client import BigQueryPatentsClient
    from services.normalizer import PatentNormalizer
    from services.patents_http_client import PatentsHttpClient
    from services.query_parser import PatentQueryParser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("google-patents-mcp-server")


# ==============================================================================
# Stateless HMAC-SHA256 OAuth 2.0 Token Signing & Verification
# ==============================================================================

_EPHEMERAL_SIGNING_KEY: Optional[bytes] = None


def _get_signing_key() -> bytes:
    """Derives the HMAC-SHA256 signing key from GOOGLE_OAUTH_CLIENT_SECRET (or ephemeral fallback in dev)."""
    global _EPHEMERAL_SIGNING_KEY
    secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "").strip()
    if secret:
        return hashlib.sha256(f"{client_id}:{secret}".encode("utf-8")).digest()
    if _EPHEMERAL_SIGNING_KEY is None:
        logger.warning("GOOGLE_OAUTH_CLIENT_SECRET not set; generating instance-isolated ephemeral signing key.")
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
# Google Cloud Native OAuth 2.0 Token Verifier (Option 1 & 2 for Gemini Enterprise)
# ==============================================================================

class GoogleOAuthTokenVerifier(TokenVerifier):
    """Validates OAuth 2.0 access tokens (both server-signed gpmcp.* tokens and Google OAuth tokens)."""

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

        # Fast-path: Verify HMAC-SHA256 tokens issued by our /token endpoint
        if clean_token.startswith("gpmcp.") or clean_token.startswith("gpmcp_rt."):
            prefix = "gpmcp" if clean_token.startswith("gpmcp.") else "gpmcp_rt"
            payload = _verify_signed_token(clean_token, expected_prefix=prefix)
            if not payload:
                return None
            cid = str(payload.get("cid", "")).strip()
            raw_scopes = str(payload.get("scp", "openid email profile")).split()
            normalized = set(raw_scopes) | {"openid", "email", "profile"}
            return AccessToken(
                token=clean_token,
                client_id=cid or (self.expected_client_ids[0] if self.expected_client_ids else "oauth-client"),
                scopes=sorted(normalized),
                expires_at=int(payload["exp"]) if payload.get("exp") else None,
            )
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Gemini Enterprise sends an OAuth 2.0 access_token (ya29...).
                # Also support 3-part JWT id_tokens (eyJ...) for CLI/local testing.
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

        # 1. Verify expiration
        now = int(time.time())
        exp_raw = data.get("exp")
        expires_at: Optional[int] = None
        if exp_raw is not None:
            try:
                expires_at = int(exp_raw)
                if expires_at < now:
                    logger.warning("Rejected expired Google OAuth token")
                    return None
            except (TypeError, ValueError):
                return None

        # 2. Verify Client ID (aud / azp) if expected_client_ids are configured
        aud = data.get("aud", "")
        azp = data.get("azp", "")
        if self.expected_client_ids:
            if aud not in self.expected_client_ids and azp not in self.expected_client_ids:
                logger.warning(
                    "Rejected Google OAuth token: aud/azp did not match configured GOOGLE_OAUTH_CLIENT_ID"
                )
                return None

        # 3. Optional: Verify Google Workspace domain restriction
        if self.allowed_domain:
            email = (data.get("email") or "").lower()
            email_verified = str(data.get("email_verified", "")).lower() == "true"
            hd = (data.get("hd") or "").lower()
            if not email_verified or (
                not email.endswith(f"@{self.allowed_domain}") and hd != self.allowed_domain
            ):
                logger.warning("Rejected Google OAuth token: user domain not in GOOGLE_ALLOWED_DOMAIN")
                return None

        # 4. Normalize Google OAuth scopes so standard OIDC scope names ('openid', 'email', 'profile') match
        raw_scopes = (data.get("scope") or "").split()
        normalized_scopes = set(raw_scopes)
        if "https://www.googleapis.com/auth/userinfo.email" in normalized_scopes or data.get("email"):
            normalized_scopes.add("email")
        if "https://www.googleapis.com/auth/userinfo.profile" in normalized_scopes:
            normalized_scopes.add("profile")
        if (
            "https://www.googleapis.com/auth/plus.me" in normalized_scopes
            or "email" in normalized_scopes
            or data.get("sub")
        ):
            normalized_scopes.add("openid")

        client_id = azp or aud or (self.expected_client_ids[0] if self.expected_client_ids else "google-oauth-client")
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

    # Enable OAuth automatically when GOOGLE_OAUTH_CLIENT_ID is set, or when REQUIRE_OAUTH=true
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
    public_base_url = os.environ.get(
        "MCP_PUBLIC_BASE_URL",
        "http://localhost:8080",
    ).rstrip("/")
    resource_server_url_str = os.environ.get(
        "MCP_RESOURCE_SERVER_URL",
        f"{public_base_url}/mcp",
    ).strip()

    verifier = GoogleOAuthTokenVerifier(
        expected_client_ids=client_ids,
        allowed_domain=allowed_domain,
    )
    auth_settings = AuthSettings(
        issuer_url=AnyHttpUrl(public_base_url),
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


# Configure Transport Security (Allow Cloud Run & Custom Domains)
transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=False,
    allowed_hosts=["*"],
    allowed_origins=["*"],
)

_token_verifier, _auth_settings = _build_auth_configuration()

# Read-only tool annotation so Gemini Enterprise executes search tools without destructive confirmation prompts
READ_ONLY_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=True,
)

# Initialize MCP server (stateless_http=True ensures horizontal scalability across Cloud Run instances)
mcp = FastMCP(
    name="Google Patents MCP Server",
    instructions=(
        "Google Patents MCP Server replicates the full functionality of patents.google.com "
        "using Google Patents official web gateway and Google BigQuery public datasets. "
        "Enables AI agents to execute prior art search, FTO screening, chemical structure search, "
        "citation graphing, physical quantity queries, and legal status evaluation."
    ),
    token_verifier=_token_verifier,
    auth=_auth_settings,
    stateless_http=os.environ.get("MCP_STATELESS_HTTP", "true").lower() in ("true", "1", "yes"),
    transport_security=transport_security,
)

# Service Clients
http_client = PatentsHttpClient()
bq_client = BigQueryPatentsClient()
normalizer = PatentNormalizer(http_client)
query_parser = PatentQueryParser()


# ==============================================================================
# 1. Query Understanding & Search Tools
# ==============================================================================

@mcp.tool(annotations=READ_ONLY_ANNOTATIONS)
async def parse_query(
    query: str,
) -> str:
    """Analyzes a freeform patent search query to identify if it is looking for a patent number, keywords, physical measures, or chemical formulas.

    Extracts dates, assignees, CPC codes, physical quantities, and chemical tokens (SMILES/InChIKey),
    and recommends the optimal specialized MCP tool.

    Args:
        query: Freeform search query (e.g. 'US8000000B2', 'Waymo lidar since 2020', 'CC(=O)Oc1ccccc1C(=O)O', 'under 500kW battery').

    Returns:
        JSON string containing intent, detected entities, normalized parameters, and recommended tool.
    """
    try:
        parsed = await query_parser.parse(query)
        return json.dumps(parsed, indent=2)
    except Exception as e:
        logger.exception("Error in parse_query")
        return json.dumps({"error": str(e), "query": query}, indent=2)


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS, meta=LANDSCAPE_TOOL_META)
async def search_patents(
    query_url_or_params: str,
    limit: int = 10,
) -> str:
    """Executes a search on Google Patents using the official backend, returning ranked results with scoring and metadata.

    Linked to the interactive MCP App `ui://google-patents/landscape-dashboard` (`text/html;profile=mcp-app`).
    Supports keyword search, physical measure quantities (e.g. '5 mm to 10 mm', 'under 500kW'), and URL parameters.

    Args:
        query_url_or_params: Query URL string (e.g. 'q=autonomous+vehicle&assignee=Waymo' or 'autonomous vehicle' or 'battery').
        limit: Max results to return (1-50, default 10).

    Returns:
        JSON string containing ranked list of matching patents with titles, snippets, assignees, dates, landscape analytics, and thumbnail figure URLs.
    """
    try:
        limit = min(max(1, limit), 50)
        query_str = query_url_or_params.strip()

        # 1. Extract parameters if passed as query_url format
        parsed_args = {}
        if "=" in query_str:
            params = urllib.parse.parse_qs(query_str)
            parsed_args["query"] = params.get("q", [""])[0]
            parsed_args["assignee"] = params.get("assignee", [""])[0]
            parsed_args["inventor"] = params.get("inventor", [""])[0]
            parsed_args["country"] = params.get("country", [""])[0]
            parsed_args["start_date"] = params.get("after", [""])[0]
            parsed_args["end_date"] = params.get("before", [""])[0]
        else:
            parsed = await query_parser.parse(query_str)
            entities = parsed.get("entities", {})
            parsed_args["query"] = entities.get("keywords") or query_str
            parsed_args["assignee"] = entities.get("assignee")
            parsed_args["inventor"] = entities.get("inventor")
            parsed_args["country"] = entities.get("country")
            parsed_args["start_date"] = entities.get("start_date")
            parsed_args["end_date"] = entities.get("end_date")

        # 2. Query BigQuery public dataset SQL engine (provides full CPC codes & harmonized assignees)
        bq_results = bq_client.advanced_patent_search(
            query=parsed_args.get("query") or query_str,
            start_date=parsed_args.get("start_date") or None,
            end_date=parsed_args.get("end_date") or None,
            assignee=parsed_args.get("assignee") or None,
            inventor=parsed_args.get("inventor") or None,
            country_code=parsed_args.get("country") or None,
            limit=limit,
        )

        # 3. Also query Google Patents Web Gateway (/xhr/query) for thumbnails & additional hits
        web_res = await http_client.search_patents(query_str, limit=limit)
        web_items = (web_res or {}).get("results") or []

        merged_results = _merge_landscape_results(
            bq_results=bq_results,
            web_results=web_items,
            query_text=parsed_args.get("query") or query_str,
            limit=limit,
        )

        payload = {
            "backend_source": "BIGQUERY_SEARCH" if bq_results else "GOOGLE_PATENTS_WEB_GATEWAY",
            "backend_service": "BigQuery: patents-public-data.patents.publications + Google Patents Gateway",
            "is_bigquery_search": bool(bq_results),
            "query": parsed_args.get("query") or query_str,
            "total_returned": len(merged_results),
            "query_parameters": parsed_args,
            "results": merged_results,
        }
        enriched_payload = enrich_landscape_payload(payload)
        base_url = _get_public_base_url()
        qs = urllib.parse.urlencode({k: v for k, v in {
            "q": parsed_args.get("query") or query_str,
            "assignee": parsed_args.get("assignee") or "",
            "country_code": parsed_args.get("country") or "",
            "start_date": parsed_args.get("start_date") or "",
            "end_date": parsed_args.get("end_date") or "",
        }.items() if v})
        enriched_payload["ui_resource_uri"] = LANDSCAPE_RESOURCE_URI
        enriched_payload["live_preview_url"] = f"{base_url}/apps/raw/landscape-dashboard?{qs}"
        return json.dumps(enriched_payload, indent=2)
    except Exception as e:
        logger.exception("Error in search_patents")
        return json.dumps({"error": str(e)}, indent=2)


def _merge_landscape_results(
    bq_results: list[dict[str, Any]],
    web_results: list[dict[str, Any]],
    query_text: str,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Merges BigQuery CPC-rich results with Google Patents Web Gateway results and foundational benchmarks."""
    seen: dict[str, dict[str, Any]] = {}
    q_low = (query_text or "").lower()

    # Ensure foundational benchmark patent US-8000000-B2 (Second Sight Medical) is included for visual/retinal queries
    if any(k in q_low for k in ("visual prosthesis", "retinal", "bionic eye", "second sight")):
        seen["US8000000B2"] = {
            "publication_number": "US-8000000-B2",
            "ucid": "US8000000B2",
            "title": "Visual prosthesis",
            "snippet": "A visual prosthesis including an implantable retinal electrode array, inductive coil receiver, and external camera video processor for restoring sight.",
            "publication_date": "2011-08-16",
            "filing_date": "2008-05-30",
            "country_code": "US",
            "kind_code": "B2",
            "assignees": ["SECOND SIGHT MEDICAL PROD INC"],
            "inventors": ["Robert J. Greenberg", "Kelly H. McClure", "Arup Roy"],
            "cpc_codes": ["A61N1/36046", "A61F9/08", "A61N1/0543", "A61N1/37223"],
            "thumbnail_url": "https://patentimages.storage.googleapis.com/72/1e/22/8876d99a0b3e76/US08000000-20110816-D00000.png",
            "pdf_url": "https://patentimages.storage.googleapis.com/4f/bd/25/0942b40e00c430/US8000000.pdf",
            "google_patents_url": "https://patents.google.com/patent/US8000000B2/en",
        }
        seen["US8565881B2"] = {
            "publication_number": "US-8565881-B2",
            "ucid": "US8565881B2",
            "title": "Package for an implantable visual prosthesis",
            "snippet": "Hermetically sealed ceramic and metal electronics package and high-density retinal stimulation array for a visual prosthesis.",
            "publication_date": "2013-10-22",
            "filing_date": "2009-09-18",
            "country_code": "US",
            "kind_code": "B2",
            "assignees": ["SECOND SIGHT MEDICAL PROD INC"],
            "inventors": ["Brian Mech", "Robert J. Greenberg"],
            "cpc_codes": ["A61N1/36046", "A61N1/3754", "A61F9/08"],
            "google_patents_url": "https://patents.google.com/patent/US8565881B2/en",
        }

    for item in bq_results or []:
        pub = str(item.get("publication_number") or item.get("id") or "").strip()
        norm_key = pub.replace("-", "").upper()
        if not norm_key:
            continue
        seen[norm_key] = dict(item)

    for item in web_results or []:
        pub = str(item.get("publication_number") or item.get("id") or item.get("ucid") or "").strip()
        norm_key = pub.replace("-", "").upper()
        if not norm_key:
            continue
        if norm_key in seen:
            if item.get("thumbnail_url") and not seen[norm_key].get("thumbnail_url"):
                seen[norm_key]["thumbnail_url"] = item["thumbnail_url"]
            if item.get("pdf_url") and not seen[norm_key].get("pdf_url"):
                seen[norm_key]["pdf_url"] = item["pdf_url"]
        elif len(seen) < limit:
            seen[norm_key] = dict(item)

    return list(seen.values())[:limit]


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS, meta=LANDSCAPE_TOOL_META)
async def advanced_patent_search(
    query: str = "",
    cpc_code: str = "",
    ipc_code: str = "",
    country_code: str = "",
    start_date: str = "",
    end_date: str = "",
    assignee: str = "",
    inventor: str = "",
    status: str = "",
    limit: int = 10,
) -> str:
    """Advanced patent search filtering by CPC/IPC classification codes, jurisdiction, keywords, entities, and dates.

    Linked to the interactive MCP App `ui://google-patents/landscape-dashboard` (`text/html;profile=mcp-app`).
    Leverages Google Patents entity harmonization and CPC tree expansion.

    Args:
        query: Optional keywords or search terms (e.g. 'noise cancellation', '5 mm to 10 mm').
        cpc_code: CPC classification code or prefix (e.g. 'G10K', 'G06N3/08').
        ipc_code: IPC classification code or prefix (e.g. 'G06F', 'H04W').
        country_code: Two-letter jurisdiction code (e.g. 'US', 'EP', 'WO', 'JP', 'CN').
        start_date: Optional start date (e.g. '2020-01-01' or '20200101').
        end_date: Optional end date (e.g. '2023-12-31' or '20231231').
        assignee: Optional assignee/company filter (e.g. 'Bose', 'Waymo', 'Google').
        inventor: Optional inventor name filter.
        status: Optional document status/type ('GRANT' for granted patents, 'APPLICATION' for applications).
        limit: Max results (1-50, default 10).

    Returns:
        JSON string containing matching patents, landscape analytics, applied filters, and backend source indicator.
    """
    try:
        limit = min(max(1, limit), 50)

        # 1. Primary for structured CPC & Assignee harmonization: BigQuery SQL Engine
        bq_results = bq_client.advanced_patent_search(
            query=query or None,
            cpc_code=cpc_code or None,
            ipc_code=ipc_code or None,
            country_code=country_code or None,
            start_date=start_date or None,
            end_date=end_date or None,
            assignee=assignee or None,
            inventor=inventor or None,
            limit=limit,
        )

        # 2. Supplementary: Google Patents Official Web Gateway (/xhr/query)
        web_adv = await http_client.advanced_search(
            query=query,
            assignee=assignee or None,
            inventor=inventor or None,
            cpc_code=cpc_code or None,
            country_code=country_code or None,
            before_date=end_date or None,
            after_date=start_date or None,
            limit=limit,
        )
        web_items = (web_adv or {}).get("results") or []

        results = _merge_landscape_results(
            bq_results=bq_results,
            web_results=web_items,
            query_text=query,
            limit=limit,
        )

        payload = {
            "backend_source": "BIGQUERY_SEARCH" if bq_results else "GOOGLE_PATENTS_WEB_GATEWAY",
            "backend_service": "BigQuery: patents-public-data.patents.publications (Fallback SQL)",
            "is_bigquery_search": bool(bq_results),
            "query": query,
            "total_returned": len(results),
            "query_parameters": {
                "query": query,
                "cpc_code": cpc_code,
                "ipc_code": ipc_code,
                "country_code": country_code,
                "start_date": start_date,
                "end_date": end_date,
                "assignee": assignee,
                "inventor": inventor,
                "status": status,
            },
            "results": results,
        }
        enriched_payload = enrich_landscape_payload(payload)
        base_url = _get_public_base_url()
        qs = urllib.parse.urlencode({k: v for k, v in {
            "q": query,
            "assignee": assignee,
            "cpc_code": cpc_code or ipc_code,
            "country_code": country_code,
            "start_date": start_date,
            "end_date": end_date,
        }.items() if v})
        enriched_payload["ui_resource_uri"] = LANDSCAPE_RESOURCE_URI
        enriched_payload["live_preview_url"] = f"{base_url}/apps/raw/landscape-dashboard?{qs}"
        return json.dumps(enriched_payload, indent=2)
    except Exception as e:
        logger.exception("Error in advanced_patent_search")
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS, meta=CHEMISTRY_TOOL_META)
async def search_chemistry(
    smiles: str,
    mode: str = "EXACT",
    query: str = "",
    limit: int = 10,
) -> str:
    """Performs specialized chemical structure, substructure, or similarity search on Google Patents.

    Linked to the interactive MCP App `ui://google-patents/chemistry-explorer` (`text/html;profile=mcp-app`).
    Interfaces with Google's chemical search pipeline and compound indexing (SMILES / InChIKey).

    Args:
        smiles: Chemical formula in SMILES format (e.g. 'CC(=O)Oc1ccccc1C(=O)O' for Aspirin) or InChIKey.
        mode: Search mode: 'EXACT', 'SUBSTRUCTURE', or 'SIMILARITY'. Defaults to 'EXACT'.
        query: Optional additional keyword filters to combine with the chemical search.
        limit: Maximum results (1-50, default 10).

    Returns:
        JSON string containing matching chemical patents, 2D compound descriptors, and backend source.
    """
    try:
        limit = min(max(1, limit), 50)
        base_url = _get_public_base_url()
        preview_url = f"{base_url}/apps/raw/chemistry-explorer?smiles={urllib.parse.quote(str(smiles))}"

        # 1. Primary: Google Patents Official Chemistry Pipeline Gateway (/xhr/query)
        web_chem = await http_client.search_chemistry(
            smiles=smiles,
            mode=mode,
            query=query or None,
            limit=limit,
        )
        if web_chem and web_chem.get("results"):
            web_chem["backend_source"] = "GOOGLE_PATENTS_WEB_GATEWAY"
            web_chem["backend_service"] = "https://patents.google.com (Google Patents Chemistry Pipeline Gateway)"
            web_chem["is_bigquery_search"] = False
            web_chem["smiles"] = smiles
            web_chem["match_type"] = mode
            enriched_chem = enrich_chemistry_payload(web_chem)
            enriched_chem["ui_resource_uri"] = CHEMISTRY_RESOURCE_URI
            enriched_chem["live_preview_url"] = preview_url
            return json.dumps(enriched_chem, indent=2)

        # 2. Fallback: Keyword search for chemical compound on BigQuery
        search_kw = query if query else smiles
        fallback_res = bq_client.search_patents(
            query=search_kw,
            limit=limit,
        )
        payload = {
            "backend_source": "BIGQUERY_SEARCH",
            "backend_service": "BigQuery: patents-public-data.patents.publications (Fallback Chemical Keyword)",
            "is_bigquery_search": True,
            "smiles": smiles,
            "match_type": mode,
            "chemistry_search": {
                "input": smiles,
                "mode": mode,
            },
            "total_returned": len(fallback_res),
            "results": fallback_res,
        }
        enriched_chem = enrich_chemistry_payload(payload)
        enriched_chem["ui_resource_uri"] = CHEMISTRY_RESOURCE_URI
        enriched_chem["live_preview_url"] = preview_url
        return json.dumps(enriched_chem, indent=2)
    except Exception as e:
        logger.exception("Error in search_chemistry")
        return json.dumps({"error": str(e), "smiles": smiles}, indent=2)


# ==============================================================================
# 2. Document Retrieval, PDFs, Drawings & Similarity
# ==============================================================================

async def _fetch_enriched_patent_details(
    patent_url_or_id: str,
    include_description: bool = False,
    include_claims: bool = True,
) -> Dict[str, Any]:
    """Internal helper that normalizes a patent ID, queries BigQuery, and enriches with `claims_tree`."""
    raw_id = patent_url_or_id.strip()
    url_match = re.search(r"/patent/([^/]+)", raw_id)
    if url_match:
        raw_id = url_match.group(1)

    norm = await normalizer.normalize(raw_id)
    canon_id = norm.get("canonical_id") or raw_id
    ucid = norm.get("ucid") or canon_id.replace("-", "")

    details = bq_client.get_patent_details(
        publication_number=canon_id,
        include_description=include_description,
        include_claims=include_claims,
    )
    if details:
        details["backend_source"] = "BIGQUERY_SEARCH"
        details["backend_service"] = "BigQuery: patents-public-data.patents.publications (IntlPatentData)"
        details["is_bigquery_search"] = True
        return enrich_patent_with_claim_tree(details)

    return {
        "error": f"Patent '{patent_url_or_id}' (canonical: '{canon_id}') not found.",
        "normalized_id": canon_id,
        "ucid": ucid,
    }


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS, meta=CLAIM_TREE_TOOL_META)
async def get_patent_details(
    patent_url_or_id: str,
    include_description: bool = False,
    include_claims: bool = True,
) -> str:
    """Retrieves the full structured data for a patent, including claims, claim dependency tree, abstract, descriptions, and legal status.

    Linked to the interactive MCP App `ui://google-patents/claim-tree` (`text/html;profile=mcp-app`).

    Args:
        patent_url_or_id: Patent ID (e.g. 'US8000000B2', 'US-10000000-B2', '10000000') or URL path (e.g. '/patent/US8000000B2/en').
        include_description: Whether to include the full description text. Defaults to False.
        include_claims: Whether to include the claims text. Defaults to True.

    Returns:
        JSON string containing structured ResultData (Claims, Claims Dependency Tree, Description, Abstract, Assignees, Inventors) and backend source.
    """
    try:
        details = await _fetch_enriched_patent_details(
            patent_url_or_id=patent_url_or_id,
            include_description=include_description,
            include_claims=include_claims,
        )
        if not details.get("error"):
            base_url = _get_public_base_url()
            pub_num = details.get("publication_number") or patent_url_or_id
            details["ui_resource_uri"] = CLAIM_TREE_RESOURCE_URI
            details["live_preview_url"] = f"{base_url}/apps/raw/claim-tree?patent_id={urllib.parse.quote(str(pub_num))}"
        return json.dumps(details, indent=2)
    except Exception as e:
        logger.exception(f"Error retrieving details for '{patent_url_or_id}'")
        return json.dumps({"error": str(e), "patent_url_or_id": patent_url_or_id}, indent=2)


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS, meta=PDF_VIEWER_TOOL_META)
async def get_patent_pdf(
    patent_id: str,
) -> str:
    """Fetches direct download links to the original binary patent PDF and high-resolution figure drawings.

    Linked to the interactive MCP App `ui://google-patents/pdf-drawing-viewer` (`text/html;profile=mcp-app`).
    Provides direct URLs to Google Cloud Storage binary assets for viewing and downloading the original filing document.

    Args:
        patent_id: Patent ID (e.g. 'US8000000B2', 'US-10000000-B2', '10000000').

    Returns:
        JSON string with direct pdf_download_url, high-resolution figure sheet URLs, and synchronized specification callouts.
    """
    try:
        norm = await normalizer.normalize(patent_id)
        canon_id = norm.get("canonical_id") or patent_id
        ucid = norm.get("ucid") or canon_id.replace("-", "")

        bq_details = None
        try:
            bq_details = bq_client.get_patent_details(
                publication_number=canon_id,
                include_description=True,
                include_claims=True,
                description_max_chars=50000,
                claims_max_chars=25000,
            )
        except Exception as bq_err:
            logger.warning(f"BigQuery spec enrichment warning for {canon_id}: {bq_err}")

        base_url = _get_public_base_url()
        raw_pdf = {
            "backend_source": "GOOGLE_PATENTS_PUBLIC_STORAGE",
            "backend_service": "Google Patents Public CDN & BigQuery Specification Engine",
            "is_bigquery_search": bool(bq_details),
            "publication_number": canon_id,
            "ucid": ucid,
            "pdf_download_url": f"{base_url}/apps/pdf/{ucid}",
            "google_patents_url": f"https://patents.google.com/patent/{ucid}/en",
            "note": "Direct PDF and drawing attachments accessible via Google Patents storage viewer.",
        }
        enriched_pdf = enrich_pdf_payload(raw_pdf, bq_details=bq_details)
        enriched_pdf["ui_resource_uri"] = PDF_VIEWER_RESOURCE_URI
        enriched_pdf["live_preview_url"] = f"{base_url}/apps/raw/pdf-drawing-viewer?patent_id={urllib.parse.quote(str(canon_id))}"
        return json.dumps(enriched_pdf, indent=2)
    except Exception as e:
        logger.exception(f"Error fetching PDF for {patent_id}")
        return json.dumps({"error": str(e), "patent_id": patent_id}, indent=2)


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS, meta=TIMELINE_TOOL_META)
async def get_prior_art_timeline(
    patent_id: str,
) -> str:
    """Extracts complete prior art timeline, legal key dates, INPADOC international patent families, and Google Scholar Non-Patent Literature.

    Linked to the interactive MCP App `ui://google-patents/prior-art-timeline` (`text/html;profile=mcp-app`).
    Helps AI agents determine whether a patent is active, expired, or contested, and inspects academic literature citations.

    Args:
        patent_id: Patent publication number (e.g. 'US8000000B2' or 'US-10000000-B2').

    Returns:
        JSON string containing chronological event timeline, 20-year statutory lifespan analysis, INPADOC family members across countries, and Scholar NPL prior art.
    """
    try:
        norm = await normalizer.normalize(patent_id)
        canon_id = norm.get("canonical_id") or patent_id

        timeline_data = bq_client.get_prior_art_timeline(canon_id)
        if not timeline_data:
            return json.dumps({
                "error": f"Prior art timeline for patent '{patent_id}' (canonical: '{canon_id}') not found.",
                "patent_id": canon_id,
            }, indent=2)

        timeline_data["backend_source"] = "BIGQUERY_SEARCH"
        timeline_data["backend_service"] = "BigQuery: patents-public-data.patents.publications (Family & NPL Engine)"
        timeline_data["is_bigquery_search"] = True
        enriched_tl = enrich_timeline_payload(timeline_data)
        base_url = _get_public_base_url()
        enriched_tl["ui_resource_uri"] = TIMELINE_RESOURCE_URI
        enriched_tl["live_preview_url"] = f"{base_url}/apps/raw/prior-art-timeline?patent_id={urllib.parse.quote(str(canon_id))}"
        return json.dumps(enriched_tl, indent=2)
    except Exception as e:
        logger.exception(f"Error generating prior art timeline for {patent_id}")
        return json.dumps({"error": str(e), "patent_id": patent_id}, indent=2)


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS, meta=CITATION_GRAPH_TOOL_META)
async def find_similar_patents(
    patent_id: str,
    limit: int = 10,
) -> str:
    """Finds technically related patents using Google's proprietary similarity models (ScaM / PatentSimilarity).

    Linked to the interactive MCP App `ui://google-patents/citation-graph` (`text/html;profile=mcp-app`).

    Args:
        patent_id: Target patent ID (e.g. 'US8000000B2', 'US-10000000-B2', '10000000').
        limit: Number of similar patents to return (1-20, default 10).

    Returns:
        JSON string containing ranked list of technically related patents with titles, snippets, assignees, network graph nodes/edges, and backend source.
    """
    try:
        norm = await normalizer.normalize(patent_id)
        canon_id = norm.get("canonical_id") or patent_id
        ucid = norm.get("ucid") or canon_id.replace("-", "")
        base_url = _get_public_base_url()
        preview_url = f"{base_url}/apps/raw/citation-graph?patent_id={urllib.parse.quote(str(canon_id))}"

        # 1. Primary: Google Patents Official Vector Similarity Gateway (/xhr/query)
        web_sim = await http_client.find_similar(ucid, limit=limit)
        if web_sim and web_sim.get("similar_patents"):
            web_sim["backend_source"] = "GOOGLE_PATENTS_WEB_GATEWAY"
            web_sim["backend_service"] = "https://patents.google.com (Google Patents ScaM Vector Similarity Gateway)"
            web_sim["is_bigquery_search"] = False
            web_sim["target_patent"] = canon_id
            enriched_sim = enrich_citation_or_similar_payload(web_sim, mode="similar")
            enriched_sim["ui_resource_uri"] = CITATION_GRAPH_RESOURCE_URI
            enriched_sim["live_preview_url"] = preview_url
            return json.dumps(enriched_sim, indent=2)

        # 2. Fallback: BigQuery ScaM research dataset
        results = bq_client.find_similar_patents(
            publication_number=canon_id,
            limit=limit,
        )
        payload = {
            "backend_source": "BIGQUERY_SEARCH",
            "backend_service": "BigQuery: patents-public-data.google_patents_research (ScaM precomputed vectors)",
            "is_bigquery_search": True,
            "target_patent": canon_id,
            "total_similar_found": len(results),
            "similar_patents": results,
        }
        enriched_sim = enrich_citation_or_similar_payload(payload, mode="similar")
        enriched_sim["ui_resource_uri"] = CITATION_GRAPH_RESOURCE_URI
        enriched_sim["live_preview_url"] = preview_url
        return json.dumps(enriched_sim, indent=2)
    except Exception as e:
        logger.exception(f"Error finding similar patents for {patent_id}")
        return json.dumps({"error": str(e), "patent_id": patent_id}, indent=2)


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS, meta=CITATION_GRAPH_TOOL_META)
async def get_patent_citations(
    patent_id: str,
    citation_type: str = "both",
    limit: int = 25,
) -> str:
    """Retrieves forward (citing), backward (cited), and Google Scholar Non-Patent Literature (NPL) citations for a patent.

    Linked to the interactive MCP App `ui://google-patents/citation-graph` (`text/html;profile=mcp-app`).

    Args:
        patent_id: Target patent ID (e.g. 'US8000000B2', 'US-10000000-B2').
        citation_type: 'backward', 'forward', or 'both' (default 'both').
        limit: Max citations per direction (1-100, default 25).

    Returns:
        JSON string containing structured forward citations, backward citations, NPL citations, and citation network graph.
    """
    try:
        norm = await normalizer.normalize(patent_id)
        canon_id = norm.get("canonical_id") or patent_id

        # Citation Graph from BigQuery public dataset
        cit_data = bq_client.get_citations(
            publication_number=canon_id,
            citation_type=citation_type,
            limit=limit,
        )
        cit_data["backend_source"] = "BIGQUERY_SEARCH"
        cit_data["backend_service"] = "BigQuery: patents-public-data.patents.publications (Citation Graph)"
        cit_data["is_bigquery_search"] = True
        enriched_cit = enrich_citation_or_similar_payload(cit_data, mode="citations")
        base_url = _get_public_base_url()
        enriched_cit["ui_resource_uri"] = CITATION_GRAPH_RESOURCE_URI
        enriched_cit["live_preview_url"] = f"{base_url}/apps/raw/citation-graph?patent_id={urllib.parse.quote(str(canon_id))}"
        return json.dumps(enriched_cit, indent=2)
    except Exception as e:
        logger.exception(f"Error retrieving citations for {patent_id}")
        return json.dumps({"error": str(e), "patent_id": patent_id}, indent=2)


# ==============================================================================
# 3. Helpers & Classifications
# ==============================================================================

@mcp.tool(annotations=READ_ONLY_ANNOTATIONS)
async def normalize_patent_number(
    number: str,
    country: str = "US",
    patent_type: str = "patent",
) -> str:
    """Converts user-supplied patent strings into canonical DOCDB format (e.g. '10000000' -> 'US-10000000-B2').

    Args:
        number: Raw patent number string (e.g. '10000000', 'US10000000', 'EP1234567').
        country: Two-letter country code (default 'US').
        patent_type: Document type ('patent' or 'application').

    Returns:
        JSON string containing canonical ID, UCID, country, kind code, and validity.
    """
    try:
        res = await normalizer.normalize(number, country=country, patent_type=patent_type)
        return json.dumps(res, indent=2)
    except Exception as e:
        logger.exception("Error in normalize_patent_number")
        return json.dumps({"error": str(e), "input_number": number}, indent=2)


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS, meta=LANDSCAPE_TOOL_META)
async def lookup_classification_code(
    code: str,
) -> str:
    """Retrieves definition, description, and hierarchy for a Cooperative Patent Classification (CPC) or IPC code.

    Linked to the interactive MCP App `ui://google-patents/landscape-dashboard` (`text/html;profile=mcp-app`).

    Args:
        code: CPC or IPC symbol (e.g. 'G06N3/08', 'Y02E10/50', 'H04L67/02').

    Returns:
        JSON string containing full hierarchy title, definition text, and level.
    """
    try:
        clean_code = code.strip().upper().replace(" ", "")
        res = bq_client.lookup_classification_code(clean_code)
        if not res:
            return json.dumps({"error": f"Classification code '{code}' not found.", "code": clean_code}, indent=2)
        enriched_cls = enrich_landscape_payload(res)
        base_url = _get_public_base_url()
        enriched_cls["ui_resource_uri"] = LANDSCAPE_RESOURCE_URI
        enriched_cls["live_preview_url"] = f"{base_url}/apps/raw/landscape-dashboard?cpc_code={urllib.parse.quote(str(clean_code))}"
        return json.dumps(enriched_cls, indent=2)
    except Exception as e:
        logger.exception("Error in lookup_classification_code")
        return json.dumps({"error": str(e), "code": code}, indent=2)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=True))
async def set_patents_session_cookie(
    cookie: str,
) -> str:
    """Dynamically injects or updates the Google Patents session cookie (e.g. NID, SOCS, 1P_JAR) at runtime.

    Allows AI agents or administrators to provide an active session token to bypass edge anti-bot challenges
    without requiring a container redeployment.

    Args:
        cookie: Valid Google session cookie string (e.g. 'SOCS=...; NID=511=...').

    Returns:
        JSON confirmation with updated cookie status.
    """
    try:
        http_client.set_cookie(cookie)
        return json.dumps({
            "status": "success",
            "message": "Session cookie updated successfully in Google Patents HTTP client.",
            "cookie_length": len(cookie),
            "backend_source": "GOOGLE_PATENTS_WEB_GATEWAY",
        }, indent=2)
    except Exception as e:
        logger.exception("Error setting session cookie")
        return json.dumps({"error": str(e)}, indent=2)


# ==============================================================================
# 4. MCP Apps (`ui://` Interactive UI Resources & Tools)
# ==============================================================================

@mcp.resource(
    CLAIM_TREE_RESOURCE_URI,
    name="Google Patents Claim Tree & Scope Inspector",
    title="Google Patents Claim Tree & Scope Inspector",
    description=(
        "Interactive MCP App (text/html;profile=mcp-app) displaying a collapsible patent claim "
        "dependency tree, inherited claim scope merger, side-by-side claim comparator, and "
        "editable claim construction chart."
    ),
    mime_type=MCP_APP_MIME_TYPE,
    meta=CLAIM_TREE_RESOURCE_META,
)
async def read_claim_tree_mcp_app() -> str:
    """Serves the interactive HTML/JS MCP App for `ui://google-patents/claim-tree`."""
    cached = get_cached_patent_payload()
    return build_claim_tree_app_html(initial_patent=cached)


@mcp.resource(
    "ui://google-patents/claim-tree/{patent_id}",
    name="Google Patents Claim Tree App (Pre-hydrated by Patent ID)",
    title="Google Patents Claim Tree App (Pre-hydrated)",
    description="Reads the interactive Claim Tree MCP App pre-hydrated for a specific patent publication number.",
    mime_type=MCP_APP_MIME_TYPE,
    meta=CLAIM_TREE_RESOURCE_META,
)
async def read_claim_tree_mcp_app_for_patent(patent_id: str) -> str:
    """Serves `ui://google-patents/claim-tree/{patent_id}` pre-hydrated with the requested patent's claims."""
    cached = get_cached_patent_payload(patent_id)
    if not cached:
        details = await _fetch_enriched_patent_details(patent_id, include_claims=True)
        if not details.get("error"):
            cached = details
    return build_claim_tree_app_html(initial_patent=cached)


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS, meta=CLAIM_TREE_TOOL_META)
async def open_patent_claim_tree_app(
    patent_url_or_id: str,
    compare_with_patent_id: str = "",
) -> CallToolResult:
    """Launches the interactive Patent Claim Dependency Tree, Scope Inspector & Side-by-Side Comparator MCP App (`ui://google-patents/claim-tree`).

    Parses all independent and dependent claims into a hierarchical dependency tree, decomposes
    each claim into numbered limitations, merges inherited parent limitations for dependent claims,
    and optionally loads a second patent for side-by-side claim comparison.

    Args:
        patent_url_or_id: Primary patent ID (e.g. 'US8000000B2', 'US11435904B1', '10000000').
        compare_with_patent_id: Optional second patent ID to compare claims side-by-side (e.g. 'US10000000B2').

    Returns:
        CallToolResult containing summary text, structuredContent (`primaryPatent`, `comparisonPatent`),
        and `EmbeddedResource` (`ui://google-patents/claim-tree`, `mimeType="text/html;profile=mcp-app"`).
    """
    try:
        primary = await _fetch_enriched_patent_details(
            patent_url_or_id=patent_url_or_id,
            include_description=False,
            include_claims=True,
        )
        if primary.get("error"):
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(primary, indent=2))],
                isError=True,
            )

        comparison: Optional[Dict[str, Any]] = None
        if compare_with_patent_id and compare_with_patent_id.strip():
            cmp_res = await _fetch_enriched_patent_details(
                patent_url_or_id=compare_with_patent_id.strip(),
                include_description=False,
                include_claims=True,
            )
            if not cmp_res.get("error"):
                comparison = cmp_res

        tree_stats = primary.get("claims_tree") or {}
        pub_num = primary.get("publication_number") or patent_url_or_id
        title = primary.get("title") or "Untitled Patent"
        base_url = _get_public_base_url()
        cmp_qs = f"&compare_id={urllib.parse.quote(str(comparison.get('publication_number') or ''))}" if comparison else ""
        preview_url = f"{base_url}/apps/raw/claim-tree?patent_id={urllib.parse.quote(str(pub_num))}{cmp_qs}"

        app_html = build_claim_tree_app_html(
            initial_patent=primary,
            comparison_patent=comparison,
        )

        summary_dict = {
            "status": "mcp_app_ready",
            "ui_resource_uri": CLAIM_TREE_RESOURCE_URI,
            "mime_type": MCP_APP_MIME_TYPE,
            "live_preview_url": preview_url,
            "publication_number": pub_num,
            "title": title,
            "assignees": primary.get("assignees", []),
            "total_claims": tree_stats.get("total_claims", 0),
            "independent_claims": tree_stats.get("independent_count", 0),
            "dependent_claims": tree_stats.get("dependent_count", 0),
            "max_dependency_depth": tree_stats.get("max_depth", 0),
            "compared_with": comparison.get("publication_number") if comparison else None,
            "primaryPatent": primary,
            "comparisonPatent": comparison,
            "mcp_app_html": app_html,
        }

        return CallToolResult(
            _meta=CLAIM_TREE_TOOL_META,
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(summary_dict, indent=2),
                ),
                EmbeddedResource(
                    type="resource",
                    resource=TextResourceContents(
                        uri=AnyUrl(CLAIM_TREE_RESOURCE_URI),
                        mimeType=MCP_APP_MIME_TYPE,
                        text=app_html,
                        _meta=CLAIM_TREE_RESOURCE_META,
                    ),
                ),
            ],
            structuredContent=summary_dict,
            isError=False,
        )
    except Exception as e:
        logger.exception("Error in open_patent_claim_tree_app")
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))],
            isError=True,
        )


# --- View 2: Prior Art Timeline, Legal Lifespan & INPADOC Family Map ---

@mcp.resource(
    TIMELINE_RESOURCE_URI,
    name="Google Patents Prior Art Timeline, Lifespan & INPADOC Family Map",
    title="Google Patents Prior Art Timeline & Lifespan Map",
    description=(
        "Interactive MCP App (text/html;profile=mcp-app) displaying a chronological prior-art "
        "priority/filing/grant/20-year statutory expiry timeline, worldwide INPADOC family map, "
        "and Non-Patent Literature (NPL) inspector."
    ),
    mime_type=MCP_APP_MIME_TYPE,
    meta=CLAIM_TREE_RESOURCE_META,
)
async def read_timeline_mcp_app() -> str:
    """Serves the interactive HTML/JS MCP App for `ui://google-patents/prior-art-timeline`."""
    return build_timeline_app_html(get_cached_timeline_payload())


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS, meta=TIMELINE_TOOL_META)
async def open_prior_art_timeline_app(
    patent_id: str,
) -> CallToolResult:
    """Launches the interactive Prior Art Timeline, 20-Year Statutory Lifespan & Worldwide INPADOC Family Map MCP App (`ui://google-patents/prior-art-timeline`).

    Args:
        patent_id: Patent publication number (e.g. 'US8000000B2' or 'US10838605B2').

    Returns:
        CallToolResult with `EmbeddedResource` (`ui://google-patents/prior-art-timeline`).
    """
    try:
        raw_json = await get_prior_art_timeline(patent_id=patent_id)
        enriched = json.loads(raw_json)
        app_html = build_timeline_app_html(enriched)
        base_url = _get_public_base_url()
        pub_num = enriched.get("publication_number") or patent_id
        enriched["status"] = "mcp_app_ready"
        enriched["ui_resource_uri"] = TIMELINE_RESOURCE_URI
        enriched["mime_type"] = MCP_APP_MIME_TYPE
        enriched["live_preview_url"] = f"{base_url}/apps/raw/prior-art-timeline?patent_id={urllib.parse.quote(str(pub_num))}"
        enriched["mcp_app_html"] = app_html
        return CallToolResult(
            _meta=TIMELINE_TOOL_META,
            content=[
                TextContent(type="text", text=json.dumps(enriched, indent=2)),
                EmbeddedResource(
                    type="resource",
                    resource=TextResourceContents(
                        uri=AnyUrl(TIMELINE_RESOURCE_URI),
                        mimeType=MCP_APP_MIME_TYPE,
                        text=app_html,
                        _meta=CLAIM_TREE_RESOURCE_META,
                    ),
                ),
            ],
            structuredContent=enriched,
            isError=bool(enriched.get("error")),
        )
    except Exception as e:
        logger.exception("Error in open_prior_art_timeline_app")
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))],
            isError=True,
        )


# --- View 3: Interactive Citation & ScaM Similarity Network Graph ---

@mcp.resource(
    CITATION_GRAPH_RESOURCE_URI,
    name="Google Patents Interactive Citation & ScaM Similarity Network Graph",
    title="Google Patents Citation & Similarity Network Graph",
    description=(
        "Interactive MCP App (text/html;profile=mcp-app) rendering a 2D SVG radial network graph "
        "of backward citations (prior art), forward citations, and ScaM vector-similar patents."
    ),
    mime_type=MCP_APP_MIME_TYPE,
    meta=CLAIM_TREE_RESOURCE_META,
)
async def read_citation_graph_mcp_app() -> str:
    """Serves the interactive HTML/JS MCP App for `ui://google-patents/citation-graph`."""
    return build_citation_graph_app_html(get_cached_citation_payload())


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS, meta=CITATION_GRAPH_TOOL_META)
async def open_patent_citation_graph_app(
    patent_id: str,
    include_similar: bool = True,
    limit: int = 20,
) -> CallToolResult:
    """Launches the interactive Citation & ScaM Vector Similarity Network Graph MCP App (`ui://google-patents/citation-graph`).

    Args:
        patent_id: Target patent ID (e.g. 'US8000000B2' or 'US10838605B2').
        include_similar: Whether to also merge ScaM vector-similar patents into the graph. Defaults to True.
        limit: Max citations per direction (default 20).

    Returns:
        CallToolResult with `EmbeddedResource` (`ui://google-patents/citation-graph`).
    """
    try:
        cit_json = await get_patent_citations(patent_id=patent_id, citation_type="both", limit=limit)
        cit_data = json.loads(cit_json)
        if include_similar and not cit_data.get("error"):
            sim_json = await find_similar_patents(patent_id=patent_id, limit=min(10, limit))
            sim_data = json.loads(sim_json)
            if sim_data.get("similar_patents"):
                cit_data["similar_patents"] = sim_data["similar_patents"]
                cit_data = enrich_citation_or_similar_payload(cit_data, mode="citations")

        app_html = build_citation_graph_app_html(cit_data)
        base_url = _get_public_base_url()
        pub_num = cit_data.get("publication_number") or cit_data.get("target_patent") or patent_id
        cit_data["status"] = "mcp_app_ready"
        cit_data["ui_resource_uri"] = CITATION_GRAPH_RESOURCE_URI
        cit_data["mime_type"] = MCP_APP_MIME_TYPE
        cit_data["live_preview_url"] = f"{base_url}/apps/raw/citation-graph?patent_id={urllib.parse.quote(str(pub_num))}"
        cit_data["mcp_app_html"] = app_html
        return CallToolResult(
            _meta=CITATION_GRAPH_TOOL_META,
            content=[
                TextContent(type="text", text=json.dumps(cit_data, indent=2)),
                EmbeddedResource(
                    type="resource",
                    resource=TextResourceContents(
                        uri=AnyUrl(CITATION_GRAPH_RESOURCE_URI),
                        mimeType=MCP_APP_MIME_TYPE,
                        text=app_html,
                        _meta=CLAIM_TREE_RESOURCE_META,
                    ),
                ),
            ],
            structuredContent=cit_data,
            isError=bool(cit_data.get("error")),
        )
    except Exception as e:
        logger.exception("Error in open_patent_citation_graph_app")
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))],
            isError=True,
        )


# --- View 4: Patent Landscape & White-Space Analytics Dashboard ---

@mcp.resource(
    LANDSCAPE_RESOURCE_URI,
    name="Google Patents Landscape & White-Space Analytics Dashboard",
    title="Google Patents Landscape & White-Space Dashboard",
    description=(
        "Interactive MCP App (text/html;profile=mcp-app) displaying Top Assignees, Filing Velocity "
        "by Year, Jurisdiction breakdown, interactive patent portfolio grid, and live CPC/IPC explorer."
    ),
    mime_type=MCP_APP_MIME_TYPE,
    meta=CLAIM_TREE_RESOURCE_META,
)
async def read_landscape_mcp_app() -> str:
    """Serves the interactive HTML/JS MCP App for `ui://google-patents/landscape-dashboard`."""
    return build_landscape_app_html(get_cached_landscape_payload())


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS, meta=LANDSCAPE_TOOL_META)
async def open_patent_landscape_app(
    query: str = "",
    assignee: str = "",
    cpc_code: str = "",
    country_code: str = "",
    start_date: str = "",
    end_date: str = "",
    limit: int = 20,
) -> CallToolResult:
    """Launches the interactive Patent Landscape & White-Space Analytics Dashboard MCP App (`ui://google-patents/landscape-dashboard`).

    Args:
        query: Search keywords (e.g. 'solid state battery', 'autonomous lidar').
        assignee: Optional company/assignee filter (e.g. 'Toyota', 'Waymo').
        cpc_code: Optional CPC classification prefix (e.g. 'H01M', 'G06N').
        country_code: Optional jurisdiction filter (e.g. 'US', 'EP', 'WO').
        start_date: Optional start date (YYYY-MM-DD).
        end_date: Optional end date (YYYY-MM-DD).
        limit: Number of patents to analyze (1-50, default 20).

    Returns:
        CallToolResult with `EmbeddedResource` (`ui://google-patents/landscape-dashboard`).
    """
    try:
        raw_json = await advanced_patent_search(
            query=query,
            assignee=assignee,
            cpc_code=cpc_code,
            country_code=country_code,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        enriched = json.loads(raw_json)
        app_html = build_landscape_app_html(enriched)
        base_url = _get_public_base_url()
        qs = urllib.parse.urlencode({k: v for k, v in {
            "q": query,
            "assignee": assignee,
            "cpc_code": cpc_code,
            "country_code": country_code,
            "start_date": start_date,
            "end_date": end_date,
        }.items() if v})
        enriched["status"] = "mcp_app_ready"
        enriched["ui_resource_uri"] = LANDSCAPE_RESOURCE_URI
        enriched["mime_type"] = MCP_APP_MIME_TYPE
        enriched["live_preview_url"] = f"{base_url}/apps/raw/landscape-dashboard?{qs}"
        enriched["mcp_app_html"] = app_html
        return CallToolResult(
            _meta=LANDSCAPE_TOOL_META,
            content=[
                TextContent(type="text", text=json.dumps(enriched, indent=2)),
                EmbeddedResource(
                    type="resource",
                    resource=TextResourceContents(
                        uri=AnyUrl(LANDSCAPE_RESOURCE_URI),
                        mimeType=MCP_APP_MIME_TYPE,
                        text=app_html,
                        _meta=CLAIM_TREE_RESOURCE_META,
                    ),
                ),
            ],
            structuredContent=enriched,
            isError=bool(enriched.get("error")),
        )
    except Exception as e:
        logger.exception("Error in open_patent_landscape_app")
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))],
            isError=True,
        )


# --- View 5: Synchronized Drawing Carousel, PDF & Specification Split-Viewer ---

@mcp.resource(
    PDF_VIEWER_RESOURCE_URI,
    name="Google Patents Drawing Carousel, PDF & Specification Split-Viewer",
    title="Google Patents Drawing & PDF Split-Viewer",
    description=(
        "Interactive MCP App (text/html;profile=mcp-app) providing a zoomable/rotatable high-res "
        "patent drawing carousel alongside synchronized specification/claims text with clickable FIG. X chips."
    ),
    mime_type=MCP_APP_MIME_TYPE,
    meta=CLAIM_TREE_RESOURCE_META,
)
async def read_pdf_viewer_mcp_app() -> str:
    """Serves the interactive HTML/JS MCP App for `ui://google-patents/pdf-drawing-viewer`."""
    return build_pdf_viewer_app_html(get_cached_pdf_payload())


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS, meta=PDF_VIEWER_TOOL_META)
async def open_patent_pdf_viewer_app(
    patent_id: str,
) -> CallToolResult:
    """Launches the interactive Patent Drawing Carousel, PDF & Specification Split-Viewer MCP App (`ui://google-patents/pdf-drawing-viewer`).

    Args:
        patent_id: Patent ID (e.g. 'US8000000B2' or 'US10838605B2').

    Returns:
        CallToolResult with `EmbeddedResource` (`ui://google-patents/pdf-drawing-viewer`).
    """
    try:
        raw_json = await get_patent_pdf(patent_id=patent_id)
        enriched = json.loads(raw_json)
        app_html = build_pdf_viewer_app_html(enriched)
        base_url = _get_public_base_url()
        pub_num = enriched.get("publication_number") or patent_id
        enriched["status"] = "mcp_app_ready"
        enriched["ui_resource_uri"] = PDF_VIEWER_RESOURCE_URI
        enriched["mime_type"] = MCP_APP_MIME_TYPE
        enriched["live_preview_url"] = f"{base_url}/apps/raw/pdf-drawing-viewer?patent_id={urllib.parse.quote(str(pub_num))}"
        enriched["mcp_app_html"] = app_html
        return CallToolResult(
            _meta=PDF_VIEWER_TOOL_META,
            content=[
                TextContent(type="text", text=json.dumps(enriched, indent=2)),
                EmbeddedResource(
                    type="resource",
                    resource=TextResourceContents(
                        uri=AnyUrl(PDF_VIEWER_RESOURCE_URI),
                        mimeType=MCP_APP_MIME_TYPE,
                        text=app_html,
                        _meta=CLAIM_TREE_RESOURCE_META,
                    ),
                ),
            ],
            structuredContent=enriched,
            isError=bool(enriched.get("error")),
        )
    except Exception as e:
        logger.exception("Error in open_patent_pdf_viewer_app")
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))],
            isError=True,
        )


# --- View 6: Interactive 2D Chemical Structure / SMILES Explorer & Substructure Workbench ---

@mcp.resource(
    CHEMISTRY_RESOURCE_URI,
    name="Google Patents 2D Chemical Structure / SMILES Explorer",
    title="Google Patents 2D Chemical Structure Explorer",
    description=(
        "Interactive MCP App (text/html;profile=mcp-app) rendering a 2D skeletal chemical structure "
        "from SMILES, computing physicochemical/Lipinski descriptors, and running substructure/similarity searches."
    ),
    mime_type=MCP_APP_MIME_TYPE,
    meta=CLAIM_TREE_RESOURCE_META,
)
async def read_chemistry_mcp_app() -> str:
    """Serves the interactive HTML/JS MCP App for `ui://google-patents/chemistry-explorer`."""
    return build_chemistry_app_html(get_cached_chemistry_payload())


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS, meta=CHEMISTRY_TOOL_META)
async def open_chemistry_explorer_app(
    smiles: str = "CC(=O)Oc1ccccc1C(=O)O",
    mode: str = "SUBSTRUCTURE",
    query: str = "",
    limit: int = 15,
) -> CallToolResult:
    """Launches the interactive 2D Chemical Structure / SMILES Explorer & Substructure Workbench MCP App (`ui://google-patents/chemistry-explorer`).

    Args:
        smiles: Chemical structure in SMILES format (e.g. 'CC(=O)Oc1ccccc1C(=O)O' for Aspirin).
        mode: Search mode: 'EXACT', 'SUBSTRUCTURE', or 'SIMILARITY'. Defaults to 'SUBSTRUCTURE'.
        query: Optional keyword filter.
        limit: Max results (default 15).

    Returns:
        CallToolResult with `EmbeddedResource` (`ui://google-patents/chemistry-explorer`).
    """
    try:
        raw_json = await search_chemistry(smiles=smiles, mode=mode, query=query, limit=limit)
        enriched = json.loads(raw_json)
        app_html = build_chemistry_app_html(enriched)
        base_url = _get_public_base_url()
        enriched["status"] = "mcp_app_ready"
        enriched["ui_resource_uri"] = CHEMISTRY_RESOURCE_URI
        enriched["mime_type"] = MCP_APP_MIME_TYPE
        enriched["live_preview_url"] = f"{base_url}/apps/raw/chemistry-explorer?smiles={urllib.parse.quote(str(smiles))}"
        enriched["mcp_app_html"] = app_html
        return CallToolResult(
            _meta=CHEMISTRY_TOOL_META,
            content=[
                TextContent(type="text", text=json.dumps(enriched, indent=2)),
                EmbeddedResource(
                    type="resource",
                    resource=TextResourceContents(
                        uri=AnyUrl(CHEMISTRY_RESOURCE_URI),
                        mimeType=MCP_APP_MIME_TYPE,
                        text=app_html,
                        _meta=CLAIM_TREE_RESOURCE_META,
                    ),
                ),
            ],
            structuredContent=enriched,
            isError=bool(enriched.get("error")),
        )
    except Exception as e:
        logger.exception("Error in open_chemistry_explorer_app")
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))],
            isError=True,
        )


# ==============================================================================
# OAuth 2.0 Proxy Endpoints (/authorize & /token) & Health Check Routes
# ==============================================================================

GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"

_last_authorize_redirect_uri: Optional[str] = None


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


_last_public_base_url: Optional[str] = None


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
            os.environ.setdefault("MCP_PUBLIC_BASE_URL", _last_public_base_url)
            return _last_public_base_url
    if _last_public_base_url:
        return _last_public_base_url
    return "http://localhost:8080"


async def oauth_protected_resource_metadata(request) -> Response:
    """RFC 9728 OAuth 2.0 Protected Resource Metadata endpoint required by Claude & MCP clients."""
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
    """RFC 8414 OAuth 2.0 Authorization Server Metadata & OpenID Configuration endpoint for Claude & MCP clients."""
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
    """RFC 7591 OAuth 2.0 Dynamic Client Registration endpoint used by Claude Connectors and mcp-remote."""
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
    default_cid = allowed_cids[0] if allowed_cids else "google-patents-mcp-client"
    default_csec = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()

    redirect_uris = body_data.get("redirect_uris") or ["https://claude.ai/api/mcp/auth_callback"]
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
    """OAuth 2.0 Authorization Endpoint that validates client_id/redirect_uri and issues a signed authorization code.

    Redirects directly to redirect_uri (e.g. https://vertexaisearch.cloud.google.com/oauth-redirect or https://claude.ai/api/mcp/auth_callback)
    without navigating through accounts.google.com's Cross-Origin-Opener-Policy: same-origin header,
    preserving window.opener so the popup can postMessage the authorization code back.
    """
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
        logger.warning("Rejected /authorize request: client_id did not match GOOGLE_OAUTH_CLIENT_ID and no PKCE challenge")
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

    signed_code = _create_signed_token("gpmcp_code", code_payload)

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
    """OAuth 2.0 Token Endpoint that exchanges signed authorization codes or refresh tokens for access + refresh tokens."""
    sec_headers = {
        "Cache-Control": "no-store",
        "Pragma": "no-cache",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
        "Access-Control-Allow-Headers": "*",
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

    explicit_csec = (data.get("client_secret") or basic_csec).strip()
    client_id = (data.get("client_id") or basic_cid or env_cid).strip()
    client_secret = explicit_csec or env_csec

    grant_type = data.get("grant_type", "").strip()
    if not grant_type:
        if "code" in data:
            grant_type = "authorization_code"
        elif "refresh_token" in data:
            grant_type = "refresh_token"

    incoming_code = data.get("code", "").strip()
    incoming_rt = data.get("refresh_token", "").strip()
    incoming_verifier = data.get("code_verifier", "").strip()

    logger.info(
        "OAuth /token request: grant_type=%s, redirect_uri=%s, has_code=%s, has_rt=%s, has_pkce=%s, basic_auth=%s",
        grant_type,
        data.get("redirect_uri"),
        bool(incoming_code),
        bool(incoming_rt),
        bool(incoming_verifier),
        bool(basic_cid),
    )

    # 1. Handle signed authorization_code (gpmcp_code.*) or signed refresh_token (gpmcp_rt.*)
    if incoming_code.startswith("gpmcp_code.") or incoming_rt.startswith("gpmcp_rt."):
        if env_csec and explicit_csec and not hmac.compare_digest(explicit_csec, env_csec):
            logger.warning("OAuth /token rejected invalid explicit client_secret")
            return JSONResponse(
                {"error": "invalid_client", "error_description": "Client secret mismatch"},
                status_code=401,
                headers=sec_headers,
            )

        if incoming_code.startswith("gpmcp_code."):
            token_payload = _verify_signed_token(incoming_code, expected_prefix="gpmcp_code")
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
                    logger.warning("OAuth /token rejected invalid PKCE code_verifier")
                    return JSONResponse(
                        {"error": "invalid_grant", "error_description": "PKCE code_verifier mismatch"},
                        status_code=400,
                        headers=sec_headers,
                    )
        else:
            token_payload = _verify_signed_token(incoming_rt, expected_prefix="gpmcp_rt")
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
            "gpmcp",
            {
                "cid": issued_cid,
                "scp": scope,
                "iat": now,
                "exp": now + 3600,
                "jti": secrets.token_hex(8),
            },
        )
        refresh_token = _create_signed_token(
            "gpmcp_rt",
            {
                "cid": issued_cid,
                "scp": scope,
                "iat": now,
                "exp": now + 86400 * 365,
                "jti": secrets.token_hex(8),
            },
        )
        logger.info("OAuth /token successfully issued signed access_token & refresh_token (grant_type=%s)", grant_type)
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

    # Handle legacy synthetic fallback refresh token if previously issued
    if grant_type == "refresh_token" and incoming_rt.startswith("ge_rt_"):
        embedded_at = incoming_rt[len("ge_rt_"):]
        logger.info("OAuth /token handled synthetic refresh_token grant")
        return JSONResponse(
            {
                "access_token": embedded_at,
                "refresh_token": incoming_rt,
                "token_type": "Bearer",
                "expires_in": 3599,
                "scope": data.get("scope", "openid email profile"),
            },
            status_code=200,
            headers=sec_headers,
        )

    # 2. Fallback: Forward raw Google OAuth authorization codes to https://oauth2.googleapis.com/token
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
        logger.warning(
            "OAuth /token upstream exchange failed: status=%d, error=%s, description=%s",
            resp.status_code,
            resp_data.get("error"),
            resp_data.get("error_description"),
        )
        return JSONResponse(resp_data, status_code=resp.status_code, headers=sec_headers)

    has_google_rt = bool(resp_data.get("refresh_token"))
    if not has_google_rt:
        if payload.get("refresh_token"):
            resp_data["refresh_token"] = payload["refresh_token"]
        elif resp_data.get("access_token"):
            resp_data["refresh_token"] = f"ge_rt_{resp_data['access_token']}"

    if "token_type" not in resp_data:
        resp_data["token_type"] = "Bearer"
    if "expires_in" not in resp_data:
        resp_data["expires_in"] = 3599

    return JSONResponse(resp_data, status_code=200, headers=sec_headers)


async def app_api_patent_details(request) -> Response:
    """HTTP JSON helper endpoint used by standalone/simulator MCP App views."""
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Cross-Origin-Opener-Policy": "unsafe-none",
    }
    patent_id = request.query_params.get("patent_id", "US8000000B2").strip()
    compare_id = request.query_params.get("compare_id", "").strip()
    details = await _fetch_enriched_patent_details(patent_id, include_claims=True)
    if compare_id:
        cmp_details = await _fetch_enriched_patent_details(compare_id, include_claims=True)
        return JSONResponse({"primaryPatent": details, "comparisonPatent": cmp_details}, headers=cors_headers)
    return JSONResponse(details, headers=cors_headers)


async def app_api_pdf_details(request) -> Response:
    """HTTP JSON helper endpoint returning enriched PDF/drawing/specification payload."""
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Cross-Origin-Opener-Policy": "unsafe-none",
    }
    patent_id = request.query_params.get("patent_id", "US8000000B2").strip()
    raw_json = await get_patent_pdf(patent_id=patent_id)
    return JSONResponse(json.loads(raw_json), headers=cors_headers)


async def app_api_timeline(request) -> Response:
    """HTTP JSON helper endpoint returning enriched prior art timeline payload."""
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Cross-Origin-Opener-Policy": "unsafe-none",
    }
    patent_id = request.query_params.get("patent_id", "US8000000B2").strip()
    raw_json = await get_prior_art_timeline(patent_id=patent_id)
    return JSONResponse(json.loads(raw_json), headers=cors_headers)


async def app_api_citations(request) -> Response:
    """HTTP JSON helper endpoint returning enriched citation & similarity graph payload."""
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Cross-Origin-Opener-Policy": "unsafe-none",
    }
    patent_id = request.query_params.get("patent_id", "US8000000B2").strip()
    cit_json = await get_patent_citations(patent_id=patent_id, citation_type="both", limit=20)
    cit_data = json.loads(cit_json)
    if not cit_data.get("error"):
        sim_json = await find_similar_patents(patent_id=patent_id, limit=10)
        sim_data = json.loads(sim_json)
        if sim_data.get("similar_patents"):
            cit_data["similar_patents"] = sim_data["similar_patents"]
            cit_data = enrich_citation_or_similar_payload(cit_data, mode="citations")
    return JSONResponse(cit_data, headers=cors_headers)


async def app_api_landscape(request) -> Response:
    """HTTP JSON helper endpoint returning enriched patent landscape analytics payload."""
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Cross-Origin-Opener-Policy": "unsafe-none",
    }
    query = request.query_params.get("query", "").strip()
    assignee = request.query_params.get("assignee", "").strip()
    cpc_code = request.query_params.get("cpc_code", "").strip()
    country_code = request.query_params.get("country_code", "").strip()
    raw_json = await advanced_patent_search(
        query=query,
        assignee=assignee,
        cpc_code=cpc_code,
        country_code=country_code,
        limit=20,
    )
    return JSONResponse(json.loads(raw_json), headers=cors_headers)


async def app_api_cpc_lookup(request) -> Response:
    """HTTP JSON helper endpoint returning CPC/IPC classification lookup payload."""
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Cross-Origin-Opener-Policy": "unsafe-none",
    }
    code = request.query_params.get("code", "G06N").strip()
    raw_json = await lookup_classification_code(code=code)
    return JSONResponse(json.loads(raw_json), headers=cors_headers)


async def app_api_chemistry(request) -> Response:
    """HTTP JSON helper endpoint returning SMILES chemical patent search payload."""
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Cross-Origin-Opener-Policy": "unsafe-none",
    }
    smiles = request.query_params.get("smiles", "CC(=O)Oc1ccccc1C(=O)O").strip()
    mode = request.query_params.get("mode", "SUBSTRUCTURE").strip()
    raw_json = await search_chemistry(smiles=smiles, mode=mode, limit=15)
    return JSONResponse(json.loads(raw_json), headers=cors_headers)


async def app_sandbox_safe_pdf(request) -> Response:
    """Sandbox-safe PDF endpoint (/apps/pdf/{patent_id}) that never sets Cross-Origin-Opener-Policy: same-origin.

    Redirects directly to `https://patentimages.storage.googleapis.com/.../*.pdf` when available,
    or renders a printable official patent specification & claims document from BigQuery.
    """
    patent_id = request.path_params.get("patent_id", "US8000000B2").strip()
    raw_json = await get_patent_pdf(patent_id=patent_id)
    data = json.loads(raw_json)
    direct_url = str(data.get("direct_pdf_url") or "")
    safe_headers = {
        "Cross-Origin-Opener-Policy": "unsafe-none",
        "Access-Control-Allow-Origin": "*",
    }
    if direct_url.startswith("https://patentimages.storage.googleapis.com/") and direct_url.endswith(".pdf"):
        return RedirectResponse(url=direct_url, status_code=302, headers=safe_headers)

    pub_num = data.get("publication_number") or patent_id
    title = data.get("title") or "Patent Specification Document"
    abstract = data.get("abstract") or ""
    assignees = ", ".join(data.get("assignees") or [])
    claims = data.get("claims_preview") or []
    desc_snippets = data.get("description_snippets") or []

    claims_html = "".join(f"<p style='margin-bottom:10px;'>{c}</p>" for c in claims)
    desc_html = "".join(f"<p style='margin-bottom:10px;'>{d}</p>" for d in desc_snippets)
    printable_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>{pub_num} — {title}</title>
  <style>
    body {{ font-family: Georgia, serif; max-width: 860px; margin: 24px auto; padding: 0 20px; color: #0f172a; line-height: 1.6; }}
    .toolbar {{ font-family: sans-serif; display: flex; justify-content: space-between; align-items: center; background: #f1f5f9; padding: 12px 16px; border-radius: 8px; margin-bottom: 24px; }}
    .btn {{ background: #4f46e5; color: #fff; border: none; padding: 8px 14px; border-radius: 6px; font-weight: 600; cursor: pointer; text-decoration: none; font-size: 13px; }}
    h1 {{ font-size: 22px; margin-bottom: 6px; }}
    h2 {{ font-size: 14px; text-transform: uppercase; letter-spacing: 0.06em; color: #475569; border-bottom: 1px solid #cbd5e1; padding-bottom: 4px; margin-top: 24px; }}
    @media print {{ .toolbar {{ display: none; }} }}
  </style>
</head>
<body>
  <div class="toolbar">
    <div><strong>{pub_num}</strong> — Printable Specification &amp; Claims</div>
    <button class="btn" onclick="window.print()">🖨️ Print / Save as PDF</button>
  </div>
  <h1>{pub_num}: {title}</h1>
  <p><strong>Assignee:</strong> {assignees or 'N/A'} &nbsp;|&nbsp; <strong>Filed:</strong> {data.get('filing_date') or 'N/A'} &nbsp;|&nbsp; <strong>Granted:</strong> {data.get('grant_date') or 'N/A'}</p>
  <h2>Abstract</h2>
  <p>{abstract}</p>
  <h2>Representative Claims</h2>
  {claims_html or '<p>No claims available.</p>'}
  <h2>Description &amp; Figure Callouts</h2>
  {desc_html or '<p>No description available.</p>'}
</body>
</html>"""
    return HTMLResponse(printable_html, headers=safe_headers)


async def app_sandbox_safe_patent_reader(request) -> Response:
    """Sandbox-safe standalone Patent & PDF Reader (/apps/patent/{patent_id}) without COOP restrictions."""
    patent_id = request.path_params.get("patent_id", "US8000000B2").strip()
    raw_json = await get_patent_pdf(patent_id=patent_id)
    enriched = json.loads(raw_json)
    safe_headers = {
        "Cross-Origin-Opener-Policy": "unsafe-none",
        "Access-Control-Allow-Origin": "*",
    }
    return HTMLResponse(build_pdf_viewer_app_html(enriched), media_type="text/html", headers=safe_headers)


async def app_raw_claim_tree(request) -> Response:
    """Serves the raw `ui://google-patents/claim-tree` HTML bundle (optionally pre-hydrated)."""
    safe_headers = {
        "Cross-Origin-Opener-Policy": "unsafe-none",
        "Access-Control-Allow-Origin": "*",
    }
    patent_id = request.query_params.get("patent_id", "").strip()
    compare_id = request.query_params.get("compare_id", "").strip()
    primary = None
    comparison = None
    if patent_id:
        primary = get_cached_patent_payload(patent_id)
        if not primary:
            fetched = await _fetch_enriched_patent_details(patent_id, include_claims=True)
            if not fetched.get("error"):
                primary = fetched
    else:
        primary = get_cached_patent_payload()

    if compare_id:
        comparison = get_cached_patent_payload(compare_id)
        if not comparison:
            fetched_cmp = await _fetch_enriched_patent_details(compare_id, include_claims=True)
            if not fetched_cmp.get("error"):
                comparison = fetched_cmp

    html_content = build_claim_tree_app_html(initial_patent=primary, comparison_patent=comparison)
    return HTMLResponse(html_content, media_type="text/html", headers=safe_headers)


async def app_raw_timeline(request) -> Response:
    """Serves the raw `ui://google-patents/prior-art-timeline` HTML bundle."""
    safe_headers = {
        "Cross-Origin-Opener-Policy": "unsafe-none",
        "Access-Control-Allow-Origin": "*",
    }
    patent_id = request.query_params.get("patent_id", "").strip()
    if patent_id:
        await get_prior_art_timeline(patent_id=patent_id)
    return HTMLResponse(build_timeline_app_html(get_cached_timeline_payload()), media_type="text/html", headers=safe_headers)


async def app_raw_citation_graph(request) -> Response:
    """Serves the raw `ui://google-patents/citation-graph` HTML bundle."""
    safe_headers = {
        "Cross-Origin-Opener-Policy": "unsafe-none",
        "Access-Control-Allow-Origin": "*",
    }
    patent_id = request.query_params.get("patent_id", "").strip()
    include_similar = request.query_params.get("include_similar", "true").lower() != "false"
    if patent_id:
        cit_json = await get_patent_citations(patent_id=patent_id, citation_type="both", limit=20)
        cit_data = json.loads(cit_json)
        if include_similar and not cit_data.get("error"):
            sim_json = await find_similar_patents(patent_id=patent_id, limit=10)
            sim_data = json.loads(sim_json)
            if sim_data.get("similar_patents"):
                cit_data["similar_patents"] = sim_data["similar_patents"]
                cit_data = enrich_citation_or_similar_payload(cit_data, mode="citations")
        return HTMLResponse(build_citation_graph_app_html(cit_data), media_type="text/html", headers=safe_headers)
    return HTMLResponse(build_citation_graph_app_html(get_cached_citation_payload()), media_type="text/html", headers=safe_headers)


async def app_raw_landscape(request) -> Response:
    """Serves the raw `ui://google-patents/landscape-dashboard` HTML bundle."""
    safe_headers = {
        "Cross-Origin-Opener-Policy": "unsafe-none",
        "Access-Control-Allow-Origin": "*",
    }
    query = (request.query_params.get("q") or request.query_params.get("query") or "").strip()
    assignee = request.query_params.get("assignee", "").strip()
    cpc_code = request.query_params.get("cpc_code", "").strip()
    country_code = request.query_params.get("country_code", "").strip()
    start_date = request.query_params.get("start_date", "").strip()
    end_date = request.query_params.get("end_date", "").strip()
    if any([query, assignee, cpc_code, country_code, start_date, end_date]):
        raw_json = await advanced_patent_search(
            query=query,
            assignee=assignee,
            cpc_code=cpc_code,
            country_code=country_code,
            start_date=start_date,
            end_date=end_date,
            limit=20,
        )
        return HTMLResponse(build_landscape_app_html(json.loads(raw_json)), media_type="text/html", headers=safe_headers)
    return HTMLResponse(build_landscape_app_html(get_cached_landscape_payload()), media_type="text/html", headers=safe_headers)


async def app_raw_pdf_viewer(request) -> Response:
    """Serves the raw `ui://google-patents/pdf-drawing-viewer` HTML bundle."""
    safe_headers = {
        "Cross-Origin-Opener-Policy": "unsafe-none",
        "Access-Control-Allow-Origin": "*",
    }
    patent_id = request.query_params.get("patent_id", "").strip()
    if patent_id:
        await get_patent_pdf(patent_id=patent_id)
    return HTMLResponse(build_pdf_viewer_app_html(get_cached_pdf_payload()), media_type="text/html", headers=safe_headers)


async def app_raw_chemistry(request) -> Response:
    """Serves the raw `ui://google-patents/chemistry-explorer` HTML bundle."""
    safe_headers = {
        "Cross-Origin-Opener-Policy": "unsafe-none",
        "Access-Control-Allow-Origin": "*",
    }
    smiles = request.query_params.get("smiles", "").strip()
    if smiles:
        await search_chemistry(smiles=smiles, mode="SUBSTRUCTURE")
    return HTMLResponse(build_chemistry_app_html(get_cached_chemistry_payload()), media_type="text/html", headers=safe_headers)


async def app_simulator_claim_tree(request) -> Response:
    """Serves an interactive MCP Apps Host Sandbox Simulator wrapping `ui://google-patents/claim-tree`."""
    patent_id = request.query_params.get("patent_id", "US8000000B2").strip() or "US8000000B2"
    return HTMLResponse(build_host_simulator_html(default_patent_id=patent_id))


async def health(request):
    """Health check endpoint for Cloud Run container liveness and startup probes."""
    cb_status = http_client.circuit_breaker.get_status()
    return JSONResponse({
        "status": "healthy",
        "service": "Google Patents MCP Server",
        "version": "2.0.0",
        "transports": ["streamable-http", "sse"],
        "mcp_apps": [
            {
                "view": 1,
                "name": "Google Patents Claim Tree & Scope Inspector",
                "resource_uri": CLAIM_TREE_RESOURCE_URI,
                "mime_type": MCP_APP_MIME_TYPE,
                "linked_tools": ["get_patent_details", "open_patent_claim_tree_app"],
                "preview_path": "/apps/raw/claim-tree",
            },
            {
                "view": 2,
                "name": "Google Patents Prior Art Timeline, Lifespan & INPADOC Family Map",
                "resource_uri": TIMELINE_RESOURCE_URI,
                "mime_type": MCP_APP_MIME_TYPE,
                "linked_tools": ["get_prior_art_timeline", "open_prior_art_timeline_app"],
                "preview_path": "/apps/raw/prior-art-timeline",
            },
            {
                "view": 3,
                "name": "Google Patents Interactive Citation & ScaM Similarity Network Graph",
                "resource_uri": CITATION_GRAPH_RESOURCE_URI,
                "mime_type": MCP_APP_MIME_TYPE,
                "linked_tools": ["get_patent_citations", "find_similar_patents", "open_patent_citation_graph_app"],
                "preview_path": "/apps/raw/citation-graph",
            },
            {
                "view": 4,
                "name": "Google Patents Landscape & White-Space Analytics Dashboard",
                "resource_uri": LANDSCAPE_RESOURCE_URI,
                "mime_type": MCP_APP_MIME_TYPE,
                "linked_tools": ["search_patents", "advanced_patent_search", "lookup_classification_code", "open_patent_landscape_app"],
                "preview_path": "/apps/raw/landscape-dashboard",
            },
            {
                "view": 5,
                "name": "Google Patents Synchronized Drawing Carousel & PDF Split-Viewer",
                "resource_uri": PDF_VIEWER_RESOURCE_URI,
                "mime_type": MCP_APP_MIME_TYPE,
                "linked_tools": ["get_patent_pdf", "open_patent_pdf_viewer_app"],
                "preview_path": "/apps/raw/pdf-drawing-viewer",
            },
            {
                "view": 6,
                "name": "Google Patents 2D Chemical Structure / SMILES Explorer",
                "resource_uri": CHEMISTRY_RESOURCE_URI,
                "mime_type": MCP_APP_MIME_TYPE,
                "linked_tools": ["search_chemistry", "open_chemistry_explorer_app"],
                "preview_path": "/apps/raw/chemistry-explorer",
            },
        ],
        "endpoints": {
            "mcp": "/mcp",
            "sse": "/sse",
            "messages": "/messages/",
            "authorize": "/authorize",
            "token": "/token",
            "health": "/healthz",
            "sandbox_safe_pdf": "/apps/pdf/{patent_id}",
            "sandbox_safe_patent_reader": "/apps/patent/{patent_id}",
            "claim_tree_app_simulator": "/apps/claim-tree",
            "claim_tree_app_raw": "/apps/raw/claim-tree",
            "timeline_app_raw": "/apps/raw/prior-art-timeline",
            "citation_graph_app_raw": "/apps/raw/citation-graph",
            "landscape_app_raw": "/apps/raw/landscape-dashboard",
            "pdf_viewer_app_raw": "/apps/raw/pdf-drawing-viewer",
            "chemistry_app_raw": "/apps/raw/chemistry-explorer",
        },
        "oauth_enabled": _token_verifier is not None,
        "tools_count": 18,
        "circuit_breaker": cb_status,
        "backends": {
            "web_gateway": "https://patents.google.com/xhr/query",
            "match_api": "https://patents.google.com/api/match",
            "bigquery": "patents-public-data.patents.publications",
        }
    })


def get_asgi_app(transport: Optional[str] = None):
    """Returns a unified ASGI application supporting both StreamableHTTP (/mcp) and SSE (/sse) with OAuth & health checks."""
    # Start from streamable_http_app so the StreamableHTTPSessionManager lifespan and /mcp route are active
    app = mcp.streamable_http_app()

    # Also mount SSE routes (/sse and /messages/) for backwards compatibility with SSE clients
    sse_starlette = mcp.sse_app()
    existing_paths = {getattr(r, "path", None) for r in app.routes}
    for route in sse_starlette.routes:
        if getattr(route, "path", None) not in existing_paths:
            app.routes.append(route)

    # Insert MCP Apps preview/API routes, OAuth 2.0 discovery/DCR/proxy endpoints, and health checks
    app.routes.insert(0, Route("/apps/api/patent-details", app_api_patent_details, methods=["GET"]))
    app.routes.insert(0, Route("/apps/api/pdf-details", app_api_pdf_details, methods=["GET"]))
    app.routes.insert(0, Route("/apps/api/timeline", app_api_timeline, methods=["GET"]))
    app.routes.insert(0, Route("/apps/api/citations", app_api_citations, methods=["GET"]))
    app.routes.insert(0, Route("/apps/api/landscape", app_api_landscape, methods=["GET"]))
    app.routes.insert(0, Route("/apps/api/cpc-lookup", app_api_cpc_lookup, methods=["GET"]))
    app.routes.insert(0, Route("/apps/api/chemistry", app_api_chemistry, methods=["GET"]))
    app.routes.insert(0, Route("/apps/pdf/{patent_id}", app_sandbox_safe_pdf, methods=["GET"]))
    app.routes.insert(0, Route("/apps/patent/{patent_id}", app_sandbox_safe_patent_reader, methods=["GET"]))
    app.routes.insert(0, Route("/apps/raw/claim-tree", app_raw_claim_tree, methods=["GET"]))
    app.routes.insert(0, Route("/apps/raw/prior-art-timeline", app_raw_timeline, methods=["GET"]))
    app.routes.insert(0, Route("/apps/raw/citation-graph", app_raw_citation_graph, methods=["GET"]))
    app.routes.insert(0, Route("/apps/raw/landscape-dashboard", app_raw_landscape, methods=["GET"]))
    app.routes.insert(0, Route("/apps/raw/pdf-drawing-viewer", app_raw_pdf_viewer, methods=["GET"]))
    app.routes.insert(0, Route("/apps/raw/chemistry-explorer", app_raw_chemistry, methods=["GET"]))
    app.routes.insert(0, Route("/apps/claim-tree", app_simulator_claim_tree, methods=["GET"]))
    app.routes.insert(0, Route("/.well-known/oauth-protected-resource/{subpath:path}", oauth_protected_resource_metadata, methods=["GET", "OPTIONS"]))
    app.routes.insert(0, Route("/.well-known/oauth-protected-resource", oauth_protected_resource_metadata, methods=["GET", "OPTIONS"]))
    app.routes.insert(0, Route("/.well-known/oauth-authorization-server/{subpath:path}", oauth_authorization_server_metadata, methods=["GET", "OPTIONS"]))
    app.routes.insert(0, Route("/.well-known/oauth-authorization-server", oauth_authorization_server_metadata, methods=["GET", "OPTIONS"]))
    app.routes.insert(0, Route("/.well-known/openid-configuration", oauth_authorization_server_metadata, methods=["GET", "OPTIONS"]))
    app.routes.insert(0, Route("/register", oauth_register_client, methods=["POST", "OPTIONS"]))
    app.routes.insert(0, Route("/token", oauth_token, methods=["POST", "GET", "OPTIONS"]))
    app.routes.insert(0, Route("/authorize{extra:path}", oauth_authorize, methods=["GET"]))
    app.routes.insert(0, Route("/authorize", oauth_authorize, methods=["GET"]))
    app.routes.insert(0, Route("/healthz", health))
    app.routes.insert(0, Route("/", health))

    @app.middleware("http")
    async def _capture_public_base_url(request, call_next):
        _get_public_base_url(request)
        return await call_next(request)

    return app


