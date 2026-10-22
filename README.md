# Intelligent Academic Research Assistant (ARA)

This is the **Phase 1 (Foundations), Phase 2 (Multi-Source Retrieval), and Phase 3 (RAG Core & Multi-Tier LLM Router)**
build of the project described in the SRS (`Group_7___SRS_MINOR_PROJECT_II.docx`)
and the full architecture blueprint.

> 📖 **Full Project Documentation**: See [PROJECT.md](PROJECT.md) for in-depth architecture diagrams, database schema, complete API specifications, LLM failover details, and SRS requirement mapping.  
> 📌 **Milestones & Status**: See [PROGRESS.md](PROGRESS.md) for current implementation progress and next steps.

## What's here

- **backend/** — FastAPI + SQLAlchemy (async, SQLite) + JWT auth + multi-source academic search (arXiv, Semantic Scholar, CrossRef) + RAG engine with cascading multi-tier LLM router (Gemini -> Groq -> Ollama -> Extractive).
- **frontend/** — React + TypeScript + Vite + Tailwind, featuring Multi-Source Search and an Interactive Academic Assistant with grounded citations.
- **docker-compose.yml** — runs both together for local dev.

## Quick start (without Docker)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env         # edit JWT_SECRET_KEY at minimum
uvicorn app.main:app --reload
```

Backend runs at `http://localhost:8000` — interactive API docs at
`http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

## Quick start (with Docker)

```bash
cp .env.example .env    # edit JWT_SECRET_KEY at minimum
docker compose up --build
```

## Verifying it works

```bash
# Health check
curl http://localhost:8000/health

# Register + login
curl -X POST http://localhost:8000/auth/register -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"testpass123"}'

curl -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" \
  -d '{"name":"x","email":"test@example.com","password":"testpass123"}'

# Paper search (real arXiv API call — needs internet)
curl "http://localhost:8000/search/papers?q=retrieval%20augmented%20generation&max_results=3"
```

All three were tested and confirmed working during development (see
`PROGRESS.md` for details and known environment caveats).

## Tech stack (per SRS Section 7.4)

| Layer | Choice |
|---|---|
| Backend | Python 3.11+, FastAPI, SQLAlchemy (async), SQLite (dev) |
| Frontend | React (TypeScript), Vite, TailwindCSS |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Academic data | arXiv API (live), Semantic Scholar + CrossRef (next) |
| Future (Phase 3+) | LangChain, ChromaDB, Gemini/Groq/Ollama failover |

## Project structure

```
backend/
  app/
    core/       # config, security (JWT, password hashing)
    db/         # SQLAlchemy engine/session/base
    models/     # User, ResearchProject, Paper (ORM)
    schemas/    # Pydantic request/response models
    api/routes/ # health, auth, search
    services/   # arxiv_service.py (Phase 2)
    main.py     # app entrypoint, router wiring, CORS
frontend/
  src/
    api/client.ts   # typed API client
    pages/          # Home, Search
    App.tsx          # routing
```
