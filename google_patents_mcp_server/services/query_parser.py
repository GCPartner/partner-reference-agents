"""Query understanding and parsing service for Google Patents MCP Server."""

import logging
import re
import urllib.parse
from typing import Any, Dict, Optional
from .normalizer import PatentNormalizer

logger = logging.getLogger(__name__)

# Patterns for identifying classification codes (e.g., G06N, G06N3/08, H04L)
REGEX_CPC = re.compile(r"^[A-HY]\d{2}[A-Z](\s*\d+/\d+)?$", re.IGNORECASE)


class PatentQueryParser:
    """Parses freeform queries into structured search parameters and actions."""

    def __init__(self, normalizer: Optional[PatentNormalizer] = None):
        self.normalizer = normalizer or PatentNormalizer()

    async def parse(self, query: str) -> Dict[str, Any]:
        """Analyzes a freeform query string to identify intent, entities, and canonical URLs.

        Args:
            query: Freeform input text (e.g., 'US8000000B2', 'autonomous vehicle assignee:Waymo', 'similar:US8000000').

        Returns:
            Dict containing query interpretation, flags, entities, canonical query_url, and recommended action.
        """
        raw = query.strip()

        # 1. Check if similarity query (e.g. "similar:US8000000B2" or "similar to US10000000")
        sim_match = re.search(r"(?:similar\s*:\s*|similar\s+to\s+)([A-Z0-9\-]+)", raw, re.IGNORECASE)
        if sim_match:
            target_id = sim_match.group(1)
            norm = await self.normalizer.normalize(target_id)
            canon = norm.get("canonical_id") or target_id
            return {
                "backend_source": "GOOGLE_PATENTS_MATCH_API_AND_LOCAL_PARSER",
                "backend_service": "https://patents.google.com/api/match & Local Parser",
                "is_bigquery_search": False,
                "raw_query": raw,
                "is_patent_number_search": False,
                "is_similarity_search": True,
                "is_classification_search": False,
                "target_patent_id": canon,
                "recommended_tool": "find_similar_patents",
                "query_url": f"q=similar:{norm.get('ucid') or canon}",
                "description": f"Similarity search for patent {canon}",
            }

        # 2. Check if patent number search
        # Quick syntax check
        norm = await self.normalizer.normalize(raw)
        if norm.get("canonical_id") and norm.get("all_matches"):
            # Strong match from match API
            canon_id = norm["canonical_id"]
            ucid = norm.get("ucid") or canon_id.replace("-", "")
            return {
                "backend_source": "GOOGLE_PATENTS_MATCH_API",
                "backend_service": "https://patents.google.com/api/match (Google Patents Official Normalizer Gateway)",
                "is_bigquery_search": False,
                "raw_query": raw,
                "is_patent_number_search": True,
                "is_similarity_search": False,
                "is_classification_search": False,
                "patent_id": canon_id,
                "ucid": ucid,
                "recommended_tool": "get_patent_details",
                "direct_patent_url": f"/patent/{ucid}/en",
                "google_patents_url": f"https://patents.google.com/patent/{ucid}/en",
                "description": f"Direct document lookup for patent {canon_id}",
            }

        # 3. Check if classification code (CPC / IPC)
        clean_cpc = raw.replace(" ", "").upper()
        if REGEX_CPC.match(clean_cpc):
            return {
                "backend_source": "LOCAL_PARSER",
                "backend_service": "Local Classification Tokenizer",
                "is_bigquery_search": False,
                "raw_query": raw,
                "is_patent_number_search": False,
                "is_similarity_search": False,
                "is_classification_search": True,
                "classification_code": clean_cpc,
                "recommended_tool": "advanced_patent_search",
                "query_url": f"q={clean_cpc}",
                "description": f"Classification code search for {clean_cpc}",
            }

        # 4. Extract entities and operators from keyword search (e.g. assignee:Waymo, inventor:..., after:2020)
        entities: Dict[str, Any] = {}
        keywords = raw

        # Extract assignee: (assignee:X or "by assignee X" or "assigned to X")
        assignee_match = re.search(r'(?:assignee:\s*|assigned\s+to\s+|assignee\s+is\s+)(?:"([^"]+)"|([a-zA-Z0-9\s,\.\-]+?)(?=\s+(?:inventor|by|after|before|country|$)))', keywords, re.IGNORECASE)
        if assignee_match:
            val = (assignee_match.group(1) or assignee_match.group(2) or "").strip()
            if val:
                entities["assignee"] = val
                keywords = keywords[:assignee_match.start()] + " " + keywords[assignee_match.end():]
                keywords = keywords.strip()

        # Extract inventor: (inventor:X or "by inventor X" or "invented by X" or "inventor is X")
        inventor_match = re.search(r'(?:inventor:\s*|invented\s+by\s+|by\s+inventor\s+|inventor\s+is\s+)(?:"([^"]+)"|([a-zA-Z0-9\s,\.\-]+?)(?=\s+(?:assignee|after|before|country|$)))', keywords, re.IGNORECASE)
        if inventor_match:
            val = (inventor_match.group(1) or inventor_match.group(2) or "").strip()
            if val:
                entities["inventor"] = val
                keywords = keywords[:inventor_match.start()] + " " + keywords[inventor_match.end():]
                keywords = keywords.strip()

        # Extract dates (after:, before:)
        after_match = re.search(r'after:([0-9\-]+)', keywords, re.IGNORECASE)
        if after_match:
            entities["start_date"] = after_match.group(1)
            keywords = keywords.replace(after_match.group(0), "").strip()

        before_match = re.search(r'before:([0-9\-]+)', keywords, re.IGNORECASE)
        if before_match:
            entities["end_date"] = before_match.group(1)
            keywords = keywords.replace(before_match.group(0), "").strip()

        # Extract country (country:US)
        country_match = re.search(r'country:([A-Z]{2})', keywords, re.IGNORECASE)
        if country_match:
            entities["country"] = country_match.group(1).upper()
            keywords = keywords.replace(country_match.group(0), "").strip()

        entities["keywords"] = keywords

        # Build canonical query_url string
        query_params = []
        if keywords:
            query_params.append(f"q={urllib.parse.quote_plus(keywords)}")
        if "assignee" in entities:
            query_params.append(f"assignee={urllib.parse.quote_plus(entities['assignee'])}")
        if "inventor" in entities:
            query_params.append(f"inventor={urllib.parse.quote_plus(entities['inventor'])}")
        if "start_date" in entities:
            query_params.append(f"after={entities['start_date']}")
        if "end_date" in entities:
            query_params.append(f"before={entities['end_date']}")
        if "country" in entities:
            query_params.append(f"country={entities['country']}")

        query_url = "&".join(query_params)

        return {
            "backend_source": "LOCAL_PARSER",
            "backend_service": "Local Entity & Measure Tokenizer",
            "is_bigquery_search": False,
            "raw_query": raw,
            "is_patent_number_search": False,
            "is_similarity_search": False,
            "is_classification_search": False,
            "entities": entities,
            "query_url": query_url,
            "recommended_tool": "search_patents",
            "description": f"Keyword and entity search for '{keywords or raw}'",
        }
