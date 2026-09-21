from .policy import approval_steps


def on_approval_requested(event: dict) -> dict:
    return {
        "expense_id": event["expense_id"],
        "status": "PENDING",
        "steps": [step.role for step in approval_steps(event.get("amount", 0))],
    }

