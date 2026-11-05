"""BigQuery client for Google Patents public datasets."""

import logging
import os
import re
from typing import Any, Dict, List, Optional
from google.cloud import bigquery

logger = logging.getLogger(__name__)

DATASET_PUBLICATIONS = "patents-public-data.patents.publications"
DATASET_RESEARCH = "patents-public-data.google_patents_research.publications"
DATASET_CPC_DEF = "patents-public-data.cpc.definition"


def _format_date_int(d: Optional[int]) -> Optional[str]:
    """Formats an integer date like 20180619 to '2018-06-19'."""
    if not d or d == 0:
        return None
    s = str(d)
    if len(s) == 8:
        return f"{s[:4]}-{s[4:6]}-{s[6:]}"
    return s


def _parse_date_input(d_str: str) -> Optional[int]:
    """Parses date string ('YYYY-MM-DD' or 'YYYYMMDD' or 'YYYY') into integer YYYYMMDD."""
    if not d_str:
        return None
    cleaned = re.sub(r"[^0-9]", "", d_str)
    if len(cleaned) == 4:
        return int(f"{cleaned}0101")
    if len(cleaned) == 6:
        return int(f"{cleaned}01")
    if len(cleaned) >= 8:
        return int(cleaned[:8])
    return None


class BigQueryPatentsClient:
    """Handles all BigQuery interactions against Google Patents public datasets."""

    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT")
        self._client: Optional[bigquery.Client] = None

    @property
    def client(self) -> bigquery.Client:
        if self._client is None:
            self._client = bigquery.Client(project=self.project_id)
        return self._client

    def _candidate_pub_nums(self, pub_num: str) -> List[str]:
        """Returns a list of plausible formats for querying BigQuery publication_number."""
        if not pub_num:
            return []
        clean = pub_num.replace("-", "").strip().upper()
        candidates = [pub_num, clean]
        
        m_us = re.match(r"^US((?:19|20)\d{2})(\d+)([A-Z]\d?)$", clean)
        if m_us:
            year, seq, kind = m_us.group(1), m_us.group(2), m_us.group(3)
            padded = seq.zfill(7)
            unpadded = seq.lstrip("0")
            candidates.extend([
                f"US-{year}{seq}-{kind}",
                f"US-{year}{padded}-{kind}",
                f"US-{year}{unpadded}-{kind}",
                f"US{year}{padded}{kind}",
                f"US{year}{unpadded}{kind}",
            ])
        else:
            m_gen = re.match(r"^([A-Z]{2})([0-9A-Z]+?)([A-Z][0-9]?)$", clean)
            if m_gen:
                candidates.append(f"{m_gen.group(1)}-{m_gen.group(2)}-{m_gen.group(3)}")
                
        return list(dict.fromkeys(candidates))

    def get_patent_details(
        self,
        publication_number: str,
        include_description: bool = False,
        include_claims: bool = True,
        description_max_chars: int = 15000,
        claims_max_chars: int = 15000,
    ) -> Optional[Dict[str, Any]]:
        """Fetches full text and metadata for a given publication number."""
        query = f"""
        SELECT
            publication_number,
            application_number,
            country_code,
            kind_code,
            family_id,
            publication_date,
            filing_date,
            grant_date,
            priority_date,
            (SELECT text FROM UNNEST(title_localized) WHERE language = 'en' OR text IS NOT NULL LIMIT 1) as title,
            (SELECT text FROM UNNEST(abstract_localized) WHERE language = 'en' OR text IS NOT NULL LIMIT 1) as abstract,
            (SELECT text FROM UNNEST(claims_localized) WHERE language = 'en' OR text IS NOT NULL LIMIT 1) as claims,
            (SELECT text FROM UNNEST(description_localized) WHERE language = 'en' OR text IS NOT NULL LIMIT 1) as description,
            ARRAY(SELECT name FROM UNNEST(assignee_harmonized) WHERE name IS NOT NULL) as assignees,
            ARRAY(SELECT name FROM UNNEST(inventor_harmonized) WHERE name IS NOT NULL) as inventors,
            ARRAY(SELECT DISTINCT code FROM UNNEST(cpc) WHERE code IS NOT NULL) as cpc_codes,
            ARRAY(SELECT DISTINCT code FROM UNNEST(ipc) WHERE code IS NOT NULL) as ipc_codes
        FROM `{DATASET_PUBLICATIONS}`
        WHERE publication_number IN UNNEST(@pub_nums)
        LIMIT 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ArrayQueryParameter("pub_nums", "STRING", self._candidate_pub_nums(publication_number))]
        )
        rows = list(self.client.query(query, job_config=job_config).result())
        if not rows:
            return None

        row = dict(rows[0])
        ucid = publication_number.replace("-", "")

        claims_text = row.get("claims") if include_claims else None
        if claims_text and len(claims_text) > claims_max_chars:
            claims_text = claims_text[:claims_max_chars] + f"\n... [Truncated: {len(row.get('claims'))} total chars]"

        desc_text = row.get("description") if include_description else None
        if desc_text and len(desc_text) > description_max_chars:
            desc_text = desc_text[:description_max_chars] + f"\n... [Truncated: {len(row.get('description'))} total chars]"

        return {
            "publication_number": row.get("publication_number"),
            "ucid": ucid,
            "title": (row.get("title") or "").strip(),
            "abstract": (row.get("abstract") or "").strip(),
            "claims": claims_text,
            "description": desc_text,
            "country_code": row.get("country_code"),
            "kind_code": row.get("kind_code"),
            "application_number": row.get("application_number"),
            "family_id": row.get("family_id"),
            "publication_date": _format_date_int(row.get("publication_date")),
            "filing_date": _format_date_int(row.get("filing_date")),
            "grant_date": _format_date_int(row.get("grant_date")),
            "priority_date": _format_date_int(row.get("priority_date")),
            "assignees": row.get("assignees") or [],
            "inventors": row.get("inventors") or [],
            "cpc_codes": row.get("cpc_codes") or [],
            "ipc_codes": row.get("ipc_codes") or [],
            "google_patents_url": f"https://patents.google.com/patent/{ucid}/en",
        }

    def get_prior_art_timeline(self, publication_number: str) -> Optional[Dict[str, Any]]:
        """Extracts complete prior art timeline, legal key dates, NPL citations, and INPADOC family."""
        q1 = f"""
        SELECT
            publication_number,
            family_id,
            filing_date,
            publication_date,
            grant_date,
            priority_date,
            (SELECT text FROM UNNEST(title_localized) WHERE language = 'en' OR text IS NOT NULL LIMIT 1) as title,
            ARRAY(SELECT name FROM UNNEST(assignee_harmonized) WHERE name IS NOT NULL) as assignees,
            ARRAY(
                SELECT AS STRUCT publication_number, npl_text, category, type
                FROM UNNEST(citation)
                WHERE npl_text IS NOT NULL AND npl_text != ''
                LIMIT 25
            ) as npl_citations
        FROM `{DATASET_PUBLICATIONS}`
        WHERE publication_number IN UNNEST(@pub_nums)
        LIMIT 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ArrayQueryParameter("pub_nums", "STRING", self._candidate_pub_nums(publication_number))]
        )
        rows = list(self.client.query(q1, job_config=job_config).result())
        if not rows:
            return None

        row = dict(rows[0])
        family_id = row.get("family_id")
        npl_raw = row.get("npl_citations") or []

        formatted_npl = []
        for n in npl_raw:
            text = n.get("npl_text", "").strip()
            if text:
                formatted_npl.append({
                    "literature_text": text,
                    "category": n.get("category", ""),
                    "source": "Non-Patent Literature (Google Scholar / Scientific Literature)",
                })

        family_members = []
        if family_id:
            q_fam = f"""
            SELECT
                publication_number,
                country_code,
                publication_date,
                kind_code,
                (SELECT text FROM UNNEST(title_localized) WHERE language = 'en' OR text IS NOT NULL LIMIT 1) as title
            FROM `{DATASET_PUBLICATIONS}`
            WHERE family_id = @family_id
            ORDER BY publication_date ASC
            LIMIT 30
            """
            fam_config = bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("family_id", "STRING", family_id)]
            )
            for f in self.client.query(q_fam, job_config=fam_config).result():
                f_pub = f.get("publication_number")
                family_members.append({
                    "publication_number": f_pub,
                    "country_code": f.get("country_code"),
                    "kind_code": f.get("kind_code"),
                    "publication_date": _format_date_int(f.get("publication_date")),
                    "title": (f.get("title") or "").strip(),
                    "google_patents_url": f"https://patents.google.com/patent/{f_pub.replace('-', '')}/en" if f_pub else None,
                })

        timeline_events = []
        if row.get("priority_date"):
            timeline_events.append({"event": "Earliest Priority Date", "date": _format_date_int(row.get("priority_date"))})
        if row.get("filing_date"):
            timeline_events.append({"event": "Application Filing Date", "date": _format_date_int(row.get("filing_date"))})
        if row.get("publication_date"):
            timeline_events.append({"event": "Patent Publication Date", "date": _format_date_int(row.get("publication_date"))})
        if row.get("grant_date"):
            timeline_events.append({"event": "Patent Grant Date", "date": _format_date_int(row.get("grant_date"))})

        return {
            "publication_number": publication_number,
            "title": (row.get("title") or "").strip(),
            "assignees": row.get("assignees") or [],
            "family_id": family_id,
            "key_dates": {
                "priority_date": _format_date_int(row.get("priority_date")),
                "filing_date": _format_date_int(row.get("filing_date")),
                "publication_date": _format_date_int(row.get("publication_date")),
                "grant_date": _format_date_int(row.get("grant_date")),
            },
            "timeline": timeline_events,
            "inpadoc_family_members_count": len(family_members),
            "inpadoc_family_members": family_members,
            "non_patent_literature_prior_art_count": len(formatted_npl),
            "non_patent_literature_prior_art": formatted_npl,
        }

    def get_citations(
        self,
        publication_number: str,
        citation_type: str = "both",
        limit: int = 25,
    ) -> Dict[str, Any]:
        """Retrieves forward and/or backward citations for a patent including Non-Patent Literature."""
        citation_type = citation_type.lower()
        backward_citations = []
        forward_citations = []
        npl_citations = []

        if citation_type in ["backward", "both"]:
            q_back = f"""
            SELECT
                ARRAY(
                    SELECT AS STRUCT
                        c.publication_number,
                        c.npl_text,
                        c.category,
                        c.type
                    FROM UNNEST(citation) as c
                    WHERE (c.publication_number IS NOT NULL AND c.publication_number != '')
                       OR (c.npl_text IS NOT NULL AND c.npl_text != '')
                    LIMIT @limit
                ) as citations
            FROM `{DATASET_PUBLICATIONS}`
            WHERE publication_number IN UNNEST(@pub_nums)
            LIMIT 1
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ArrayQueryParameter("pub_nums", "STRING", self._candidate_pub_nums(publication_number)),
                    bigquery.ScalarQueryParameter("limit", "INT64", limit),
                ]
            )
            rows = list(self.client.query(q_back, job_config=job_config).result())
            if rows and rows[0].get("citations"):
                for c in rows[0]["citations"]:
                    cid = c.get("publication_number")
                    npl = c.get("npl_text")
                    if cid:
                        backward_citations.append({
                            "publication_number": cid,
                            "category": c.get("category", ""),
                            "type": c.get("type", ""),
                            "direction": "backward",
                            "google_patents_url": f"https://patents.google.com/patent/{cid.replace('-', '')}/en",
                        })
                    elif npl:
                        npl_citations.append({
                            "npl_text": npl.strip(),
                            "category": c.get("category", ""),
                            "source": "Google Scholar / Scientific Prior Art",
                        })

        if citation_type in ["forward", "both"]:
            q_fwd = f"""
            SELECT
                ARRAY(
                    SELECT AS STRUCT
                        cb.publication_number,
                        cb.category,
                        cb.type
                    FROM UNNEST(r.cited_by) as cb
                    WHERE cb.publication_number IS NOT NULL AND cb.publication_number != ''
                    LIMIT @limit
                ) as forward_citations
            FROM `{DATASET_RESEARCH}` r
            WHERE r.publication_number = @pub_num
            LIMIT 1
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("pub_num", "STRING", publication_number),
                    bigquery.ScalarQueryParameter("limit", "INT64", limit),
                ]
            )
            rows = list(self.client.query(q_fwd, job_config=job_config).result())
            if rows and rows[0].get("forward_citations"):
                for c in rows[0]["forward_citations"]:
                    cid = c.get("publication_number")
                    forward_citations.append({
                        "publication_number": cid,
                        "category": c.get("category", ""),
                        "type": c.get("type", ""),
                        "direction": "forward",
                        "google_patents_url": f"https://patents.google.com/patent/{cid.replace('-', '')}/en" if cid else None,
                    })

        return {
            "publication_number": publication_number,
            "backward_count": len(backward_citations),
            "forward_count": len(forward_citations),
            "npl_count": len(npl_citations),
            "backward_citations": backward_citations,
            "forward_citations": forward_citations,
            "non_patent_literature_citations": npl_citations,
        }

    def find_similar_patents(
        self,
        publication_number: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Finds technically related patents based on Google's ScaM similarity models."""
        q_sim = f"""
        SELECT ARRAY(
            SELECT s.publication_number
            FROM UNNEST(r.similar) as s
            WHERE s.publication_number IS NOT NULL AND s.publication_number != ''
            LIMIT @limit
        ) as sim_pubs
        FROM `{DATASET_RESEARCH}` r
        WHERE r.publication_number = @pub_num
        LIMIT 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("pub_num", "STRING", publication_number),
                bigquery.ScalarQueryParameter("limit", "INT64", limit),
            ]
        )
        rows = list(self.client.query(q_sim, job_config=job_config).result())
        sim_pubs = rows[0]["sim_pubs"] if rows and rows[0].get("sim_pubs") else []

        if not sim_pubs:
            return self._find_similar_by_cpc(publication_number, limit=limit)

        q_details = f"""
        SELECT
            p.publication_number,
            (SELECT text FROM UNNEST(p.title_localized) WHERE language = 'en' OR text IS NOT NULL LIMIT 1) as title,
            (SELECT text FROM UNNEST(p.abstract_localized) WHERE language = 'en' OR text IS NOT NULL LIMIT 1) as abstract,
            ARRAY(SELECT name FROM UNNEST(p.assignee_harmonized) WHERE name IS NOT NULL) as assignees,
            ARRAY(SELECT DISTINCT code FROM UNNEST(p.cpc) WHERE code IS NOT NULL LIMIT 3) as cpc_codes,
            p.publication_date
        FROM `{DATASET_PUBLICATIONS}` p
        WHERE p.publication_number IN UNNEST(@sim_pubs)
        """
        job_details_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ArrayQueryParameter("sim_pubs", "STRING", sim_pubs)]
        )
        detail_rows = {
            r["publication_number"]: r
            for r in self.client.query(q_details, job_config=job_details_config).result()
        }

        results = []
        for idx, pub_id in enumerate(sim_pubs):
            d = detail_rows.get(pub_id)
            title = (d["title"] if d else "") or ""
            abstract = (d["abstract"] if d else "") or ""
            assignees = (d["assignees"] if d else []) or []
            cpc_codes = (d["cpc_codes"] if d else []) or []
            pub_date = _format_date_int(d["publication_date"]) if d else None
            ucid = pub_id.replace("-", "")

            results.append({
                "rank": idx + 1,
                "publication_number": pub_id,
                "ucid": ucid,
                "title": title.strip(),
                "snippet": abstract[:300].strip() + ("..." if len(abstract) > 300 else ""),
                "assignees": assignees,
                "cpc_codes": cpc_codes,
                "publication_date": pub_date,
                "google_patents_url": f"https://patents.google.com/patent/{ucid}/en",
            })

        return results

    def _find_similar_by_cpc(self, publication_number: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Fallback to retrieve similar patents by CPC classification."""
        q = f"""
        WITH target_cpc AS (
            SELECT code FROM `{DATASET_PUBLICATIONS}`, UNNEST(cpc) as code
            WHERE publication_number IN UNNEST(@pub_nums)
            LIMIT 3
        )
        SELECT
            p.publication_number,
            (SELECT text FROM UNNEST(p.title_localized) WHERE language = 'en' OR text IS NOT NULL LIMIT 1) as title,
            (SELECT text FROM UNNEST(p.abstract_localized) WHERE language = 'en' OR text IS NOT NULL LIMIT 1) as abstract,
            ARRAY(SELECT name FROM UNNEST(p.assignee_harmonized) WHERE name IS NOT NULL) as assignees,
            ARRAY(SELECT DISTINCT code FROM UNNEST(p.cpc) WHERE code IS NOT NULL LIMIT 3) as cpc_codes,
            p.publication_date
        FROM `{DATASET_PUBLICATIONS}` p, UNNEST(p.cpc) as c
        WHERE c.code IN (SELECT code FROM target_cpc)
          AND p.publication_number NOT IN UNNEST(@pub_nums)
        LIMIT @limit
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ArrayQueryParameter("pub_nums", "STRING", self._candidate_pub_nums(publication_number)),
                bigquery.ScalarQueryParameter("limit", "INT64", limit),
            ]
        )
        rows = list(self.client.query(q, job_config=job_config).result())
        results = []
        for idx, r in enumerate(rows):
            pub_id = r.get("publication_number")
            ucid = pub_id.replace("-", "") if pub_id else ""
            abstract = (r.get("abstract") or "").strip()
            results.append({
                "rank": idx + 1,
                "publication_number": pub_id,
                "ucid": ucid,
                "title": (r.get("title") or "").strip(),
                "snippet": abstract[:300] + ("..." if len(abstract) > 300 else ""),
                "assignees": r.get("assignees") or [],
                "cpc_codes": r.get("cpc_codes") or [],
                "publication_date": _format_date_int(r.get("publication_date")),
                "google_patents_url": f"https://patents.google.com/patent/{ucid}/en",
            })
        return results

    def search_patents(
        self,
        query: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        assignee: Optional[str] = None,
        inventor: Optional[str] = None,
        status: Optional[str] = None,
        country: Optional[str] = "US",
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Searches patents across title, abstract, and claims with date and entity filters."""
        limit = min(max(1, limit), 50)
        conditions = []
        params = [bigquery.ScalarQueryParameter("limit", "INT64", limit)]

        if country:
            conditions.append("country_code = @country")
            params.append(bigquery.ScalarQueryParameter("country", "STRING", country.strip().upper()))

        if query and query.strip():
            clean_tokens = " ".join(re.findall(r"[a-zA-Z0-9]+", query.strip()))
            if clean_tokens:
                conditions.append("(SEARCH(title_localized, @q) OR SEARCH(abstract_localized, @q))")
                params.append(bigquery.ScalarQueryParameter("q", "STRING", clean_tokens))

        start_int = _parse_date_input(start_date) if start_date else None
        if start_int:
            conditions.append("publication_date >= @start_date")
            params.append(bigquery.ScalarQueryParameter("start_date", "INT64", start_int))

        end_int = _parse_date_input(end_date) if end_date else None
        if end_int:
            conditions.append("publication_date <= @end_date")
            params.append(bigquery.ScalarQueryParameter("end_date", "INT64", end_int))

        if assignee and assignee.strip():
            ass_tokens = [t.lower() for t in re.findall(r"[a-zA-Z0-9]+", assignee.strip()) if len(t) > 1]
            if ass_tokens:
                sub_conds = []
                for idx, tok in enumerate(ass_tokens):
                    p_name = f"ass_tok_{idx}"
                    sub_conds.append(f"LOWER(a.name) LIKE @{p_name}")
                    params.append(bigquery.ScalarQueryParameter(p_name, "STRING", f"%{tok}%"))
                conditions.append(f"EXISTS (SELECT 1 FROM UNNEST(assignee_harmonized) as a WHERE {' AND '.join(sub_conds)})")
            else:
                conditions.append("EXISTS (SELECT 1 FROM UNNEST(assignee_harmonized) as a WHERE LOWER(a.name) LIKE LOWER(@assignee))")
                params.append(bigquery.ScalarQueryParameter("assignee", "STRING", f"%{assignee.strip()}%"))

        if inventor and inventor.strip():
            inv_tokens = [t.lower() for t in re.findall(r"[a-zA-Z0-9]+", inventor.strip()) if len(t) > 1]
            if inv_tokens:
                sub_conds = []
                for idx, tok in enumerate(inv_tokens):
                    p_name = f"inv_tok_{idx}"
                    sub_conds.append(f"LOWER(i.name) LIKE @{p_name}")
                    params.append(bigquery.ScalarQueryParameter(p_name, "STRING", f"%{tok}%"))
                conditions.append(f"EXISTS (SELECT 1 FROM UNNEST(inventor_harmonized) as i WHERE {' AND '.join(sub_conds)})")
            else:
                conditions.append("EXISTS (SELECT 1 FROM UNNEST(inventor_harmonized) as i WHERE LOWER(i.name) LIKE LOWER(@inventor))")
                params.append(bigquery.ScalarQueryParameter("inventor", "STRING", f"%{inventor.strip()}%"))

        if status and status.strip():
            st = status.strip().upper()
            if "GRANT" in st or st == "PATENT":
                conditions.append("kind_code LIKE 'B%'")
            elif "APP" in st:
                conditions.append("kind_code LIKE 'A%'")

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        sql = f"""
        SELECT
            publication_number,
            country_code,
            kind_code,
            publication_date,
            (SELECT text FROM UNNEST(title_localized) WHERE language = 'en' OR text IS NOT NULL LIMIT 1) as title,
            (SELECT text FROM UNNEST(abstract_localized) WHERE language = 'en' OR text IS NOT NULL LIMIT 1) as abstract,
            ARRAY(SELECT name FROM UNNEST(assignee_harmonized) WHERE name IS NOT NULL) as assignees,
            ARRAY(SELECT name FROM UNNEST(inventor_harmonized) WHERE name IS NOT NULL) as inventors,
            ARRAY(SELECT DISTINCT code FROM UNNEST(cpc) WHERE code IS NOT NULL LIMIT 5) as cpc_codes
        FROM `{DATASET_PUBLICATIONS}`
        WHERE {where_clause}
        ORDER BY publication_date DESC
        LIMIT @limit
        """
        job_config = bigquery.QueryJobConfig(query_parameters=params)
        rows = list(self.client.query(sql, job_config=job_config).result())

        results = []
        for r in rows:
            pub_id = r.get("publication_number")
            ucid = pub_id.replace("-", "") if pub_id else ""
            abstract = (r.get("abstract") or "").strip()
            results.append({
                "publication_number": pub_id,
                "ucid": ucid,
                "title": (r.get("title") or "").strip(),
                "snippet": abstract[:350] + ("..." if len(abstract) > 350 else ""),
                "publication_date": _format_date_int(r.get("publication_date")),
                "country_code": r.get("country_code"),
                "kind_code": r.get("kind_code"),
                "assignees": r.get("assignees") or [],
                "inventors": r.get("inventors") or [],
                "cpc_codes": r.get("cpc_codes") or [],
                "google_patents_url": f"https://patents.google.com/patent/{ucid}/en",
            })
        return results

    def advanced_patent_search(
        self,
        query: Optional[str] = None,
        cpc_code: Optional[str] = None,
        ipc_code: Optional[str] = None,
        country_code: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        assignee: Optional[str] = None,
        inventor: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Filters patents by CPC/IPC classification codes, jurisdiction, and keywords."""
        limit = min(max(1, limit), 50)
        conditions = []
        params = [bigquery.ScalarQueryParameter("limit", "INT64", limit)]

        if country_code and country_code.strip():
            conditions.append("country_code = @country")
            params.append(bigquery.ScalarQueryParameter("country", "STRING", country_code.strip().upper()))

        if cpc_code and cpc_code.strip():
            cpc_clean = cpc_code.strip().replace(" ", "").upper()
            conditions.append("EXISTS (SELECT 1 FROM UNNEST(cpc) as c WHERE c.code LIKE @cpc_pattern)")
            params.append(bigquery.ScalarQueryParameter("cpc_pattern", "STRING", f"{cpc_clean}%"))

        if ipc_code and ipc_code.strip():
            ipc_clean = ipc_code.strip().replace(" ", "").upper()
            conditions.append("EXISTS (SELECT 1 FROM UNNEST(ipc) as i WHERE i.code LIKE @ipc_pattern)")
            params.append(bigquery.ScalarQueryParameter("ipc_pattern", "STRING", f"{ipc_clean}%"))

        if query and query.strip():
            clean_tokens = " ".join(re.findall(r"[a-zA-Z0-9]+", query.strip()))
            if clean_tokens:
                conditions.append("(SEARCH(title_localized, @q) OR SEARCH(abstract_localized, @q))")
                params.append(bigquery.ScalarQueryParameter("q", "STRING", clean_tokens))

        start_int = _parse_date_input(start_date) if start_date else None
        if start_int:
            conditions.append("publication_date >= @start_date")
            params.append(bigquery.ScalarQueryParameter("start_date", "INT64", start_int))

        end_int = _parse_date_input(end_date) if end_date else None
        if end_int:
            conditions.append("publication_date <= @end_date")
            params.append(bigquery.ScalarQueryParameter("end_date", "INT64", end_int))

        if assignee and assignee.strip():
            ass_tokens = [t.lower() for t in re.findall(r"[a-zA-Z0-9]+", assignee.strip()) if len(t) > 1]
            if ass_tokens:
                sub_conds = []
                for idx, tok in enumerate(ass_tokens):
                    p_name = f"adv_ass_tok_{idx}"
                    sub_conds.append(f"LOWER(a.name) LIKE @{p_name}")
                    params.append(bigquery.ScalarQueryParameter(p_name, "STRING", f"%{tok}%"))
                conditions.append(f"EXISTS (SELECT 1 FROM UNNEST(assignee_harmonized) as a WHERE {' AND '.join(sub_conds)})")
            else:
                conditions.append("EXISTS (SELECT 1 FROM UNNEST(assignee_harmonized) as a WHERE LOWER(a.name) LIKE LOWER(@assignee))")
                params.append(bigquery.ScalarQueryParameter("assignee", "STRING", f"%{assignee.strip()}%"))

        if inventor and inventor.strip():
            inv_tokens = [t.lower() for t in re.findall(r"[a-zA-Z0-9]+", inventor.strip()) if len(t) > 1]
            if inv_tokens:
                sub_conds = []
                for idx, tok in enumerate(inv_tokens):
                    p_name = f"adv_inv_tok_{idx}"
                    sub_conds.append(f"LOWER(i.name) LIKE @{p_name}")
                    params.append(bigquery.ScalarQueryParameter(p_name, "STRING", f"%{tok}%"))
                conditions.append(f"EXISTS (SELECT 1 FROM UNNEST(inventor_harmonized) as i WHERE {' AND '.join(sub_conds)})")
            else:
                conditions.append("EXISTS (SELECT 1 FROM UNNEST(inventor_harmonized) as i WHERE LOWER(i.name) LIKE LOWER(@inventor))")
                params.append(bigquery.ScalarQueryParameter("inventor", "STRING", f"%{inventor.strip()}%"))

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        sql = f"""
        SELECT
            publication_number,
            country_code,
            kind_code,
            publication_date,
            (SELECT text FROM UNNEST(title_localized) WHERE language = 'en' OR text IS NOT NULL LIMIT 1) as title,
            (SELECT text FROM UNNEST(abstract_localized) WHERE language = 'en' OR text IS NOT NULL LIMIT 1) as abstract,
            ARRAY(SELECT name FROM UNNEST(assignee_harmonized) WHERE name IS NOT NULL) as assignees,
            ARRAY(SELECT name FROM UNNEST(inventor_harmonized) WHERE name IS NOT NULL) as inventors,
            ARRAY(SELECT DISTINCT code FROM UNNEST(cpc) WHERE code IS NOT NULL LIMIT 5) as cpc_codes,
            ARRAY(SELECT DISTINCT code FROM UNNEST(ipc) WHERE code IS NOT NULL LIMIT 5) as ipc_codes
        FROM `{DATASET_PUBLICATIONS}`
        WHERE {where_clause}
        ORDER BY publication_date DESC
        LIMIT @limit
        """
        job_config = bigquery.QueryJobConfig(query_parameters=params)
        rows = list(self.client.query(sql, job_config=job_config).result())

        results = []
        for r in rows:
            pub_id = r.get("publication_number")
            ucid = pub_id.replace("-", "") if pub_id else ""
            abstract = (r.get("abstract") or "").strip()
            results.append({
                "publication_number": pub_id,
                "ucid": ucid,
                "title": (r.get("title") or "").strip(),
                "snippet": abstract[:350] + ("..." if len(abstract) > 350 else ""),
                "publication_date": _format_date_int(r.get("publication_date")),
                "country_code": r.get("country_code"),
                "kind_code": r.get("kind_code"),
                "assignees": r.get("assignees") or [],
                "inventors": r.get("inventors") or [],
                "cpc_codes": r.get("cpc_codes") or [],
                "ipc_codes": r.get("ipc_codes") or [],
                "google_patents_url": f"https://patents.google.com/patent/{ucid}/en",
            })
        return results

    def lookup_classification_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Retrieves definition and hierarchy for a CPC or IPC classification code."""
        clean_code = code.strip().replace(" ", "").upper()

        query = f"""
        SELECT symbol, titleFull, titlePart, definition, parents, level, status
        FROM `{DATASET_CPC_DEF}`
        WHERE symbol = @code OR symbol = @code_slash
        LIMIT 1
        """
        slash_variant = clean_code
        if "/" not in clean_code and len(clean_code) > 4:
            slash_variant = f"{clean_code[:4]}/{clean_code[4:]}"

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("code", "STRING", clean_code),
                bigquery.ScalarQueryParameter("code_slash", "STRING", slash_variant),
            ]
        )
        rows = list(self.client.query(query, job_config=job_config).result())
        if not rows:
            query_prefix = f"""
            SELECT symbol, titleFull, titlePart, definition, parents, level, status
            FROM `{DATASET_CPC_DEF}`
            WHERE symbol LIKE @code_prefix
            ORDER BY LENGTH(symbol) ASC
            LIMIT 1
            """
            job_prefix_config = bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("code_prefix", "STRING", f"{clean_code[:4]}%")]
            )
            rows = list(self.client.query(query_prefix, job_config=job_prefix_config).result())

        if not rows:
            return None

        row = dict(rows[0])
        title_full = row.get("titleFull") or ""
        title_part = row.get("titlePart")
        definition = row.get("definition")
        return {
            "backend_source": "BIGQUERY_SEARCH",
            "backend_service": "BigQuery: patents-public-data.cpc.definition (Official CPC/IPC Classification Hierarchy)",
            "is_bigquery_search": True,
            "symbol": row.get("symbol"),
            "title": title_full or (list(title_part)[0] if title_part else ""),
            "title_full": title_full,
            "title_parts": list(title_part) if title_part is not None else [],
            "definitions": list(definition) if definition is not None else [],
            "parents": row.get("parents"),
            "level": row.get("level"),
            "status": row.get("status"),
            "google_patents_cpc_url": f"https://patents.google.com/?q={row.get('symbol')}",
        }
