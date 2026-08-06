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
