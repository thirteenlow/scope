import type { CalendarEvent, Category, Dashboard, DeveloperUpdate, Insight, MeetingAction, MeetingWorkspace, UpdateItem, User } from "./types";

export const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
let userId = localStorage.getItem("sync-user") ?? "bryan";
export function setApiUser(id: string) { userId = id; localStorage.setItem("sync-user", id); }

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", "X-User-Id": userId, ...(options?.headers ?? {}) },
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail ?? `Request failed: ${response.status}`);
  return response.json() as Promise<T>;
}

export const api = {
  users: () => request<User[]>("/api/session/users"),
  dashboard: () => request<Dashboard>("/api/dashboard"),
  insights: () => request<Insight[]>("/api/insights"),
  calendar: () => request<CalendarEvent[]>("/api/calendar"),
  updates: () => request<DeveloperUpdate[]>("/api/updates"),
  addItem: (developerId: string, body: { title: string; detail: string; category: Category; target_date?: string | null }) => request<UpdateItem>(`/api/updates/${developerId}/items`, { method: "POST", body: JSON.stringify(body) }),
  editItem: (id: string, body: Partial<Pick<UpdateItem, "title" | "detail" | "category" | "target_date">>) => request<UpdateItem>(`/api/update-items/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteItem: (id: string) => request(`/api/update-items/${id}`, { method: "DELETE" }),
  acceptSuggestion: (id: string) => request<UpdateItem>(`/api/suggestions/${id}/accept`, { method: "POST", body: "{}" }),
  dismissSuggestion: (id: string) => request(`/api/suggestions/${id}`, { method: "DELETE" }),
  approveUpdate: (id: string) => request(`/api/updates/${id}/approve`, { method: "POST" }),
  meeting: () => request<MeetingWorkspace>("/api/meeting"),
  saveNotes: (text: string) => request("/api/meeting/notes", { method: "PUT", body: JSON.stringify({ text }) }),
  suggestActions: () => request<MeetingAction[]>("/api/meeting/actions/suggest", { method: "POST" }),
  approveAction: (id: string) => request<MeetingAction>(`/api/meeting/actions/${id}/approve`, { method: "POST" }),
};
