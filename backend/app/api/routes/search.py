from fastapi import APIRouter, Query

from app.schemas.paper import PaperResult
from app.services.arxiv_service import search_arxiv

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/papers", response_model=list[PaperResult])
def search_papers(q: str = Query(..., min_length=2), max_results: int = 10):
    """
    FR2 — search research papers by keyword/topic.

    Currently fans out to arXiv only (no API key required). Semantic
    Scholar and CrossRef plug in here next: call each provider's
    `search()`, merge + de-duplicate by DOI/title, same PaperResult shape.
    """
    return search_arxiv(query=q, max_results=max_results)
