from datetime import datetime
from pydantic import BaseModel, Field


class IndexPaperRequest(BaseModel):
    title: str
    abstract: str = ""
    authors: list[str] = []
    year: int | None = None
    doi: str | None = None
    source: str = "manual"
    pdf_url: str | None = None


class IndexPaperResponse(BaseModel):
    paper_id: str
    title: str
    chunks_created: int
    status: str


class RAGQueryRequest(BaseModel):
    query: str
    paper_ids: list[str] | None = None
    top_k: int = Field(default=5, ge=1, le=20)
    api_key: str | None = None
    mode: str = "qa"  # qa | summarize | methodology | gaps | bibtex


class Citation(BaseModel):
    paper_title: str
    authors: list[str] = []
    year: int | None = None
    page_number: int | None = None
    chunk_index: int
    snippet: str
    similarity_score: float


class RAGQueryResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    answer: str
    citations: list[Citation]
    mode_used: str
    fallback_mode: bool
    model_used: str


class IndexedPaperOut(BaseModel):
    paper_id: str
    title: str
    authors: list[str]
    year: int | None
    source: str
    chunk_count: int
    created_at: datetime
