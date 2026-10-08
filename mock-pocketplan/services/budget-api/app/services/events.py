def publish(event_name: str, payload: dict) -> None:
    """Mock event publisher for the sample codebase."""
    print({"event": event_name, "payload": payload})

