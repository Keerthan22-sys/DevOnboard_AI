export interface User {
  id: string;
  email: string;
  name: string;
  role: "admin" | "lead" | "developer" | "viewer";
  created_at: string;
}

export interface Project {
  id: string;
  name: string;
  description: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface Document {
  id: string;
  project_id: string;
  title: string;
  source_type: "pdf" | "markdown" | "confluence" | "github" | "gitlab" | "text";
  source_url: string | null;
  status: "processing" | "ready" | "failed";
  chunk_count: number;
  created_at: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources: SourceCitation[];
  created_at: string;
}

export interface SourceCitation {
  document_id: string;
  section_title: string;
  source_url: string | null;
  page_number: number | null;
  relevance_score: number;
}

export interface ChatSession {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectStats {
  document_count: number;
  chunk_count: number;
  query_count: number;
  member_count: number;
  source_types: Record<string, number>;
}

export interface IntegrationCredential {
  id: string;
  project_id: string;
  integration_type: "github" | "gitlab" | "confluence";
  label: string;
  email: string | null;
  base_url: string | null;
  has_token: boolean;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  error: string | null;
}
