from contextlib import asynccontextmanager

from app.models import papers
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, health, paper, projects, rag, search
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine

from app.models import user, research_project, paper_chunk  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(search.router)
app.include_router(projects.router)
app.include_router(paper.router)
app.include_router(rag.router)


@app.get("/")
def root():
    return {"app": settings.APP_NAME, "status": "running", "docs": "/docs"}