from datetime import datetime, timezone
import os
import boto3
from botocore.exceptions import ClientError
from src.application.repositories.user_profile_repository import UserProfileRepository
from src.domain.entities.user_profile import UserProfile


class DynamoDBUserRepo(UserProfileRepository):
    def __init__(self, table=None):
        self._table = table or boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])

    def create(self, profile: UserProfile) -> None:
        try:
            now = datetime.now(timezone.utc).isoformat()
            self._table.put_item(
                Item={
                    "PK": f"USER#{profile.user_id}",
                    "SK": "PROFILE",
                    "GSI1PK": f"USER#{profile.user_id}#USER_PROFILE",
                    "GSI1SK": now,  # Technical Metadata cho GSI1
                    "GSI3PK": "USER_PROFILE",
                    "GSI3SK": now,  # Technical Metadata cho GSI3 (joined_at)
                    "EntityType": "USER_PROFILE",
                    "user_id": profile.user_id,
                    "email": profile.email,
                    "display_name": profile.display_name,
                    "role": profile.role.value if hasattr(profile.role, "value") else profile.role,
                    "is_active": profile.is_active,
                    "current_level": profile.current_level.value if hasattr(profile.current_level, "value") else profile.current_level,
                    "learning_goal": profile.learning_goal,
                    "current_streak": profile.current_streak,
                    "last_completed_at": profile.last_completed_at,
                    "total_words_learned": profile.total_words_learned,
                    "joined_at": now,  # Chỉ tồn tại dưới DB
                },
                ConditionExpression="attribute_not_exists(PK)",
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return
            raise
