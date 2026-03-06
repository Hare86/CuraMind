import type { IKnowledgeBase } from "@/lib/types";

interface KBStatsProps {
  knowledgeBases: IKnowledgeBase[];
}

export default function KBStats({ knowledgeBases }: KBStatsProps) {
  const totalDocs = knowledgeBases.reduce((s, kb) => s + kb.document_count, 0);
  const totalChunks = knowledgeBases.reduce((s, kb) => s + kb.chunk_count, 0);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-indigo-50 rounded-lg p-3 text-center">
          <p className="text-xl font-bold text-indigo-700">{knowledgeBases.length}</p>
          <p className="text-xs text-indigo-500">Bases</p>
        </div>
        <div className="bg-blue-50 rounded-lg p-3 text-center">
          <p className="text-xl font-bold text-blue-700">{totalDocs}</p>
          <p className="text-xs text-blue-500">Documents</p>
        </div>
        <div className="bg-green-50 rounded-lg p-3 text-center">
          <p className="text-xl font-bold text-green-700">{totalChunks.toLocaleString()}</p>
          <p className="text-xs text-green-500">Chunks</p>
        </div>
      </div>

      <div className="space-y-2">
        {knowledgeBases.map((kb) => (
          <div key={kb.id} className="flex items-center justify-between py-2 border-b border-gray-100">
            <div>
              <p className="text-sm font-medium text-gray-800">{kb.name}</p>
              <p className="text-xs text-gray-400">{kb.category ?? "uncategorized"}</p>
            </div>
            <div className="text-right">
              <p className="text-xs text-gray-600">{kb.document_count} docs</p>
              <p className="text-xs text-gray-400">{kb.chunk_count.toLocaleString()} chunks</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
