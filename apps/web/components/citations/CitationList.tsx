import type { ICitation } from "@/lib/types";
import CitationCard from "./CitationCard";

interface CitationListProps {
  citations: ICitation[];
}

export default function CitationList({ citations }: CitationListProps) {
  if (!citations.length) return null;

  return (
    <div className="mt-6">
      <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        Sources ({citations.length})
      </h3>
      <div className="space-y-2">
        {citations.map((citation) => (
          <CitationCard key={citation.index} citation={citation} />
        ))}
      </div>
    </div>
  );
}
