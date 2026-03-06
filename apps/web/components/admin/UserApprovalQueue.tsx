"use client";

import { useState } from "react";
import type { IPendingUser } from "@/lib/types";
import { adminApi } from "@/lib/api";

interface UserApprovalQueueProps {
  users: IPendingUser[];
  onUpdate: () => void;
}

const ROLE_LABELS: Record<string, string> = {
  psychologist: "Psychologist",
  rehab_staff: "Rehabilitation Staff",
  hospital_admin: "Hospital Administrator",
  researcher: "Researcher",
  doctor: "Doctor",
};

export default function UserApprovalQueue({ users, onUpdate }: UserApprovalQueueProps) {
  const [processing, setProcessing] = useState<string | null>(null);

  const handleDecision = async (userId: string, approve: boolean) => {
    setProcessing(userId);
    try {
      if (approve) {
        await adminApi.approveUser(userId);
      } else {
        await adminApi.rejectUser(userId);
      }
      onUpdate();
    } catch (err) {
      console.error(err);
    } finally {
      setProcessing(null);
    }
  };

  if (!users.length) {
    return (
      <div className="text-center py-8">
        <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
          <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <p className="text-sm text-gray-500">No pending user approvals.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {users.map((user) => (
        <div key={user.id} className="border border-gray-200 rounded-xl p-4 bg-white">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                <span className="text-blue-700 font-bold text-sm uppercase">
                  {(user.username ?? user.email).charAt(0)}
                </span>
              </div>
              <div>
                <div className="flex items-center gap-2">
                  {user.salutation && (
                    <span className="text-xs text-gray-500">{user.salutation}</span>
                  )}
                  <p className="text-sm font-semibold text-gray-900">
                    {user.full_name ?? user.username ?? "—"}
                  </p>
                </div>
                <p className="text-xs text-gray-500">{user.email}</p>
                {user.username && (
                  <p className="text-xs text-gray-400">@{user.username}</p>
                )}
              </div>
            </div>

            <div className="text-right flex-shrink-0">
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
                {ROLE_LABELS[user.pending_role_name] ?? user.pending_role_name}
              </span>
              <p className="text-xs text-gray-400 mt-1">
                {new Date(user.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 mt-4">
            <button
              onClick={() => handleDecision(user.id, true)}
              disabled={processing === user.id}
              className="flex-1 py-1.5 text-xs font-medium bg-green-600 text-white rounded-lg
                         hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              {processing === user.id ? "Processing..." : "Approve"}
            </button>
            <button
              onClick={() => handleDecision(user.id, false)}
              disabled={processing === user.id}
              className="flex-1 py-1.5 text-xs font-medium bg-red-100 text-red-700 rounded-lg
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
