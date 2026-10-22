from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Intelligent Academic Research Assistant"
    ENV: str = "development"

    DATABASE_URL: str = "sqlite+aiosqlite:///./ara.db"

    JWT_SECRET_KEY: str = "change-me-in-.env"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    SEMANTIC_SCHOLAR_API_KEY: str | None = None
    CROSSREF_MAILTO: str | None = None

    GEMINI_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None

    # NEW — where downloaded PDFs are stored on disk
    STORAGE_DIR: str = "./storage/pdfs"
    # NEW — where the ChromaDB vector database is stored
    CHROMA_DIR: str = "./storage/chroma"
    # NEW — which embedding model to use
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()