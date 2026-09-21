import type { ExpenseStatus as Status } from "@expenseflow/shared-types";

const labels: Record<Status, string> = {
  DRAFT: "Draft",
  SUBMITTED: "Awaiting manager",
  FINANCE_REVIEW: "Finance review",
  APPROVED: "Approved",
  PAID: "Paid",
  REJECTED: "Rejected",
};

export function ExpenseStatus({ status }: { status: Status }) {
  return <span data-status={status.toLowerCase()}>{labels[status]}</span>;
}

