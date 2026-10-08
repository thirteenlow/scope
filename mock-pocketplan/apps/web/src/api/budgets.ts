import type { BudgetMonth, CategoryAssignment } from "@pocketplan/domain";

const API_URL = "/api";

export async function getBudgetMonth(month: string): Promise<BudgetMonth> {
  const response = await fetch(`${API_URL}/budgets/${month}`);
  if (!response.ok) throw new Error("Unable to load budget month");
  return response.json();
}

export async function assignCategory(
  month: string,
  categoryId: string,
  assignedCents: number,
): Promise<CategoryAssignment> {
  const response = await fetch(`${API_URL}/budgets/${month}/categories/${categoryId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ assignedCents }),
  });
  if (!response.ok) throw new Error("Unable to update category budget");
  return response.json();
}

