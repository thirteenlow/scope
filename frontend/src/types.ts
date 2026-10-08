export type Screen = "chat" | "features" | "jira";

export type Feature = {
  id: string;
  title: string;
  description: string;
  target_weeks: number;
  owner: string;
  status: "draft" | "analyzed" | "approved" | "synced";
  created_at: string;
  selected_option?: string;
};

export type Evidence = {
  id: string;
  type: "verified" | "inferred" | "question";
  title: string;
  detail: string;
  path?: string;
  line?: number;
  confidence: number;
};

export type ScopeOption = {
  id: string;
  name: string;
  duration: string;
  confidence: "high" | "medium" | "low";
  summary: string;
  includes: string[];
  excludes: string[];
  recommended: boolean;
};

export type PlanItem = {
  temp_key: string;
  type: "Epic" | "Story" | "Task" | "Spike";
  title: string;
  description: string;
  parent?: string;
  estimate?: number;
  discipline?: string;
  evidence_ids: string[];
};

export type Analysis = {
  feature_id: string;
  verdict: string;
  feasibility: number;
  timeline_confidence: number;
  risk: "low" | "medium" | "high";
  summary: string;
  affected_areas: string[];
  evidence: Evidence[];
  options: ScopeOption[];
  plan: PlanItem[];
  questions: string[];
};

export type JiraIssue = {
  key: string;
  type: "Epic" | "Story" | "Task" | "Spike";
  summary: string;
  description: string;
  status: string;
  parent?: string;
  estimate?: number;
  assignee?: string;
  labels: string[];
  evidence_paths: string[];
};

export type RepoNode = { name: string; path: string; type: "file" | "folder"; children?: RepoNode[] };
export type RepoFile = { path: string; language: string; content: string; lines: number };
export type Bootstrap = {
  repository: { name: string; branch: string; commit: string; files: number; services: number; languages: { name: string; value: number }[]; indexed_at: string };
  features: Feature[];
  jira: JiraIssue[];
  team: { name: string; role: string; initials: string }[];
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
};

export type LlmStatus = { configured: boolean; provider: string; model: string };
export type ChatResponse = { message: string; model: string; analysis?: Analysis; feature_id?: string; conversation_id: string };

export type ConversationSummary = {
  id: string;
  title: string;
  target_weeks: number;
  created_at: string;
  updated_at: string;
  message_count: number;
  has_plan: boolean;
};

export type ConversationDetail = Omit<ConversationSummary, "message_count" | "has_plan"> & {
  messages: { id: string; role: "user" | "assistant"; content: string; created_at: string }[];
  analysis: Analysis | null;
  selected_option: string | null;
  prd_markdown: string | null;
  prd_model: string | null;
  prd_updated_at: string | null;
  jira_synced_at: string | null;
  jira_issue_keys: string[];
};

export type PrdResponse = {
  markdown: string;
  model: string;
  selected_option: string;
};

export type ProductFeature = {
  id: string;
  name: string;
  summary: string;
  category: string;
  status: string;
  capabilities: string[];
  evidence_paths: string[];
  accent: "violet" | "blue" | "orange" | "green" | "pink" | "cyan";
};
