"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/ui/Sidebar";
import ApprovalQueue from "@/components/admin/ApprovalQueue";
import FeedbackReport from "@/components/admin/FeedbackReport";
import KBStats from "@/components/admin/KBStats";
import UserApprovalQueue from "@/components/admin/UserApprovalQueue";
import { researchApi, feedbackApi, kbApi, adminApi } from "@/lib/api";
import type { IResearchArticle, IFeedback, IKnowledgeBase, IPendingUser } from "@/lib/types";

type AdminTab = "users" | "research" | "feedback" | "kbstats";

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<AdminTab>("users");
  const [articles, setArticles] = useState<IResearchArticle[]>([]);
  const [feedbacks, setFeedbacks] = useState<IFeedback[]>([]);
  const [kbs, setKbs] = useState<IKnowledgeBase[]>([]);
  const [pendingUsers, setPendingUsers] = useState<IPendingUser[]>([]);
  const [loading, setLoading] = useState(true);

  const loadAll = () => {
    setLoading(true);
    Promise.all([
      researchApi.getQueue(),
      feedbackApi.getLowRated(),
      kbApi.list(),
      adminApi.listPendingApprovals(),
    ])
      .then(([a, f, k, pu]) => {
        setArticles(a);
        setFeedbacks(f);
        setKbs(k);
        setPendingUsers(pu);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadAll(); }, []);

  const TABS: { key: AdminTab; label: string; badge?: number }[] = [
    { key: "users", label: "User Approvals", badge: pendingUsers.length },
    { key: "research", label: "Research Queue", badge: articles.length },
    { key: "feedback", label: "Low-Rated Responses", badge: feedbacks.length },
    { key: "kbstats", label: "KB Statistics" },
  ];

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 p-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">Admin Panel</h1>
        <p className="text-gray-500 text-sm mb-6">Review, approve, and monitor platform content and users</p>

        {/* Tab bar */}
        <div className="flex border-b border-gray-200 mb-6">
          {TABS.map(({ key, label, badge }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={`px-4 py-2.5 text-sm font-medium flex items-center gap-2 transition-colors
                ${activeTab === key
                  ? "border-b-2 border-blue-700 text-blue-700"
                  : "text-gray-500 hover:text-gray-700"
                }`}
            >
              {label}
              {badge != null && badge > 0 && (
                <span className="bg-red-500 text-white text-xs rounded-full w-5 h-5
                                 flex items-center justify-center">
                  {badge > 99 ? "99+" : badge}
                </span>
              )}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="bg-white rounded-xl border border-gray-100 animate-pulse h-48" />
        ) : (
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
            {activeTab === "users" && (
              <UserApprovalQueue
                users={pendingUsers}
                onUpdate={loadAll}
              />
            )}
            {activeTab === "research" && (
              <ApprovalQueue
                articles={articles}
                knowledgeBases={kbs}
                onUpdate={loadAll}
              />
            )}
            {activeTab === "feedback" && <FeedbackReport feedbacks={feedbacks} />}
            {activeTab === "kbstats" && <KBStats knowledgeBases={kbs} />}
          </div>
        )}
      </main>
    </div>
  );
}
