import json


def parse_body(event: dict) -> dict:
    try:
        return json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON body")


def require_fields(body: dict, *fields: str) -> None:
    missing = [f for f in fields if not body.get(f)]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")
