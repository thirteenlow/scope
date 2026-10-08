from fastapi import APIRouter, HTTPException

from ..models.budget import BudgetMonth, MonthStatus


router = APIRouter(prefix="/budgets")
BUDGETS: dict[str, BudgetMonth] = {}


@router.get("/{month}")
def get_budget_month(month: str) -> BudgetMonth:
    if month not in BUDGETS:
        raise HTTPException(404, "Budget month not found")
    return BUDGETS[month]


@router.patch("/{month}/categories/{category_id}")
def assign_category(month: str, category_id: str, changes: dict) -> dict:
    budget = get_budget_month(month)
    if budget.status == MonthStatus.CLOSED:
        raise HTTPException(409, "Closed budget months cannot be changed")
    assignment = next((item for item in budget.categories if item.category_id == category_id), None)
    if not assignment:
        raise HTTPException(404, "Category assignment not found")
    assignment.assigned_cents = int(changes["assignedCents"])
    assignment.available_cents = assignment.assigned_cents - assignment.activity_cents
    return assignment.__dict__

