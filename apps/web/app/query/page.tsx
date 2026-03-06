"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/ui/Sidebar";
import QueryPanel from "@/components/query/QueryPanel";
import { kbApi } from "@/lib/api";
import type { IKnowledgeBase } from "@/lib/types";

export default function QueryPage() {
  const [knowledgeBases, setKnowledgeBases] = useState<IKnowledgeBase[]>([]);

  useEffect(() => {
    kbApi.list().then(setKnowledgeBases).catch(() => {});
  }, []);

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-8 max-w-4xl">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Query Knowledge Base</h1>
        <p className="text-gray-500 text-sm mb-8">
          All answers are grounded in verified source documents with citations.
        </p>
        <QueryPanel knowledgeBases={knowledgeBases} />
      </main>
    </div>
  );
}
