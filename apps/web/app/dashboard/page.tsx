"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/ui/Sidebar";
import { adminApi, notificationsApi } from "@/lib/api";
import { getCurrentUser, STAFF_ROLES } from "@/lib/auth";
import type { IDashboardStats, INotification } from "@/lib/types";

const STAT_CARDS = [
  { key: "total_knowledge_bases" as const, label: "Knowledge Bases", color: "bg-blue-600", icon: "M4 6h16M4 10h16M4 14h16M4 18h16" },
  { key: "total_documents" as const, label: "Documents", color: "bg-cyan-600", icon: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" },
  { key: "total_users" as const, label: "Total Users", color: "bg-teal-600", icon: "M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" },
  { key: "pending_user_approvals" as const, label: "Pending Approvals", color: "bg-amber-500", icon: "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" },
  { key: "pending_research_articles" as const, label: "Pending Research", color: "bg-orange-500", icon: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" },
  { key: "low_rated_responses" as const, label: "Low-Rated Responses", color: "bg-red-500", icon: "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" },
];

export default function DashboardPage() {
  const router = useRouter();
  const [stats, setStats] = useState<IDashboardStats | null>(null);
  const [notifications, setNotifications] = useState<INotification[]>([]);
  const [loading, setLoading] = useState(true);
  const user = getCurrentUser();

  useEffect(() => {
    // Redirect students away from dashboard
    if (!user || !STAFF_ROLES.includes(user.role ?? "")) {
      router.replace("/knowledge-bases");
      return;
    }

    Promise.all([
      adminApi.getDashboard().catch(() => null),
      notificationsApi.list(true).catch(() => []),
    ]).then(([s, n]) => {
      if (s) setStats(s);
      setNotifications(n as INotification[]);
    }).finally(() => setLoading(false));
  }, [router, user]);

  const newArticleNotifs = notifications.filter((n) => n.notification_type === "new_article");

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 p-8">
        {/* New articles banner */}
        {newArticleNotifs.length > 0 && (
          <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-xl flex items-center gap-3">
            <svg className="w-5 h-5 text-blue-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            <p className="text-sm text-blue-800">
              <strong>{newArticleNotifs.length} new article(s)</strong> have been approved and added to the knowledge base.
            </p>
          </div>
        )}

        <h1 className="text-2xl font-bold text-gray-900 mb-1">Dashboard</h1>
        <p className="text-gray-500 text-sm mb-8">Platform overview &amp; system health</p>

        {loading ? (
          <div className="grid grid-cols-3 gap-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="bg-white rounded-xl border border-gray-100 animate-pulse h-28" />
            ))}
          </div>
        ) : stats ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {STAT_CARDS.map(({ key, label, color, icon }) => (
              <div key={key} className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 flex items-center gap-4">
                <div className={`${color} w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0`}>
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d={icon} />
                  </svg>
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">{stats[key]}</p>
                  <p className="text-sm text-gray-500">{label}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-gray-100 p-8 text-center">
            <p className="text-gray-500 text-sm">Could not load dashboard stats. Admin access may be required.</p>
          </div>
        )}
      </main>
    </div>
  );
}
