from fastapi import APIRouter, HTTPException

from ..models.expense import Expense, ExpenseStatus
from ..services.submission import submit


router = APIRouter(prefix="/expenses")
EXPENSES: dict[str, Expense] = {}


@router.get("/{expense_id}")
def get_expense(expense_id: str) -> Expense:
    if expense_id not in EXPENSES:
        raise HTTPException(404, "Expense not found")
    return EXPENSES[expense_id]


@router.patch("/{expense_id}")
def update_expense(expense_id: str, changes: dict) -> Expense:
    expense = get_expense(expense_id)

    # Business invariant: submitted expenses are immutable.
    if expense.status != ExpenseStatus.DRAFT:
        raise HTTPException(409, "Only draft expenses can be edited")

    for field in ("description", "category", "amount", "currency"):
        if field in changes:
            setattr(expense, field, changes[field])
    return expense


@router.post("/{expense_id}/submit")
def submit_expense(expense_id: str) -> Expense:
    return submit(get_expense(expense_id))

