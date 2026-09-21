def on_expense_submitted(event: dict) -> None:
    send(event["employee_id"], "Your expense was submitted")


def on_approval_requested(event: dict) -> None:
    send(event["manager_id"], "An expense is waiting for your review")


def send(user_id: str, message: str) -> None:
    print({"recipient": user_id, "message": message})

