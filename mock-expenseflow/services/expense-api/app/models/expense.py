from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class ExpenseStatus(StrEnum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    FINANCE_REVIEW = "FINANCE_REVIEW"
    APPROVED = "APPROVED"
    PAID = "PAID"
    REJECTED = "REJECTED"


@dataclass
class Expense:
    id: str
    employee_id: str
    description: str
    category: str
    amount: int
    currency: str
    status: ExpenseStatus = ExpenseStatus.DRAFT
    submitted_at: datetime | None = None

