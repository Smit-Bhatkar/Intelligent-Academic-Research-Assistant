"""
Semantic Scholar search service — Phase 2 academic repository integration (FR2).
"""

import logging
from typing import Any

import httpx

from app.core.config import settings
from app.schemas.paper import PaperResult

logger = logging.getLogger(__name__)

SEMANTIC_SCHOLAR_API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"


async def search_semantic_scholar(
    query: str, max_results: int = 10
) -> list[PaperResult]:
    """
    Searches Semantic Scholar Academic Graph API for research papers.
    Returns a list of PaperResult objects.
    """
    max_results = max(1, min(max_results, 20))
    params = {
        "query": query,
        "offset": 0,
        "limit": max_results,
        "fields": "title,authors,abstract,year,externalIds,openAccessPdf",
    }
    headers: dict[str, str] = {}
    if settings.SEMANTIC_SCHOLAR_API_KEY:
        headers["x-api-key"] = settings.SEMANTIC_SCHOLAR_API_KEY

    results: list[PaperResult] = []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                SEMANTIC_SCHOLAR_API_URL, params=params, headers=headers
            )
            if response.status_code == 429:
                logger.warning("Semantic Scholar rate limit hit (HTTP 429).")
                return []
            response.raise_for_status()
            data: dict[str, Any] = response.json()
    except Exception as exc:
        logger.warning(f"Semantic Scholar search failed for query '{query}': {exc}")
        return []

    papers = data.get("data", [])
    for item in papers:
        title = (item.get("title") or "").strip()
        if not title:
            continue

        abstract = (item.get("abstract") or "").strip()
        authors = [
            a.get("name").strip()
            for a in item.get("authors", [])
            if a.get("name") and a.get("name").strip()
        ]
        year = item.get("year")
        external_ids = item.get("externalIds") or {}
        doi = external_ids.get("DOI")

        open_access_pdf = item.get("openAccessPdf") or {}
        pdf_url = open_access_pdf.get("url")

        results.append(
            PaperResult(
                title=title,
                authors=authors,
                abstract=abstract,
                doi=doi,
                source="semanticscholar",
                year=year,
                pdf_url=pdf_url,
            )
        )

    return results
