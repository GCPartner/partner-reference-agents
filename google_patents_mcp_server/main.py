"""Main entry point for Google Patents MCP Server."""

import argparse
import os
import sys
import uvicorn

# Ensure package is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from google_patents_mcp_server.server import get_asgi_app, mcp
except ImportError:
    from server import get_asgi_app, mcp

app = get_asgi_app()


def main():
    parser = argparse.ArgumentParser(description="Google Patents MCP Server")
    parser.add_argument(
        "--transport",
        choices=["sse", "stdio", "streamable-http"],
        default=os.environ.get("MCP_TRANSPORT", "streamable-http" if os.environ.get("PORT") else "stdio"),
        help="Transport mode (streamable-http, sse, stdio). Defaults to streamable-http if PORT is set, else stdio.",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("HOST", "0.0.0.0"),
        help="Host address for HTTP/SSE transport (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", "8080")),
        help="Port for HTTP/SSE transport (default: 8080 or $PORT)",
    )

    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    elif args.transport in ("streamable-http", "sse"):
        app = get_asgi_app(transport=args.transport)
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()

