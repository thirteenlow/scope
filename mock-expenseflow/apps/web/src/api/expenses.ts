import type { Expense, ExpenseInput } from "@expenseflow/shared-types";

const API_URL = "/api";

export async function getExpense(id: string): Promise<Expense> {
  const response = await fetch(`${API_URL}/expenses/${id}`);
  if (!response.ok) throw new Error("Unable to load expense");
  return response.json();
}

export async function updateExpense(id: string, input: ExpenseInput): Promise<Expense> {
  const response = await fetch(`${API_URL}/expenses/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!response.ok) throw new Error("Unable to update expense");
  return response.json();
}

export async function submitExpense(id: string): Promise<Expense> {
  const response = await fetch(`${API_URL}/expenses/${id}/submit`, { method: "POST" });
  if (!response.ok) throw new Error("Unable to submit expense");
  return response.json();
}

