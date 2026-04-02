import os
import boto3
from botocore.exceptions import ClientError
from src.application.ports.user_repo import IUserRepo
from src.domain.entities.user import UserProfile


class DynamoDBUserRepo(IUserRepo):
    def __init__(self, table=None):
        self._table = table or boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])

    def create(self, profile: UserProfile) -> None:
        try:
            self._table.put_item(
                Item={
                    "PK": f"USER#{profile.user_id}",
                    "SK": "PROFILE",
                    "GSI1PK": f"USER#{profile.user_id}#USER_PROFILE",
                    "GSI1SK": profile.created_at,
                    "EntityType": "USER_PROFILE",
                    "user_id": profile.user_id,
                    "email": profile.email,
                    "display_name": profile.display_name,
                    "role": profile.role,
                    "is_active": profile.is_active,
                    "is_onboarded": profile.is_onboarded,
                    "current_level": profile.current_level,
                    "learning_goal": profile.learning_goal,
                    "current_streak": profile.current_streak,
                    "last_completed_at": profile.last_completed_at,
                    "total_sessions": profile.total_sessions,
                    "total_words_learned": profile.total_words_learned,
                    "created_at": profile.created_at,
                    "updated_at": profile.updated_at,
                },
                ConditionExpression="attribute_not_exists(PK)",
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return  # idempotent — profile đã tồn tại, Cognito retry
            raise
