from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_auth
from app.db.session import get_db
from app.models.papers import Paper
from app.models.research_project import ResearchProject
from app.models.user import User
from app.services.pdf_service import PDFDownloadError, download_pdf

router = APIRouter(prefix="/papers", tags=["papers"])


async def _get_owned_paper(paper_id: str, current_user: User, db: AsyncSession) -> Paper:
    paper = await db.scalar(select(Paper).where(Paper.id == paper_id))
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    project = await db.scalar(
        select(ResearchProject).where(ResearchProject.id == paper.project_id)
    )
    if project is None or project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your paper")
    return paper


@router.post("/{paper_id}/download")
async def download_paper_pdf(
    paper_id: str,
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    paper = await _get_owned_paper(paper_id, current_user, db)
    if not paper.pdf_url:
        raise HTTPException(status_code=400, detail="Paper has no pdf_url")

    try:
        local_path = await download_pdf(paper.id, paper.pdf_url)
    except PDFDownloadError as e:
        raise HTTPException(status_code=502, detail=str(e))

    paper.local_pdf_path = local_path
    await db.commit()
    return {"paper_id": paper.id, "local_pdf_path": local_path}