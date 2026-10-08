from uuid import uuid4

from ..models.budget import BudgetMonth, CategoryAssignment, MonthStatus
from .events import publish


def create_next_month(current: BudgetMonth, next_month: str) -> BudgetMonth:
    """Current behavior creates independent months with zero category balances."""
    current.status = MonthStatus.CLOSED
    categories = [
        CategoryAssignment(
            category_id=item.category_id,
            category_name=item.category_name,
            assigned_cents=0,
            activity_cents=0,
            available_cents=0,
        )
        for item in current.categories
    ]
    created = BudgetMonth(
        id=str(uuid4()),
        user_id=current.user_id,
        month=next_month,
        categories=categories,
    )
    publish("budget.month_created", {"user_id": current.user_id, "month": next_month})
    return created

