import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",
});

export interface PaperResult {
  title: string;
  authors: string[];
  abstract: string;
  doi: string | null;
  source: string;
  year: number | null;
  pdf_url: string | null;
}

// FR2 — paper search (currently arXiv only; Semantic Scholar/CrossRef
// will be added on the backend without changing this call shape).
export async function searchPapers(query: string, maxResults = 10): Promise<PaperResult[]> {
  const { data } = await api.get<PaperResult[]>("/search/papers", {
    params: { q: query, max_results: maxResults },
  });
  return data;
}

// ---------------------------------------------------------------------------
// Phase 3 — RAG (Retrieval-Augmented Generation) API client methods
// ---------------------------------------------------------------------------

export interface Citation {
  paper_title: string;
  authors: string[];
  year: number | null;
  page_number: number | null;
  chunk_index: number;
  snippet: string;
  similarity_score: number;
}

export interface RAGQueryResponse {
  answer: string;
  citations: Citation[];
  mode_used: string;
  fallback_mode: boolean;
  model_used: string;
}

export interface IndexedPaper {
  paper_id: string;
  title: string;
  authors: string[];
  year: number | null;
  source: string;
  chunk_count: number;
  created_at: string;
}

export interface IndexPaperPayload {
  title: string;
  abstract?: string;
  authors?: string[];
  year?: number | null;
  doi?: string | null;
  source?: string;
  pdf_url?: string | null;
}

export async function indexPaperForRAG(payload: IndexPaperPayload): Promise<{ paper_id: string; chunks_created: number }> {
  const { data } = await api.post("/rag/index", payload);
  return data;
}

export async function uploadPDFForRAG(file: File): Promise<{ paper_id: string; chunks_created: number }> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post("/rag/upload", formData);
  return data;
}

export async function queryRAG(params: {
  query: string;
  paper_ids?: string[];
  top_k?: number;
  api_key?: string;
  mode?: "qa" | "summarize" | "methodology" | "gaps" | "bibtex";
}): Promise<RAGQueryResponse> {
  const { data } = await api.post<RAGQueryResponse>("/rag/query", params);
  return data;
}

export async function getIndexedPapers(): Promise<IndexedPaper[]> {
  const { data } = await api.get<IndexedPaper[]>("/rag/papers");
  return data;
}

export async function removeIndexedPaper(paperId: string): Promise<{ deleted: boolean }> {
  const { data } = await api.delete(`/rag/papers/${paperId}`);
  return data;
}
