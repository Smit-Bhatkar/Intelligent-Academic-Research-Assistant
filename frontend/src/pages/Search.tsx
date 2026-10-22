import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { searchPapers, indexPaperForRAG, type PaperResult } from "../api/client";

export default function Search() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<PaperResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [indexedStatus, setIndexedStatus] = useState<Record<string, { status: "loading" | "success" | "error"; message?: string }>>({});
  const [toast, setToast] = useState<{ title: string; paperId?: string } | null>(null);
  const navigate = useNavigate();

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await searchPapers(query);
      setResults(data);
    } catch (err) {
      setError("Search failed. Is the backend running on :8000?");
    } finally {
      setLoading(false);
    }
  }

  async function handleAddToRAG(paper: PaperResult) {
    setIndexedStatus((prev) => ({
      ...prev,
      [paper.title]: { status: "loading" },
    }));

    try {
      const res = await indexPaperForRAG({
        title: paper.title,
        abstract: paper.abstract,
        authors: paper.authors,
        year: paper.year,
        doi: paper.doi,
        source: paper.source,
        pdf_url: paper.pdf_url,
      });

      setIndexedStatus((prev) => ({
        ...prev,
        [paper.title]: {
          status: "success",
          message: `${res.chunks_created} chunks`,
        },
      }));

      setToast({ title: paper.title, paperId: res.paper_id });
    } catch (err: any) {
      setIndexedStatus((prev) => ({
        ...prev,
        [paper.title]: {
          status: "error",
          message: err?.response?.data?.detail || "Failed to index",
        },
      }));
    }
  }

  function handleAskRAG(paper: PaperResult) {
    const params = new URLSearchParams({
      title: paper.title,
      abstract: paper.abstract,
      pdfUrl: paper.pdf_url || "",
      authors: paper.authors.join(", "),
      year: paper.year ? String(paper.year) : "",
    });
    navigate(`/assistant?${params.toString()}`);
  }

  return (
    <div className="max-w-3xl mx-auto px-6 py-10">
      {/* Toast notification */}
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 bg-navy text-white px-5 py-3.5 rounded-xl shadow-xl flex items-center gap-3 border border-navy/20 animate-fade-in">
          <span className="text-sm">
            Added <strong>{toast.title.slice(0, 35)}…</strong> to RAG!
          </span>
          <Link
            to="/assistant"
            className="bg-white/20 hover:bg-white/30 text-white text-xs px-3 py-1.5 rounded-md font-medium transition-colors"
          >
            Open in Assistant →
          </Link>
          <button
            onClick={() => setToast(null)}
            className="text-white/60 hover:text-white ml-1 text-sm font-bold"
          >
            ✕
          </button>
        </div>
      )}

      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-navy">Search Research Papers</h2>
          <p className="text-xs text-gray-500 mt-1">
            Search across arXiv, Semantic Scholar, and CrossRef with instant deduplication and RAG analysis.
          </p>
        </div>
        <Link
          to="/assistant"
          className="text-xs font-medium text-navy hover:text-accent bg-navy/5 hover:bg-navy/10 px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5"
        >
          <span>Open Assistant</span>
          <span>→</span>
        </Link>
      </div>

      <form onSubmit={handleSearch} className="flex gap-2 mb-8">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. retrieval augmented generation"
          className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-accent"
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-navy text-white px-5 py-2 rounded-lg font-medium hover:bg-accent transition-colors disabled:opacity-50"
        >
          {loading ? "Searching…" : "Search"}
        </button>
      </form>

      {error && <p className="text-red-600 mb-4">{error}</p>}

      <div className="space-y-4">
        {results.map((paper, idx) => {
          const itemState = indexedStatus[paper.title];

          return (
            <div key={idx} className="border border-gray-200 rounded-lg p-5 bg-white shadow-2xs hover:border-gray-300 transition-all">
              <h3 className="font-semibold text-gray-900 text-base leading-snug">{paper.title}</h3>
              <div className="flex flex-wrap items-center gap-2 my-2 text-xs text-gray-500">
                <span>{paper.authors.join(", ")} {paper.year ? `· ${paper.year}` : ""}</span>
                <span className="text-gray-300">|</span>
                <div className="flex gap-1.5">
                  {paper.source.split("/").map((src) => {
                    const badgeColors: Record<string, string> = {
                      arxiv: "bg-red-50 text-red-700 border-red-200",
                      semanticscholar: "bg-blue-50 text-blue-700 border-blue-200",
                      crossref: "bg-purple-50 text-purple-700 border-purple-200",
                    };
                    const color = badgeColors[src.toLowerCase()] || "bg-gray-100 text-gray-700 border-gray-200";
                    return (
                      <span
                        key={src}
                        className={`uppercase text-[10px] font-semibold tracking-wider px-2 py-0.5 rounded-full border ${color}`}
                      >
                        {src === "semanticscholar" ? "Semantic Scholar" : src}
                      </span>
                    );
                  })}
                </div>
              </div>
              <p className="text-xs text-gray-700 leading-relaxed mb-4">{paper.abstract.slice(0, 320)}…</p>
              
              <div className="flex flex-wrap items-center gap-3 pt-3 border-t border-gray-100">
                {itemState?.status === "loading" ? (
                  <button
                    disabled
                    className="bg-navy/10 text-navy text-xs px-3.5 py-1.5 rounded-md font-medium flex items-center gap-1.5 cursor-wait"
                  >
                    <span className="animate-spin text-xs">⏳</span>
                    <span>Indexing into RAG…</span>
                  </button>
                ) : itemState?.status === "success" ? (
                  <button
                    disabled
                    className="bg-green-50 border border-green-200 text-green-700 text-xs px-3.5 py-1.5 rounded-md font-medium flex items-center gap-1.5"
                  >
                    <span>✓ Added to RAG</span>
                    <span className="text-[10px] opacity-75">({itemState.message})</span>
                  </button>
                ) : (
                  <button
                    onClick={() => handleAddToRAG(paper)}
                    className="bg-navy text-white text-xs px-3.5 py-1.5 rounded-md font-medium hover:bg-accent transition-colors flex items-center gap-1.5 shadow-2xs"
                  >
                    <span>+ Add to RAG</span>
                  </button>
                )}

                <button
                  onClick={() => handleAskRAG(paper)}
                  className="bg-white border border-gray-300 text-gray-700 text-xs px-3.5 py-1.5 rounded-md font-medium hover:bg-gray-50 transition-colors flex items-center gap-1.5 shadow-2xs"
                >
                  <span>✨ Ask with RAG</span>
                </button>

                {paper.pdf_url && (
                  <a
                    href={paper.pdf_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-gray-600 border border-gray-300 hover:bg-gray-50 text-xs px-3 py-1.5 rounded-md font-medium transition-colors inline-block"
                  >
                    View PDF ↗
                  </a>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
