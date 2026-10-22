"""
arXiv search service — Phase 2, first data source (FR2).
"""

import requests

from app.schemas.paper import PaperResult


ARXIV_API_URL = "https://export.arxiv.org/api/query"


def search_arxiv(query: str, max_results: int = 10) -> list[PaperResult]:
    # Keep requests reasonably small.
    max_results = max(1, min(max_results, 20))

    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }

    response = requests.get(
        ARXIV_API_URL,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    # arXiv returns Atom XML.
    import xml.etree.ElementTree as ET

    root = ET.fromstring(response.text)

    namespace = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }

    results: list[PaperResult] = []

    for entry in root.findall("atom:entry", namespace):
        title_element = entry.find("atom:title", namespace)
        summary_element = entry.find("atom:summary", namespace)
        published_element = entry.find("atom:published", namespace)

        title = (
            title_element.text.strip()
            if title_element is not None and title_element.text
            else ""
        )

        abstract = (
            summary_element.text.strip().replace("\n", " ")
            if summary_element is not None and summary_element.text
            else ""
        )

        authors = []

        for author in entry.findall("atom:author", namespace):
            name_element = author.find("atom:name", namespace)

            if name_element is not None and name_element.text:
                authors.append(name_element.text.strip())

        # Extract PDF URL from the <link> elements.
        pdf_url = None

        for link in entry.findall("atom:link", namespace):
            if link.attrib.get("title") == "pdf":
                pdf_url = link.attrib.get("href")
                break

        # Extract DOI if available.
        doi = None

        doi_element = entry.find("arxiv:doi", namespace)

        if doi_element is not None and doi_element.text:
            doi = doi_element.text.strip()

        # Extract publication year.
        year = None

        if published_element is not None and published_element.text:
            year = int(published_element.text[:4])

        results.append(
            PaperResult(
                title=title,
                authors=authors,
                abstract=abstract,
                doi=doi,
                source="arxiv",
                year=year,
                pdf_url=pdf_url,
            )
        )

    return results