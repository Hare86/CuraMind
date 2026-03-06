// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export interface ITokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user_id: string;
  username: string | null;
  full_name: string | null;
  role: string | null;
  requires_login?: boolean;   // student registration: redirect to login
  pending_approval?: boolean; // non-student: pending admin approval
}

export interface ILoginRequest {
  email: string;
  password: string;
}

export interface IRegisterRequest {
  email: string;
  password: string;
  username: string;
  full_name?: string;
  salutation?: string;
  role_request?: string;
}

export interface IPendingUser {
  id: string;
  email: string;
  username: string | null;
  full_name: string | null;
  salutation: string | null;
  pending_role_name: string;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Query
// ---------------------------------------------------------------------------

export type QueryMode =
  | "question_answer"
  | "mcq"
  | "case_study"
  | "long_academic"
  | "symptoms_to_disorder"
  | "disorder_to_symptoms"
  | "treatment_approach";

export interface ICitation {
  index: number;
  document_title: string;
  page_number: number | null;
  source_url: string | null;
  kb_name: string | null;
  chunk_excerpt: string | null;
  relevance_score: number | null;
}

export interface IQueryRequest {
  query: string;
  mode: QueryMode;
  kb_ids?: string[];
  include_citations?: boolean;
  stream?: boolean;
}

export interface IQueryResponse {
  answer: string;
  citations: ICitation[];
  query_mode: QueryMode;
  kb_ids_searched: string[];
  retrieval_count: number;
  was_blocked: boolean;
  query_id: string | null;
}

export interface IMCQOption {
  label: string;
  text: string;
  is_correct: boolean;
}

export interface IMCQItem {
  question: string;
  options: IMCQOption[];
  explanation: string;
  citations: ICitation[];
}

export interface IMCQRequest {
  topic: string;
  count: number;
  kb_ids?: string[];
  difficulty: "beginner" | "intermediate" | "advanced";
}

export interface IMCQResponse {
  topic: string;
  items: IMCQItem[];
  kb_ids_searched: string[];
}

export interface ICaseRequest {
  disorder?: string;
  symptoms?: string[];
  scenario_context?: string;
  kb_ids?: string[];
}

export interface ICaseResponse {
  case_description: string;
  presenting_symptoms: string[];
  differential_diagnosis: string;
  treatment_considerations: string;
  citations: ICitation[];
}

// ---------------------------------------------------------------------------
// Knowledge Base
// ---------------------------------------------------------------------------

export interface IKnowledgeBase {
  id: string;
  name: string;
  description: string | null;
  category: string | null;
  is_public: boolean;
  document_count: number;
  chunk_count: number;
  owner_id: string | null;
  created_at: string;
}

export interface IKnowledgeBaseCreate {
  name: string;
  description?: string;
  category?: string;
  is_public?: boolean;
}

export interface IDocument {
  id: string;
  kb_id: string;
  filename: string;
  file_type: string;
  status: "pending" | "processing" | "completed" | "failed";
  page_count: number | null;
  chunk_count: number | null;
  error_message: string | null;
  created_at: string;
  processed_at: string | null;
}

// ---------------------------------------------------------------------------
// Research
// ---------------------------------------------------------------------------

export interface IResearchArticle {
  id: string;
  title: string;
  url: string;
  source: string;
  authors: string | null;
  abstract: string | null;
  summary: string | null;
  status: string;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Admin
// ---------------------------------------------------------------------------

export interface IDashboardStats {
  pending_research_articles: number;
  pending_submissions: number;
  total_knowledge_bases: number;
  total_documents: number;
  total_users: number;
  low_rated_responses: number;
  pending_user_approvals: number;
}

export interface IFeedback {
  id: string;
  rating: "useful" | "incorrect" | "needs_review";
  comment: string | null;
  query_mode: string | null;
  created_at: string;
}

export interface ISourceSubmission {
  id: string;
  submission_type: string;
  url: string | null;
  title: string | null;
  summary: string | null;
  status: string;
  created_at: string;
}

export interface INotification {
  id: string;
  message: string;
  notification_type: string;
  is_read: boolean;
  reference_id: string | null;
  created_at: string;
}
