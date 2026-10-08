def on_bill_due(event: dict) -> None:
    send(event["user_id"], f"{event['bill_name']} is due in {event['days_until_due']} days")


def on_goal_progress(event: dict) -> None:
    send(event["user_id"], f"Your {event['goal_name']} goal is {event['percent']}% funded")


def send(user_id: str, message: str) -> None:
    print({"recipient": user_id, "message": message})

