export type ExpenseStatus =
  | "DRAFT"
  | "SUBMITTED"
  | "FINANCE_REVIEW"
  | "APPROVED"
  | "PAID"
  | "REJECTED";

export type Expense = {
  id: string;
  employeeId: string;
  description: string;
  category: string;
  amount: number;
  currency: string;
  receiptUrl?: string;
  status: ExpenseStatus;
  submittedAt?: string;
  updatedAt: string;
};

export type ExpenseInput = Pick<Expense, "description" | "category" | "amount" | "currency" | "receiptUrl">;

