import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Paper(Base):
    """
    Matches the `Paper` entity in the SRS Class Diagram (Section 10).

    NOTE: per the SRS System Architecture (Section 8), full paper chunks +
    embeddings will live in ChromaDB once the RAG pipeline (Phase 3) is
    built. This table is a lightweight relational cache of search-result
    metadata (from arXiv/Semantic Scholar/CrossRef) so results, favorites,
    and project associations survive across sessions in the meantime.
    """

    __tablename__ = "papers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(500))
    authors: Mapped[str] = mapped_column(Text)  # comma-separated for now
    abstract: Mapped[str] = mapped_column(Text)
    doi: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source: Mapped[str] = mapped_column(String(50))  # "arxiv" | "semantic_scholar" | "crossref"
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pdf_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
