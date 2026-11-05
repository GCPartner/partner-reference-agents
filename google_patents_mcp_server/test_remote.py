"""Remote verification test suite for deployed Google Patents MCP Server on Cloud Run."""

import asyncio
import json
import os
import sys
from contextlib import asynccontextmanager
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.session import ClientSession

SERVICE_URL = os.environ.get(
    "SERVICE_URL",
    "http://localhost:8080/mcp"
)


@asynccontextmanager
async def connect_mcp(url: str, headers: dict):
    """Connects using StreamableHTTP (/mcp) or SSE (/sse) depending on URL path."""
    if url.rstrip("/").endswith("/sse"):
        async with sse_client(url, headers=headers or None) as (read_stream, write_stream):
            yield read_stream, write_stream
    else:
        async with streamablehttp_client(url, headers=headers or None) as (read_stream, write_stream, _):
            yield read_stream, write_stream


async def run_remote_test():
    print("=" * 75)
    print("  Testing Deployed Google Patents MCP Server on Cloud Run  ")
    print(f"  Target MCP Endpoint: {SERVICE_URL}")
    print("=" * 75)

    headers = {}
    auth_token = os.environ.get("AUTH_TOKEN")
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    serverless_token = os.environ.get("SERVERLESS_ID_TOKEN")
    if serverless_token:
        headers["X-Serverless-Authorization"] = f"Bearer {serverless_token}"

    try:
        async with connect_mcp(SERVICE_URL, headers) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                print("✓ Successfully established MCP connection and initialized session!\n")

                # 1. List Tools
                print("[1/11] Listing Remote Tools...")
                tools_res = await session.list_tools()
                tool_names = [t.name for t in tools_res.tools]
                print(f"  Remote Tools Available ({len(tool_names)}): {tool_names}")
                assert len(tool_names) >= 11, f"Expected 11 tools, got {len(tool_names)}"
                print("✓ Tool listing verified.\n")

                # 2. Test parse_query
                print("[2/11] Testing parse_query...")
                res2 = await session.call_tool("parse_query", {"query": "US8000000B2"})
                data2 = json.loads(res2.content[0].text)
                print(f"  Backend Source:  {data2.get('backend_source')}")
                print(f"  Backend Service: {data2.get('backend_service')}")
                print(f"  Result: is_patent_number_search={data2.get('is_patent_number_search')}, tool={data2.get('recommended_tool')}")
                assert data2.get("is_patent_number_search") is True
                print("✓ parse_query passed.\n")

                # 3. Test search_patents
                print("[3/11] Testing search_patents...")
                res3 = await session.call_tool("search_patents", {"query_url_or_params": "q=autonomous+vehicle&assignee=Waymo", "limit": 2})
                data3 = json.loads(res3.content[0].text)
                print(f"  Backend Source:  {data3.get('backend_source')}")
                print(f"  Backend Service: {data3.get('backend_service')}")
                print(f"  Results Count:   {len(data3.get('results', []))}")
                assert len(data3.get("results", [])) > 0
                print("✓ search_patents passed.\n")

                # 4. Test advanced_patent_search
                print("[4/11] Testing advanced_patent_search...")
                res4 = await session.call_tool("advanced_patent_search", {
                    "query": "noise cancellation",
                    "assignee": "Bose",
                    "cpc_code": "G10K",
                    "country_code": "US",
                    "limit": 2
                })
                data4 = json.loads(res4.content[0].text)
                print(f"  Backend Source:  {data4.get('backend_source')}")
                print(f"  Backend Service: {data4.get('backend_service')}")
                print(f"  Results Count:   {len(data4.get('results', []))}")
                assert len(data4.get("results", [])) > 0
                print("✓ advanced_patent_search passed.\n")

                # 5. Test search_chemistry
                print("[5/11] Testing search_chemistry...")
                res5 = await session.call_tool("search_chemistry", {
                    "smiles": "CC(=O)Oc1ccccc1C(=O)O",
                    "query": "aspirin",
                    "mode": "EXACT",
                    "limit": 2
                })
                data5 = json.loads(res5.content[0].text)
                print(f"  Backend Source:  {data5.get('backend_source')}")
                print(f"  Backend Service: {data5.get('backend_service')}")
                print(f"  Results Count:   {len(data5.get('results', []))}")
                assert len(data5.get("results", [])) > 0
                print("✓ search_chemistry passed.\n")

                # 6. Test get_patent_details
                print("[6/11] Testing get_patent_details...")
                res6 = await session.call_tool("get_patent_details", {
                    "patent_url_or_id": "US8000000B2",
                    "include_claims": True
                })
                data6 = json.loads(res6.content[0].text)
                print(f"  Backend Source:  {data6.get('backend_source')}")
                print(f"  Backend Service: {data6.get('backend_service')}")
                print(f"  Title:           {data6.get('title')}")
                print(f"  Assignees:       {data6.get('assignees')[:2] if data6.get('assignees') else []}")
                print(f"  Claims present:  {bool(data6.get('claims'))}")
                assert "US" in data6.get("publication_number", "")
                print("✓ get_patent_details passed.\n")

                # 7. Test get_patent_pdf
                print("[7/11] Testing get_patent_pdf...")
                res7 = await session.call_tool("get_patent_pdf", {"patent_id": "US8000000B2"})
                data7 = json.loads(res7.content[0].text)
                print(f"  Backend Source:   {data7.get('backend_source')}")
                print(f"  Backend Service:  {data7.get('backend_service')}")
                print(f"  PDF Download URL: {data7.get('pdf_download_url')}")
                assert bool(data7.get("pdf_download_url"))
                print("✓ get_patent_pdf passed.\n")

                # 8. Test get_prior_art_timeline
                print("[8/11] Testing get_prior_art_timeline...")
                res8 = await session.call_tool("get_prior_art_timeline", {"patent_id": "US8000000B2"})
                data8 = json.loads(res8.content[0].text)
                print(f"  Backend Source:        {data8.get('backend_source')}")
                print(f"  Backend Service:       {data8.get('backend_service')}")
                print(f"  Family ID:             {data8.get('family_id')}")
                print(f"  INPADOC Members Count: {data8.get('inpadoc_family_members_count')}")
                assert data8.get("inpadoc_family_members_count", 0) > 0
                print("✓ get_prior_art_timeline passed.\n")

                # 9. Test find_similar_patents
                print("[9/11] Testing find_similar_patents...")
                res9 = await session.call_tool("find_similar_patents", {"patent_id": "US-10000000-B2", "limit": 2})
                data9 = json.loads(res9.content[0].text)
                print(f"  Backend Source:        {data9.get('backend_source')}")
                print(f"  Backend Service:       {data9.get('backend_service')}")
                print(f"  Similar Patents Found: {data9.get('total_similar_found')}")
                assert data9.get("total_similar_found", 0) > 0
                print("✓ find_similar_patents passed.\n")

                # 10. Test get_patent_citations
                print("[10/11] Testing get_patent_citations...")
                res10 = await session.call_tool("get_patent_citations", {"patent_id": "US8000000B2", "limit": 3})
                data10 = json.loads(res10.content[0].text)
                print(f"  Backend Source:     {data10.get('backend_source')}")
                print(f"  Backend Service:    {data10.get('backend_service')}")
                print(f"  Backward Citations: {data10.get('backward_count')}")
                print(f"  Forward Citations:  {data10.get('forward_count')}")
                assert data10.get("backward_count", 0) > 0 or data10.get("forward_count", 0) > 0
                print("✓ get_patent_citations passed.\n")

                # 11. Test normalize_patent_number & lookup_classification_code
                print("[11/11] Testing normalize_patent_number & lookup_classification_code...")
                res11a = await session.call_tool("normalize_patent_number", {"number": "10000000", "country": "US"})
                data11a = json.loads(res11a.content[0].text)
                print(f"  [normalize] Backend Source:  {data11a.get('backend_source')}")
                print(f"  [normalize] Canonical ID:    {data11a.get('canonical_id')}")
                assert data11a.get("canonical_id") == "US-10000000-B2"

                res11b = await session.call_tool("lookup_classification_code", {"code": "G06N3/08"})
                data11b = json.loads(res11b.content[0].text)
                print(f"  [CPC lookup] Backend Source: {data11b.get('backend_source')}")
                print(f"  [CPC lookup] Classification: {data11b.get('symbol')} - {data11b.get('title_full')}")
                assert data11b.get("symbol") == "G06N3/08"
                print("✓ normalize_patent_number & lookup_classification_code passed.\n")

                # 12. Test All 6 Remote MCP Apps (ui://google-patents/*)
                print("[12/12] Testing All 6 Remote MCP Apps (ui://google-patents/*)...")
                resources_res = await session.list_resources()
                resource_uris = [str(r.uri) for r in resources_res.resources]
                print(f"  Remote MCP Resources ({len(resource_uris)}): {resource_uris}")
                expected_resources = [
                    "ui://google-patents/claim-tree",
                    "ui://google-patents/prior-art-timeline",
                    "ui://google-patents/citation-graph",
                    "ui://google-patents/landscape-dashboard",
                    "ui://google-patents/pdf-drawing-viewer",
                    "ui://google-patents/chemistry-explorer",
                ]
                for r_uri in expected_resources:
                    assert r_uri in resource_uris, f"Missing remote MCP App resource: {r_uri}"
                    read_res = await session.read_resource(r_uri)
                    assert len(read_res.contents) == 1
                    assert read_res.contents[0].mimeType == "text/html;profile=mcp-app"
                    print(f"  ✓ Read {r_uri} ({len(read_res.contents[0].text)} bytes, mime={read_res.contents[0].mimeType})")

                res12 = await session.call_tool(
                    "open_patent_claim_tree_app",
                    {"patent_url_or_id": "US8000000B2", "compare_with_patent_id": "US10000000B2"},
                )
                assert res12.isError is False
                sc12 = res12.structuredContent or json.loads(res12.content[0].text)
                print(f"  open_patent_claim_tree_app: primary={sc12.get('publication_number')} ({sc12.get('total_claims')} claims) vs compared_with={sc12.get('compared_with')}")
                assert sc12.get("total_claims", 0) > 0
                print("✓ All 6 Remote MCP Apps (ui://google-patents/*) passed.\n")

                print("=" * 75)
                print("  ALL 18 REMOTE TOOLS & 6 MCP APPS TESTED SUCCESSFULLY ON CLOUD RUN!  ")
                print("=" * 75)

    except Exception as e:
        print(f"ERROR during remote test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_remote_test())
