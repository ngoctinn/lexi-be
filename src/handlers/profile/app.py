import json
import boto3
import os
from datetime import datetime, timezone
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])


def _user_id(event):
    return event["requestContext"]["authorizer"]["claims"]["sub"]


def _now():
    return datetime.now(timezone.utc).isoformat()


def response(status, body):
    return {"statusCode": status, "headers": {"Content-Type": "application/json"}, "body": json.dumps(body)}


def handler(event, context):
    method = event["httpMethod"]
    user_id = _user_id(event)

    if method == "GET":
        result = table.get_item(Key={"PK": f"USER#{user_id}", "SK": "PROFILE"})
        item = result.get("Item")
        if not item:
            return response(404, {"error": "Profile not found"})
        return response(200, item)

    if method == "PUT":
        try:
            body = json.loads(event.get("body") or "{}")
        except json.JSONDecodeError:
            return response(400, {"error": "Invalid JSON"})

        allowed = {"display_name", "current_level"}
        updates = {k: v for k, v in body.items() if k in allowed and v}
        if not updates:
            return response(400, {"error": "No valid fields to update"})

        updates["updated_at"] = _now()
        expr = "SET " + ", ".join(f"#{k}=:{k}" for k in updates)
        names = {f"#{k}": k for k in updates}
        values = {f":{k}": v for k, v in updates.items()}

        table.update_item(
            Key={"PK": f"USER#{user_id}", "SK": "PROFILE"},
            UpdateExpression=expr,
            ExpressionAttributeNames=names,
            ExpressionAttributeValues=values,
        )
        return response(200, {"message": "Profile updated"})
