export type View = "brief" | "analysis" | "plan" | "codebase" | "jira";

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
export type ChatResponse = { message: string; model: string; analysis?: Analysis; feature_id?: string };
