def publish(event_name: str, payload: dict) -> None:
    """Mock message-bus publisher used by the sample codebase."""
    print({"event": event_name, "payload": payload})

