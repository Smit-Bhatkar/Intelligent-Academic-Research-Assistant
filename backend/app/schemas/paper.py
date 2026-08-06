from pydantic import BaseModel


class PaperResult(BaseModel):
    """Response shape for FR2 — unified paper search results across sources."""

    title: str
    authors: list[str]
    abstract: str
    doi: str | None = None
    source: str
    year: int | None = None
    pdf_url: str | None = None
