"use client";

import { useState } from "react";
import type { IResearchArticle, IKnowledgeBase } from "@/lib/types";
import { researchApi } from "@/lib/api";

interface ApprovalQueueProps {
  articles: IResearchArticle[];
  knowledgeBases: IKnowledgeBase[];
  onUpdate: () => void;
}

export default function ApprovalQueue({ articles, knowledgeBases, onUpdate }: ApprovalQueueProps) {
  const [selectedKb, setSelectedKb] = useState<Record<string, string>>({});
  const [processing, setProcessing] = useState<string | null>(null);

  const handleDecision = async (articleId: string, approved: boolean) => {
    setProcessing(articleId);
    try {
      await researchApi.approve(articleId, approved, selectedKb[articleId]);
      onUpdate();
    } catch (err) {
      console.error(err);
    } finally {
      setProcessing(null);
    }
  };

  if (!articles.length) {
    return (
      <p className="text-sm text-gray-500 py-4">No articles pending review.</p>
    );
  }

  return (
    <div className="space-y-4">
      {articles.map((article) => (
        <div key={article.id} className="border border-gray-200 rounded-xl p-4">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0 flex-1">
              <a
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm font-medium text-indigo-700 hover:underline line-clamp-2"
              >
                {article.title}
              </a>
              <div className="flex items-center gap-3 mt-1">
                <span className="text-xs text-gray-500 uppercase bg-gray-100 px-2 py-0.5 rounded">
                  {article.source}
                </span>
                {article.authors && (
                  <span className="text-xs text-gray-500 truncate">{article.authors}</span>
                )}
              </div>
              {article.summary && (
                <p className="text-xs text-gray-600 mt-2 line-clamp-3">{article.summary}</p>
              )}
            </div>
          </div>

          <div className="flex items-center gap-3 mt-4">
            <select
              className="input text-xs py-1.5 max-w-[200px]"
              value={selectedKb[article.id] ?? ""}
              onChange={(e) => setSelectedKb((prev) => ({ ...prev, [article.id]: e.target.value }))}
            >
              <option value="">Select KB...</option>
              {knowledgeBases.map((kb) => (
                <option key={kb.id} value={kb.id}>{kb.name}</option>
              ))}
            </select>

            <button
              onClick={() => handleDecision(article.id, true)}
              disabled={processing === article.id || !selectedKb[article.id]}
              className="px-3 py-1.5 text-xs bg-green-600 text-white rounded-lg
                         hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              Approve & Ingest
            </button>
            <button
              onClick={() => handleDecision(article.id, false)}
              disabled={processing === article.id}
              className="px-3 py-1.5 text-xs bg-red-100 text-red-700 rounded-lg
                         hover:bg-red-200 disabled:opacity-50 transition-colors"
            >
              Reject
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
