def last_session_names(history: list[dict], limit: int = 3) -> list[str]:
    return [item.get("name", "") for item in history[-limit:]]
