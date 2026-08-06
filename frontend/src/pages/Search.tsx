import { useState } from "react";
import { searchPapers, type PaperResult } from "../api/client";

export default function Search() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<PaperResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  return (
    <div className="max-w-3xl mx-auto px-6 py-10">
      <h2 className="text-2xl font-bold text-navy mb-6">Search Research Papers</h2>

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
        {results.map((paper, idx) => (
          <div key={idx} className="border border-gray-200 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900">{paper.title}</h3>
            <p className="text-sm text-gray-500 mb-2">
              {paper.authors.join(", ")} {paper.year ? `· ${paper.year}` : ""} ·{" "}
              <span className="uppercase text-xs tracking-wide">{paper.source}</span>
            </p>
            <p className="text-sm text-gray-700">{paper.abstract.slice(0, 280)}…</p>
            {paper.pdf_url && (
              <a
                href={paper.pdf_url}
                target="_blank"
                rel="noreferrer"
                className="text-accent text-sm font-medium mt-2 inline-block"
              >
                View PDF →
              </a>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
