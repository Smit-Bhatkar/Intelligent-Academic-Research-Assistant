from datetime import datetime

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    title: str
    topic: str


class ProjectOut(BaseModel):
    id: str
    title: str
    topic: str
    created_at: datetime

    class Config:
        from_attributes = True


class SavePaperRequest(BaseModel):
    title: str
    authors: list[str]
    abstract: str
    doi: str | None = None
    source: str
    year: int | None = None
    pdf_url: str | None = None


class PaperOut(BaseModel):
    id: str
    project_id: str
    title: str
    authors: list[str]
    abstract: str
    doi: str | None
    source: str
    year: int | None
    pdf_url: str | None
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_paper(cls, paper) -> "PaperOut":
        return cls(
            id=paper.id,
            project_id=paper.project_id,
            title=paper.title,
            authors=[a.strip() for a in paper.authors.split(",") if a.strip()],
            abstract=paper.abstract,
            doi=paper.doi,
            source=paper.source,
            year=paper.year,
            pdf_url=paper.pdf_url,
            created_at=paper.created_at,
        )