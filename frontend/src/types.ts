export type Evidence = {
  label: string;
  reference: string;
};

export type WorkItem = {
  issue_key: string;
  summary: string;
  evidence: Evidence[];
};

export type Issue = {
  key: string;
  summary: string;
  status: "To Do" | "In Progress" | "Blocked" | "Done";
  assignee: string;
  updated_at: string;
  blocked_reason: string | null;
  planned: boolean;
};

export type Dashboard = {
  month: string;
  completed: number;
  active: number;
  blocked: number;
  stale: number;
  open_reviews: number;
  issues: Issue[];
};

export type DeveloperUpdate = {
  developer_id: string;
  developer_name: string;
  completed: WorkItem[];
  in_progress: WorkItem[];
  blockers: WorkItem[];
  needs_attention: WorkItem[];
  approved: boolean;
};

export type MeetingReport = {
  month: string;
  achievements: string[];
  blockers: string[];
  decisions_needed: string[];
  approved_updates: number;
};

