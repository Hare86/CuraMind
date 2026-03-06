import { getAccessToken, clearAuth } from "./auth";
import type {
  ITokenResponse,
  ILoginRequest,
  IRegisterRequest,
  IQueryRequest,
  IQueryResponse,
  IMCQRequest,
  IMCQResponse,
  ICaseRequest,
  ICaseResponse,
  IKnowledgeBase,
  IKnowledgeBaseCreate,
  IDocument,
  IResearchArticle,
  IDashboardStats,
  IFeedback,
  ISourceSubmission,
  INotification,
  IPendingUser,
} from "./types";

// Always use relative URLs so requests route through Next.js proxy (avoids CORS).
// NEXT_PUBLIC_API_URL is only used in next.config.ts as the proxy destination.
const API_BASE = "";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  authenticated = true
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (authenticated) {
    const token = getAccessToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 401) {
    clearAuth();
    window.location.href = "/login";
    throw new ApiError(401, "Session expired");
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = body.detail;
    const message = Array.isArray(detail)
      ? detail.map((d: any) => d.msg ?? JSON.stringify(d)).join("; ")
      : typeof detail === "string"
      ? detail
      : `HTTP ${res.status}`;
    throw new ApiError(res.status, message);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export const authApi = {
  login: (data: ILoginRequest) =>
    request<ITokenResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    }, false),

  register: (data: IRegisterRequest) =>
    request<ITokenResponse>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }, false),

  refresh: (refreshToken: string) =>
    request<ITokenResponse>("/api/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    }, false),
};

// ---------------------------------------------------------------------------
// Query
// ---------------------------------------------------------------------------

export const queryApi = {
  query: (data: IQueryRequest) =>
    request<IQueryResponse>("/api/query", { method: "POST", body: JSON.stringify(data) }),

  generateMCQ: (data: IMCQRequest) =>
    request<IMCQResponse>("/api/generate-mcq", { method: "POST", body: JSON.stringify(data) }),

  generateCase: (data: ICaseRequest) =>
    request<ICaseResponse>("/api/generate-case", { method: "POST", body: JSON.stringify(data) }),
};

// ---------------------------------------------------------------------------
// Knowledge Base
// ---------------------------------------------------------------------------

export const kbApi = {
  list: () => request<IKnowledgeBase[]>("/api/kb-list"),

  create: (data: IKnowledgeBaseCreate) =>
    request<IKnowledgeBase>("/api/kb-create", { method: "POST", body: JSON.stringify(data) }),

  upload: (kbId: string, file: File) => {
    const form = new FormData();
    form.append("kb_id", kbId);
    form.append("file", file);
    const token = getAccessToken();
    return fetch(`${API_BASE}/api/kb-upload`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    }).then(async (res) => {
      if (!res.ok) throw new ApiError(res.status, "Upload failed");
      return res.json() as Promise<IDocument>;
    });
  },

  listDocuments: (kbId: string) =>
    request<IDocument[]>(`/api/kb/${kbId}/documents`),
};

// ---------------------------------------------------------------------------
// Research
// ---------------------------------------------------------------------------

export const researchApi = {
  getQueue: () => request<IResearchArticle[]>("/api/research-queue"),

  approve: (articleId: string, approved: boolean, targetKbId?: string) =>
    request("/api/research-approve", {
      method: "POST",
      body: JSON.stringify({ article_id: articleId, approved, target_kb_id: targetKbId }),
    }),

  triggerSearch: () =>
    request("/api/research-search", { method: "POST" }),
};

// ---------------------------------------------------------------------------
// Submissions
// ---------------------------------------------------------------------------

export const submissionsApi = {
  submit: (data: { submission_type: string; url?: string; title?: string }) => {
    const form = new FormData();
    Object.entries(data).forEach(([k, v]) => v && form.append(k, v));
    const token = getAccessToken();
    return fetch(`${API_BASE}/api/source-submit`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    }).then((res) => res.json() as Promise<ISourceSubmission>);
  },

  list: () => request<ISourceSubmission[]>("/api/source-submissions"),

  review: (id: string, approved: boolean, targetKbId?: string) =>
    request(`/api/source-submissions/${id}/review`, {
      method: "POST",
      body: JSON.stringify({ approved, target_kb_id: targetKbId }),
    }),
};

// ---------------------------------------------------------------------------
// Feedback
// ---------------------------------------------------------------------------

export const feedbackApi = {
  submit: (data: {
    query_text: string;
    response_text: string;
    rating: string;
    comment?: string;
  }) =>
    request<IFeedback>("/api/feedback", { method: "POST", body: JSON.stringify(data) }),

  getLowRated: () => request<IFeedback[]>("/api/feedback/low-rated"),
};

// ---------------------------------------------------------------------------
// Notifications
// ---------------------------------------------------------------------------

export const notificationsApi = {
  list: (unreadOnly = false) =>
    request<INotification[]>(`/api/notifications?unread_only=${unreadOnly}`),

  markRead: () =>
    request("/api/notifications/mark-read", { method: "POST" }),
};

// ---------------------------------------------------------------------------
// Admin
// ---------------------------------------------------------------------------

export const adminApi = {
  getDashboard: () => request<IDashboardStats>("/api/admin/dashboard"),
  listUsers: () => request<any[]>("/api/admin/users"),
  listPendingApprovals: () => request<IPendingUser[]>("/api/admin/users/pending-approval"),
  approveUser: (userId: string) =>
    request(`/api/admin/users/${userId}/approve`, { method: "POST" }),
  rejectUser: (userId: string) =>
    request(`/api/admin/users/${userId}/reject`, { method: "POST" }),
  assignRole: (userId: string, role: string) =>
    request(`/api/admin/users/${userId}/role`, {
      method: "PATCH",
      body: JSON.stringify({ role_name: role }),
    }),
};
