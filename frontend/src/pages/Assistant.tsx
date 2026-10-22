import { useEffect, useRef, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import {
  getIndexedPapers,
  indexPaperForRAG,
  queryRAG,
  removeIndexedPaper,
  uploadPDFForRAG,
  type Citation,
  type IndexedPaper,
} from "../api/client";

interface Message {
  id: string;
  sender: "user" | "assistant";
  text: string;
  citations?: Citation[];
  mode?: string;
  fallbackMode?: boolean;
  modelUsed?: string;
  timestamp: string;
}

export default function Assistant() {
  const [searchParams] = useSearchParams();
  const [papers, setPapers] = useState<IndexedPaper[]>([]);
  const [selectedPaperId, setSelectedPaperId] = useState<string>("all");
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputQuery, setInputQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [indexingNotice, setIndexingNotice] = useState<string | null>(null);
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Load indexed papers
  async function loadPapers() {
    try {
      const data = await getIndexedPapers();
      setPapers(data);
    } catch (err) {
      console.error("Failed to fetch indexed papers", err);
    }
  }

  useEffect(() => {
    loadPapers();
  }, []);

  // Handle incoming query params from Search page ("Ask with RAG")
  useEffect(() => {
    const title = searchParams.get("title");
    const abstract = searchParams.get("abstract");
    const pdfUrl = searchParams.get("pdfUrl");
    const authorsStr = searchParams.get("authors");
    const yearStr = searchParams.get("year");

    if (title) {
      const authors = authorsStr ? authorsStr.split(", ") : [];
      const year = yearStr ? parseInt(yearStr, 10) : undefined;

      setIndexingNotice(`Indexing "${title}" for RAG analysis...`);
      indexPaperForRAG({
        title,
        abstract: abstract || "",
        pdf_url: pdfUrl || undefined,
        authors,
        year: isNaN(year!) ? undefined : year,
      })
        .then((res) => {
          setIndexingNotice(`Successfully indexed "${title}" (${res.chunks_created} chunks created).`);
          loadPapers().then(() => {
            setSelectedPaperId(res.paper_id);
          });
          // Add a welcoming prompt
          setMessages([
            {
              id: "welcome",
              sender: "assistant",
              text: `I've indexed **${title}** into your research context.\n\nYou can ask any question about this paper, or click one of the quick research actions below to summarize its methodology, key contributions, or limitations.`,
              timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
            },
          ]);
          setTimeout(() => setIndexingNotice(null), 5000);
        })
        .catch((err) => {
          setIndexingNotice(`Error indexing paper: ${err.message}`);
        });
    }
  }, [searchParams]);

  // Handle asking question / RAG query
  async function handleSend(queryText?: string, mode: "qa" | "summarize" | "methodology" | "gaps" | "bibtex" = "qa") {
    const query = queryText || inputQuery;
    if (!query.trim()) return;

    const userMsg: Message = {
      id: Math.random().toString(),
      sender: "user",
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!queryText) setInputQuery("");
    setLoading(true);

    try {
      const paperFilter = selectedPaperId === "all" ? undefined : [selectedPaperId];
      const res = await queryRAG({
        query,
        paper_ids: paperFilter,
        mode,
      });

      const assistantMsg: Message = {
        id: Math.random().toString(),
        sender: "assistant",
        text: res.answer,
        citations: res.citations,
        mode: res.mode_used,
        fallbackMode: res.fallback_mode,
        modelUsed: res.model_used,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: Math.random().toString(),
          sender: "assistant",
          text: `⚠️ Query error: ${err?.response?.data?.detail || err.message || "Failed to query RAG service."}`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  // Handle PDF upload
  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setIndexingNotice(`Uploading and parsing "${file.name}"...`);
    try {
      const res = await uploadPDFForRAG(file);
      setIndexingNotice(`Indexed "${file.name}" (${res.chunks_created} text chunks extracted).`);
      await loadPapers();
      setSelectedPaperId(res.paper_id);
      setMessages((prev) => [
        ...prev,
        {
          id: Math.random().toString(),
          sender: "assistant",
          text: `Successfully uploaded and indexed **${file.name}** into the RAG knowledge base. You can now ask questions directly about this document!`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
      setTimeout(() => setIndexingNotice(null), 5000);
    } catch (err: any) {
      setIndexingNotice(`Upload failed: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  // Handle paper removal
  async function handleDeletePaper(paperId: string, title: string) {
    if (!confirm(`Remove "${title}" from RAG index?`)) return;
    try {
      await removeIndexedPaper(paperId);
      if (selectedPaperId === paperId) setSelectedPaperId("all");
      await loadPapers();
    } catch (err) {
      console.error("Failed to delete paper", err);
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Top Banner Notice */}
      {indexingNotice && (
        <div className="mb-4 bg-blue-50 border-l-4 border-blue-500 p-4 rounded text-sm text-blue-800 flex justify-between items-center shadow-sm">
          <span>{indexingNotice}</span>
          <button onClick={() => setIndexingNotice(null)} className="text-blue-500 font-bold hover:text-blue-700 ml-4">
            ×
          </button>
        </div>
      )}

      {/* Header bar */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pb-6 border-b border-gray-200 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-navy flex items-center gap-2">
            <span>Research Assistant</span>
          </h1>
          <p className="text-sm text-gray-600">
            Ask questions grounded across indexed research literature with citations and semantic source verification.
          </p>
        </div>

        <div className="flex items-center gap-3">

          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".pdf"
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="bg-gray-100 text-gray-700 border border-gray-300 hover:bg-gray-200 text-xs px-3.5 py-1.5 rounded-lg font-medium transition-colors disabled:opacity-50"
          >
            {uploading ? "Parsing PDF…" : "📁 Upload PDF Paper"}
          </button>

          <Link
            to="/search"
            className="bg-navy text-white text-xs px-3.5 py-1.5 rounded-lg font-medium hover:bg-accent transition-colors"
          >
            🔍 Search & Add Papers
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Column: Indexed Papers Knowledge Base */}
        <div className="lg:col-span-1 bg-white border border-gray-200 rounded-xl p-4 shadow-sm h-fit">
          <div className="flex justify-between items-center mb-3">
            <h3 className="font-semibold text-gray-900 text-sm">Indexed Literature</h3>
            <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full font-medium">
              {papers.length} {papers.length === 1 ? "paper" : "papers"}
            </span>
          </div>

          <div className="mb-3">
            <label className="text-xs text-gray-500 block mb-1 font-medium">Active Research Scope:</label>
            <select
              value={selectedPaperId}
              onChange={(e) => setSelectedPaperId(e.target.value)}
              className="w-full text-xs border border-gray-300 rounded-lg p-2 bg-gray-50 focus:bg-white focus:outline-none focus:ring-1 focus:ring-navy"
            >
              <option value="all">All Indexed Papers ({papers.reduce((acc, p) => acc + p.chunk_count, 0)} chunks)</option>
              {papers.map((p) => (
                <option key={p.paper_id} value={p.paper_id}>
                  {p.title.length > 40 ? p.title.slice(0, 40) + "…" : p.title} ({p.chunk_count} chunks)
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
            {papers.length === 0 ? (
              <div className="text-center py-6 px-2 text-gray-500">
                <p className="text-xs">No papers indexed yet.</p>
                <p className="text-xs text-gray-400 mt-1">
                  Upload a PDF or search arXiv to add papers into your RAG context.
                </p>
              </div>
            ) : (
              papers.map((p) => (
                <div
                  key={p.paper_id}
                  onClick={() => setSelectedPaperId(p.paper_id)}
                  className={`p-2.5 rounded-lg border text-xs cursor-pointer transition-all ${
                    selectedPaperId === p.paper_id
                      ? "border-navy bg-navy/5 shadow-xs"
                      : "border-gray-200 hover:border-gray-300 bg-white"
                  }`}
                >
                  <div className="flex justify-between items-start gap-1">
                    <p className="font-medium text-gray-900 line-clamp-2">{p.title}</p>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeletePaper(p.paper_id, p.title);
                      }}
                      title="Remove from RAG"
                      className="text-gray-400 hover:text-red-600 px-1"
                    >
                      ×
                    </button>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-gray-500 mt-1.5">
                    <span>{p.year || "Unknown year"} · {p.source}</span>
                    <span className="bg-gray-100 px-1.5 py-0.2 rounded text-[10px] text-gray-600 font-mono">
                      {p.chunk_count} chunks
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Column: Interactive Chat & RAG Workspace */}
        <div className="lg:col-span-3 flex flex-col bg-white border border-gray-200 rounded-xl shadow-sm min-h-[620px] max-h-[750px]">
          {/* Quick Action Prompt Chips */}
          <div className="border-b border-gray-100 p-3 bg-gray-50/50 flex flex-wrap gap-2 items-center rounded-t-xl">
            <span className="text-xs text-gray-500 font-medium mr-1">Quick Prompts:</span>
            <button
              onClick={() => handleSend("Summarize the main contribution, core methodology, and findings of the paper.", "summarize")}
              disabled={loading || papers.length === 0}
              className="text-xs bg-white border border-gray-200 hover:border-navy hover:text-navy px-2.5 py-1 rounded-full text-gray-700 transition-colors shadow-2xs disabled:opacity-40"
            >
              📝 Summarize Paper
            </button>
            <button
              onClick={() => handleSend("Analyze the methodology, algorithms, and experimental setup used in this research.", "methodology")}
              disabled={loading || papers.length === 0}
              className="text-xs bg-white border border-gray-200 hover:border-navy hover:text-navy px-2.5 py-1 rounded-full text-gray-700 transition-colors shadow-2xs disabled:opacity-40"
            >
              🔬 Methodology Analysis
            </button>
            <button
              onClick={() => handleSend("What are the primary limitations, open questions, and research gaps mentioned?", "gaps")}
              disabled={loading || papers.length === 0}
              className="text-xs bg-white border border-gray-200 hover:border-navy hover:text-navy px-2.5 py-1 rounded-full text-gray-700 transition-colors shadow-2xs disabled:opacity-40"
            >
              ⚠️ Research Gaps & Limitations
            </button>
            <button
              onClick={() => handleSend("Generate a BibTeX entry and APA citation for the indexed paper.", "bibtex")}
              disabled={loading || papers.length === 0}
              className="text-xs bg-white border border-gray-200 hover:border-navy hover:text-navy px-2.5 py-1 rounded-full text-gray-700 transition-colors shadow-2xs disabled:opacity-40"
            >
              📚 Generate Citations
            </button>
          </div>

          {/* Messages Stream */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-8 text-gray-500">
                <div className="w-12 h-12 rounded-full bg-navy/10 text-navy flex items-center justify-center text-xl mb-3">
                  🎓
                </div>
                <h4 className="font-semibold text-gray-800 text-base mb-1">
                  Ready to assist your academic research
                </h4>
                <p className="text-xs text-gray-500 max-w-md mb-4">
                  Ask specific research questions, compare methodologies, or extract literature review points from your indexed papers.
                </p>
                {papers.length === 0 ? (
                  <div className="flex gap-2">
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="text-xs bg-navy text-white px-3.5 py-2 rounded-lg font-medium hover:bg-accent transition-colors"
                    >
                      Upload a Research PDF
                    </button>
                    <Link
                      to="/search"
                      className="text-xs bg-gray-100 text-gray-700 border border-gray-300 px-3.5 py-2 rounded-lg font-medium hover:bg-gray-200 transition-colors"
                    >
                      Search arXiv Papers
                    </Link>
                  </div>
                ) : (
                  <p className="text-xs text-navy font-medium">
                    {papers.length} paper(s) ready in context. Try clicking one of the quick prompts above!
                  </p>
                )}
              </div>
            ) : (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex flex-col ${msg.sender === "user" ? "items-end" : "items-start"}`}
                >
                  <div
                    className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm ${
                      msg.sender === "user"
                        ? "bg-navy text-white rounded-br-none"
                        : "bg-gray-50 border border-gray-200 text-gray-800 rounded-bl-none shadow-2xs"
                    }`}
                  >
                    {/* Render message content */}
                    <div className="prose prose-sm max-w-none whitespace-pre-wrap leading-relaxed">
                      {msg.text}
                    </div>

                    {/* Citations section if present */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-200">
                        <p className="text-xs font-semibold text-gray-600 mb-1.5 flex items-center gap-1">
                          <span>📌 Grounded Sources ({msg.citations.length}):</span>
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {msg.citations.map((c, idx) => (
                            <button
                              key={idx}
                              onClick={() => setActiveCitation(c)}
                              className="text-[11px] bg-white border border-gray-300 hover:border-navy hover:text-navy px-2 py-0.5 rounded text-gray-700 font-medium transition-colors text-left"
                            >
                              [{idx + 1}] {c.paper_title.slice(0, 24)}… {c.page_number ? `(p.${c.page_number})` : ""}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Footer metadata */}
                    <div className="flex items-center justify-between gap-4 mt-2 text-[10px] text-gray-400">
                      <span>{msg.timestamp}</span>
                      {msg.modelUsed && (
                        <span className="font-mono">
                          model: {msg.modelUsed} {msg.fallbackMode ? "(extractive)" : "(generative)"}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
            {loading && (
              <div className="flex items-start">
                <div className="bg-gray-50 border border-gray-200 rounded-2xl rounded-bl-none px-4 py-3 text-sm text-gray-600 flex items-center gap-2">
                  <span className="animate-spin text-navy text-base">⭮</span>
                  <span>Synthesizing grounded answer from indexed literature…</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input form */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="p-3 border-t border-gray-200 bg-white rounded-b-xl flex gap-2"
          >
            <input
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              placeholder={
                papers.length === 0
                  ? "Index a paper first to ask questions..."
                  : "Ask a research question (e.g., 'What datasets were used for training?')..."
              }
              disabled={loading}
              className="flex-1 border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-navy focus:border-transparent disabled:bg-gray-50"
            />
            <button
              type="submit"
              disabled={loading || !inputQuery.trim() || papers.length === 0}
              className="bg-navy text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-accent transition-colors disabled:opacity-50 flex items-center gap-1.5"
            >
              <span>Ask</span>
              <span>→</span>
            </button>
          </form>
        </div>
      </div>

      {/* Citation Detail Modal */}
      {activeCitation && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-lg w-full p-6 shadow-xl border border-gray-200">
            <div className="flex justify-between items-start mb-3">
              <h3 className="font-bold text-navy text-base">Source Citation Details</h3>
              <button
                onClick={() => setActiveCitation(null)}
                className="text-gray-400 hover:text-gray-700 font-bold text-lg"
              >
                ×
              </button>
            </div>
            <div className="space-y-2 text-xs text-gray-700">
              <p>
                <strong className="text-gray-900">Paper:</strong> {activeCitation.paper_title}
              </p>
              {activeCitation.authors.length > 0 && (
                <p>
                  <strong className="text-gray-900">Authors:</strong> {activeCitation.authors.join(", ")}
                </p>
              )}
              {activeCitation.year && (
                <p>
                  <strong className="text-gray-900">Year:</strong> {activeCitation.year}
                </p>
              )}
              {activeCitation.page_number && (
                <p>
                  <strong className="text-gray-900">Page:</strong> {activeCitation.page_number}
                </p>
              )}
              <p>
                <strong className="text-gray-900">Relevance Score:</strong>{" "}
                {(activeCitation.similarity_score * 100).toFixed(1)}%
              </p>
              <div className="mt-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
                <p className="font-mono text-[11px] text-gray-800 leading-relaxed">
                  "{activeCitation.snippet}"
                </p>
              </div>
            </div>
            <div className="mt-5 text-right">
              <button
                onClick={() => setActiveCitation(null)}
                className="bg-navy text-white text-xs px-4 py-2 rounded-lg font-medium hover:bg-accent"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
