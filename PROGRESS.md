# PROGRESS.md — Intelligent Academic Research Assistant

Single reference for continuing this project in a future session (this chat,
a new chat, or Claude Code) without re-explaining context. Read this first.

**Status: ~20% complete**, mapped against the SRS Gantt chart (Section 12):
Phase 1 (Foundations) is done, and the first slice of Phase 2 (Paper
Retrieval) is done. Phases 2 (remainder), 3, 4, 5, 6 are not started.

---

## ✅ Done and verified working

### Phase 1 — Foundations
- FastAPI project skeleton with the layered structure from SRS Section 8
  (`core/`, `db/`, `models/`, `schemas/`, `api/routes/`, `services/`).
- Async SQLAlchemy setup (SQLite for dev, swappable to Postgres via
  `DATABASE_URL` — no code changes needed, per SRS NFR6).
- ORM models: `User`, `ResearchProject`, `Paper` (matches SRS Class Diagram,
  Section 10). `Paper` here is a lightweight relational cache of search
  results — full chunk/embedding storage in ChromaDB is Phase 3, not built.
- Auth (FR1): register, login, JWT issuance, bcrypt password hashing.
  **Tested live**: register → login → duplicate-email rejection (400) all
  passed against a running server.
- React + TypeScript + Vite + Tailwind frontend skeleton, with routing
  (Home, Search pages). **Verified**: `npm install`, `tsc -b` typecheck,
  and `vite build` all pass cleanly.
- `docker-compose.yml` wiring backend + frontend for local dev.

### Phase 2 — Paper Retrieval (started)
- arXiv search service (FR2), no API key required. Code is correct and
  follows a `search(query, max_results) -> list[PaperResult]` provider
  shape, specifically so Semantic Scholar and CrossRef can be added next
  without changing the route or the frontend.
- Search page in the frontend calls this endpoint and renders results.

### Bugs found and fixed during build (worth knowing about)
- `passlib` 1.7.4 + `bcrypt` 4.1+ are incompatible (`AttributeError: module
  'bcrypt' has no attribute '__about__'`). Pinned `bcrypt==4.0.1` in
  `requirements.txt`. If you ever bump bcrypt, re-test register/login.
- `pydantic[email]` (`EmailStr`) needs `email-validator` explicitly —
  added to `requirements.txt`.
- Vite's `import.meta.env` needs `frontend/src/vite-env.d.ts` with
  `/// <reference types="vite/client" />` or `tsc` fails. Already added.

### Known environment caveat (not a code bug)
- The arXiv live call could only be *code-reviewed*, not *proven end-to-end*,
  inside the sandboxed dev environment used to build this — that sandbox's
  network allowlist covers npm/PyPI but not `export.arxiv.org`, so the call
  returned a 403 from the proxy, not from arXiv itself. Run the same curl
  command from `README.md` on your own machine (which has normal internet
  access) to confirm — the `arxiv` Python package usage is standard and
  should work as written.

---

## ⏭️ Next up (rest of Phase 2, in order)

1. Add `semantic_scholar_service.py` and `crossref_service.py` following the
   exact same `search()` shape as `arxiv_service.py`.
2. Update `search.py` route to fan out to all three, merge results, and
   de-duplicate by DOI (fall back to title similarity if DOI is missing).
3. Add `POST /projects` and `POST /projects/{id}/papers` endpoints so a
   logged-in user can save search results into a `ResearchProject` (uses
   the `Paper` and `ResearchProject` models already built).
4. Add a `require_auth` FastAPI dependency (decode JWT → load `User`) and
   protect the new project endpoints with it — `core/security.py` already
   has `create_access_token`; decoding + a dependency still needs writing.

## Then Phase 3 — RAG Core (the big one)
- PDF ingestion (pymupdf/pdfplumber) → chunking → embeddings
  (sentence-transformers) → ChromaDB.
- `LLMRouter` / `LLMResolver` — the Gemini → Groq → Ollama failover chain,
  fully designed already in the blueprint's Section 11 (reference
  implementation included there — it can likely be dropped in with minimal
  changes).
- Chat endpoint wired through the RAG pipeline + LLMRouter, with streaming
  (SSE) and citation display on the frontend.

## Then Phases 4–6
Summarization / keyword extraction / topic modeling → paper comparison /
research gap identification / citation generator / literature review +
proposal generation → auth polish, deployment, docs. See the blueprint's
Section 12 (Suggested Phased Build Order) for the fuller breakdown — it
hasn't changed.

---

## How to resume this in one line

> "Continue the Academic Research Assistant from PROGRESS.md — build the
> Semantic Scholar and CrossRef services next."

That's enough context for a fresh session to pick this up correctly.
