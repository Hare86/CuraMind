"use client";

import type { IKnowledgeBase } from "@/lib/types";

interface KnowledgeBaseSelectorProps {
  knowledgeBases: IKnowledgeBase[];
  selected: string[];
  onToggle: (id: string) => void;
}

const CATEGORY_COLORS: Record<string, string> = {
  dsm: "bg-purple-100 text-purple-700",
  cbt: "bg-blue-100 text-blue-700",
  rehab: "bg-green-100 text-green-700",
  research: "bg-orange-100 text-orange-700",
  custom: "bg-gray-100 text-gray-700",
};

export default function KnowledgeBaseSelector({
  knowledgeBases,
  selected,
  onToggle,
}: KnowledgeBaseSelectorProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {knowledgeBases.map((kb) => {
        const isSelected = selected.includes(kb.id);
        const catColor = CATEGORY_COLORS[kb.category ?? "custom"] ?? CATEGORY_COLORS.custom;

        return (
          <button
            key={kb.id}
            onClick={() => onToggle(kb.id)}
            className={`text-left p-4 rounded-xl border-2 transition-all
              ${isSelected
                ? "border-indigo-500 bg-indigo-50"
                : "border-gray-200 bg-white hover:border-gray-300"
              }`}
          >
            <div className="flex items-start justify-between mb-2">
              <h3 className="text-sm font-semibold text-gray-900 truncate">{kb.name}</h3>
              {kb.category && (
                <span className={`text-xs px-2 py-0.5 rounded-full ml-2 flex-shrink-0 ${catColor}`}>
                  {kb.category}
                </span>
              )}
            </div>
            {kb.description && (
              <p className="text-xs text-gray-500 line-clamp-2 mb-3">{kb.description}</p>
            )}
            <div className="flex gap-3 text-xs text-gray-400">
              <span>{kb.document_count} docs</span>
              <span>{kb.chunk_count.toLocaleString()} chunks</span>
            </div>
          </button>
        );
      })}
    </div>
  );
}
