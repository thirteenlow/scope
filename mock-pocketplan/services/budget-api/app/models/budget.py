from dataclasses import dataclass, field
from enum import StrEnum


class MonthStatus(StrEnum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


@dataclass
class CategoryAssignment:
    category_id: str
    category_name: str
    assigned_cents: int = 0
    activity_cents: int = 0
    available_cents: int = 0


@dataclass
class BudgetMonth:
    id: str
    user_id: str
    month: str
    status: MonthStatus = MonthStatus.OPEN
    available_to_assign_cents: int = 0
    categories: list[CategoryAssignment] = field(default_factory=list)

