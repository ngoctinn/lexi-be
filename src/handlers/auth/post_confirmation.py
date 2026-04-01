import boto3
import os
import logging
from datetime import datetime, timezone
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])


def handler(event, context):
    user_id = event["request"]["userAttributes"]["sub"]
    email = event["request"]["userAttributes"]["email"]
    now = datetime.now(timezone.utc).isoformat()

    try:
        table.put_item(
            Item={
                "PK": f"USER#{user_id}",
                "SK": "PROFILE",
                "EntityType": "USER_PROFILE",
                "user_id": user_id,
                "email": email,
                "display_name": email.split("@")[0],
                "role": "LEARNER",
                "is_active": True,
                "current_level": "A1",
                "current_streak": 0,
                "total_sessions": 0,
                "total_words_learned": 0,
                "created_at": now,
                "updated_at": now,
                "GSI3PK": "USER_PROFILE",
                "GSI3SK": now,
            },
            ConditionExpression="attribute_not_exists(PK)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
            logger.error("Failed to create user profile: %s", e)
        # Luôn return event để không block Cognito confirmation

    return event
