"""MCP Apps (ui://) module for Google Patents MCP Server (All 6 Views)."""

from .chemistry_app import (
    CHEMISTRY_RESOURCE_URI,
    CHEMISTRY_TOOL_META,
    build_chemistry_app_html,
    enrich_chemistry_payload,
    get_cached_chemistry_payload,
    set_cached_chemistry_payload,
)
from .citation_graph_app import (
    CITATION_GRAPH_RESOURCE_URI,
    CITATION_GRAPH_TOOL_META,
    build_citation_graph_app_html,
    enrich_citation_or_similar_payload,
    get_cached_citation_payload,
    set_cached_citation_payload,
)
from .claim_tree_app import (
    CLAIM_TREE_RESOURCE_META,
    CLAIM_TREE_RESOURCE_URI,
    CLAIM_TREE_TOOL_META,
    MCP_APP_MIME_TYPE,
    build_claim_tree_app_html,
    build_host_simulator_html,
    enrich_patent_with_claim_tree,
    get_cached_patent_payload,
    parse_claim_dependency_tree,
    set_cached_patent_payload,
)
from .landscape_app import (
    LANDSCAPE_RESOURCE_URI,
    LANDSCAPE_TOOL_META,
    build_landscape_app_html,
    enrich_landscape_payload,
    get_cached_landscape_payload,
    set_cached_landscape_payload,
)
from .pdf_viewer_app import (
    PDF_VIEWER_RESOURCE_URI,
    PDF_VIEWER_TOOL_META,
    build_pdf_viewer_app_html,
    enrich_pdf_payload,
    get_cached_pdf_payload,
    set_cached_pdf_payload,
)
from .timeline_app import (
    TIMELINE_RESOURCE_URI,
    TIMELINE_TOOL_META,
    build_timeline_app_html,
    enrich_timeline_payload,
    get_cached_timeline_payload,
    set_cached_timeline_payload,
)

__all__ = [
    # Common
    "MCP_APP_MIME_TYPE",
    # View 1: Claim Tree & Comparator
    "CLAIM_TREE_RESOURCE_META",
    "CLAIM_TREE_RESOURCE_URI",
    "CLAIM_TREE_TOOL_META",
    "build_claim_tree_app_html",
    "build_host_simulator_html",
    "enrich_patent_with_claim_tree",
    "get_cached_patent_payload",
    "parse_claim_dependency_tree",
    "set_cached_patent_payload",
    # View 2: Prior Art Timeline & Lifespan
    "TIMELINE_RESOURCE_URI",
    "TIMELINE_TOOL_META",
    "build_timeline_app_html",
    "enrich_timeline_payload",
    "get_cached_timeline_payload",
    "set_cached_timeline_payload",
    # View 3: Citation & ScaM Similarity Graph
    "CITATION_GRAPH_RESOURCE_URI",
    "CITATION_GRAPH_TOOL_META",
    "build_citation_graph_app_html",
    "enrich_citation_or_similar_payload",
    "get_cached_citation_payload",
    "set_cached_citation_payload",
    # View 4: Landscape & White-Space Dashboard
    "LANDSCAPE_RESOURCE_URI",
    "LANDSCAPE_TOOL_META",
    "build_landscape_app_html",
    "enrich_landscape_payload",
    "get_cached_landscape_payload",
    "set_cached_landscape_payload",
    # View 5: PDF & Drawing Carousel Split-Viewer
    "PDF_VIEWER_RESOURCE_URI",
    "PDF_VIEWER_TOOL_META",
    "build_pdf_viewer_app_html",
    "enrich_pdf_payload",
    "get_cached_pdf_payload",
    "set_cached_pdf_payload",
    # View 6: 2D Chemical Structure & SMILES Explorer
    "CHEMISTRY_RESOURCE_URI",
    "CHEMISTRY_TOOL_META",
    "build_chemistry_app_html",
    "enrich_chemistry_payload",
    "get_cached_chemistry_payload",
    "set_cached_chemistry_payload",
]
