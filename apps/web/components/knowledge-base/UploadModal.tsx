"use client";

import { useRef, useState } from "react";
import { kbApi } from "@/lib/api";
import type { IKnowledgeBase } from "@/lib/types";

interface UploadModalProps {
  knowledgeBases: IKnowledgeBase[];
  onClose: () => void;
  onSuccess: () => void;
}

const ALLOWED_EXTENSIONS = ["pdf", "docx", "pptx", "txt", "csv", "md"];

export default function UploadModal({ knowledgeBases, onClose, onSuccess }: UploadModalProps) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [selectedKb, setSelectedKb] = useState(knowledgeBases[0]?.id ?? "");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    const ext = f.name.split(".").pop()?.toLowerCase() ?? "";
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setError(`Unsupported type. Allowed: ${ALLOWED_EXTENSIONS.join(", ")}`);
      return;
    }
    setError("");
    setFile(f);
  };

  const handleUpload = async () => {
    if (!file || !selectedKb) return;
    setLoading(true);
    setError("");
    try {
      await kbApi.upload(selectedKb, file);
      onSuccess();
    } catch (err: any) {
      setError(err.message ?? "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="card w-full max-w-md">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-gray-900">Upload Document</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Knowledge Base</label>
            <select
              className="input"
              value={selectedKb}
              onChange={(e) => setSelectedKb(e.target.value)}
            >
              {knowledgeBases.map((kb) => (
                <option key={kb.id} value={kb.id}>{kb.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">File</label>
            <div
              className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center
                          cursor-pointer hover:border-indigo-300 transition-colors"
              onClick={() => fileRef.current?.click()}
            >
              {file ? (
                <div>
                  <p className="font-medium text-gray-900 text-sm">{file.name}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              ) : (
                <div>
                  <svg className="w-10 h-10 text-gray-300 mx-auto mb-2" fill="none"
                    stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                      d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <p className="text-sm text-gray-500">Click to select a file</p>
                  <p className="text-xs text-gray-400 mt-1">{ALLOWED_EXTENSIONS.join(", ")}</p>
                </div>
              )}
            </div>
            <input
              ref={fileRef}
              type="file"
              className="hidden"
              accept={ALLOWED_EXTENSIONS.map((e) => `.${e}`).join(",")}
              onChange={handleFileChange}
            />
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <div className="flex gap-3">
            <button onClick={onClose} className="btn-secondary flex-1">Cancel</button>
            <button
              onClick={handleUpload}
              className="btn-primary flex-1"
              disabled={!file || !selectedKb || loading}
            >
              {loading ? "Uploading..." : "Upload & Ingest"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
