"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/ui/Sidebar";
import KnowledgeBaseSelector from "@/components/knowledge-base/KnowledgeBaseSelector";
import UploadModal from "@/components/knowledge-base/UploadModal";
import { kbApi, notificationsApi } from "@/lib/api";
import { getCurrentUser, STAFF_ROLES } from "@/lib/auth";
import type { IKnowledgeBase, INotification } from "@/lib/types";

export default function KnowledgeBasesPage() {
  const [kbs, setKbs] = useState<IKnowledgeBase[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [showUpload, setShowUpload] = useState(false);
  const [loading, setLoading] = useState(true);
  const [newArticleNotifs, setNewArticleNotifs] = useState<INotification[]>([]);
  const [notifDismissed, setNotifDismissed] = useState(false);
  const user = getCurrentUser();
  const isStudent = !user?.role || !STAFF_ROLES.includes(user.role);

  const loadKbs = () => {
    setLoading(true);
    kbApi.list().then(setKbs).catch(() => {}).finally(() => setLoading(false));
  };

  useEffect(() => {
    loadKbs();
    // Load unread new-article notifications for all users
    notificationsApi.list(true).then((notifs) => {
      setNewArticleNotifs(notifs.filter((n) => n.notification_type === "new_article"));
    }).catch(() => {});
  }, []);

  const toggleSelect = (id: string) => {
    setSelected((prev) => prev.includes(id) ? prev.filter((k) => k !== id) : [...prev, id]);
  };

  const dismissNotif = () => {
    notificationsApi.markRead().catch(() => {});
    setNotifDismissed(true);
  };

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 p-8">
        {/* New articles notification banner */}
        {newArticleNotifs.length > 0 && !notifDismissed && (
          <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-xl flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <svg className="w-5 h-5 text-blue-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              <p className="text-sm text-blue-800">
                <strong>{newArticleNotifs.length} new article(s)</strong> have been approved and are now available in the knowledge base.
              </p>
            </div>
            <button
              onClick={dismissNotif}
              className="text-blue-400 hover:text-blue-600 text-xs flex-shrink-0"
            >
              Dismiss
            </button>
          </div>
        )}

        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Knowledge Bases</h1>
            <p className="text-gray-500 text-sm mt-1">
              {kbs.length} knowledge base{kbs.length !== 1 ? "s" : ""} available
            </p>
          </div>
          {/* Only non-students can upload */}
          {!isStudent && (
            <button onClick={() => setShowUpload(true)} className="btn-primary">
              + Upload Document
            </button>
          )}
        </div>

        {loading ? (
          <div className="grid grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="card animate-pulse h-32" />
            ))}
          </div>
        ) : kbs.length === 0 ? (
          <div className="card text-center py-12">
            <p className="text-gray-500">No knowledge bases available yet.</p>
          </div>
        ) : (
          <KnowledgeBaseSelector
            knowledgeBases={kbs}
            selected={selected}
            onToggle={toggleSelect}
          />
        )}

        {showUpload && kbs.length > 0 && (
          <UploadModal
            knowledgeBases={kbs}
            onClose={() => setShowUpload(false)}
            onSuccess={() => { setShowUpload(false); loadKbs(); }}
          />
        )}
      </main>
    </div>
  );
}
