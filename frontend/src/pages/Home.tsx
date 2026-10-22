import { Link } from "react-router-dom";

export default function Home() {
  return (
    <div className="max-w-4xl mx-auto px-6 py-16 text-center">
      <h1 className="text-4xl font-bold text-navy mb-4 tracking-tight">
        Intelligent Academic Research Assistant
      </h1>
      <p className="text-gray-600 mb-10 max-w-2xl mx-auto leading-relaxed text-base">
        Accelerate your literature review with arXiv retrieval, automated PDF parsing,
        semantic chunking, and Retrieval-Augmented Generation (RAG) with verified citations.
      </p>

      <div className="flex justify-center gap-4 mb-16">
        <Link
          to="/assistant"
          className="bg-navy text-white px-6 py-3 rounded-lg font-medium hover:bg-accent transition-colors shadow-sm flex items-center gap-2"
        >
          <span>Open Research Assistant</span>
          <span>→</span>
        </Link>
        <Link
          to="/search"
          className="bg-white border border-gray-300 text-gray-700 px-6 py-3 rounded-lg font-medium hover:bg-gray-50 transition-colors shadow-2xs"
        >
          Search Papers
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-2xs">
          <div className="text-2xl mb-2">🔍</div>
          <h3 className="font-semibold text-gray-900 mb-1">Paper Retrieval</h3>
          <p className="text-xs text-gray-600 leading-relaxed">
            Live search across arXiv publications with instant abstract previews, author metadata, and PDF links.
          </p>
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-2xs">
          <div className="text-2xl mb-2">🧠</div>
          <h3 className="font-semibold text-gray-900 mb-1">RAG Grounding</h3>
          <p className="text-xs text-gray-600 leading-relaxed">
            Automatic text extraction from PDFs and abstracts with semantic chunking and vector similarity retrieval.
          </p>
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-2xs">
          <div className="text-2xl mb-2">📚</div>
          <h3 className="font-semibold text-gray-900 mb-1">Citations & Gaps</h3>
          <p className="text-xs text-gray-600 leading-relaxed">
            Answers backed by verifiable source snippets, with quick prompts for methodologies, research gaps, and BibTeX.
          </p>
        </div>
      </div>
    </div>
  );
}
