import json
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.paper_chunk import PaperChunk
from app.schemas.rag import (
    IndexedPaperOut,
    IndexPaperRequest,
    IndexPaperResponse,
    RAGQueryRequest,
    RAGQueryResponse,
)
from app.services.rag_service import extract_pdf_pages_from_bytes, index_paper, query_rag

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/index", response_model=IndexPaperResponse, status_code=status.HTTP_201_CREATED)
async def index_paper_endpoint(
    payload: IndexPaperRequest,
    db: AsyncSession = Depends(get_db),
):
    """Indexes a research paper from search results or manual input into RAG."""
    paper_id = str(uuid.uuid4())
    p_id, chunk_count = await index_paper(
        title=payload.title,
        abstract=payload.abstract,
        authors=payload.authors,
        year=payload.year,
        doi=payload.doi,
        source=payload.source,
        pdf_url=payload.pdf_url,
        paper_id=paper_id,
        db=db,
    )
    return IndexPaperResponse(
        paper_id=p_id,
        title=payload.title,
        chunks_created=chunk_count,
        status="indexed",
    )


@router.post("/upload", response_model=IndexPaperResponse, status_code=status.HTTP_201_CREATED)
async def upload_pdf_endpoint(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Uploads a PDF paper and indexes all pages into RAG."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported.",
        )

    paper_id = str(uuid.uuid4())
    paper_title = os.path.splitext(file.filename)[0].replace("_", " ").replace("-", " ")

    # Save to disk
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    local_path = os.path.join(settings.STORAGE_DIR, f"{paper_id}.pdf")
    content = await file.read()
    with open(local_path, "wb") as f:
        f.write(content)

    p_id, chunk_count = await index_paper(
        title=paper_title,
        abstract="",
        source="upload",
        local_pdf_path=local_path,
        paper_id=paper_id,
        db=db,
    )

    return IndexPaperResponse(
        paper_id=p_id,
        title=paper_title,
        chunks_created=chunk_count,
        status="indexed",
    )


@router.post("/query", response_model=RAGQueryResponse)
async def query_rag_endpoint(
    payload: RAGQueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """Queries indexed research papers using RAG with citation grounding."""
    return await query_rag(
        query=payload.query,
        paper_ids=payload.paper_ids,
        top_k=payload.top_k,
        api_key=payload.api_key,
        mode=payload.mode,
        db=db,
    )


@router.get("/papers", response_model=list[IndexedPaperOut])
async def list_indexed_papers(
    db: AsyncSession = Depends(get_db),
):
    """Returns all papers currently indexed in the RAG knowledge base."""
    # Group chunks by paper_id
    stmt = (
        select(
            PaperChunk.paper_id,
            PaperChunk.paper_title,
            PaperChunk.metadata_json,
            func.count(PaperChunk.id).label("chunk_count"),
            func.min(PaperChunk.created_at).label("created_at"),
        )
        .group_by(PaperChunk.paper_id, PaperChunk.paper_title, PaperChunk.metadata_json)
        .order_by(func.min(PaperChunk.created_at).desc())
    )
    results = await db.execute(stmt)

    papers = []
    for row in results:
        meta = json.loads(row.metadata_json) if row.metadata_json else {}
        papers.append(
            IndexedPaperOut(
                paper_id=row.paper_id or "unknown",
                title=row.paper_title,
                authors=meta.get("authors", []),
                year=meta.get("year"),
                source=meta.get("source", "manual"),
                chunk_count=row.chunk_count,
                created_at=row.created_at,
            )
        )
    return papers


@router.delete("/papers/{paper_id}")
async def delete_indexed_paper(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Removes a paper and its chunks from the RAG knowledge base."""
    await db.execute(delete(PaperChunk).where(PaperChunk.paper_id == paper_id))
    await db.commit()
    return {"deleted": True, "paper_id": paper_id}
