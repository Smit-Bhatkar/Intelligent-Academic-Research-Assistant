import asyncio
import re
from fastapi import APIRouter, Query

from app.schemas.paper import PaperResult
from app.services.arxiv_service import search_arxiv
from app.services.crossref_service import search_crossref
from app.services.semantic_scholar_service import search_semantic_scholar

router = APIRouter(prefix="/search", tags=["search"])


def _normalize_title(title: str) -> str:
    """Normalizes title by removing punctuation and collapsing whitespace for fuzzy comparison."""
    return re.sub(r"[^\w\s]", "", title.lower()).strip()


def _merge_paper_results(existing: PaperResult, incoming: PaperResult) -> PaperResult:
    """Merges two duplicate paper results, preserving the richest metadata."""
    # Choose longer abstract
    best_abstract = (
        incoming.abstract
        if len(incoming.abstract or "") > len(existing.abstract or "")
        else existing.abstract
    )
    # Prefer existing pdf_url, fallback to incoming
    best_pdf = existing.pdf_url or incoming.pdf_url
    # Prefer non-empty authors
    best_authors = existing.authors if existing.authors else incoming.authors
    # Prefer valid DOI
    best_doi = existing.doi or incoming.doi
    # Prefer year
    best_year = existing.year or incoming.year
    # Combine sources if distinct
    sources = set(filter(None, [existing.source, incoming.source]))
    combined_source = "/".join(sorted(sources)) if sources else existing.source

    return PaperResult(
        title=existing.title or incoming.title,
        authors=best_authors,
        abstract=best_abstract,
        doi=best_doi,
        source=combined_source,
        year=best_year,
        pdf_url=best_pdf,
    )


def deduplicate_papers(papers: list[PaperResult]) -> list[PaperResult]:
    """
    De-duplicates papers primarily by DOI, and secondarily by normalized title.
    Enriches duplicate entries with the highest quality metadata.
    """
    doi_map: dict[str, PaperResult] = {}
    title_map: dict[str, PaperResult] = {}
    merged_list: list[PaperResult] = []

    for paper in papers:
        norm_doi = paper.doi.strip().lower() if paper.doi else None
        norm_title = _normalize_title(paper.title)

        matched_paper: PaperResult | None = None

        if norm_doi and norm_doi in doi_map:
            matched_paper = doi_map[norm_doi]
        elif norm_title and norm_title in title_map:
            matched_paper = title_map[norm_title]

        if matched_paper:
            # Merge into the existing record
            updated = _merge_paper_results(matched_paper, paper)
            # Update mappings
            idx = merged_list.index(matched_paper)
            merged_list[idx] = updated
            if norm_doi:
                doi_map[norm_doi] = updated
            if norm_title:
                title_map[norm_title] = updated
        else:
            merged_list.append(paper)
            if norm_doi:
                doi_map[norm_doi] = paper
            if norm_title:
                title_map[norm_title] = paper

    return merged_list


@router.get("/papers", response_model=list[PaperResult])
async def search_papers(q: str = Query(..., min_length=2), max_results: int = 10):
    """
    FR2 — multi-source paper retrieval.
    Fans out concurrently to arXiv, Semantic Scholar, and CrossRef,
    then merges and de-duplicates results by DOI and title.
    """
    # Run all three retrievers concurrently
    results = await asyncio.gather(
        asyncio.to_thread(search_arxiv, q, max_results),
        search_semantic_scholar(q, max_results),
        search_crossref(q, max_results),
        return_exceptions=True,
    )

    all_papers: list[PaperResult] = []
    for res in results:
        if isinstance(res, list):
            all_papers.extend(res)

    deduped = deduplicate_papers(all_papers)
    # Return up to requested total or max_results * 2 for high discovery yield
    limit = max(max_results, min(len(deduped), max_results * 2))
    return deduped[:limit]
