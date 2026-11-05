"""Patent number normalization utilities."""

import logging
import re
from typing import Any, Dict, Optional
from .patents_http_client import PatentsHttpClient

logger = logging.getLogger(__name__)

# Regular expressions for patent number components
REGEX_CANONICAL = re.compile(r"^([A-Z]{2})-([A-Z0-9]+)-([A-Z0-9]+)$", re.IGNORECASE)
REGEX_COMPACT = re.compile(r"^([A-Z]{2})([0-9]{5,12})([A-Z][0-9]?)$", re.IGNORECASE)
REGEX_COUNTRY_NUM = re.compile(r"^([A-Z]{2})([0-9]{4,12})$", re.IGNORECASE)
REGEX_NUM_ONLY = re.compile(r"^([0-9]{5,12})$")


class PatentNormalizer:
    """Handles conversion between various patent identifier formats."""

    def __init__(self, http_client: Optional[PatentsHttpClient] = None):
        self.http_client = http_client or PatentsHttpClient()

    async def normalize(
        self,
        number: str,
        country: Optional[str] = None,
        patent_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Normalizes an input patent identifier to canonical DOCDB and Google Patents formats.

        Args:
            number: Ambiguous patent identifier (e.g. '10000000', 'US10000000', 'US-10000000-B2', 'EP 1234567').
            country: Optional country code hint (e.g. 'US', 'EP').
            patent_type: Optional document type hint (e.g. 'patent', 'application').

        Returns:
            Dict containing canonical_id, ucid, country, number, kind_code, and google_patents_url.
        """
        raw_clean = number.strip().replace(" ", "").replace("/", "").replace(":", "")

        # 1. Try Google Patents match API
        matches = await self.http_client.match_number(raw_clean, country=country, patent_type=patent_type)
        if not matches and country and not raw_clean.upper().startswith(country.upper()):
            # Retry with country prefix prepended (e.g. 'US10000000' if input was '10000000')
            matches = await self.http_client.match_number(f"{country.upper()}{raw_clean}", country=country, patent_type=patent_type)

        if matches:
            # If country filter provided, find the matching country
            selected = None
            if country:
                country_upper = country.upper()
                for m in matches:
                    if m.get("id", "").startswith(f"{country_upper}-") or m.get("ucid", "").startswith(country_upper):
                        selected = m
                        break
            if not selected:
                selected = matches[0]

            canon_id = selected.get("id")
            ucid = selected.get("ucid") or canon_id.replace("-", "")
            parsed = self._parse_canonical_id(canon_id)

            return {
                "backend_source": "GOOGLE_PATENTS_MATCH_API",
                "backend_service": "https://patents.google.com/api/match (Google Patents Official Normalizer Gateway)",
                "is_bigquery_search": False,
                "canonical_id": canon_id,
                "ucid": ucid,
                "raw_input": number,
                "country": parsed.get("country"),
                "number": parsed.get("number"),
                "kind_code": parsed.get("kind_code"),
                "google_patents_url": f"https://patents.google.com/patent/{ucid}/en",
                "all_matches": matches,
            }

        # 2. Heuristic fallback
        return self._heuristic_normalize(raw_clean, country=country)

    def _parse_canonical_id(self, canonical_id: str) -> Dict[str, str]:
        """Parses a canonical ID like 'US-10000000-B2' into components."""
        match = REGEX_CANONICAL.match(canonical_id)
        if match:
            return {
                "country": match.group(1).upper(),
                "number": match.group(2),
                "kind_code": match.group(3).upper(),
            }
        parts = canonical_id.split("-")
        if len(parts) == 3:
            return {"country": parts[0].upper(), "number": parts[1], "kind_code": parts[2].upper()}
        return {"country": "", "number": canonical_id, "kind_code": ""}

    def _heuristic_normalize(self, raw: str, country: Optional[str] = None) -> Dict[str, Any]:
        """Performs local heuristic parsing when the match API is unavailable."""
        raw_upper = raw.upper()

        # Check if already canonical (US-10000000-B2)
        match_canon = REGEX_CANONICAL.match(raw_upper)
        if match_canon:
            c, n, k = match_canon.group(1), match_canon.group(2), match_canon.group(3)
            ucid = f"{c}{n}{k}"
            return {
                "backend_source": "LOCAL_NORMALIZER_HEURISTIC",
                "backend_service": "Local DOCDB Normalizer Regex",
                "is_bigquery_search": False,
                "canonical_id": f"{c}-{n}-{k}",
                "ucid": ucid,
                "raw_input": raw,
                "country": c,
                "number": n,
                "kind_code": k,
                "google_patents_url": f"https://patents.google.com/patent/{ucid}/en",
            }

        # Check compact format (US10000000B2)
        match_compact = REGEX_COMPACT.match(raw_upper)
        if match_compact:
            c, n, k = match_compact.group(1), match_compact.group(2), match_compact.group(3)
            canon = f"{c}-{n}-{k}"
            return {
                "backend_source": "LOCAL_NORMALIZER_HEURISTIC",
                "backend_service": "Local DOCDB Normalizer Regex",
                "is_bigquery_search": False,
                "canonical_id": canon,
                "ucid": raw_upper,
                "raw_input": raw,
                "country": c,
                "number": n,
                "kind_code": k,
                "google_patents_url": f"https://patents.google.com/patent/{raw_upper}/en",
            }

        # Check country + number format (US10000000)
        match_cn = REGEX_COUNTRY_NUM.match(raw_upper)
        if match_cn:
            c, n = match_cn.group(1), match_cn.group(2)
            # Default to B2/A1 kind if not specified
            canon = f"{c}-{n}-B2" if len(n) <= 8 else f"{c}-{n}-A1"
            ucid = f"{c}{n}"
            return {
                "backend_source": "LOCAL_NORMALIZER_HEURISTIC",
                "backend_service": "Local DOCDB Normalizer Regex",
                "is_bigquery_search": False,
                "canonical_id": canon,
                "ucid": ucid,
                "raw_input": raw,
                "country": c,
                "number": n,
                "kind_code": "B2" if len(n) <= 8 else "A1",
                "google_patents_url": f"https://patents.google.com/patent/{ucid}/en",
            }

        # Check pure digits (10000000)
        match_num = REGEX_NUM_ONLY.match(raw)
        if match_num:
            n = match_num.group(1)
            c = (country or "US").upper()
            canon = f"{c}-{n}-B2" if len(n) <= 8 else f"{c}-{n}-A1"
            ucid = f"{c}{n}"
            return {
                "backend_source": "LOCAL_NORMALIZER_HEURISTIC",
                "backend_service": "Local DOCDB Normalizer Regex",
                "is_bigquery_search": False,
                "canonical_id": canon,
                "ucid": ucid,
                "raw_input": raw,
                "country": c,
                "number": n,
                "kind_code": "B2" if len(n) <= 8 else "A1",
                "google_patents_url": f"https://patents.google.com/patent/{ucid}/en",
            }

        # Fallback raw
        return {
            "backend_source": "LOCAL_NORMALIZER_HEURISTIC",
            "backend_service": "Local DOCDB Normalizer Regex",
            "is_bigquery_search": False,
            "canonical_id": raw_upper,
            "ucid": raw_upper.replace("-", ""),
            "raw_input": raw,
            "country": country or "",
            "number": raw,
            "kind_code": "",
            "google_patents_url": f"https://patents.google.com/patent/{raw_upper}/en",
        }
