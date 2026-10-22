from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_auth
from app.db.session import get_db
from app.models.papers import Paper
from app.models.research_project import ResearchProject
from app.models.user import User
from app.schemas.project import PaperOut, ProjectCreate, ProjectOut, SavePaperRequest

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    project = ResearchProject(
        user_id=current_user.id,
        title=payload.title,
        topic=payload.topic,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("", response_model=list[ProjectOut])
async def list_projects(
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    result = await db.scalars(
        select(ResearchProject).where(ResearchProject.user_id == current_user.id)
    )
    return list(result)


async def _get_owned_project(
    project_id: str, current_user: User, db: AsyncSession
) -> ResearchProject:
    project = await db.scalar(
        select(ResearchProject).where(ResearchProject.id == project_id)
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your project")
    return project


@router.post(
    "/{project_id}/papers", response_model=PaperOut, status_code=status.HTTP_201_CREATED
)
async def save_paper(
    project_id: str,
    payload: SavePaperRequest,
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_project(project_id, current_user, db)

    paper = Paper(
        project_id=project_id,
        title=payload.title,
        authors=", ".join(payload.authors),
        abstract=payload.abstract,
        doi=payload.doi,
        source=payload.source,
        year=payload.year,
        pdf_url=payload.pdf_url,
    )
    db.add(paper)
    await db.commit()
    await db.refresh(paper)
    return PaperOut.from_orm_paper(paper)


@router.get("/{project_id}/papers", response_model=list[PaperOut])
async def list_papers(
    project_id: str,
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_project(project_id, current_user, db)

    result = await db.scalars(select(Paper).where(Paper.project_id == project_id))
    return [PaperOut.from_orm_paper(p) for p in result]