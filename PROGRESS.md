# PROGRESS.md — Intelligent Academic Research Assistant

Single reference for continuing this project in a future session (this chat,
a new chat, or Claude Code) without re-explaining context. Read this first.

**Status: ~55% complete**, mapped against the SRS Gantt chart (Section 12):
Phase 1 (Foundations) is done, Phase 2 (Paper Retrieval) is complete, and
Phase 3 (RAG Core & LLM Router) is active and integrated. Phases 4, 5, 6
are up next.

---

## ✅ Done and verified working

### Phase 1 — Foundations
- FastAPI project skeleton with the layered structure from SRS Section 8
  (`core/`, `db/`, `models/`, `schemas/`, `api/routes/`, `services/`).
- Async SQLAlchemy setup (SQLite for dev, swappable to Postgres via
  `DATABASE_URL` — no code changes needed, per SRS NFR6).
- ORM models: `User`, `ResearchProject`, `Paper` (matches SRS Class Diagram,
  Section 10). `PaperChunk` model for RAG chunks and vector embeddings.
- Auth (FR1): register, login, JWT issuance, bcrypt password hashing.
  **Tested live**: register → login → duplicate-email rejection (400) all
  passed against a running server.
- `require_auth` dependency in `core/deps.py` protecting `/projects` and `/papers`.
- React + TypeScript + Vite + Tailwind frontend skeleton, with routing
  (Home, Search, Assistant pages). **Verified**: `npm install`, `tsc -b` typecheck,
  and `vite build` all pass cleanly.
- `docker-compose.yml` wiring backend + frontend for local dev.

### Phase 2 — Multi-Source Paper Retrieval (Complete)
- **arXiv search service** (`arxiv_service.py`) using arXiv API.
- **Semantic Scholar search service** (`semantic_scholar_service.py`) querying
  Semantic Scholar Graph API with optional API key support.
- **CrossRef search service** (`crossref_service.py`) with polite User-Agent,
  JATS XML tag stripping from abstracts, and open-access PDF extraction.
- **Concurrent Fan-Out & Deduplication** (`search.py`):
  - Concurrent `asyncio.gather` across arXiv, Semantic Scholar, and CrossRef.
  - Two-stage deduplication by normalized DOI and normalized title.
  - Metadata merging preserving richest abstracts, authors, and direct PDF links.
- **Frontend Search Page** (`Search.tsx`):
  - Distinct colored badges for sources (arXiv, Semantic Scholar, CrossRef).
  - Direct "Ask with RAG" integration carrying paper metadata into the Assistant.
- **Project & Paper Management**:
  - `POST /projects` and `POST /projects/{id}/papers` endpoints for saving search results.
  - `POST /papers/{id}/download` for automated PDF caching to disk.

### Phase 3 — RAG Core & LLM Router
- PDF text extraction (`pypdf`) and semantic chunking with overlap.
- Vector embedding and cosine similarity ranking.
- **LLM Router Failover Chain** (`llm_router.py`):
  - Cascades through **Gemini** → **Groq** → **Local Ollama** → **Extractive Fallback**.
  - Provides zero-API-key offline fallback ensuring the system never breaks.
- Interactive Research Assistant UI (`Assistant.tsx`):
  - Indexed paper management, PDF upload, multi-paper selection.
  - Specialized research prompts: Comprehensive Q&A, Executive Summary, Methodology Analysis, Research Gaps, BibTeX generation.
  - Grounded citation badges with snippet inspection and similarity scoring.

---

## ⏭️ Next up (Phases 4–6)

1. **Phase 4: Advanced Analysis & Knowledge Synthesis**
   - Automated keyword extraction & topic modeling across project papers.
   - Cross-paper comparison matrix (comparing methodologies, datasets, findings).
   - Automated research gap identification and literature review generation.
2. **Phase 5: Citation & Export Tools**
   - Direct export to BibTeX, APA, MLA, Chicago formats.
   - Project export as Markdown or PDF report.
3. **Phase 6: Production Polish & Deployment**
   - Background worker tasks for large PDF processing.
   - Production Docker configurations and CI/CD pipelines.

---

## How to resume this in one line

> "Continue the Academic Research Assistant from PROGRESS.md — build Phase 4 (topic modeling and paper comparison matrix)."

That's enough context for a fresh session to pick this up correctly.
