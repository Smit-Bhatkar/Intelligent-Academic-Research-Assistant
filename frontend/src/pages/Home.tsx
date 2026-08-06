import { Link } from "react-router-dom";

export default function Home() {
  return (
    <div className="max-w-3xl mx-auto px-6 py-16 text-center">
      <h1 className="text-3xl font-bold text-navy mb-3">
        Intelligent Academic Research Assistant
      </h1>
      <p className="text-gray-600 mb-8">
        RAG-grounded search, summarization, and citation assistance for
        academic research. This is the Phase&nbsp;1/2 foundation build —
        chat, summarization, and citation features arrive in later phases.
      </p>
      <Link
        to="/search"
        className="inline-block bg-navy text-white px-6 py-3 rounded-lg font-medium hover:bg-accent transition-colors"
      >
        Try Paper Search →
      </Link>
    </div>
  );
}
