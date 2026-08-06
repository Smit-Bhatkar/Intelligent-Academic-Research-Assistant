"""
arXiv search service — Phase 2, first data source (FR2).

arXiv needs no API key, so this is the first end-to-end-testable piece of
the retrieval pipeline. Semantic Scholar and CrossRef follow the same
`search(query, max_results) -> list[PaperResult]` shape, so the search
route (Section 8, System Architecture) can fan out to all three later
without changing its own code — this is deliberately built as a small
"provider" interface, mirroring the Chain-of-Responsibility shape used
later for the LLM failover (Section 11 of the blueprint).
"""

import arxiv

from app.schemas.paper import PaperResult


def search_arxiv(query: str, max_results: int = 10) -> list[PaperResult]:
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    results: list[PaperResult] = []
    for entry in client.results(search):
        results.append(
            PaperResult(
                title=entry.title.strip(),
                authors=[a.name for a in entry.authors],
                abstract=entry.summary.strip().replace("\n", " "),
                doi=entry.doi,
                source="arxiv",
                year=entry.published.year if entry.published else None,
                pdf_url=entry.pdf_url,
            )
        )
    return results
