from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Central app configuration. Values are read from environment variables /
    a .env file at the backend/ root. See .env.example at the repo root.
    """

    APP_NAME: str = "Intelligent Academic Research Assistant"
    ENV: str = "development"

    # Database — SQLite for dev, swap DATABASE_URL for Postgres later
    # (SQLAlchemy async URL, e.g. postgresql+asyncpg://... for Neon)
    DATABASE_URL: str = "sqlite+aiosqlite:///./ara.db"

    # Auth
    JWT_SECRET_KEY: str = "change-me-in-.env"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # CORS — frontend dev server
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # External academic APIs (Phase 2 — arXiv needs no key; add others later)
    SEMANTIC_SCHOLAR_API_KEY: str | None = None
    CROSSREF_MAILTO: str | None = None

    # LLM providers (Phase 3 — not wired yet, placeholders for later)
    GEMINI_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
