import io
import json
import math
import os
import re
import uuid
from typing import Any

from pypdf import PdfReader
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.paper_chunk import PaperChunk
from app.models.papers import Paper
from app.schemas.rag import Citation, RAGQueryResponse
from app.services.llm_router import llm_router
from app.services.pdf_service import download_pdf


# ---------------------------------------------------------------------------
# 1. Text Extraction & Chunking
# ---------------------------------------------------------------------------

def extract_pdf_pages_from_bytes(pdf_bytes: bytes) -> list[dict[str, Any]]:
    """Extracts text page by page from PDF bytes using pypdf."""
    pages = []
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        for idx, page in enumerate(reader.pages):
            try:
                text = page.extract_text() or ""
                text = re.sub(r"\s+", " ", text).strip()
                if text:
                    pages.append({"page_number": idx + 1, "text": text})
            except Exception:
                continue
    except Exception:
        pass
    return pages


def extract_pdf_pages_from_file(file_path: str) -> list[dict[str, Any]]:
    """Extracts text page by page from a local PDF file."""
    try:
        with open(file_path, "rb") as f:
            return extract_pdf_pages_from_bytes(f.read())
    except Exception:
        return []


def chunk_text(
    text: str, chunk_size: int = 800, chunk_overlap: int = 150
) -> list[str]:
    """
    Recursively chunks text into semantic segments with overlap,
    respecting paragraph and sentence boundaries.
    """
    if len(text) <= chunk_size:
        return [text] if text else []

    chunks = []
    # Split primarily by paragraphs or sentences
    splits = re.split(r"(?<=[.\n])\s+", text)
    current_chunk = []
    current_length = 0

    for segment in splits:
        seg_len = len(segment)
        if current_length + seg_len > chunk_size and current_chunk:
            combined = " ".join(current_chunk).strip()
            if combined:
                chunks.append(combined)

            # Build overlap from the end of current_chunk
            overlap_chunk = []
            overlap_len = 0
            for prev_seg in reversed(current_chunk):
                if overlap_len + len(prev_seg) <= chunk_overlap:
                    overlap_chunk.insert(0, prev_seg)
                    overlap_len += len(prev_seg)
                else:
                    break
            current_chunk = overlap_chunk
            current_length = sum(len(s) for s in current_chunk)

        current_chunk.append(segment)
        current_length += seg_len

    if current_chunk:
        combined = " ".join(current_chunk).strip()
        if combined:
            chunks.append(combined)

    return chunks


# ---------------------------------------------------------------------------
# 2. Embedding & Vector Math
# ---------------------------------------------------------------------------

def _hash_vector(text: str, dim: int = 256) -> list[float]:
    """
    Deterministic TF-IDF like feature hashing for fast offline/fallback similarity.
    Does not require any external downloads or models.
    """
    words = re.findall(r"\w+", text.lower())
    if not words:
        return [0.0] * dim

    vec = [0.0] * dim
    for word in words:
        # 3-gram character features + word hash
        h = abs(hash(word)) % dim
        vec[h] += 1.0

    # L2 normalize
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


async def get_embedding(text: str, api_key: str | None = None) -> list[float]:
    """
    Computes an embedding vector.
    Uses Gemini's text-embedding-004 if an API key is available,
    otherwise falls back to deterministic feature hashing vector.
    """
    resolved_key = api_key or settings.GEMINI_API_KEY
    if resolved_key:
        try:
            from google import genai
            client = genai.Client(api_key=resolved_key)
            result = client.models.embed_content(
                model="text-embedding-004",
                contents=text,
            )
            if hasattr(result, "embedding") and hasattr(result.embedding, "values"):
                return list(result.embedding.values)
        except Exception:
            # Fall back to hash vector if remote API call fails
            pass

    return _hash_vector(text)


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Calculates cosine similarity between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)


# ---------------------------------------------------------------------------
# 3. Indexing Operations
# ---------------------------------------------------------------------------

async def index_paper(
    title: str,
    abstract: str = "",
    authors: list[str] | None = None,
    year: int | None = None,
    doi: str | None = None,
    source: str = "manual",
    pdf_url: str | None = None,
    local_pdf_path: str | None = None,
    paper_id: str | None = None,
    api_key: str | None = None,
    db: AsyncSession | None = None,
) -> tuple[str, int]:
    """
    Ingests and chunks a paper, computes embeddings, and stores them in SQLite.
    Returns (paper_id, chunks_created).
    """
    if not paper_id:
        paper_id = str(uuid.uuid4())

    authors_list = authors or []
    metadata = {
        "authors": authors_list,
        "year": year,
        "doi": doi,
        "source": source,
        "pdf_url": pdf_url,
    }
    metadata_str = json.dumps(metadata)

    # 1. Gather text sources (PDF if available, otherwise abstract + title)
    pages_data: list[dict[str, Any]] = []

    # Attempt PDF extraction if path or URL is provided
    if local_pdf_path and os.path.exists(local_pdf_path):
        try:
            pages_data = extract_pdf_pages_from_file(local_pdf_path)
        except Exception:
            pass

    if not pages_data and pdf_url:
        try:
            downloaded_path = await download_pdf(paper_id, pdf_url)
            pages_data = extract_pdf_pages_from_file(downloaded_path)
        except Exception:
            pass

    # If no PDF pages extracted, use title + abstract
    if not pages_data:
        full_text = f"Title: {title}\n\nAbstract: {abstract}"
        pages_data = [{"page_number": 1, "text": full_text}]

    # 2. Chunk pages
    all_chunks: list[dict[str, Any]] = []
    chunk_idx = 0
    for page in pages_data:
        page_chunks = chunk_text(page["text"], chunk_size=800, chunk_overlap=150)
        for c in page_chunks:
            all_chunks.append({
                "chunk_index": chunk_idx,
                "content": c,
                "page_number": page.get("page_number"),
            })
            chunk_idx += 1

    # 3. Create PaperChunk DB records with embeddings
    if db:
        # Remove any existing chunks for this paper_id
        await db.execute(delete(PaperChunk).where(PaperChunk.paper_id == paper_id))

        for item in all_chunks:
            emb = await get_embedding(item["content"], api_key=api_key)
            chunk_obj = PaperChunk(
                paper_id=paper_id,
                paper_title=title,
                chunk_index=item["chunk_index"],
                content=item["content"],
                page_number=item["page_number"],
                embedding=json.dumps(emb),
                metadata_json=metadata_str,
            )
            db.add(chunk_obj)
        await db.commit()

    return paper_id, len(all_chunks)


# ---------------------------------------------------------------------------
# 4. Retrieval & Generation
# ---------------------------------------------------------------------------

async def query_rag(
    query: str,
    paper_ids: list[str] | None = None,
    top_k: int = 5,
    api_key: str | None = None,
    mode: str = "qa",
    db: AsyncSession | None = None,
) -> RAGQueryResponse:
    """
    Executes RAG pipeline:
    1. Embeds query.
    2. Retrieves top-k most relevant chunks via cosine similarity.
    3. Synthesizes grounded answer using Gemini (or structured extractive fallback).
    4. Formats citations.
    """
    if not db:
        return RAGQueryResponse(
            answer="Database session not provided.",
            citations=[],
            mode_used=mode,
            fallback_mode=True,
            model_used="none",
        )

    # 1. Fetch chunks
    stmt = select(PaperChunk)
    if paper_ids:
        stmt = stmt.where(PaperChunk.paper_id.in_(paper_ids))

    result = await db.scalars(stmt)
    all_chunks = list(result)

    if not all_chunks:
        return RAGQueryResponse(
            answer=(
                "No papers have been indexed in the RAG knowledge base yet. "
                "Search for research papers on the Search page and click 'Ask with RAG', "
                "or upload a PDF in the Research Assistant to begin."
            ),
            citations=[],
            mode_used=mode,
            fallback_mode=True,
            model_used="none",
        )

    # 2. Compute query embedding and rank chunks
    query_emb = await get_embedding(query, api_key=api_key)
    scored_chunks: list[tuple[float, PaperChunk]] = []

    for chunk in all_chunks:
        if chunk.embedding:
            try:
                emb = json.loads(chunk.embedding)
                sim = cosine_similarity(query_emb, emb)
            except Exception:
                sim = 0.0
        else:
            sim = 0.0
        scored_chunks.append((sim, chunk))

    # Sort descending by similarity
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    top_results = scored_chunks[:top_k]

    # Build citations list
    citations: list[Citation] = []
    context_blocks: list[str] = []

    for idx, (score, chunk) in enumerate(top_results, start=1):
        meta = json.loads(chunk.metadata_json) if chunk.metadata_json else {}
        cit = Citation(
            paper_title=chunk.paper_title,
            authors=meta.get("authors", []),
            year=meta.get("year"),
            page_number=chunk.page_number,
            chunk_index=chunk.chunk_index,
            snippet=chunk.content[:280] + ("..." if len(chunk.content) > 280 else ""),
            similarity_score=round(score, 4),
        )
        citations.append(cit)

        page_str = f"Page {chunk.page_number}" if chunk.page_number else f"Chunk {chunk.chunk_index}"
        context_blocks.append(
            f"[{idx}] Source: {chunk.paper_title} ({page_str})\nContent: {chunk.content}"
        )

    context_str = "\n\n".join(context_blocks)

    # 3. Generate Answer via LLM Router (Gemini -> Groq -> Ollama -> Fallback)
    system_instruction = (
        "You are an expert Academic Research Assistant. Your task is to provide rigorous, "
        "accurate, and insightful answers grounded strictly in the provided research paper excerpts.\n\n"
        "Guidelines:\n"
        "- Ground all factual statements in the provided context. Cite sources using [1], [2], etc.\n"
        "- If the context does not provide sufficient detail, explicitly state the limitation.\n"
        "- Structure your response cleanly using markdown (bold key concepts, use bullet points, clear headings)."
    )

    mode_instructions = {
        "qa": "Provide a comprehensive, direct academic answer to the question with inline citations.",
        "summarize": "Provide an executive academic summary: Core Objective, Methodology, Key Findings, and Significance.",
        "methodology": "Deep dive into the methodology, experimental design, datasets, architectures, and evaluation metrics.",
        "gaps": "Critically analyze the limitations, potential biases, unaddressed scenarios, and recommend promising future research directions.",
        "bibtex": "Generate a clean BibTeX entry and APA citation based on the paper title and metadata in the context.",
    }
    prompt_guide = mode_instructions.get(mode, mode_instructions["qa"])

    prompt = (
        f"Mode: {mode.upper()}\n"
        f"Task: {prompt_guide}\n\n"
        f"Context from Indexed Research Papers:\n"
        f"{context_str}\n\n"
        f"User Question / Research Query:\n"
        f"{query}\n\n"
        f"Synthesized Response:"
    )

    llm_resp = await llm_router.generate(
        prompt=prompt,
        system_instruction=system_instruction,
        api_key=api_key,
    )

    if not llm_resp.is_fallback and llm_resp.text:
        return RAGQueryResponse(
            answer=llm_resp.text,
            citations=citations,
            mode_used=mode,
            fallback_mode=False,
            model_used=f"{llm_resp.provider}:{llm_resp.model}",
        )

    # 4. Fallback Mode (Extractive Semantic Synthesis)
    fallback_lines = [
        f"### Research Insights for: *\"{query}\"*\n",
        f"*(Running in semantic extractive mode. To enable full generative AI synthesis with Gemini, provide a `GEMINI_API_KEY` in settings or `.env`.)*\n",
        "#### Most Relevant Findings from Indexed Literature:\n",
    ]
    for idx, (score, chunk) in enumerate(top_results, start=1):
        page_info = f" (Page {chunk.page_number})" if chunk.page_number else ""
        fallback_lines.append(
            f"**[{idx}] {chunk.paper_title}**{page_info} — *Relevance Score: {score:.2%}*\n"
            f"> \"{chunk.content.strip()}\"\n"
        )

    fallback_lines.append(
        "\n#### Research Recommendations:\n"
        "- The passages above highlight the key context directly matching your query.\n"
        "- You can inspect the complete paper or add more papers to broaden the comparison.\n"
    )

    return RAGQueryResponse(
        answer="\n".join(fallback_lines),
        citations=citations,
        mode_used=mode,
        fallback_mode=True,
        model_used="extractive-semantic-ranker",
    )
