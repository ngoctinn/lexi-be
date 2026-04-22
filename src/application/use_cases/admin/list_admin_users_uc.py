from typing import Optional
from application.repositories.user_profile_repository import UserProfileRepository
from domain.value_objects.enums import Role
from shared.result import Result


class ListAdminUsersUseCase:
    """Liệt kê tất cả learner — dùng cho Admin."""

    def __init__(self, repo: UserProfileRepository):
        self._repo = repo

    def execute(self, limit: int = 20, last_key: Optional[dict] = None) -> Result:
        profiles, next_key = self._repo.list_learners(limit=limit, last_key=last_key)

        # Chỉ trả về LEARNER (GSI3 có thể trả về cả ADMIN)
        users = [
            {
                "user_id": p.user_id,
                "email": p.email,
                "display_name": p.display_name,
                "avatar_url": p.avatar_url,
                "current_level": p.current_level.value if hasattr(p.current_level, "value") else p.current_level,
                "target_level": p.target_level.value if hasattr(p.target_level, "value") else p.target_level,
                "is_active": p.is_active,
                "is_new_user": p.is_new_user,
                "current_streak": p.current_streak,
                "total_words_learned": p.total_words_learned,
                "last_completed_at": p.last_completed_at,
            }
            for p in profiles
            if (p.role.value if hasattr(p.role, "value") else p.role) == Role.LEARNER.value
        ]

        return Result.success({"users": users, "next_key": next_key})
