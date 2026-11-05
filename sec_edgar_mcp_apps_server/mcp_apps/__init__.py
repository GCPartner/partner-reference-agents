"""Interactive MCP Apps (`ui://sec-edgar/*`, `text/html;profile=mcp-app`) for SEC EDGAR."""

from .brand_theme import APEX_BRAND_THEME, MCP_APP_MIME_TYPE
from .financial_dossier_app import (
    DOSSIER_APP_RESOURCE_META,
    DOSSIER_APP_TOOL_META,
    DOSSIER_RESOURCE_URI,
    build_dossier_workbench_html,
    enrich_dossier_workbench_payload,
    get_cached_dossier_payload,
    set_cached_dossier_payload,
)
from .peer_comparator_app import (
    PEER_APP_RESOURCE_META,
    PEER_APP_TOOL_META,
    PEER_RESOURCE_URI,
    build_peer_comparator_html,
    enrich_peer_comparator_payload,
    get_cached_peer_payload,
    set_cached_peer_payload,
)

__all__ = [
    "APEX_BRAND_THEME",
    "MCP_APP_MIME_TYPE",
    "DOSSIER_RESOURCE_URI",
    "DOSSIER_APP_TOOL_META",
    "DOSSIER_APP_RESOURCE_META",
    "set_cached_dossier_payload",
    "get_cached_dossier_payload",
    "enrich_dossier_workbench_payload",
    "build_dossier_workbench_html",
    "PEER_RESOURCE_URI",
    "PEER_APP_TOOL_META",
    "PEER_APP_RESOURCE_META",
    "set_cached_peer_payload",
    "get_cached_peer_payload",
    "enrich_peer_comparator_payload",
    "build_peer_comparator_html",
]
