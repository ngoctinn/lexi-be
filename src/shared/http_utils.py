import json


def parse_body(event: dict) -> dict:
    try:
        return json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON body")


def require_fields(body: dict, *fields: str) -> None:
    # Consider a field missing only if it's not present in the body or is None.
    # This avoids treating falsy-but-valid values like 0 or False as missing.
    missing = [f for f in fields if f not in body or body.get(f) is None]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")
