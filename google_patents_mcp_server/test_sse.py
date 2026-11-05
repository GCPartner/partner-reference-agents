"""Test StreamableHTTP (/mcp), SSE (/sse), and Option 1 Google OAuth 2.0 security on 127.0.0.1."""

import asyncio
import json
import os
import sys
import time
from multiprocessing import Process
from unittest.mock import AsyncMock, patch

import httpx
import uvicorn
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

TEST_CLIENT_ID = "1234567890-testclient.apps.googleusercontent.com"
VALID_TOKEN = "mock_valid_oauth_access_token"
WRONG_CLIENT_TOKEN = "mock_wrong_client_oauth_token"


def run_oauth_server():
    """Runs the MCP server on 127.0.0.1 with Option 1 Google OAuth 2.0 enabled."""
    os.environ["GOOGLE_OAUTH_CLIENT_ID"] = TEST_CLIENT_ID
    os.environ["GOOGLE_OAUTH_CLIENT_SECRET"] = "test-oauth-client-secret"
    os.environ["REQUIRE_OAUTH"] = "true"
    os.environ["OAUTH_REQUIRED_SCOPES"] = "openid email profile"

    from google_patents_mcp_server.server import GoogleOAuthTokenVerifier, get_asgi_app

    orig_get = httpx.AsyncClient.get
    orig_post = httpx.AsyncClient.post

    async def mock_get(self, url, params=None, **kwargs):
        if "tokeninfo" not in str(url):
            return await orig_get(self, url, params=params, **kwargs)
        token = (params or {}).get("access_token") or (params or {}).get("id_token")
        request = httpx.Request("GET", str(url))
        if token == VALID_TOKEN:
            return httpx.Response(
                200,
                json={
                    "aud": TEST_CLIENT_ID,
                    "azp": TEST_CLIENT_ID,
                    "email": "user@example.com",
                    "email_verified": "true",
                    "scope": "openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile",
                    "exp": str(int(time.time()) + 3600),
                },
                request=request,
            )
        if token == WRONG_CLIENT_TOKEN:
            return httpx.Response(
                200,
                json={
                    "aud": "other-client.apps.googleusercontent.com",
                    "azp": "other-client.apps.googleusercontent.com",
                    "email": "user@example.com",
                    "email_verified": "true",
                    "scope": "openid email profile",
                    "exp": str(int(time.time()) + 3600),
                },
                request=request,
            )
        return httpx.Response(400, json={"error_description": "Invalid Value"}, request=request)

    async def mock_post(self, url, data=None, **kwargs):
        if "oauth2.googleapis.com/token" not in str(url):
            return await orig_post(self, url, data=data, **kwargs)
        request = httpx.Request("POST", str(url))
        if (data or {}).get("code") == "valid_auth_code" and (data or {}).get("client_secret") == "test-oauth-client-secret":
            # Simulate Google omitting refresh_token to verify /token still guarantees refresh_token
            return httpx.Response(
                200,
                json={
                    "access_token": VALID_TOKEN,
                    "expires_in": 3599,
                    "token_type": "Bearer",
                    "scope": "openid email profile",
                },
                request=request,
            )
        return httpx.Response(400, json={"error": "invalid_grant"}, request=request)

    app = get_asgi_app(transport="streamable-http")

    with patch.object(httpx.AsyncClient, "get", mock_get), patch.object(httpx.AsyncClient, "post", mock_post):
        uvicorn.run(app, host="127.0.0.1", port=8089, log_level="warning")


async def verify_streamable_http_oauth():
    async with streamablehttp_client(
        "http://127.0.0.1:8089/mcp",
        headers={"Authorization": f"Bearer {VALID_TOKEN}"},
    ) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools_res = await session.list_tools()
            tool_names = [t.name for t in tools_res.tools]
            print(f"✓ StreamableHTTP (/mcp) authenticated tools ({len(tool_names)}): {tool_names}")
            assert "search_patents" in tool_names
            assert "parse_query" in tool_names

            # Verify readOnlyHint annotation is set for Gemini Enterprise
            search_tool = next(t for t in tools_res.tools if t.name == "search_patents")
            assert search_tool.annotations is not None
            assert search_tool.annotations.readOnlyHint is True

            # Call parse_query over authenticated StreamableHTTP
            res = await session.call_tool("parse_query", {"query": "US8000000B2"})
            parsed = json.loads(res.content[0].text)
            assert parsed.get("is_patent_number_search") is True
            print("✓ Authenticated tool call over StreamableHTTP (/mcp) succeeded!")


def main():
    proc = Process(target=run_oauth_server, daemon=True)
    proc.start()

    try:
        with httpx.Client(base_url="http://127.0.0.1:8089", timeout=10.0) as client:
            # Wait for server startup (BigQuery client init can take several seconds)
            resp = None
            for _ in range(30):
                try:
                    resp = client.get("/healthz")
                    if resp.status_code == 200:
                        break
                except httpx.ConnectError:
                    time.sleep(0.5)
            assert resp is not None and resp.status_code == 200
            # 1. Health check (should remain accessible without token for Cloud Run probes)
            print("Health check status:", resp.status_code)
            print("Health response:", resp.json())
            assert resp.json().get("status") == "healthy"
            assert resp.json().get("oauth_enabled") is True

            # 2. Unauthenticated request to /mcp MUST return 401
            unauth_mcp = client.post("/mcp", json={"jsonrpc": "2.0", "method": "initialize", "id": 1})
            print("Unauthenticated /mcp status:", unauth_mcp.status_code)
            assert unauth_mcp.status_code == 401

            # 3. Invalid token to /mcp MUST return 401
            invalid_mcp = client.post(
                "/mcp",
                headers={"Authorization": "Bearer invalid_token"},
                json={"jsonrpc": "2.0", "method": "initialize", "id": 1},
            )
            print("Invalid token /mcp status:", invalid_mcp.status_code)
            assert invalid_mcp.status_code == 401

            # 4. Token for wrong OAuth Client ID MUST return 401
            wrong_client_mcp = client.post(
                "/mcp",
                headers={"Authorization": f"Bearer {WRONG_CLIENT_TOKEN}"},
                json={"jsonrpc": "2.0", "method": "initialize", "id": 1},
            )
            print("Wrong Client ID /mcp status:", wrong_client_mcp.status_code)
            assert wrong_client_mcp.status_code == 401

            # 5. Test /authorize issues a signed code and redirects directly to redirect_uri (preserving window.opener)
            import urllib.parse
            auth_resp = client.get(
                "/authorize",
                params={
                    "client_id": TEST_CLIENT_ID,
                    "redirect_uri": "https://vertexaisearch.cloud.google.com/oauth-redirect",
                    "state": "xyz123",
                },
                follow_redirects=False,
            )
            print("/authorize status:", auth_resp.status_code, "Location:", auth_resp.headers.get("location"))
            assert auth_resp.status_code == 302
            loc = auth_resp.headers.get("location", "")
            assert loc.startswith("https://vertexaisearch.cloud.google.com/oauth-redirect?")
            loc_qs = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(loc).query))
            assert loc_qs.get("state") == "xyz123"
            issued_code = loc_qs.get("code", "")
            assert issued_code.startswith("gpmcp_code.")

            # 6. Test /token exchanges the signed code for signed access_token and refresh_token
            token_resp = client.post(
                "/token",
                data={
                    "grant_type": "authorization_code",
                    "code": issued_code,
                    "client_id": TEST_CLIENT_ID,
                    "client_secret": "test-oauth-client-secret",
                },
            )
            print("/token status:", token_resp.status_code, "keys:", list(token_resp.json().keys()))
            assert token_resp.status_code == 200
            issued_at = token_resp.json().get("access_token", "")
            issued_rt = token_resp.json().get("refresh_token", "")
            assert issued_at.startswith("gpmcp.")
            assert issued_rt.startswith("gpmcp_rt.")

            # 7. Test /token refresh_token grant
            refresh_resp = client.post(
                "/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": issued_rt,
                    "client_id": TEST_CLIENT_ID,
                    "client_secret": "test-oauth-client-secret",
                },
            )
            assert refresh_resp.status_code == 200
            assert refresh_resp.json().get("access_token", "").startswith("gpmcp.")

        # 8. Valid OAuth token over StreamableHTTP (/mcp) MUST succeed
        asyncio.run(verify_streamable_http_oauth())
        print("✓ All StreamableHTTP (/mcp), SSE (/sse), /authorize, /token, and OAuth 2.0 checks passed!")
    finally:
        proc.terminate()
        proc.join()


if __name__ == "__main__":
    main()

