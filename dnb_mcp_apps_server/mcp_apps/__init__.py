"""Interactive MCP Apps (`ui://dnb/*`, `text/html;profile=mcp-app`) for Dun & Bradstreet."""

from .brand_theme import (
    DEFAULT_PUBLIC_API_BASE_URL,
    DNB_BRAND_THEME,
    LOCK_DESIGN_THEME,
    MCP_APP_MIME_TYPE,
)
from .company_360_app import (
    COMPANY_360_APP_RESOURCE_META,
    COMPANY_360_APP_TOOL_META,
    COMPANY_360_RESOURCE_URI,
    build_company_360_html,
    get_cached_company_360_payload,
    set_cached_company_360_payload,
)
from .entity_matcher_app import (
    ENTITY_MATCHER_APP_RESOURCE_META,
    ENTITY_MATCHER_APP_TOOL_META,
    ENTITY_MATCHER_RESOURCE_URI,
    build_entity_matcher_html,
    get_cached_matcher_payload,
    set_cached_matcher_payload,
)
from .family_tree_app import (
    FAMILY_TREE_APP_RESOURCE_META,
    FAMILY_TREE_APP_TOOL_META,
    FAMILY_TREE_RESOURCE_URI,
    build_family_tree_html,
    get_cached_family_tree_payload,
    set_cached_family_tree_payload,
)
from .supplier_risk_app import (
    SUPPLIER_RISK_APP_RESOURCE_META,
    SUPPLIER_RISK_APP_TOOL_META,
    SUPPLIER_RISK_RESOURCE_URI,
    build_supplier_risk_html,
    get_cached_supplier_risk_payload,
    set_cached_supplier_risk_payload,
)

__all__ = [
    "DNB_BRAND_THEME",
    "MCP_APP_MIME_TYPE",
    "LOCK_DESIGN_THEME",
    "DEFAULT_PUBLIC_API_BASE_URL",
    "ENTITY_MATCHER_RESOURCE_URI",
    "ENTITY_MATCHER_APP_TOOL_META",
    "ENTITY_MATCHER_APP_RESOURCE_META",
    "set_cached_matcher_payload",
    "get_cached_matcher_payload",
    "build_entity_matcher_html",
    "COMPANY_360_RESOURCE_URI",
    "COMPANY_360_APP_TOOL_META",
    "COMPANY_360_APP_RESOURCE_META",
    "set_cached_company_360_payload",
    "get_cached_company_360_payload",
    "build_company_360_html",
    "FAMILY_TREE_RESOURCE_URI",
    "FAMILY_TREE_APP_TOOL_META",
    "FAMILY_TREE_APP_RESOURCE_META",
    "set_cached_family_tree_payload",
    "get_cached_family_tree_payload",
    "build_family_tree_html",
    "SUPPLIER_RISK_RESOURCE_URI",
    "SUPPLIER_RISK_APP_TOOL_META",
    "SUPPLIER_RISK_APP_RESOURCE_META",
    "set_cached_supplier_risk_payload",
    "get_cached_supplier_risk_payload",
    "build_supplier_risk_html",
]
