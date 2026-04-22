"""Shared utilities cho admin handlers."""
import json
from typing import Optional, Tuple

from infrastructure.persistence.dynamo_user_repo import DynamoDBUserRepo


def _response(status: int, body: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }


def check_admin(event: dict, user_repo: DynamoDBUserRepo) -> Tuple[Optional[str], Optional[dict]]:
    """
    Kiểm tra JWT và role ADMIN.
    Trả về (user_id, None) nếu hợp lệ, hoặc (None, error_response) nếu không.
    """
    try:
        user_id = event["requestContext"]["authorizer"]["claims"]["sub"]
    except KeyError:
        return None, _response(401, {"error": "Unauthorized"})

    profile = user_repo.get_by_user_id(user_id)
    role_value = profile.role.value if profile and hasattr(profile.role, "value") else (profile.role if profile else None)
    if not profile or role_value != "ADMIN":
        return None, _response(403, {"error": "Forbidden"})

    return user_id, None


def parse_body(event: dict) -> dict:
    try:
        return json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return {}
