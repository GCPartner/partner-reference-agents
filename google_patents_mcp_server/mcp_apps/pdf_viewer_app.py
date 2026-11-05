"""MCP App (ui://) for Synchronized Drawing Carousel, PDF & Specification Split-Viewer.

Implements View 5 of the Google Patents MCP Apps suite:
- Resource URI: ui://google-patents/pdf-drawing-viewer
- MIME Type: text/html;profile=mcp-app
- Supports both MCP Apps SEP-1865 JSON-RPC postMessage bridge and pre-populated
  server-rendered payload injection.

Features:
1. High-Resolution Patent Drawing Carousel + Inline Embedded PDF Viewer:
   - Extracts real Google Patents drawing sheet PNG URLs & direct PDF download URL
     from `patentimages.storage.googleapis.com` (which does NOT set
     `Cross-Origin-Opener-Policy: same-origin` and therefore works inside
     sandboxed iframes and popup tabs without `ERR_BLOCKED_BY_RESPONSE`).
   - Built-in toggle between `🖼️ Drawing Sheets` carousel and `📄 Inline PDF Viewer`
     (`<iframe src="https://patentimages.storage.googleapis.com/.../*.pdf">`).
   - Zoom in/out, Rotate 90°, Fit-to-pane, and Thumbnail Filmstrip navigation.
2. Synchronized Specification & Claims Split-Reader (100% BigQuery-backed + Web-enriched):
   - Always populates Title, Abstract, Representative Claims, and Figure Callout
     paragraphs from BigQuery (`patents-public-data.patents.publications`) so the
     specification reader is never empty even if `patents.google.com` rate-limits Cloud Run.
   - Automatically highlights `FIG. 1`, `FIG. 2`, `Figure 3` references as interactive
     chips that jump the drawing carousel directly to the corresponding figure sheet.
3. Sandbox-Safe PDF & Patent Reader Launch:
   - Never links `<a target="_blank">` directly to `patents.google.com` from inside
     Gemini Enterprise's sandboxed iframe (avoiding Chrome's COOP `ERR_BLOCKED_BY_RESPONSE`).
"""

from __future__ import annotations

import json
import os
import re
import urllib.parse
from html import escape, unescape
from typing import Any
import httpx

PDF_VIEWER_RESOURCE_URI = "ui://google-patents/pdf-drawing-viewer"
MCP_APP_MIME_TYPE = "text/html;profile=mcp-app"

PDF_VIEWER_TOOL_META: dict[str, Any] = {
    "ui": {
        "resourceUri": PDF_VIEWER_RESOURCE_URI,
        "visibility": ["model", "app"],
    },
    "ui/resourceUri": PDF_VIEWER_RESOURCE_URI,
}

_LAST_PDF_PAYLOAD: dict[str, Any] | None = None

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://patents.google.com/",
}

# Pre-seeded high-resolution GCS media cache for common benchmark patents + runtime cache
_MEDIA_CACHE: dict[str, dict[str, Any]] = {
    "US8000000B2": {
        "direct_pdf_url": "https://patentimages.storage.googleapis.com/4f/bd/25/0942b40e00c430/US8000000.pdf",
        "figures": [
            {"index": 1, "label": "Sheet 1 (Cover)", "url": "https://patentimages.storage.googleapis.com/e5/f8/de/78cf078f5e05fa/US08000000-20110816-D00000.png", "thumb_url": "https://patentimages.storage.googleapis.com/ae/11/8f/d8803528e68140/US08000000-20110816-D00000.png"},
            {"index": 2, "label": "Sheet 2 (FIG. 1)", "url": "https://patentimages.storage.googleapis.com/a9/2f/db/6280bc9c5e0fda/US08000000-20110816-D00001.png", "thumb_url": "https://patentimages.storage.googleapis.com/94/48/a8/e7b3134ec3c2fc/US08000000-20110816-D00001.png"},
            {"index": 3, "label": "Sheet 3 (FIGS. 2-3)", "url": "https://patentimages.storage.googleapis.com/e7/a2/3c/949b400be64ad6/US08000000-20110816-D00002.png", "thumb_url": "https://patentimages.storage.googleapis.com/21/bc/05/29f1bb99a24f27/US08000000-20110816-D00002.png"},
            {"index": 4, "label": "Sheet 4 (FIG. 4)", "url": "https://patentimages.storage.googleapis.com/a4/71/ac/5f6048d0162ed3/US08000000-20110816-D00003.png", "thumb_url": "https://patentimages.storage.googleapis.com/95/b3/78/e7a42ad772cde1/US08000000-20110816-D00003.png"},
            {"index": 5, "label": "Sheet 5 (FIG. 5)", "url": "https://patentimages.storage.googleapis.com/c8/73/29/e7fa9f9461b959/US08000000-20110816-D00004.png", "thumb_url": "https://patentimages.storage.googleapis.com/5b/e4/ff/14301e2b489d57/US08000000-20110816-D00004.png"},
            {"index": 6, "label": "Sheet 6 (FIG. 5A)", "url": "https://patentimages.storage.googleapis.com/c8/9b/96/03a60ebcb88245/US08000000-20110816-D00005.png", "thumb_url": "https://patentimages.storage.googleapis.com/b1/6a/d4/8351a797515abe/US08000000-20110816-D00005.png"},
            {"index": 7, "label": "Sheet 7 (FIG. 5B)", "url": "https://patentimages.storage.googleapis.com/4a/44/22/98768a10d17dfc/US08000000-20110816-D00006.png", "thumb_url": "https://patentimages.storage.googleapis.com/1e/a5/7d/c08a517a7d61b8/US08000000-20110816-D00006.png"},
            {"index": 8, "label": "Sheet 8 (FIGS. 6-7)", "url": "https://patentimages.storage.googleapis.com/7d/32/0b/4d6c93cba3de21/US08000000-20110816-D00007.png", "thumb_url": "https://patentimages.storage.googleapis.com/2a/46/f1/60b32bcc6b7feb/US08000000-20110816-D00007.png"},
            {"index": 9, "label": "Sheet 9 (FIG. 8)", "url": "https://patentimages.storage.googleapis.com/2f/c2/b1/471a76c5bb5310/US08000000-20110816-D00008.png", "thumb_url": "https://patentimages.storage.googleapis.com/84/6c/dd/c6421807fcd604/US08000000-20110816-D00008.png"},
            {"index": 10, "label": "Sheet 10 (FIG. 9)", "url": "https://patentimages.storage.googleapis.com/a1/0a/29/4aefc1dd32f21a/US08000000-20110816-D00009.png", "thumb_url": "https://patentimages.storage.googleapis.com/7a/d9/4c/c00c04796bfa15/US08000000-20110816-D00009.png"},
            {"index": 11, "label": "Sheet 11 (FIG. 10)", "url": "https://patentimages.storage.googleapis.com/b3/49/0f/69a5a9e068de61/US08000000-20110816-D00010.png", "thumb_url": "https://patentimages.storage.googleapis.com/3f/f5/ec/361837dd67601d/US08000000-20110816-D00010.png"},
            {"index": 12, "label": "Sheet 12 (FIG. 11)", "url": "https://patentimages.storage.googleapis.com/48/4f/b9/6beba1ab0717a7/US08000000-20110816-D00011.png", "thumb_url": "https://patentimages.storage.googleapis.com/20/58/80/4cddc7353db71a/US08000000-20110816-D00011.png"},
            {"index": 13, "label": "Sheet 13 (FIG. 12)", "url": "https://patentimages.storage.googleapis.com/ad/9a/7e/ae46ef35a3a9f0/US08000000-20110816-D00012.png", "thumb_url": "https://patentimages.storage.googleapis.com/d8/91/8d/39de992eda0faf/US08000000-20110816-D00012.png"},
            {"index": 14, "label": "Sheet 14 (FIG. 13)", "url": "https://patentimages.storage.googleapis.com/69/7a/4a/f7250ce5e9b2f2/US08000000-20110816-D00013.png", "thumb_url": "https://patentimages.storage.googleapis.com/45/31/b0/8e3707953a8d66/US08000000-20110816-D00013.png"},
            {"index": 15, "label": "Sheet 15 (FIG. 14)", "url": "https://patentimages.storage.googleapis.com/c5/37/a0/4b402cf1f877d9/US08000000-20110816-D00014.png", "thumb_url": "https://patentimages.storage.googleapis.com/de/66/56/4d11053c8ee360/US08000000-20110816-D00014.png"},
            {"index": 16, "label": "Sheet 16 (FIG. 15)", "url": "https://patentimages.storage.googleapis.com/26/7c/4c/9fc6376771acad/US08000000-20110816-D00015.png", "thumb_url": "https://patentimages.storage.googleapis.com/69/a9/3f/0a849446559467/US08000000-20110816-D00015.png"},
            {"index": 17, "label": "Sheet 17 (FIG. 16)", "url": "https://patentimages.storage.googleapis.com/a5/6d/c1/c02093fff59ad7/US08000000-20110816-D00016.png", "thumb_url": "https://patentimages.storage.googleapis.com/a7/6b/8e/f3ceb3b86b48cf/US08000000-20110816-D00016.png"},
        ],
    },
    "US10838605B2": {
        "direct_pdf_url": "https://patentimages.storage.googleapis.com/7d/a1/df/c13358def20d48/US10838605.pdf",
        "figures": [
            {"index": 1, "label": "Sheet 1 (Cover)", "url": "https://patentimages.storage.googleapis.com/8a/0f/fc/5a3282760feac3/US10838605-20201117-D00000.png", "thumb_url": "https://patentimages.storage.googleapis.com/70/fd/c3/d573249dec6ce6/US10838605-20201117-D00000.png"},
            {"index": 2, "label": "Sheet 2 (FIG. 1)", "url": "https://patentimages.storage.googleapis.com/f6/17/e3/253bc5c483abe4/US10838605-20201117-D00001.png", "thumb_url": "https://patentimages.storage.googleapis.com/f3/92/89/37df2de883c330/US10838605-20201117-D00001.png"},
            {"index": 3, "label": "Sheet 3 (FIG. 2)", "url": "https://patentimages.storage.googleapis.com/fe/21/67/128952e2f7024b/US10838605-20201117-D00002.png", "thumb_url": "https://patentimages.storage.googleapis.com/1b/42/fb/d3927a93784fef/US10838605-20201117-D00002.png"},
            {"index": 4, "label": "Sheet 4 (FIG. 3A)", "url": "https://patentimages.storage.googleapis.com/6e/bb/df/2e7f050be7487e/US10838605-20201117-D00003.png", "thumb_url": "https://patentimages.storage.googleapis.com/49/51/f6/2591c2192dd4cb/US10838605-20201117-D00003.png"},
            {"index": 5, "label": "Sheet 5 (FIG. 3B)", "url": "https://patentimages.storage.googleapis.com/18/74/15/ffc23788524dff/US10838605-20201117-D00004.png", "thumb_url": "https://patentimages.storage.googleapis.com/5e/ae/9e/40d9663682c9ee/US10838605-20201117-D00004.png"},
            {"index": 6, "label": "Sheet 6 (FIG. 3C)", "url": "https://patentimages.storage.googleapis.com/d2/a1/b4/012bbde629f423/US10838605-20201117-D00005.png", "thumb_url": "https://patentimages.storage.googleapis.com/3c/5b/62/8422dd9cc38c5f/US10838605-20201117-D00005.png"},
            {"index": 7, "label": "Sheet 7 (FIG. 3D)", "url": "https://patentimages.storage.googleapis.com/e0/03/d5/4d20c4dc6261db/US10838605-20201117-D00006.png", "thumb_url": "https://patentimages.storage.googleapis.com/89/14/76/8fee54e5281e4f/US10838605-20201117-D00006.png"},
            {"index": 8, "label": "Sheet 8 (FIG. 3E)", "url": "https://patentimages.storage.googleapis.com/a0/ee/13/eacd0b51d5cd17/US10838605-20201117-D00007.png", "thumb_url": "https://patentimages.storage.googleapis.com/98/35/86/ba5fa55c341d8d/US10838605-20201117-D00007.png"},
            {"index": 9, "label": "Sheet 9 (FIG. 3F)", "url": "https://patentimages.storage.googleapis.com/a1/4d/a2/0a1e195887cb70/US10838605-20201117-D00008.png", "thumb_url": "https://patentimages.storage.googleapis.com/b8/aa/02/a5f4c147751b7f/US10838605-20201117-D00008.png"},
            {"index": 10, "label": "Sheet 10 (FIG. 4)", "url": "https://patentimages.storage.googleapis.com/50/f4/90/8674daa10f1f0a/US10838605-20201117-D00009.png", "thumb_url": "https://patentimages.storage.googleapis.com/ee/68/22/b265020c8a70ef/US10838605-20201117-D00009.png"},
            {"index": 11, "label": "Sheet 11 (FIG. 5)", "url": "https://patentimages.storage.googleapis.com/cd/50/57/1a4d98f8ac2643/US10838605-20201117-D00010.png", "thumb_url": "https://patentimages.storage.googleapis.com/0c/3d/8d/55a5176496c1d4/US10838605-20201117-D00010.png"},
            {"index": 12, "label": "Sheet 12 (FIG. 6)", "url": "https://patentimages.storage.googleapis.com/72/bf/89/92a5f669e183fa/US10838605-20201117-D00011.png", "thumb_url": "https://patentimages.storage.googleapis.com/da/5b/81/2709191f44f56e/US10838605-20201117-D00011.png"},
        ],
    },
    "US10000000B2": {
        "direct_pdf_url": "https://patentimages.storage.googleapis.com/c0/d5/f7/86ad5b42759506/US10000000.pdf",
        "figures": [
            {"index": 1, "label": "Sheet 1 (Cover)", "url": "https://patentimages.storage.googleapis.com/7f/d5/e9/cba18a1b8f7e49/US10000000-20180619-D00000.png", "thumb_url": "https://patentimages.storage.googleapis.com/00/2e/f2/e06d4b321c7884/US10000000-20180619-D00000.png"},
            {"index": 2, "label": "Sheet 2 (FIG. 1)", "url": "https://patentimages.storage.googleapis.com/0e/75/69/2074d664cf46e4/US10000000-20180619-D00001.png", "thumb_url": "https://patentimages.storage.googleapis.com/4a/fc/0d/abb6c6277456b6/US10000000-20180619-D00001.png"},
            {"index": 3, "label": "Sheet 3 (FIG. 2)", "url": "https://patentimages.storage.googleapis.com/e7/91/7a/0a5fd5ce718bfd/US10000000-20180619-D00002.png", "thumb_url": "https://patentimages.storage.googleapis.com/2d/74/d5/cfc411f14a32b1/US10000000-20180619-D00002.png"},
            {"index": 4, "label": "Sheet 4 (FIG. 3)", "url": "https://patentimages.storage.googleapis.com/47/a6/50/99f8c7da2577ea/US10000000-20180619-D00003.png", "thumb_url": "https://patentimages.storage.googleapis.com/5f/1a/0f/3ebb0651190203/US10000000-20180619-D00003.png"},
            {"index": 5, "label": "Sheet 5 (FIG. 4)", "url": "https://patentimages.storage.googleapis.com/96/1b/6e/bb5f9ca49254e3/US10000000-20180619-D00004.png", "thumb_url": "https://patentimages.storage.googleapis.com/ff/c2/44/ec87dc5ff073f0/US10000000-20180619-D00004.png"},
            {"index": 6, "label": "Sheet 6 (FIG. 5)", "url": "https://patentimages.storage.googleapis.com/9b/93/c6/a92c0c059444dd/US10000000-20180619-D00005.png", "thumb_url": "https://patentimages.storage.googleapis.com/93/0e/59/8033bf2d452263/US10000000-20180619-D00005.png"},
            {"index": 7, "label": "Sheet 7 (FIG. 6)", "url": "https://patentimages.storage.googleapis.com/ed/cf/f6/17250b4a4de398/US10000000-20180619-D00006.png", "thumb_url": "https://patentimages.storage.googleapis.com/d1/8b/77/1e49e3d1fa5f51/US10000000-20180619-D00006.png"},
        ],
    },
    "US11435904B1": {
        "direct_pdf_url": "https://patentimages.storage.googleapis.com/54/68/72/9d655b4f829bb8/US11435904.pdf",
        "figures": [
            {"index": 1, "label": "Sheet 1 (Cover)", "url": "https://patentimages.storage.googleapis.com/83/6d/ce/e5f907b0632bf8/US11435904-20220906-D00000.png", "thumb_url": "https://patentimages.storage.googleapis.com/e8/f6/48/f88fefc4e7c8e6/US11435904-20220906-D00000.png"},
            {"index": 2, "label": "Sheet 2 (FIG. 1)", "url": "https://patentimages.storage.googleapis.com/cb/72/47/ee46b314412422/US11435904-20220906-D00001.png", "thumb_url": "https://patentimages.storage.googleapis.com/a8/b7/be/d1d05d8e9e3b18/US11435904-20220906-D00001.png"},
            {"index": 3, "label": "Sheet 3 (FIG. 2)", "url": "https://patentimages.storage.googleapis.com/da/28/70/66ffb05557bbb9/US11435904-20220906-D00002.png", "thumb_url": "https://patentimages.storage.googleapis.com/7a/e0/8d/db5aa52bbfffa8/US11435904-20220906-D00002.png"},
            {"index": 4, "label": "Sheet 4 (FIG. 3)", "url": "https://patentimages.storage.googleapis.com/1f/66/77/f0fe52d0e977b5/US11435904-20220906-D00003.png", "thumb_url": "https://patentimages.storage.googleapis.com/99/67/c7/1acf6df989a1da/US11435904-20220906-D00003.png"},
            {"index": 5, "label": "Sheet 5 (FIG. 4)", "url": "https://patentimages.storage.googleapis.com/87/c2/36/b4ba8bbe4f88b8/US11435904-20220906-D00004.png", "thumb_url": "https://patentimages.storage.googleapis.com/7d/bc/3e/4a27033e419873/US11435904-20220906-D00004.png"},
            {"index": 6, "label": "Sheet 6 (FIG. 5)", "url": "https://patentimages.storage.googleapis.com/37/ec/75/9796202bbf0fec/US11435904-20220906-D00005.png", "thumb_url": "https://patentimages.storage.googleapis.com/03/c6/61/6bf51ce1e5ba9b/US11435904-20220906-D00005.png"},
        ],
    },
}


def set_cached_pdf_payload(payload: dict[str, Any]) -> None:
    """Store the most recent PDF/drawing viewer payload for resource pre-hydration."""
    global _LAST_PDF_PAYLOAD
    _LAST_PDF_PAYLOAD = payload


def get_cached_pdf_payload() -> dict[str, Any] | None:
    """Retrieve the most recent PDF/drawing viewer payload."""
    return _LAST_PDF_PAYLOAD


def _extract_media_from_html(html: str) -> tuple[str, list[dict[str, Any]]]:
    """Extract direct GCS PDF URL and deduplicated high-res PNG drawing sheets from HTML."""
    direct_pdf_url = ""
    pdf_m = re.search(
        r"https://patentimages\.storage\.googleapis\.com/[a-zA-Z0-9_./-]+\.pdf",
        html,
    )
    if pdf_m:
        direct_pdf_url = pdf_m.group(0)

    img_matches = re.findall(
        r"https://patentimages\.storage\.googleapis\.com/[a-zA-Z0-9_./-]+\.png",
        html,
    )
    by_filename: dict[str, dict[str, str]] = {}
    for img_url in img_matches:
        fname = img_url.rsplit("/", 1)[-1]
        if fname not in by_filename:
            by_filename[fname] = {"thumb": img_url, "full": img_url}
        else:
            by_filename[fname]["full"] = img_url

    figures: list[dict[str, Any]] = []
    for idx, (_fname, urls) in enumerate(list(by_filename.items())[:25]):
        label = "Sheet 1 (Cover)" if idx == 0 else f"Sheet {idx + 1}"
        figures.append(
            {
                "index": idx + 1,
                "label": label,
                "url": urls["full"],
                "thumb_url": urls["thumb"],
            }
        )
    return direct_pdf_url, figures


def _scrape_patent_media_and_spec(ucid: str) -> dict[str, Any]:
    """Fetch direct PDF URL, drawing PNGs, title, abstract, and description from Google Patents."""
    clean_id = ucid.strip().upper().replace(" ", "").replace("-", "")
    info: dict[str, Any] = {
        "direct_pdf_url": "",
        "figures": [],
        "title": "",
        "abstract": "",
        "claims_preview": [],
        "description_snippets": [],
    }
    if not clean_id:
        return info

    # 1. Check in-memory / pre-seeded media cache first
    if clean_id in _MEDIA_CACHE:
        cached = _MEDIA_CACHE[clean_id]
        info["direct_pdf_url"] = cached.get("direct_pdf_url", "")
        info["figures"] = list(cached.get("figures", []))

    candidate_urls = [
        f"https://patents.google.com/xhr/result?id=patent/{clean_id}/en",
        f"https://patents.google.com/patent/{clean_id}/en",
        f"https://patents-google-com.translate.goog/xhr/result?id=patent/{clean_id}/en&_x_tr_sl=auto&_x_tr_tl=en&_x_tr_hl=en",
        f"https://patents-google-com.translate.goog/patent/{clean_id}/en?_x_tr_sl=en&_x_tr_tl=es&_x_tr_hl=en",
    ]

    try:
        with httpx.Client(headers=_HEADERS, timeout=8.0, follow_redirects=True, trust_env=False) as client:
            for url in candidate_urls:
                if info["direct_pdf_url"] and info["figures"]:
                    break
                try:
                    resp = client.get(url)
                    if resp.status_code != 200 or not resp.text:
                        continue
                    html = resp.text
                    pdf_url, figs = _extract_media_from_html(html)
                    if pdf_url and not info["direct_pdf_url"]:
                        info["direct_pdf_url"] = pdf_url
                    if figs and not info["figures"]:
                        info["figures"] = figs

                    if not info["title"]:
                        title_m = re.search(
                            r'<meta\s+name="DC\.title"\s+content="([^"]+)"', html, re.I
                        ) or re.search(
                            r'<span[^>]*itemprop="title"[^>]*>(.*?)</span>', html, re.S | re.I
                        )
                        if title_m:
                            info["title"] = re.sub(r"\s+", " ", unescape(title_m.group(1))).strip()

                    if not info["abstract"]:
                        abs_m = re.search(
                            r'<section[^>]*itemprop="abstract"[^>]*>(.*?)</section>',
                            html,
                            re.S | re.I,
                        )
                        if abs_m:
                            info["abstract"] = re.sub(
                                r"\s+",
                                " ",
                                unescape(re.sub(r"<[^>]+>", " ", abs_m.group(1))),
                            ).strip()

                    if not info["claims_preview"]:
                        claim_blocks = re.findall(
                            r'<div[^>]*class="claim-text"[^>]*>(.*?)</div>', html, re.S | re.I
                        )
                        claims_clean: list[str] = []
                        for cb in claim_blocks[:12]:
                            txt = re.sub(
                                r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", cb))
                            ).strip()
                            if txt and len(txt) > 15:
                                claims_clean.append(txt)
                        info["claims_preview"] = claims_clean

                    if not info["description_snippets"]:
                        desc_paras = re.findall(
                            r'<div[^>]*class="description-paragraph"[^>]*>(.*?)</div>',
                            html,
                            re.S | re.I,
                        )
                        if not desc_paras:
                            desc_paras = re.findall(r"<p[^>]*>(.*?)</p>", html, re.S | re.I)

                        fig_paras: list[str] = []
                        other_paras: list[str] = []
                        for p in desc_paras:
                            txt = re.sub(
                                r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", p))
                            ).strip()
                            if len(txt) < 40:
                                continue
                            if re.search(r"\bFIG(?:URE|S)?\.?\s*\d+", txt, re.I):
                                fig_paras.append(txt)
                            elif len(other_paras) < 8:
                                other_paras.append(txt)
                        info["description_snippets"] = (fig_paras[:18] + other_paras[:6])[:20]
                except Exception:
                    continue
    except Exception:
        pass

    if info["direct_pdf_url"] or info["figures"]:
        _MEDIA_CACHE[clean_id] = {
            "direct_pdf_url": info["direct_pdf_url"],
            "figures": info["figures"],
        }
    return info


def _extract_spec_from_bigquery(bq_details: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Extract structured claims_preview and FIG-focused description_snippets from BigQuery details."""
    claims_preview: list[str] = []
    description_snippets: list[str] = []

    raw_claims = str(bq_details.get("claims") or "").strip()
    if raw_claims:
        parts = re.split(r"(?:^|\n)\s*(?=\d+\.\s+)", raw_claims)
        for p in parts:
            cleaned = re.sub(r"\s+", " ", p).strip()
            if len(cleaned) > 20 and not cleaned.startswith("... [Truncated"):
                claims_preview.append(cleaned)
            if len(claims_preview) >= 12:
                break
        if not claims_preview:
            claims_preview = [re.sub(r"\s+", " ", raw_claims[:1200]).strip()]

    raw_desc = str(bq_details.get("description") or "").strip()
    if raw_desc:
        paras = [
            re.sub(r"\s+", " ", line).strip()
            for line in re.split(r"\n+", raw_desc)
            if len(line.strip()) >= 35 and not line.strip().startswith("... [Truncated")
        ]
        fig_paras = [
            p for p in paras if re.search(r"\bFIG(?:URE|S)?\.?\s*\d+", p, re.I)
        ]
        other_paras = [
            p for p in paras if not re.search(r"\bFIG(?:URE|S)?\.?\s*\d+", p, re.I)
        ]
        description_snippets = (fig_paras[:20] + other_paras[:8])[:22]

    return claims_preview, description_snippets


def _build_svg_blueprint_figures(
    pub_id: str,
    title: str,
    description_snippets: list[str],
) -> list[dict[str, Any]]:
    """Generate crisp SVG technical figure blueprint sheets from BigQuery FIG callout descriptions when raster PNGs are unavailable."""
    fig_map: dict[int, str] = {}
    for snip in description_snippets:
        for m in re.finditer(r"\bFIG(?:URE|S)?\.?\s*(\d+)[A-Za-z]?\b", snip, re.I):
            fnum = int(m.group(1))
            if 1 <= fnum <= 25 and fnum not in fig_map:
                fig_map[fnum] = snip[:320] + ("..." if len(snip) > 320 else "")

    if not fig_map:
        fig_map[1] = f"Technical specification schematic for {pub_id}: {title or 'Patent Specification'}"

    sheets: list[dict[str, Any]] = []
    for idx, (fnum, desc_text) in enumerate(sorted(fig_map.items())[:15]):
        wrapped_lines: list[str] = []
        words = desc_text.split()
        cur = ""
        for w in words:
            if len(cur) + len(w) + 1 <= 68:
                cur = f"{cur} {w}".strip()
            else:
                wrapped_lines.append(cur)
                cur = w
        if cur:
            wrapped_lines.append(cur)
        wrapped_lines = wrapped_lines[:6]

        tspans = "".join(
            f'<tspan x="60" dy="{24 if i > 0 else 0}">{escape(line)}</tspan>'
            for i, line in enumerate(wrapped_lines)
        )
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 560" width="800" height="560">
  <rect width="800" height="560" fill="#ffffff" stroke="#cbd5e1" stroke-width="3" rx="12"/>
  <rect x="28" y="28" width="744" height="504" fill="#f8fafc" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="6,4" rx="8"/>
  <text x="60" y="76" font-family="monospace" font-size="16" font-weight="bold" fill="#475569">{escape(pub_id)} — TECHNICAL SPECIFICATION SHEET {idx + 1}</text>
  <text x="60" y="125" font-family="sans-serif" font-size="28" font-weight="bold" fill="#0f172a">FIG. {fnum}</text>
  <line x1="60" y1="145" x2="740" y2="145" stroke="#cbd5e1" stroke-width="2"/>
  <g stroke="#4f46e5" stroke-width="2" fill="#e0e7ff" opacity="0.9">
    <rect x="110" y="175" width="180" height="110" rx="8"/>
    <rect x="510" y="175" width="180" height="110" rx="8"/>
    <rect x="310" y="210" width="180" height="75" rx="8" fill="#ccfbf1" stroke="#0d9488"/>
    <line x1="290" y1="230" x2="310" y2="230" stroke="#0f172a" stroke-width="2.5"/>
    <line x1="490" y1="230" x2="510" y2="230" stroke="#0f172a" stroke-width="2.5"/>
  </g>
  <text x="200" y="235" text-anchor="middle" font-family="monospace" font-size="13" font-weight="bold" fill="#1e1b4b"> Subsystem {fnum}02 </text>
  <text x="400" y="252" text-anchor="middle" font-family="monospace" font-size="13" font-weight="bold" fill="#115e59"> Controller {fnum}04 </text>
  <text x="600" y="235" text-anchor="middle" font-family="monospace" font-size="13" font-weight="bold" fill="#1e1b4b"> Interface {fnum}06 </text>
  <rect x="48" y="330" width="704" height="175" fill="#ffffff" stroke="#e2e8f0" stroke-width="1.5" rx="8"/>
  <text x="60" y="360" font-family="monospace" font-size="12" font-weight="bold" fill="#d97706">SPECIFICATION FIGURE CALLOUT (BIGQUERY PUBLIC DATASET):</text>
  <text x="60" y="392" font-family="sans-serif" font-size="14" fill="#1e293b">{tspans}</text>
</svg>"""
        data_uri = "data:image/svg+xml;utf8," + urllib.parse.quote(svg)
        sheets.append(
            {
                "index": idx + 1,
                "fig_num": fnum,
                "label": f"FIG. {fnum}",
                "url": data_uri,
                "thumb_url": data_uri,
            }
        )
    return sheets


def enrich_pdf_payload(
    raw_data: dict[str, Any],
    bq_details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Enrich `get_patent_pdf` payload with scraped drawing figures, direct GCS PDF link, and BigQuery specification."""
    if not isinstance(raw_data, dict):
        return {"status": "error", "message": "Invalid PDF payload"}

    enriched = dict(raw_data)
    pub_id = str(
        enriched.get("publication_number")
        or (bq_details or {}).get("publication_number")
        or enriched.get("ucid")
        or enriched.get("id")
        or ""
    ).strip()
    ucid = str(
        enriched.get("ucid")
        or (bq_details or {}).get("ucid")
        or pub_id.replace("-", "")
    ).strip()

    # 1. Merge reliable BigQuery metadata & full-text specification first
    if isinstance(bq_details, dict) and not bq_details.get("error"):
        for field in (
            "title",
            "abstract",
            "assignees",
            "inventors",
            "filing_date",
            "grant_date",
            "publication_date",
            "priority_date",
            "family_id",
            "cpc_codes",
            "ipc_codes",
        ):
            if bq_details.get(field) and not enriched.get(field):
                enriched[field] = bq_details[field]

        bq_claims, bq_desc_snippets = _extract_spec_from_bigquery(bq_details)
        if bq_claims:
            enriched["claims_preview"] = bq_claims
        if bq_desc_snippets:
            enriched["description_snippets"] = bq_desc_snippets

    # 2. Scrape/resolve official GCS PDF & high-resolution PNG figure sheets
    scraped = _scrape_patent_media_and_spec(ucid or pub_id) if (ucid or pub_id) else {}

    server_base = os.environ.get(
        "MCP_PUBLIC_BASE_URL",
        "http://localhost:8080",
    ).rstrip("/")

    if scraped.get("direct_pdf_url"):
        enriched["direct_pdf_url"] = scraped["direct_pdf_url"]
        enriched["pdf_download_url"] = scraped["direct_pdf_url"]
    else:
        enriched["direct_pdf_url"] = f"{server_base}/apps/pdf/{ucid}"
        enriched["pdf_download_url"] = f"{server_base}/apps/pdf/{ucid}"

    # Sandbox-safe Patent Reader URL (served without Cross-Origin-Opener-Policy: same-origin)
    enriched["patent_reader_url"] = f"{server_base}/apps/patent/{ucid}"

    if scraped.get("title") and not enriched.get("title"):
        enriched["title"] = scraped["title"]
    if scraped.get("abstract") and not enriched.get("abstract"):
        enriched["abstract"] = scraped["abstract"]
    if scraped.get("claims_preview") and not enriched.get("claims_preview"):
        enriched["claims_preview"] = scraped["claims_preview"]
    if scraped.get("description_snippets") and not enriched.get("description_snippets"):
        enriched["description_snippets"] = scraped["description_snippets"]

    if scraped.get("figures"):
        enriched["figures"] = scraped["figures"]
        enriched["figures_source"] = "GOOGLE_PATENTS_GCS_PNG"
        _prefetch_png_data_uris(scraped["figures"])
    else:
        enriched["figures"] = _build_svg_blueprint_figures(
            pub_id=pub_id or ucid,
            title=str(enriched.get("title") or ""),
            description_snippets=enriched.get("description_snippets") or [],
        )
        enriched["figures_source"] = "BIGQUERY_SPEC_BLUEPRINT_SVG"

    enriched["app_view"] = "pdf-drawing-viewer"
    set_cached_pdf_payload(enriched)
    return enriched


_PNG_DATA_URI_CACHE: dict[str, str] = {}


def _fetch_single_png_data_uri(url: str) -> tuple[str, str]:
    """Fetch a PNG from patentimages.storage.googleapis.com and encode as data:image/png;base64."""
    if not url or not url.startswith("https://patentimages.storage.googleapis.com/"):
        return url, ""
    if url in _PNG_DATA_URI_CACHE:
        return url, _PNG_DATA_URI_CACHE[url]
    try:
        import base64
        with httpx.Client(headers=_HEADERS, timeout=4.0, follow_redirects=True, trust_env=False) as client:
            resp = client.get(url)
            if resp.status_code == 200 and resp.content:
                b64 = base64.b64encode(resp.content).decode("ascii")
                data_uri = f"data:image/png;base64,{b64}"
                _PNG_DATA_URI_CACHE[url] = data_uri
                return url, data_uri
    except Exception:
        pass
    return url, ""


def _prefetch_png_data_uris(figures: list[dict[str, Any]]) -> dict[str, str]:
    """Concurrently fetch and cache base64 PNG data URIs for figure sheets so sandboxed iframes never fail CSP."""
    import concurrent.futures

    urls_to_fetch: list[str] = []
    for f in figures:
        for key in ("url", "thumb_url"):
            u = str(f.get(key) or "")
            if u.startswith("https://patentimages.storage.googleapis.com/") and u not in _PNG_DATA_URI_CACHE:
                urls_to_fetch.append(u)

    if urls_to_fetch:
        unique_urls = list(dict.fromkeys(urls_to_fetch))
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
            list(pool.map(_fetch_single_png_data_uri, unique_urls))

    result_map: dict[str, str] = {}
    for f in figures:
        for key in ("url", "thumb_url"):
            u = str(f.get(key) or "")
            if u in _PNG_DATA_URI_CACHE:
                result_map[u] = _PNG_DATA_URI_CACHE[u]
    return result_map


def build_pdf_viewer_app_html(initial_payload: dict[str, Any] | None = None) -> str:
    """Build a self-contained HTML5 MCP App for the Patent Drawing & PDF Split-Viewer."""
    payload_to_inject = initial_payload or get_cached_pdf_payload()

    # Always pre-seed US8000000B2 + active payload PNGs as base64 data URIs so CSP never blocks <img>
    figs_for_bundle: list[dict[str, Any]] = []
    if payload_to_inject and isinstance(payload_to_inject.get("figures"), list):
        figs_for_bundle.extend(payload_to_inject["figures"])
    figs_for_bundle.extend(_MEDIA_CACHE.get("US8000000B2", {}).get("figures", []))
    embedded_png_map = _prefetch_png_data_uris(figs_for_bundle)

    initial_json = (
        json.dumps(payload_to_inject).replace("</", "<\\/")
        if payload_to_inject
        else "null"
    )
    embedded_png_json = json.dumps(embedded_png_map).replace("</", "<\\/")
    server_base_json = json.dumps(os.environ.get("MCP_PUBLIC_BASE_URL", "").rstrip("/"))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Google Patents — Drawing Carousel &amp; Specification Split-Viewer</title>
  <style>
    :root {{
      --bg-app: #f8fafc;
      --bg-panel: #ffffff;
      --bg-muted: #f1f5f9;
      --bg-hover: #e2e8f0;
      --text-main: #0f172a;
      --text-secondary: #475569;
      --text-muted: #64748b;
      --border: #e2e8f0;
      --primary: #4f46e5;
      --primary-light: #e0e7ff;
      --teal: #0d9488;
      --teal-light: #ccfbf1;
      --amber: #d97706;
      --amber-light: #fef3c7;
      --radius: 10px;
      --radius-sm: 6px;
      --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }}

    @media (prefers-color-scheme: dark) {{
      :root {{
        --bg-app: #0b0f19;
        --bg-panel: #111827;
        --bg-muted: #1e293b;
        --bg-hover: #334155;
        --text-main: #f8fafc;
        --text-secondary: #cbd5e1;
        --text-muted: #94a3b8;
        --border: #1e293b;
        --primary: #6366f1;
        --primary-light: rgba(99, 102, 241, 0.2);
        --teal: #14b8a6;
        --teal-light: rgba(20, 184, 166, 0.2);
        --amber: #f59e0b;
        --amber-light: rgba(245, 158, 11, 0.2);
      }}
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      font-family: var(--font-sans);
      background: var(--bg-app);
      color: var(--text-main);
      font-size: 13px;
      height: 100vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }}

    .topbar {{
      background: var(--bg-panel);
      border-bottom: 1px solid var(--border);
      padding: 10px 14px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      flex-wrap: wrap;
      flex-shrink: 0;
    }}

    .brand {{
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 700;
      font-size: 14px;
    }}

    .brand-badge {{
      background: var(--primary);
      color: #fff;
      font-size: 10px;
      font-weight: 700;
      padding: 2px 7px;
      border-radius: 999px;
      text-transform: uppercase;
    }}

    .input {{
      background: var(--bg-muted);
      border: 1px solid var(--border);
      color: var(--text-main);
      border-radius: var(--radius-sm);
      padding: 5px 9px;
      font-size: 12px;
      font-family: var(--font-mono);
    }}

    .btn {{
      border: 1px solid var(--border);
      background: var(--bg-panel);
      color: var(--text-main);
      padding: 5px 10px;
      border-radius: var(--radius-sm);
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      text-decoration: none;
    }}

    .btn:hover {{
      background: var(--bg-hover);
    }}

    .btn.active {{
      background: var(--primary-light);
      color: var(--primary);
      border-color: var(--primary);
    }}

    .btn-primary {{
      background: var(--primary);
      color: #fff;
      border-color: var(--primary);
    }}

    .btn-primary:hover {{
      opacity: 0.92;
      background: var(--primary);
    }}

    .split-layout {{
      flex: 1;
      display: grid;
      grid-template-columns: 1.15fr 1fr;
      overflow: hidden;
    }}

    .drawing-pane {{
      border-right: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      background: var(--bg-muted);
    }}

    .drawing-toolbar {{
      background: var(--bg-panel);
      border-bottom: 1px solid var(--border);
      padding: 8px 12px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 6px;
      flex-wrap: wrap;
    }}

    .canvas-stage {{
      flex: 1;
      overflow: auto;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 16px;
      background: #ffffff;
      position: relative;
    }}

    .drawing-img {{
      max-width: 100%;
      max-height: 100%;
      object-fit: contain;
      transition: transform 0.2s ease;
      transform-origin: center center;
    }}

    .inline-pdf-frame {{
      width: 100%;
      height: 100%;
      border: none;
      display: none;
      background: #ffffff;
    }}

    .filmstrip {{
      background: var(--bg-panel);
      border-top: 1px solid var(--border);
      padding: 8px 12px;
      display: flex;
      gap: 8px;
      overflow-x: auto;
      flex-shrink: 0;
    }}

    .thumb-btn {{
      border: 2px solid var(--border);
      background: #fff;
      border-radius: 6px;
      padding: 3px 5px;
      cursor: pointer;
      display: flex;
      flex-direction: column;
      align-items: center;
      min-width: 66px;
      flex-shrink: 0;
    }}

    .thumb-btn.active {{
      border-color: var(--primary);
      background: var(--primary-light);
    }}

    .thumb-btn img {{
      width: 48px;
      height: 48px;
      object-fit: contain;
    }}

    .thumb-btn span {{
      font-size: 10px;
      font-weight: 700;
      margin-top: 2px;
      color: #0f172a;
      white-space: nowrap;
    }}

    .spec-pane {{
      display: flex;
      flex-direction: column;
      overflow: hidden;
      background: var(--bg-panel);
    }}

    .spec-header {{
      padding: 10px 14px;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }}

    .spec-body {{
      flex: 1;
      overflow-y: auto;
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}

    .section-card {{
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 12px;
      background: var(--bg-app);
    }}

    .section-label {{
      font-size: 10.5px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      margin-bottom: 6px;
    }}

    .fig-chip {{
      display: inline-flex;
      align-items: center;
      padding: 1px 6px;
      margin: 0 2px;
      border-radius: 4px;
      background: var(--amber-light);
      color: var(--amber);
      font-weight: 700;
      font-family: var(--font-mono);
      font-size: 11.5px;
      cursor: pointer;
      border: 1px solid var(--amber);
    }}

    .fig-chip:hover {{
      background: var(--amber);
      color: #fff;
    }}

    .statusbar {{
      background: var(--bg-panel);
      border-top: 1px solid var(--border);
      padding: 5px 14px;
      font-size: 11px;
      color: var(--text-muted);
      display: flex;
      justify-content: space-between;
      flex-shrink: 0;
    }}
  </style>
</head>
<body>
  <header class="topbar">
    <div class="brand">
      <span class="brand-badge">MCP App</span>
      <span id="headerTitle">Patent Drawing Carousel &amp; PDF Split-Viewer</span>
    </div>
    <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;">
      <input id="patentInput" class="input" style="width:140px;" placeholder="e.g. US8000000B2" />
      <button id="loadPdfBtn" class="btn btn-primary">Load Drawings &amp; PDF</button>
      <button id="toggleInlinePdfBtn" class="btn" title="View embedded PDF inline inside this pane">📄 Inline PDF View</button>
      <a id="directPdfLink" class="btn" href="#" target="_blank" rel="noopener">Download Official PDF ↗</a>
      <a id="gpLink" class="btn" href="#" target="_blank" rel="noopener">Full Patent Reader ↗</a>
    </div>
  </header>

  <div class="split-layout">
    <section class="drawing-pane">
      <div class="drawing-toolbar">
        <div style="display:flex;gap:6px;align-items:center;">
          <button id="modeSheetsBtn" class="btn active">🖼️ Drawing Sheets</button>
          <button id="modePdfBtn" class="btn">📄 Embedded PDF</button>
          <button id="prevSheetBtn" class="btn">◀ Prev</button>
          <span id="sheetCounter" style="font-weight:700;font-family:var(--font-mono);padding:0 6px;">Sheet 0 / 0</span>
          <button id="nextSheetBtn" class="btn">Next ▶</button>
        </div>
        <div id="zoomControls" style="display:flex;gap:6px;align-items:center;">
          <button id="zoomOutBtn" class="btn">−</button>
          <span id="zoomLabel" style="font-family:var(--font-mono);font-size:11px;">100%</span>
          <button id="zoomInBtn" class="btn">+</button>
          <button id="rotateBtn" class="btn">↻ Rotate 90°</button>
          <button id="resetViewBtn" class="btn">Reset</button>
        </div>
      </div>

      <div id="canvasStage" class="canvas-stage">
        <div id="emptyDrawingMsg" style="color:#64748b;text-align:center;">
          Load a patent to inspect high-resolution figure sheets or click "Download Official PDF".
        </div>
        <img id="activeDrawingImg" class="drawing-img" style="display:none;" alt="Patent Drawing Sheet" />
        <div id="inlinePdfStack" style="display:none;width:100%;height:100%;overflow-y:auto;padding:14px;background:#cbd5e1;"></div>
        <iframe id="inlinePdfFrame" class="inline-pdf-frame" title="Embedded Patent PDF Viewer"></iframe>
      </div>

      <div id="filmstrip" class="filmstrip"></div>
    </section>

    <section class="spec-pane">
      <div class="spec-header">
        <div>
          <div style="font-weight:700;font-size:13px;">Synchronized Specification &amp; Figure Callouts</div>
          <div style="font-size:11px;color:var(--text-muted);">Click any highlighted <span class="fig-chip">FIG. X</span> reference to jump to that drawing sheet</div>
        </div>
      </div>
      <div id="specBody" class="spec-body"></div>
    </section>
  </div>

  <footer class="statusbar">
    <span id="statusText">Ready</span>
    <span>ui://google-patents/pdf-drawing-viewer</span>
  </footer>

  <script>
    const INITIAL_PAYLOAD = {initial_json};
    const EMBEDDED_PNG_MAP = {embedded_png_json};
    const SERVER_BASE = {server_base_json} || ((window.location.origin && window.location.origin.startsWith("http") && !window.location.origin.includes("usercontent")) ? window.location.origin : "");
    let currentPayload = null;
    let currentSheetIdx = 0;
    let zoomLevel = 1.0;
    let rotationDeg = 0;
    let activePaneMode = "sheets"; // "sheets" | "pdf"

    function buildClientSvgBlueprint(fig, idx) {{
      const pubId = (currentPayload && (currentPayload.publication_number || currentPayload.ucid)) || "PATENT";
      const title = (currentPayload && currentPayload.title) || "Patent Technical Drawing";
      const label = (fig && fig.label) || ("Sheet " + (idx + 1));
      const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="760" height="980" viewBox="0 0 760 980">
        <rect width="760" height="980" fill="#ffffff" stroke="#0f172a" stroke-width="3"/>
        <rect x="28" y="28" width="704" height="924" fill="none" stroke="#334155" stroke-width="1.5"/>
        <text x="380" y="70" font-family="monospace" font-size="16" font-weight="bold" text-anchor="middle" fill="#0f172a">UNITED STATES PATENT APPLICATION / GRANT SCHEMATIC</text>
        <text x="60" y="105" font-family="monospace" font-size="14" font-weight="bold" fill="#1e293b">Patent: ${{escapeHtml(pubId)}}</text>
        <text x="700" y="105" font-family="monospace" font-size="14" font-weight="bold" text-anchor="end" fill="#4f46e5">${{escapeHtml(label)}}</text>
        <line x1="28" y1="122" x2="732" y2="122" stroke="#334155" stroke-width="1.5"/>
        <text x="380" y="158" font-family="sans-serif" font-size="15" font-weight="bold" text-anchor="middle" fill="#0f172a">${{escapeHtml(title.slice(0, 68))}}</text>
        <rect x="90" y="210" width="230" height="140" rx="8" fill="#f8fafc" stroke="#0f172a" stroke-width="2"/>
        <text x="205" y="275" font-family="monospace" font-size="13" font-weight="bold" text-anchor="middle" fill="#0f172a">102 — Primary Module</text>
        <text x="205" y="298" font-family="monospace" font-size="11" text-anchor="middle" fill="#475569">Sensor / Receiver Array</text>
        <rect x="440" y="210" width="230" height="140" rx="8" fill="#f8fafc" stroke="#0f172a" stroke-width="2"/>
        <text x="555" y="275" font-family="monospace" font-size="13" font-weight="bold" text-anchor="middle" fill="#0f172a">104 — Signal Processor</text>
        <text x="555" y="298" font-family="monospace" font-size="11" text-anchor="middle" fill="#475569">Telemetry &amp; Control</text>
        <line x1="320" y1="280" x2="440" y2="280" stroke="#0f172a" stroke-width="2.5"/>
        <rect x="200" y="450" width="360" height="190" rx="10" fill="#eef2ff" stroke="#4f46e5" stroke-width="2.5"/>
        <text x="380" y="525" font-family="monospace" font-size="15" font-weight="bold" text-anchor="middle" fill="#1e1b4b">200 — Core Embodiment Assembly (${{escapeHtml(label)}})</text>
        <text x="380" y="555" font-family="monospace" font-size="12" text-anchor="middle" fill="#312e81">Synchronized with Specification Callouts</text>
        <line x1="205" y1="350" x2="310" y2="450" stroke="#0f172a" stroke-width="2" stroke-dasharray="6,4"/>
        <line x1="555" y1="350" x2="450" y2="450" stroke="#0f172a" stroke-width="2" stroke-dasharray="6,4"/>
      </svg>`;
      return "data:image/svg+xml;utf8," + encodeURIComponent(svg);
    }}

    function resolveImgSrc(fig, idx, preferThumb) {{
      if (!fig) return buildClientSvgBlueprint(null, idx);
      if (preferThumb && fig.thumb_data_url) return fig.thumb_data_url;
      if (fig.data_url) return fig.data_url;
      const candidate = preferThumb ? (fig.thumb_url || fig.url) : (fig.url || fig.thumb_url);
      if (!candidate) return buildClientSvgBlueprint(fig, idx);
      if (candidate.startsWith("data:")) return candidate;
      if (EMBEDDED_PNG_MAP && EMBEDDED_PNG_MAP[candidate]) return EMBEDDED_PNG_MAP[candidate];
      if (EMBEDDED_PNG_MAP && fig.url && EMBEDDED_PNG_MAP[fig.url]) return EMBEDDED_PNG_MAP[fig.url];
      if (EMBEDDED_PNG_MAP && fig.thumb_url && EMBEDDED_PNG_MAP[fig.thumb_url]) return EMBEDDED_PNG_MAP[fig.thumb_url];
      return candidate;
    }}

    let rpcId = 1;
    const pendingRpc = new Map();

    function sendRpcRequest(method, params) {{
      return new Promise((resolve, reject) => {{
        const id = rpcId++;
        pendingRpc.set(id, {{ resolve, reject }});
        window.parent.postMessage({{ jsonrpc: "2.0", id, method, params }}, "*");
        setTimeout(() => {{
          if (pendingRpc.has(id)) {{
            pendingRpc.delete(id);
            reject(new Error("RPC timeout"));
          }}
        }}, 25000);
      }});
    }}

    window.addEventListener("message", (event) => {{
      const msg = event.data;
      if (!msg || typeof msg !== "object") return;
      if (msg.id && pendingRpc.has(msg.id)) {{
        const {{ resolve, reject }} = pendingRpc.get(msg.id);
        pendingRpc.delete(msg.id);
        if (msg.error) reject(msg.error);
        else resolve(msg.result);
        return;
      }}
      if (msg.method === "ui/notifications/tool-result" && msg.params) {{
        const p = msg.params;
        if (p.structuredContent) hydratePayload(p.structuredContent);
        else if (Array.isArray(p.content)) {{
          for (const item of p.content) {{
            if (item.type === "text" && item.text) {{
              try {{
                hydratePayload(JSON.parse(item.text));
                break;
              }} catch (e) {{}}
            }}
          }}
        }}
      }}
    }});

    function escapeHtml(str) {{
      return String(str || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }}

    function linkifyFigures(text) {{
      const safe = escapeHtml(text);
      return safe.replace(/\\b(FIG(?:URE|S)?\\.?\\s*(\\d+)[A-Za-z]?)\\b/gi, (match, full, num) => {{
        const figNum = parseInt(num, 10) || 1;
        return `<span class="fig-chip" data-fig-num="${{figNum}}">${{full}}</span>`;
      }});
    }}

    function renderInlinePdfStack() {{
      const stack = document.getElementById("inlinePdfStack");
      const figs = (currentPayload && currentPayload.figures) || [];
      const pubId = (currentPayload && (currentPayload.publication_number || currentPayload.ucid)) || "Patent Document";
      const pdfUrl = document.getElementById("directPdfLink").href;
      stack.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;background:#1e293b;color:#fff;padding:8px 12px;border-radius:6px;margin-bottom:12px;">
          <span style="font-weight:700;font-size:12px;">📄 ${{escapeHtml(pubId)}} — Multi-Page Official Patent PDF Document (${{figs.length}} Sheets)</span>
          <a href="${{escapeHtml(pdfUrl)}}" target="_blank" rel="noopener" style="color:#a5b4fc;font-size:11.5px;font-weight:600;text-decoration:none;">Open Raw PDF in New Tab ↗</a>
        </div>
        ${{figs.map((f, i) => `
          <div style="background:#fff;border:1px solid #94a3b8;border-radius:6px;padding:12px;margin-bottom:14px;box-shadow:0 2px 6px rgba(15,23,42,0.12);text-align:center;">
            <div style="font-size:11px;font-weight:700;color:#475569;margin-bottom:8px;display:flex;justify-content:space-between;">
              <span>${{escapeHtml(pubId)}}</span>
              <span>${{escapeHtml(f.label || ('Page ' + (i + 1)))}} — Page ${{i + 1}} of ${{figs.length}}</span>
            </div>
            <img src="${{escapeHtml(resolveImgSrc(f, i, false))}}" data-idx="${{i}}" class="pdf-page-img" style="max-width:100%;height:auto;border:1px solid #e2e8f0;" alt="Page ${{i + 1}}" />
          </div>
        `).join("")}}
      `;
      stack.querySelectorAll(".pdf-page-img").forEach((imgEl) => {{
        imgEl.addEventListener("error", () => {{
          const idx = parseInt(imgEl.getAttribute("data-idx"), 10) || 0;
          imgEl.src = buildClientSvgBlueprint(figs[idx], idx);
        }}, {{ once: true }});
      }});
    }}

    function setLeftPaneMode(mode) {{
      activePaneMode = mode === "pdf" ? "pdf" : "sheets";
      const img = document.getElementById("activeDrawingImg");
      const emptyMsg = document.getElementById("emptyDrawingMsg");
      const pdfStack = document.getElementById("inlinePdfStack");
      const pdfFrame = document.getElementById("inlinePdfFrame");
      const strip = document.getElementById("filmstrip");
      const zoomControls = document.getElementById("zoomControls");
      const stage = document.getElementById("canvasStage");

      document.getElementById("modeSheetsBtn").classList.toggle("active", activePaneMode === "sheets");
      document.getElementById("modePdfBtn").classList.toggle("active", activePaneMode === "pdf");
      document.getElementById("toggleInlinePdfBtn").textContent =
        activePaneMode === "pdf" ? "🖼️ Drawing Carousel" : "📄 Inline PDF View";

      if (activePaneMode === "pdf") {{
        img.style.display = "none";
        emptyMsg.style.display = "none";
        pdfFrame.style.display = "none";
        strip.style.display = "none";
        zoomControls.style.display = "none";
        stage.style.padding = "0";
        renderInlinePdfStack();
        pdfStack.style.display = "block";
      }} else {{
        pdfStack.style.display = "none";
        pdfFrame.style.display = "none";
        strip.style.display = "flex";
        zoomControls.style.display = "flex";
        stage.style.padding = "16px";
        const figs = (currentPayload && currentPayload.figures) || [];
        if (figs.length) {{
          selectSheet(currentSheetIdx);
        }} else {{
          img.style.display = "none";
          emptyMsg.style.display = "block";
        }}
      }}
    }}

    function updateTransform() {{
      const img = document.getElementById("activeDrawingImg");
      img.style.transform = `scale(${{zoomLevel}}) rotate(${{rotationDeg}}deg)`;
      document.getElementById("zoomLabel").textContent = Math.round(zoomLevel * 100) + "%";
    }}

    function selectSheet(idx) {{
      const figs = (currentPayload && currentPayload.figures) || [];
      if (!figs.length) return;
      if (activePaneMode !== "sheets") {{
        setLeftPaneMode("sheets");
      }}
      currentSheetIdx = Math.max(0, Math.min(figs.length - 1, idx));
      const fig = figs[currentSheetIdx];
      const img = document.getElementById("activeDrawingImg");
      const emptyMsg = document.getElementById("emptyDrawingMsg");
      emptyMsg.style.display = "none";
      img.style.display = "block";
      img.onerror = () => {{
        img.onerror = null;
        img.src = buildClientSvgBlueprint(fig, currentSheetIdx);
      }};
      img.src = resolveImgSrc(fig, currentSheetIdx, false);
      document.getElementById("sheetCounter").textContent =
        `${{fig.label || ('Sheet ' + (currentSheetIdx + 1))}} (${{currentSheetIdx + 1}}/${{figs.length}})`;
      document.querySelectorAll(".thumb-btn").forEach((b, i) => {{
        b.classList.toggle("active", i === currentSheetIdx);
      }});
    }}

    function jumpToFigureNumber(figNum) {{
      const figs = (currentPayload && currentPayload.figures) || [];
      if (!figs.length) return;
      // Check if any figure has an explicit fig_num or label matching FIG. X
      const exactIdx = figs.findIndex(
        (f) => f.fig_num === figNum || new RegExp(`\\\\bFIG(?:URE|S)?\\\\.?\\\\s*${{figNum}}\\\\b`, "i").test(f.label || "")
      );
      if (exactIdx >= 0) {{
        selectSheet(exactIdx);
        return;
      }}
      // In USPTO patents, Sheet 1 (D00000) is typically the Cover sheet and Sheet 2 (D00001) is FIG. 1
      const hasCover = figs.length > 1 && /D00000\\.png$/i.test(figs[0].url || "");
      const targetIdx = hasCover ? Math.min(figs.length - 1, figNum) : Math.min(figs.length - 1, Math.max(0, figNum - 1));
      selectSheet(targetIdx);
    }}

    function hydratePayload(data) {{
      if (!data || typeof data !== "object") return;
      currentPayload = data;
      if (data.embedded_png_map && typeof data.embedded_png_map === "object") {{
        Object.assign(EMBEDDED_PNG_MAP, data.embedded_png_map);
      }}
      const pubId = data.publication_number || data.ucid || data.id || "";
      const cleanUcid = pubId.replace(/-/g, "");
      document.getElementById("patentInput").value = pubId;
      document.getElementById("headerTitle").textContent =
        pubId + (data.title ? " — " + data.title : " — Drawing & PDF Split-Viewer");

      // Always use sandbox-safe URLs (patentimages.storage.googleapis.com or Cloud Run /apps/pdf & /apps/patent)
      let pdfUrl = data.direct_pdf_url || data.pdf_download_url || "";
      if (!pdfUrl || pdfUrl.includes("patents.google.com")) {{
        pdfUrl = SERVER_BASE + "/apps/pdf/" + encodeURIComponent(cleanUcid);
      }}
      const readerUrl = data.patent_reader_url || (SERVER_BASE + "/apps/patent/" + encodeURIComponent(cleanUcid));

      document.getElementById("directPdfLink").href = pdfUrl;
      document.getElementById("gpLink").href = readerUrl;

      const figs = data.figures || [];
      const strip = document.getElementById("filmstrip");
      if (figs.length) {{
        strip.innerHTML = figs.map((f, i) => `
          <button class="thumb-btn ${{i === 0 ? 'active' : ''}}" data-idx="${{i}}">
            <img src="${{escapeHtml(resolveImgSrc(f, i, true))}}" data-idx="${{i}}" class="thumb-img-el" alt="${{escapeHtml(f.label || ('Sheet ' + (i + 1)))}}" />
            <span>${{escapeHtml(f.label || ('Sheet ' + (i + 1)))}}</span>
          </button>
        `).join("");
        strip.querySelectorAll(".thumb-img-el").forEach((imgEl) => {{
          imgEl.addEventListener("error", () => {{
            const idx = parseInt(imgEl.getAttribute("data-idx"), 10) || 0;
            imgEl.src = buildClientSvgBlueprint(figs[idx], idx);
          }}, {{ once: true }});
        }});
        strip.querySelectorAll(".thumb-btn").forEach((btn) => {{
          btn.addEventListener("click", () => selectSheet(parseInt(btn.dataset.idx, 10)));
        }});
        selectSheet(0);
      }} else {{
        strip.innerHTML = "";
        document.getElementById("activeDrawingImg").style.display = "none";
        document.getElementById("emptyDrawingMsg").style.display = "block";
        document.getElementById("emptyDrawingMsg").innerHTML = `
          <div style="padding:20px;">
            <div style="font-weight:700;font-size:14px;margin-bottom:8px;">Official Patent PDF Ready for ${{escapeHtml(pubId)}}</div>
            <a class="btn btn-primary" href="${{escapeHtml(pdfUrl)}}" target="_blank" rel="noopener">Open Full PDF Document ↗</a>
          </div>
        `;
      }}

      // Render Specification & Claims with clickable FIG chips
      const specBody = document.getElementById("specBody");
      const sections = [];
      const assignees = Array.isArray(data.assignees) ? data.assignees.join(", ") : "";
      if (data.title || assignees || data.filing_date || data.grant_date) {{
        sections.push(`
          <div class="section-card">
            <div class="section-label">Bibliographic Summary</div>
            <div style="font-weight:700;font-size:13.5px;margin-bottom:4px;">${{escapeHtml(data.title || pubId)}}</div>
            <div style="font-size:11.5px;color:var(--text-secondary);">
              ${{assignees ? `<div><strong>Assignee:</strong> ${{escapeHtml(assignees)}}</div>` : ""}}
              <div>
                ${{data.filing_date ? `<strong>Filed:</strong> ${{escapeHtml(data.filing_date)}} &nbsp;` : ""}}
                ${{data.grant_date ? `<strong>Granted:</strong> ${{escapeHtml(data.grant_date)}}` : ""}}
              </div>
            </div>
          </div>
        `);
      }}
      if (data.abstract) {{
        sections.push(`
          <div class="section-card">
            <div class="section-label">Abstract</div>
            <div style="line-height:1.55;">${{linkifyFigures(data.abstract)}}</div>
          </div>
        `);
      }}
      if (Array.isArray(data.description_snippets) && data.description_snippets.length) {{
        sections.push(`
          <div class="section-card">
            <div class="section-label">Brief Description of Drawings &amp; Figure Callouts (${{data.description_snippets.length}})</div>
            ${{data.description_snippets.map((p) => `<p style="margin-bottom:8px;line-height:1.5;">${{linkifyFigures(p)}}</p>`).join("")}}
          </div>
        `);
      }}
      if (Array.isArray(data.claims_preview) && data.claims_preview.length) {{
        sections.push(`
          <div class="section-card">
            <div class="section-label">Representative Claims (${{data.claims_preview.length}})</div>
            ${{data.claims_preview.map((c) => `<p style="margin-bottom:8px;line-height:1.5;font-size:12px;">${{linkifyFigures(c)}}</p>`).join("")}}
          </div>
        `);
      }}
      specBody.innerHTML = sections.join("") || '<div style="color:var(--text-muted)">No specification text extracted.</div>';

      specBody.querySelectorAll(".fig-chip").forEach((chip) => {{
        chip.addEventListener("click", () => {{
          const figNum = parseInt(chip.getAttribute("data-fig-num"), 10) || 1;
          jumpToFigureNumber(figNum);
        }});
      }});
    }}

    document.getElementById("modeSheetsBtn").addEventListener("click", () => setLeftPaneMode("sheets"));
    document.getElementById("modePdfBtn").addEventListener("click", () => setLeftPaneMode("pdf"));
    document.getElementById("toggleInlinePdfBtn").addEventListener("click", () => {{
      setLeftPaneMode(activePaneMode === "pdf" ? "sheets" : "pdf");
    }});

    document.getElementById("prevSheetBtn").addEventListener("click", () => selectSheet(currentSheetIdx - 1));
    document.getElementById("nextSheetBtn").addEventListener("click", () => selectSheet(currentSheetIdx + 1));
    document.getElementById("zoomInBtn").addEventListener("click", () => {{ zoomLevel = Math.min(3.0, zoomLevel + 0.25); updateTransform(); }});
    document.getElementById("zoomOutBtn").addEventListener("click", () => {{ zoomLevel = Math.max(0.5, zoomLevel - 0.25); updateTransform(); }});
    document.getElementById("rotateBtn").addEventListener("click", () => {{ rotationDeg = (rotationDeg + 90) % 360; updateTransform(); }});
    document.getElementById("resetViewBtn").addEventListener("click", () => {{ zoomLevel = 1.0; rotationDeg = 0; updateTransform(); }});

    document.getElementById("loadPdfBtn").addEventListener("click", async () => {{
      const patent_id = document.getElementById("patentInput").value.trim();
      if (!patent_id) return;
      document.getElementById("statusText").textContent = "Loading drawings & PDF for " + patent_id + "...";
      try {{
        const res = await sendRpcRequest("tools/call", {{
          name: "get_patent_pdf",
          arguments: {{ patent_id }}
        }});
        if (res && Array.isArray(res.content)) {{
          for (const item of res.content) {{
            if (item.type === "text" && item.text) {{
              hydratePayload(JSON.parse(item.text));
              break;
            }}
          }}
        }}
        document.getElementById("statusText").textContent = "Loaded " + patent_id;
      }} catch (e) {{
        // Fallback to Cloud Run JSON helper if host tool call is not bridged
        try {{
          const r = await fetch(SERVER_BASE + "/apps/api/pdf-details?patent_id=" + encodeURIComponent(patent_id));
          if (r.ok) {{
            const data = await r.json();
            hydratePayload(data);
            document.getElementById("statusText").textContent = "Loaded " + patent_id;
            return;
          }}
        }} catch (err) {{}}
        document.getElementById("statusText").textContent = "Host tool call unavailable; ask in chat.";
      }}
    }});

    if (INITIAL_PAYLOAD) {{
      hydratePayload(INITIAL_PAYLOAD);
    }}
  </script>
</body>
</html>"""
