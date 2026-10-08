from ..models.budget import CategoryAssignment


def apply_activity(assignment: CategoryAssignment, amount_cents: int) -> None:
    assignment.activity_cents += amount_cents
    assignment.available_cents = assignment.assigned_cents - assignment.activity_cents


def suggested_goal_contribution(target_cents: int, saved_cents: int, months_left: int) -> int:
    if months_left <= 0:
        return max(0, target_cents - saved_cents)
    return max(0, target_cents - saved_cents) // months_left

