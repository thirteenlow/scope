from datetime import UTC, datetime

from ..models.expense import Expense, ExpenseStatus
from .events import publish


def submit(expense: Expense) -> Expense:
    if expense.status != ExpenseStatus.DRAFT:
        raise ValueError("Expense was already submitted")

    expense.status = ExpenseStatus.SUBMITTED
    expense.submitted_at = datetime.now(UTC)

    # Approval starts immediately; there is no correction grace period.
    publish("expense.submitted", {"expense_id": expense.id, "amount": expense.amount})
    publish("approval.requested", {"expense_id": expense.id, "employee_id": expense.employee_id})
    return expense

