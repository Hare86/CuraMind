import type { ICitation } from "@/lib/types";

interface CitationCardProps {
  citation: ICitation;
}

export default function CitationCard({ citation }: CitationCardProps) {
  return (
    <div className="border border-gray-200 rounded-lg p-3 hover:border-indigo-300 transition-colors">
      <div className="flex items-start gap-2">
        <span className="inline-flex items-center justify-center w-5 h-5 bg-indigo-100 text-indigo-700
                         text-xs font-bold rounded flex-shrink-0 mt-0.5">
          {citation.index}
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-gray-900 truncate">{citation.document_title}</p>
          <div className="flex items-center gap-2 mt-0.5 flex-wrap">
            {citation.kb_name && (
              <span className="text-xs text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-full">
                {citation.kb_name}
              </span>
            )}
            {citation.page_number && (
              <span className="text-xs text-gray-500">Page {citation.page_number}</span>
            )}
            {citation.relevance_score && (
              <span className="text-xs text-gray-400">
                {(citation.relevance_score * 100).toFixed(0)}% match
              </span>
            )}
          </div>
          {citation.chunk_excerpt && (
            <p className="text-xs text-gray-500 mt-1 line-clamp-2">{citation.chunk_excerpt}</p>
          )}
          {citation.source_url && (
            <a
              href={citation.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-indigo-500 hover:underline mt-1 block truncate"
            >
              {citation.source_url}
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
