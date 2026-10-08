export type AccountType = "CASH" | "BANK" | "CREDIT_CARD";

export type CategoryAssignment = {
  categoryId: string;
  categoryName: string;
  assignedCents: number;
  activityCents: number;
  availableCents: number;
};

export type BudgetMonth = {
  id: string;
  userId: string;
  month: string;
  label: string;
  status: "OPEN" | "CLOSED";
  availableToAssignCents: number;
  categories: CategoryAssignment[];
};

export type Transaction = {
  id: string;
  userId: string;
  accountId: string;
  categoryId?: string;
  merchant: string;
  amountCents: number;
  occurredOn: string;
  cleared: boolean;
};

