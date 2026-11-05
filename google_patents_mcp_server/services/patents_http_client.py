"""HTTP client for Google Patents public web gateway (match, search, XHR query)."""

import logging
import os
import re
import urllib.parse
from typing import Any, Dict, List, Optional
import httpx

from .circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)

BASE_PATENTS_URL = "https://patents.google.com"
DEFAULT_TIMEOUT = 12.0


def _build_browser_headers(cookie: Optional[str] = None, referer_query: Optional[str] = None) -> Dict[str, str]:
    """Constructs authentic browser headers with optional session cookie and matching Referer."""
    ref_url = f"https://patents.google.com/?{referer_query}" if referer_query else "https://patents.google.com/"
    headers = {
        "User-Agent": os.environ.get(
            "PATENTS_USER_AGENT",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": ref_url,
        "Origin": "https://patents.google.com",
        "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"macOS"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "X-Requested-With": "XMLHttpRequest",
        "X-Client-Data": "CIa2yQEIorbJAQipncoBCMDdygEIqKPKAQjiq8oBCNyszAEI7vLMAQj19swBCI/4zAEI+fnMAQjn+swBCKX8zAEI6fzMAQ==",
    }
    active_cookie = cookie or os.environ.get("GOOGLE_PATENTS_COOKIE")
    if active_cookie:
        headers["Cookie"] = active_cookie.strip()
    return headers


def _clean_html(text: Optional[str]) -> str:
    """Strips HTML markup and decodes common HTML entities."""
    if not text:
        return ""
    cleaned = re.sub(r"<[^>]+>", "", text)
    cleaned = (
        cleaned.replace("&hellip;", "...")
        .replace("&amp;", "&")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
    )
    return cleaned.strip()


class PatentsHttpClient:
    """Client for interacting with Google Patents HTTP endpoints and XHR reverse-proxy."""

    def __init__(self, timeout: float = DEFAULT_TIMEOUT, cookie: Optional[str] = None):
        self.timeout = timeout
        self.cookie = cookie or os.environ.get("GOOGLE_PATENTS_COOKIE")
        self.proxy_url = os.environ.get("PATENTS_PROXY_URL")
        self.circuit_breaker = CircuitBreaker()

    def set_cookie(self, cookie: str) -> None:
        """Dynamically inject or update session cookie at runtime."""
        self.cookie = cookie.strip()
        logger.info("Updated Google Patents session cookie in PatentsHttpClient.")

    def _get_client(self, referer_query: Optional[str] = None) -> httpx.AsyncClient:
        """Creates an AsyncClient configured with browser headers and proxy settings."""
        headers = _build_browser_headers(self.cookie, referer_query=referer_query)
        kwargs: Dict[str, Any] = {
            "headers": headers,
            "timeout": self.timeout,
            "trust_env": False,
            "follow_redirects": True,
        }
        if self.proxy_url:
            kwargs["proxy"] = self.proxy_url
        return httpx.AsyncClient(**kwargs)

    async def match_number(
        self,
        number: str,
        country: Optional[str] = None,
        patent_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Calls the official Google Patents /api/match endpoint to normalize patent numbers.

        Args:
            number: Raw patent or application number (e.g. '10000000', 'US10000000', 'EP1234567').
            country: Optional two-letter country code.
            patent_type: Optional document type (e.g. 'patent', 'application').

        Returns:
            List of matched candidate dictionaries with 'id' and 'ucid'.
        """
        params: Dict[str, str] = {"num": number.strip()}
        if country:
            params["country"] = country.strip().upper()
        if patent_type and patent_type.strip().lower() not in ("patent", "any", ""):
            params["type"] = patent_type.strip().lower()

        url = f"{BASE_PATENTS_URL}/api/match"
        try:
            async with self._get_client() as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                results = []
                for item in data.get("result", []):
                    matches = item.get("match", [])
                    for match in matches:
                        if match and "id" in match:
                            results.append({
                                "id": match.get("id"),
                                "ucid": match.get("ucid"),
                            })
                return results
        except Exception as e:
            logger.warning(f"Google Patents match API error for query '{number}': {e}")
            return []

    async def query_xhr(self, query_url_param: str, num_page: int = 0) -> Optional[Dict[str, Any]]:
        """Calls Google Patents /xhr/query with CircuitBreaker protection, pacing, and caching.

        Args:
            query_url_param: URL query parameter string (e.g. 'q=autonomous+vehicle&assignee=Waymo').
            num_page: Page index (0-based).

        Returns:
            Raw response dictionary or None if unreachable or blocked.
        """
        cache_key = f"{query_url_param}:page={num_page}"
        cached = self.circuit_breaker.get_cached(cache_key)
        if cached:
            logger.info(f"Serving Google Patents XHR query from in-memory cache: {cache_key}")
            return cached

        can_try, state, remaining = self.circuit_breaker.can_attempt()
        if not can_try:
            logger.info(
                f"Circuit breaker is {state} (cooldown: {remaining}s remaining). Fast-fallback to BigQuery."
            )
            return None

        try:
            await self.circuit_breaker.pace_request()
            encoded_param = urllib.parse.quote(query_url_param)
            url = f"{BASE_PATENTS_URL}/xhr/query?url={encoded_param}%26oq%3D{encoded_param}%26page%3D{num_page}"
            async with self._get_client(referer_query=query_url_param) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        self.circuit_breaker.record_success()
                        self.circuit_breaker.set_cached(cache_key, data)
                        return data
                    except Exception:
                        pass
                logger.warning(f"Google Patents XHR returned status {resp.status_code} for query: {query_url_param}")
                self.circuit_breaker.record_failure(resp.status_code)
                return None
        except Exception as e:
            logger.warning(f"Google Patents XHR query failed for '{query_url_param}': {e}")
            self.circuit_breaker.record_failure(500)
            return None

    def parse_cluster_results(self, raw_data: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """Parses raw /xhr/query response into structured patent search result dictionaries."""
        results = []
        if not raw_data or "results" not in raw_data:
            return results

        clusters = raw_data.get("results", {}).get("cluster", [])
        for cluster in clusters:
            for item in cluster.get("result", []):
                patent = item.get("patent", {})
                patent_id = item.get("id", "")
                if patent_id.startswith("patent/"):
                    patent_id = patent_id.split("/")[1]

                title = _clean_html(patent.get("title"))
                snippet = _clean_html(patent.get("snippet"))
                assignee = patent.get("assignee")
                filing_date = patent.get("filing_date")
                grant_date = patent.get("grant_date")
                publication_date = patent.get("publication_date")
                thumbnail = patent.get("thumbnail")
                if thumbnail and not str(thumbnail).startswith("http"):
                    thumbnail = f"https://patentimages.storage.googleapis.com/{str(thumbnail).lstrip('/')}"

                results.append({
                    "id": patent_id,
                    "title": title,
                    "snippet": snippet,
                    "assignee": assignee,
                    "filing_date": filing_date,
                    "grant_date": grant_date,
                    "publication_date": publication_date,
                    "thumbnail_url": thumbnail,
                    "google_patents_url": f"https://patents.google.com/patent/{patent_id}/en",
                })
                if len(results) >= limit:
                    return results

        return results

    async def search_patents(self, query_url_or_params: str, limit: int = 10) -> Optional[Dict[str, Any]]:
        """Executes a search query via Google Patents public web gateway."""
        query_param = query_url_or_params.strip()
        if not query_param.startswith("q="):
            query_param = f"q={query_param}"

        data = await self.query_xhr(query_param)
        if not data:
            return None

        results = self.parse_cluster_results(data, limit=limit)
        total_num = data.get("results", {}).get("total_num_results", len(results))

        return {
            "total_num_results": total_num,
            "results": results,
        }

    async def advanced_search(
        self,
        query: str = "",
        assignee: Optional[str] = None,
        inventor: Optional[str] = None,
        cpc_code: Optional[str] = None,
        country_code: Optional[str] = None,
        before_date: Optional[str] = None,
        after_date: Optional[str] = None,
        limit: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """Executes an advanced filtered search via Google Patents web gateway."""
        params = []
        if query and query.strip():
            params.append(f"q={query.strip()}")

        if assignee and assignee.strip():
            params.append(f"assignee={assignee.strip()}")
        if inventor and inventor.strip():
            params.append(f"inventor={inventor.strip()}")
        if cpc_code and cpc_code.strip():
            params.append(f"cpc={cpc_code.strip().upper()}")
        if country_code and country_code.strip():
            params.append(f"country={country_code.strip().upper()}")
        if before_date and before_date.strip():
            clean_before = re.sub(r"[^0-9]", "", before_date)
            params.append(f"before={clean_before}")
        if after_date and after_date.strip():
            clean_after = re.sub(r"[^0-9]", "", after_date)
            params.append(f"after={clean_after}")

        if not params:
            params.append("q=")

        query_str = "&".join(params)
        data = await self.query_xhr(query_str)
        if not data:
            return None

        results = self.parse_cluster_results(data, limit=limit)
        total_num = data.get("results", {}).get("total_num_results", len(results))

        return {
            "total_num_results": total_num,
            "query_constructed": query_str,
            "results": results,
        }

    async def search_chemistry(
        self,
        smiles: str,
        mode: str = "EXACT",
        query: Optional[str] = None,
        limit: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """Executes a chemical structure search via Google Patents chemistry pipeline gateway."""
        mode_prefix = "chem:exact:"
        if mode.upper() == "SUBSTRUCTURE":
            mode_prefix = "chem:substructure:"
        elif mode.upper() == "SIMILARITY":
            mode_prefix = "chem:similar:"

        chem_token = f"{mode_prefix}{smiles.strip()}"
        full_query = f"{chem_token} {query}".strip() if query else chem_token
        query_str = f"q={full_query}"

        data = await self.query_xhr(query_str)
        if not data:
            return None

        results = self.parse_cluster_results(data, limit=limit)
        total_num = data.get("results", {}).get("total_num_results", len(results))

        return {
            "total_num_results": total_num,
            "chemistry_search": {
                "input": smiles,
                "mode": mode.upper(),
                "query_token": chem_token,
            },
            "results": results,
        }

    async def find_similar(
        self,
        patent_id: str,
        limit: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """Finds similar patents via Google Patents ScaM vector similarity web gateway."""
        clean_id = patent_id.replace("-", "").strip()
        query_str = f"q=similar:{clean_id}"

        data = await self.query_xhr(query_str)
        if not data:
            return None

        results = self.parse_cluster_results(data, limit=limit)
        total_num = data.get("results", {}).get("total_num_results", len(results))

        return {
            "source_patent": patent_id,
            "total_similar_found": total_num,
            "similar_patents": results,
        }
