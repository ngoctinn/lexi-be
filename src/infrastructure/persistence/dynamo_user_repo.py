from datetime import datetime, timezone
from typing import Optional
import os
import boto3
from botocore.exceptions import ClientError
from application.repositories.user_profile_repository import UserProfileRepository
from domain.entities.user_profile import UserProfile


class DynamoDBUserRepo(UserProfileRepository):
    def __init__(self, table=None):
        self._table = table or boto3.resource("dynamodb").Table(os.environ["LEXI_TABLE_NAME"])

    def create(self, profile: UserProfile) -> bool:
        """
        Tạo mới bộ hồ sơ người dùng trong DynamoDB.
        
        Args:
            profile: Thực thể UserProfile cần lưu.
            
        Returns:
            bool: True nếu tạo mới thành công, False nếu hồ sơ đã tồn tại.
        """
        try:
            now = datetime.now(timezone.utc).isoformat()
            self._table.put_item(
                Item={
                    "PK": f"USER#{profile.user_id}",
                    "SK": "PROFILE",
                    "GSI1PK": f"USER#{profile.user_id}#USER_PROFILE",
                    "GSI1SK": now,
                    "GSI3PK": "USER_PROFILE",
                    "GSI3SK": now,
                    "EntityType": "USER_PROFILE",
                    "user_id": profile.user_id,
                    "email": profile.email,
                    "display_name": profile.display_name,
                    "avatar_url": profile.avatar_url,
                    "role": profile.role.value if hasattr(profile.role, "value") else profile.role,
                    "is_active": profile.is_active,
                    "is_new_user": profile.is_new_user,
                    "current_level": profile.current_level.value if hasattr(profile.current_level, "value") else profile.current_level,
                    "learning_goal": profile.learning_goal.value if hasattr(profile.learning_goal, "value") else profile.learning_goal,
                    "current_streak": profile.current_streak,
                    "last_completed_at": profile.last_completed_at,
                    "total_words_learned": profile.total_words_learned,
                    "joined_at": now,
                },
                ConditionExpression="attribute_not_exists(PK)",
            )
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return False
            raise

    def get_by_user_id(self, user_id: str) -> Optional[UserProfile]:
        """Lấy thông tin profile người dùng từ DynamoDB."""
        response = self._table.get_item(
            Key={
                "PK": f"USER#{user_id}",
                "SK": "PROFILE"
            }
        )
        item = response.get("Item")
        if not item:
            return None
            
        # Map từ DB sang Entity (Lưu ý: Bạn cần import các Enum tương ứng)
        from domain.value_objects.enums import ProficiencyLevel, Role
        
        return UserProfile(
            user_id=item.get("user_id", user_id),
            email=item.get("email", ""),
            display_name=item.get("display_name", ""),
            avatar_url=item.get("avatar_url", ""),
            current_level=ProficiencyLevel(item.get("current_level", "A1")),
            learning_goal=ProficiencyLevel(item.get("learning_goal", "B2")),
            role=Role(item.get("role", "LEARNER")),
            is_active=item.get("is_active", True),
            is_new_user=item.get("is_new_user", True),
            current_streak=item.get("current_streak", 0),
            last_completed_at=item.get("last_completed_at", ""),
            total_words_learned=item.get("total_words_learned", 0)
        )

    def update(self, profile: UserProfile) -> None:
        """Cập nhật profile hiện có (chỉ các trường thay đổi)."""
        self._table.update_item(
            Key={
                "PK": f"USER#{profile.user_id}",
                "SK": "PROFILE"
            },
            UpdateExpression="SET display_name = :dn, avatar_url = :au, current_level = :cl, learning_goal = :lg, is_new_user = :inu, current_streak = :cs, last_completed_at = :lc, total_words_learned = :tw",
            ExpressionAttributeValues={
                ":dn": profile.display_name,
                ":au": profile.avatar_url,
                ":cl": profile.current_level.value,
                ":lg": profile.learning_goal.value,
                ":inu": profile.is_new_user,
                ":cs": profile.current_streak,
                ":lc": profile.last_completed_at,
                ":tw": profile.total_words_learned
            }
        )
