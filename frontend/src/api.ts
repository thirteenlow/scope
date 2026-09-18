import type { Dashboard, DeveloperUpdate, MeetingReport } from "./types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, options);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  dashboard: () => request<Dashboard>("/api/dashboard"),
  updates: () => request<DeveloperUpdate[]>("/api/updates"),
  report: () => request<MeetingReport>("/api/reports/monthly"),
  approve: (developerId: string) =>
    request<{ developer_id: string; approved: boolean }>(
      `/api/updates/${developerId}/approve`,
      { method: "POST" },
    ),
};

