"""Comprehensive test suite for Google Patents MCP Server (100% Feature Parity)."""

import asyncio
import json
import os
import sys

# Ensure package is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from google_patents_mcp_server.server import mcp


async def run_tests():
    print("=" * 75)
    print("  Starting Google Patents MCP Server 100% Parity Verification Suite  ")
    print("  Backends: Google Patents Web Gateway & BigQuery Public Datasets")
    print("=" * 75)

    # 1. Verify All Tools Registered
    print("\n[1/10] Verifying MCP Tool Registration...")
    tools = await mcp.list_tools()
    tool_names = [t.name for t in tools]
    print(f"Registered Tools ({len(tool_names)}): {tool_names}")
    expected_tools = [
        "parse_query",
        "search_patents",
        "advanced_patent_search",
        "search_chemistry",
        "get_patent_details",
        "get_patent_pdf",
        "get_prior_art_timeline",
        "find_similar_patents",
        "normalize_patent_number",
        "get_patent_citations",
        "lookup_classification_code",
    ]
    for exp in expected_tools:
        assert exp in tool_names, f"Missing tool: {exp}"
    print("✓ All 11 MCP tools registered successfully.")

    # 2. Test parse_query
    print("\n[2/10] Testing parse_query...")
    res1_raw, _ = await mcp.call_tool("parse_query", {"query": "US8000000B2"})
    res1 = json.loads(res1_raw[0].text)
    print(f"  Result: is_patent_number_search={res1.get('is_patent_number_search')}, tool={res1.get('recommended_tool')}")
    assert res1.get("is_patent_number_search") is True
    print("✓ parse_query passed.")

    # 3. Test search_patents
    print("\n[3/10] Testing search_patents...")
    s_raw, _ = await mcp.call_tool("search_patents", {"query_url_or_params": "q=autonomous+vehicle&assignee=Waymo", "limit": 3})
    s_res = json.loads(s_raw[0].text)
    print(f"  Search Source: {s_res.get('backend_source')} | Service: {s_res.get('backend_service')}")
    print(f"  Total Results: {s_res.get('total_num_results') or s_res.get('total_returned')}")
    assert len(s_res.get("results", [])) > 0
    print("✓ search_patents passed.")

    # 4. Test advanced_patent_search
    print("\n[4/10] Testing advanced_patent_search (Bose + G10K)...")
    adv_raw, _ = await mcp.call_tool(
        "advanced_patent_search",
        {
            "query": "noise cancellation",
            "assignee": "Bose",
            "cpc_code": "G10K",
            "country_code": "US",
            "limit": 3,
        }
    )
    adv_res = json.loads(adv_raw[0].text)
    print(f"  Advanced Search Source: {adv_res.get('backend_source')} | Service: {adv_res.get('backend_service')}")
    print(f"  Matching Patents: {adv_res.get('total_num_results') or adv_res.get('total_returned')}")
    assert len(adv_res.get("results", [])) > 0
    print("✓ advanced_patent_search passed.")

    # 5. Test search_chemistry (SMILES)
    print("\n[5/10] Testing search_chemistry (Aspirin SMILES)...")
    chem_raw, _ = await mcp.call_tool(
        "search_chemistry",
        {"smiles": "CC(=O)Oc1ccccc1C(=O)O", "query": "aspirin", "mode": "EXACT", "limit": 3}
    )
    chem_res = json.loads(chem_raw[0].text)
    print(f"  Chemistry Source: {chem_res.get('backend_source')} | Service: {chem_res.get('backend_service')}")
    print(f"  Matching Chemical Patents: {chem_res.get('total_num_results') or chem_res.get('total_returned')}")
    assert len(chem_res.get("results", [])) > 0
    print("✓ search_chemistry passed.")

    # 6. Test get_patent_pdf
    print("\n[6/10] Testing get_patent_pdf for 'US8000000B2'...")
    pdf_raw, _ = await mcp.call_tool("get_patent_pdf", {"patent_id": "US8000000B2"})
    pdf_res = json.loads(pdf_raw[0].text)
    print(f"  PDF Download URL: {pdf_res.get('pdf_download_url')}")
    assert "pdf" in pdf_res.get("pdf_download_url", "")
    print("✓ get_patent_pdf passed.")

    # 7. Test get_prior_art_timeline
    print("\n[7/10] Testing get_prior_art_timeline for 'US8000000B2'...")
    tl_raw, _ = await mcp.call_tool("get_prior_art_timeline", {"patent_id": "US8000000B2"})
    tl_res = json.loads(tl_raw[0].text)
    print(f"  Family ID: {tl_res.get('family_id')}")
    print(f"  Key Dates: {tl_res.get('key_dates')}")
    print(f"  INPADOC Family Members: {len(tl_res.get('inpadoc_family_members', []))}")
    assert len(tl_res.get("inpadoc_family_members", [])) > 0
    print("✓ get_prior_art_timeline passed.")

    # 8. Test get_patent_details
    print("\n[8/11] Testing get_patent_details for 'US8000000B2'...")
    dt_raw, _ = await mcp.call_tool("get_patent_details", {"patent_url_or_id": "US8000000B2", "include_claims": True})
    dt_res = json.loads(dt_raw[0].text)
    print(f"  Title: {dt_res.get('title')}")
    print(f"  Assignees: {dt_res.get('assignees')}")
    print(f"  Claims present: {len(dt_res.get('claims', [])) > 0}")
    claims_tree = dt_res.get("claims_tree", {})
    print(
        f"  Claim Tree Parsed: total={claims_tree.get('total_claims')}, "
        f"independent={claims_tree.get('independent_count')}, "
        f"dependent={claims_tree.get('dependent_count')}, "
        f"max_depth={claims_tree.get('max_depth')}"
    )
    assert dt_res.get("title") is not None
    assert claims_tree.get("total_claims", 0) > 0
    print("✓ get_patent_details passed.")

    # 9. Test find_similar_patents
    print("\n[9/11] Testing find_similar_patents for 'US-10000000-B2'...")
    sim_raw, _ = await mcp.call_tool("find_similar_patents", {"patent_id": "US-10000000-B2", "limit": 2})
    sim_res = json.loads(sim_raw[0].text)
    print(f"  Similar Patents Found: {len(sim_res.get('similar_patents', []))}")
    assert len(sim_res.get("similar_patents", [])) > 0
    print("✓ find_similar_patents passed.")

    # 10. Test normalize_patent_number & lookup_classification_code
    print("\n[10/11] Testing normalize_patent_number & lookup_classification_code...")
    norm_raw, _ = await mcp.call_tool("normalize_patent_number", {"number": "10000000", "country": "US"})
    norm_res = json.loads(norm_raw[0].text)
    print(f"  Normalized: {norm_res.get('canonical_id')}")
    assert norm_res.get("canonical_id") == "US-10000000-B2"

    cpc_raw, _ = await mcp.call_tool("lookup_classification_code", {"code": "G06N3/08"})
    cpc_res = json.loads(cpc_raw[0].text)
    print(f"  CPC Definition: {cpc_res.get('symbol')} | {cpc_res.get('title')}")
    assert "Learning methods" in cpc_res.get("title", "")
    print("✓ normalize_patent_number & lookup_classification_code passed.")

    # 11. Test All 6 MCP Apps (ui://google-patents/*)
    print("\n[11/11] Testing All 6 MCP Apps (ui://google-patents/*)...")
    tools_by_name = {t.name: t for t in tools}
    expected_tool_ui_links = {
        # View 1
        "get_patent_details": "ui://google-patents/claim-tree",
        "open_patent_claim_tree_app": "ui://google-patents/claim-tree",
        # View 2
        "get_prior_art_timeline": "ui://google-patents/prior-art-timeline",
        "open_prior_art_timeline_app": "ui://google-patents/prior-art-timeline",
        # View 3
        "get_patent_citations": "ui://google-patents/citation-graph",
        "find_similar_patents": "ui://google-patents/citation-graph",
        "open_patent_citation_graph_app": "ui://google-patents/citation-graph",
        # View 4
        "search_patents": "ui://google-patents/landscape-dashboard",
        "advanced_patent_search": "ui://google-patents/landscape-dashboard",
        "lookup_classification_code": "ui://google-patents/landscape-dashboard",
        "open_patent_landscape_app": "ui://google-patents/landscape-dashboard",
        # View 5
        "get_patent_pdf": "ui://google-patents/pdf-drawing-viewer",
        "open_patent_pdf_viewer_app": "ui://google-patents/pdf-drawing-viewer",
        # View 6
        "search_chemistry": "ui://google-patents/chemistry-explorer",
        "open_chemistry_explorer_app": "ui://google-patents/chemistry-explorer",
    }
    for tname, expected_uri in expected_tool_ui_links.items():
        t_obj = tools_by_name[tname]
        t_dump = json.loads(t_obj.model_dump_json(by_alias=True, exclude_none=True))
        ui_uri = t_dump.get("_meta", {}).get("ui", {}).get("resourceUri")
        print(f"  Tool '{tname}' -> _meta.ui.resourceUri = {ui_uri}")
        assert ui_uri == expected_uri, f"Expected {expected_uri} for {tname}, got {ui_uri}"

    resources = await mcp.list_resources()
    res_uris = [str(r.uri) for r in resources]
    print(f"  Registered MCP Resources ({len(res_uris)}): {res_uris}")
    expected_resources = [
        "ui://google-patents/claim-tree",
        "ui://google-patents/prior-art-timeline",
        "ui://google-patents/citation-graph",
        "ui://google-patents/landscape-dashboard",
        "ui://google-patents/pdf-drawing-viewer",
        "ui://google-patents/chemistry-explorer",
    ]
    for r_uri in expected_resources:
        assert r_uri in res_uris, f"Missing MCP App resource: {r_uri}"
        ui_contents = await mcp.read_resource(r_uri)
        assert len(ui_contents) == 1
        assert ui_contents[0].mime_type == "text/html;profile=mcp-app"
        assert len(ui_contents[0].content) > 2000
        print(f"  ✓ Read {r_uri} ({len(ui_contents[0].content)} bytes, mime={ui_contents[0].mime_type})")

    app_result = await mcp.call_tool(
        "open_patent_claim_tree_app",
        {"patent_url_or_id": "US8000000B2", "compare_with_patent_id": "US10000000B2"},
    )
    assert app_result.isError is False
    assert app_result.structuredContent["total_claims"] > 0
    assert app_result.structuredContent["compared_with"] == "US-10000000-B2"
    print("✓ All 6 MCP Apps (ui://google-patents/*) passed.")

    print("\n" + "=" * 75)
    print("  ALL 11 TESTS (INCLUDING ALL 6 MCP APPS ui://) PASSED SUCCESSFULLY!  ")
    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(run_tests())
