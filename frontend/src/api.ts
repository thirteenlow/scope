import type { Analysis, Bootstrap, ChatMessage, ChatResponse, Feature, JiraIssue, LlmStatus, RepoFile, RepoNode } from "./types";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(body.detail || "Request failed");
  }
  return response.json();
}

export const api = {
  bootstrap: () => request<Bootstrap>("/api/bootstrap"),
  updateFeature: (feature: Feature) => request<Feature>(`/api/features/${feature.id}`, { method: "PUT", body: JSON.stringify({ title: feature.title, description: feature.description, target_weeks: feature.target_weeks }) }),
  analyze: (id: string) => request<Analysis>(`/api/features/${id}/analyze`, { method: "POST" }),
  getAnalysis: (id: string) => request<Analysis>(`/api/features/${id}/analysis`),
  approve: (id: string, optionId: string) => request<Feature>(`/api/features/${id}/approve`, { method: "POST", body: JSON.stringify({ option_id: optionId }) }),
  syncJira: (id: string) => request<JiraIssue[]>(`/api/features/${id}/sync-jira`, { method: "POST" }),
  jira: () => request<JiraIssue[]>("/api/jira/issues"),
  tree: () => request<RepoNode[]>("/api/repo/tree"),
  file: (path: string) => request<RepoFile>(`/api/repo/file?path=${encodeURIComponent(path)}`),
  llmStatus: () => request<LlmStatus>("/api/llm/status"),
  chat: (messages: ChatMessage[], mode: "chat" | "plan", targetWeeks: number) => request<ChatResponse>("/api/chat", { method: "POST", body: JSON.stringify({ messages: messages.map(({ role, content }) => ({ role, content })), mode, target_weeks: targetWeeks }) }),
};
