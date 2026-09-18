export type Role = "developer" | "pm";
export type Category = "completed" | "in_progress" | "blocker";

export type User = { id: string; name: string; role: Role; title: string; avatar: string };
export type Evidence = { source: "jira" | "git" | "manual"; label: string; reference: string; url: string | null };
export type UpdateItem = { id: string; developer_id: string; title: string; detail: string; category: Category; target_date: string | null; evidence: Evidence[]; source: "suggested" | "manual" };
export type Suggestion = { id: string; developer_id: string; title: string; detail: string; category: Category; occurred_at: string; evidence: Evidence[] };
export type DeveloperUpdate = { developer: User; items: UpdateItem[]; suggestions: Suggestion[]; approved: boolean };
export type Issue = { key: string; summary: string; status: string; assignee: string; updated_at: string; due_date: string | null; blocked_reason: string | null; planned: boolean };
export type Dashboard = { month: string; meeting_date: string; completed: number; active: number; blocked: number; stale: number; open_reviews: number; planned_percent: number; issues: Issue[] };
export type Insight = { id: string; severity: "info" | "warning" | "positive"; title: string; detail: string; evidence: string[] };
export type CalendarEvent = { id: string; date: string; title: string; kind: "meeting" | "cutoff" | "issue" | "review"; owner: string | null };
export type MeetingAction = { id: string; action: "create_issue" | "carry_over"; title: string; issue_key: string | null; owner: string | null; approved: boolean };
export type MeetingWorkspace = { month: string; meeting_date: string; notes: string; actions: MeetingAction[]; approved_updates: number; total_updates: number };
