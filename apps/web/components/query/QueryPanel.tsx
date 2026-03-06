"use client";

import { useState } from "react";
import { queryApi, feedbackApi } from "@/lib/api";
import type { IQueryResponse, QueryMode, IKnowledgeBase } from "@/lib/types";
import QueryModeSelector from "./QueryModeSelector";
import CitationList from "@/components/citations/CitationList";

interface QueryPanelProps {
  knowledgeBases: IKnowledgeBase[];
}

export default function QueryPanel({ knowledgeBases }: QueryPanelProps) {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<QueryMode>("question_answer");
  const [selectedKbs, setSelectedKbs] = useState<string[]>([]);
  const [response, setResponse] = useState<IQueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [feedbackSent, setFeedbackSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError("");
    setResponse(null);
    setFeedbackSent(false);

    try {
      const result = await queryApi.query({
        query: query.trim(),
        mode,
        kb_ids: selectedKbs.length > 0 ? selectedKbs : undefined,
      });
      setResponse(result);
    } catch (err: any) {
      setError(err.message ?? "Query failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const sendFeedback = async (rating: "useful" | "incorrect" | "needs_review") => {
    if (!response) return;
    await feedbackApi.submit({
      query_text: query,
      response_text: response.answer,
      rating,
      query_mode: mode,
    }).catch(() => {});
    setFeedbackSent(true);
  };

  const toggleKb = (id: string) => {
    setSelectedKbs((prev) =>
      prev.includes(id) ? prev.filter((k) => k !== id) : [...prev, id]
    );
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Query form */}
      <div className="card">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Query Mode</label>
            <QueryModeSelector value={mode} onChange={setMode} />
          </div>

          {knowledgeBases.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Knowledge Bases (none = search all)
              </label>
              <div className="flex flex-wrap gap-2">
                {knowledgeBases.map((kb) => (
                  <button
                    key={kb.id}
                    type="button"
                    onClick={() => toggleKb(kb.id)}
                    className={`px-3 py-1 text-xs rounded-full border transition-colors
                      ${selectedKbs.includes(kb.id)
                        ? "bg-indigo-600 border-indigo-600 text-white"
                        : "border-gray-300 text-gray-600 hover:border-indigo-300"
                      }`}
                  >
                    {kb.name}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Your Question</label>
            <textarea
              className="input resize-none h-28"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="What are the DSM-5 diagnostic criteria for Major Depressive Disorder?"
              required
            />
          </div>

          <button type="submit" className="btn-primary w-full" disabled={loading}>
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Searching knowledge base...
              </span>
            ) : "Submit Query"}
          </button>
        </form>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 text-sm">
          {error}
        </div>
      )}

      {/* Response */}
      {response && (
        <div className="card">
          {response.was_blocked && (
            <div className="flex items-center gap-2 text-amber-700 bg-amber-50 border border-amber-200
                            rounded-lg p-3 mb-4 text-sm">
              <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              Safety filter applied
            </div>
          )}

          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-gray-700">Response</h2>
            <div className="flex items-center gap-2 text-xs text-gray-400">
              {response.retrieval_count > 0 && (
                <span>{response.retrieval_count} chunks retrieved</span>
              )}
            </div>
          </div>

          <div className="prose prose-sm max-w-none text-gray-800 whitespace-pre-wrap">
            {response.answer}
          </div>

          <CitationList citations={response.citations} />

          {/* Feedback */}
          {!response.was_blocked && (
            <div className="mt-6 pt-4 border-t border-gray-100">
              {feedbackSent ? (
                <p className="text-sm text-green-600">Thank you for your feedback!</p>
              ) : (
                <div className="flex items-center gap-3">
                  <span className="text-xs text-gray-500">Was this helpful?</span>
                  {(["useful", "needs_review", "incorrect"] as const).map((r) => (
                    <button
                      key={r}
                      onClick={() => sendFeedback(r)}
                      className="text-xs px-2 py-1 rounded border border-gray-200
                                 hover:border-indigo-300 hover:text-indigo-600 transition-colors capitalize"
                    >
                      {r.replace("_", " ")}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
