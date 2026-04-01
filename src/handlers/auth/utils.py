import json
import boto3
import os

cognito = boto3.client("cognito-idp")
CLIENT_ID = os.environ["COGNITO_CLIENT_ID"]


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def parse_body(event):
    """Parse JSON body, raise ValueError if invalid."""
    try:
        return json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON body")


def require_fields(body, *fields):
    """Raise ValueError if any required field is missing."""
    missing = [f for f in fields if not body.get(f)]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")
