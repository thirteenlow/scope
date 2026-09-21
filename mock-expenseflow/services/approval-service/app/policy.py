from dataclasses import dataclass


@dataclass
class ApprovalStep:
    role: str
    threshold: int | None = None


def approval_steps(amount: int) -> list[ApprovalStep]:
    steps = [ApprovalStep(role="MANAGER")]
    if amount >= 100_000:
        steps.append(ApprovalStep(role="DEPARTMENT_HEAD", threshold=100_000))
    steps.append(ApprovalStep(role="FINANCE"))
    return steps

