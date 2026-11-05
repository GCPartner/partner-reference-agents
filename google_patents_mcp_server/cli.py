"""Interactive CLI tool to quickly test any Google Patents MCP tool locally."""

import argparse
import asyncio
import json
import os
import sys

# Ensure package is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from google_patents_mcp_server.server import mcp


async def run_cli():
    parser = argparse.ArgumentParser(description="Quick CLI tester for Google Patents MCP Server")
    subparsers = parser.add_subparsers(dest="command", help="Tool to run")

    # Search
    s_p = subparsers.add_parser("search", help="Keyword or measure search")
    s_p.add_argument("query", help="Search query (e.g. 'autonomous vehicle' or 'q=battery')")
    s_p.add_argument("--limit", type=int, default=5, help="Number of results")

    # Advanced Search
    adv_p = subparsers.add_parser("advanced", help="Advanced filtered search")
    adv_p.add_argument("--query", default="", help="Keywords")
    adv_p.add_argument("--assignee", default="", help="Assignee / company")
    adv_p.add_argument("--cpc", default="", help="CPC code (e.g. G10K)")
    adv_p.add_argument("--country", default="", help="Country code (e.g. US)")
    adv_p.add_argument("--limit", type=int, default=5, help="Number of results")

    # Chemistry Search
    chem_p = subparsers.add_parser("chem", help="Chemical SMILES / InChIKey search")
    chem_p.add_argument("smiles", help="SMILES string (e.g. 'CC(=O)Oc1ccccc1C(=O)O' for Aspirin)")
    chem_p.add_argument("--mode", default="EXACT", choices=["EXACT", "SUBSTRUCTURE", "SIMILARITY"])
    chem_p.add_argument("--limit", type=int, default=5)

    # Details
    det_p = subparsers.add_parser("details", help="Full structured patent details")
    det_p.add_argument("patent_id", help="Patent number (e.g. 'US8000000B2')")
    det_p.add_argument("--claims", action="store_true", default=True, help="Include claims")
    det_p.add_argument("--description", action="store_true", default=False, help="Include description")

    # PDF & Drawings
    pdf_p = subparsers.add_parser("pdf", help="Get direct PDF download & high-res figure URLs")
    pdf_p.add_argument("patent_id", help="Patent number (e.g. 'US8000000B2')")

    # Timeline & INPADOC
    t_p = subparsers.add_parser("timeline", help="Prior art timeline, INPADOC family, and Scholar NPL")
    t_p.add_argument("patent_id", help="Patent number (e.g. 'US8000000B2')")

    # Similar
    sim_p = subparsers.add_parser("similar", help="Find similar patents using ScaM")
    sim_p.add_argument("patent_id", help="Patent number")
    sim_p.add_argument("--limit", type=int, default=5)

    # Citations
    c_p = subparsers.add_parser("citations", help="Get forward & backward citations")
    c_p.add_argument("patent_id", help="Patent number")
    c_p.add_argument("--type", default="both", choices=["backward", "forward", "both"])
    c_p.add_argument("--limit", type=int, default=10)

    # Classification
    cpc_p = subparsers.add_parser("cpc", help="Lookup CPC/IPC definition")
    cpc_p.add_argument("code", help="CPC/IPC code (e.g. 'G06N3/08')")

    # Parse query
    pq_p = subparsers.add_parser("parse", help="Parse freeform query")
    pq_p.add_argument("query", help="Raw search string")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    print(f"\n--- Executing [{args.command}] ---")

    if args.command == "search":
        res_raw, _ = await mcp.call_tool("search_patents", {"query_url_or_params": args.query, "limit": args.limit})
    elif args.command == "advanced":
        res_raw, _ = await mcp.call_tool("advanced_patent_search", {
            "query": args.query,
            "assignee": args.assignee,
            "cpc_code": args.cpc,
            "country_code": args.country,
            "limit": args.limit,
        })
    elif args.command == "chem":
        res_raw, _ = await mcp.call_tool("search_chemistry", {"smiles": args.smiles, "mode": args.mode, "limit": args.limit})
    elif args.command == "details":
        res_raw, _ = await mcp.call_tool("get_patent_details", {
            "patent_url_or_id": args.patent_id,
            "include_claims": args.claims,
            "include_description": args.description,
        })
    elif args.command == "pdf":
        res_raw, _ = await mcp.call_tool("get_patent_pdf", {"patent_id": args.patent_id})
    elif args.command == "timeline":
        res_raw, _ = await mcp.call_tool("get_prior_art_timeline", {"patent_id": args.patent_id})
    elif args.command == "similar":
        res_raw, _ = await mcp.call_tool("find_similar_patents", {"patent_id": args.patent_id, "limit": args.limit})
    elif args.command == "citations":
        res_raw, _ = await mcp.call_tool("get_patent_citations", {"patent_id": args.patent_id, "citation_type": args.type, "limit": args.limit})
    elif args.command == "cpc":
        res_raw, _ = await mcp.call_tool("lookup_classification_code", {"code": args.code})
    elif args.command == "parse":
        res_raw, _ = await mcp.call_tool("parse_query", {"query": args.query})
    else:
        print("Unknown command")
        return

    data = json.loads(res_raw[0].text)
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    asyncio.run(run_cli())
