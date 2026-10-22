"""
CrossRef search service — Phase 2 academic repository integration (FR2).
"""

import logging
import re
from typing import Any

import httpx

from app.core.config import settings
from app.schemas.paper import PaperResult

logger = logging.getLogger(__name__)

CROSSREF_API_URL = "https://api.crossref.org/works"


def _clean_jats_abstract(raw_abstract: str) -> str:
    """Strips JATS XML markup (e.g. <jats:p>, <jats:sec>) from CrossRef abstracts."""
    if not raw_abstract:
        return ""
    # Remove XML tags
    cleaned = re.sub(r"<[^>]+>", " ", raw_abstract)
    # Collapse multiple whitespace characters
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


async def search_crossref(query: str, max_results: int = 10) -> list[PaperResult]:
    """
    Searches CrossRef REST API for published academic works.
    Returns a list of PaperResult objects.
    """
    max_results = max(1, min(max_results, 20))
    params = {
        "query": query,
        "rows": max_results,
        "sort": "relevance",
        "order": "desc",
    }

    mailto = settings.CROSSREF_MAILTO or "assistant@academicresearch.org"
    headers = {
        "User-Agent": f"IntelligentAcademicResearchAssistant/1.0 (mailto:{mailto})"
    }

    results: list[PaperResult] = []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                CROSSREF_API_URL, params=params, headers=headers
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
    except Exception as exc:
        logger.warning(f"CrossRef search failed for query '{query}': {exc}")
        return []

    items = data.get("message", {}).get("items", [])
    for item in items:
        # Title is typically a list of strings
        titles = item.get("title", [])
        title = (titles[0] if titles else "").strip()
        if not title:
            continue

        # Extract authors
        authors: list[str] = []
        for author in item.get("author", []):
            given = author.get("given", "").strip()
            family = author.get("family", "").strip()
            name = f"{given} {family}".strip()
            if name:
                authors.append(name)

        # Extract and clean abstract
        raw_abstract = item.get("abstract", "")
        abstract = _clean_jats_abstract(raw_abstract)

        # Extract publication year
        year: int | None = None
        date_parts = (
            item.get("published-print", {}).get("date-parts")
            or item.get("published-online", {}).get("date-parts")
            or item.get("created", {}).get("date-parts")
        )
        if date_parts and date_parts[0] and isinstance(date_parts[0][0], int):
            year = date_parts[0][0]

        # Extract DOI
        doi = item.get("DOI")

        # Extract PDF URL if explicitly listed in links
        pdf_url: str | None = None
        for link in item.get("link", []):
            content_type = (link.get("content-type") or "").lower()
            url = link.get("URL")
            if "pdf" in content_type or (url and url.lower().endswith(".pdf")):
                pdf_url = url
                break

        results.append(
            PaperResult(
                title=title,
                authors=authors,
                abstract=abstract,
                doi=doi,
                source="crossref",
                year=year,
                pdf_url=pdf_url,
            )
        )

    return results
