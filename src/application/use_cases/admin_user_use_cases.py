from typing import Optional
from application.repositories.user_profile_repository import UserProfileRepository
from domain.value_objects.enums import ProficiencyLevel, Role
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


class UpdateAdminUserUseCase:
    """Cập nhật thông tin quản trị của user — chỉ is_active, current_level, target_level."""

    def __init__(self, repo: UserProfileRepository):
        self._repo = repo

    def execute(
        self,
        target_user_id: str,
        is_active: Optional[bool] = None,
        current_level: Optional[str] = None,
        target_level: Optional[str] = None,
    ) -> Result:
        profile = self._repo.get_by_user_id(target_user_id)
        if not profile:
            return Result.failure("Người dùng không tồn tại.")

        # Validate và convert levels nếu có
        if current_level is not None:
            try:
                profile.current_level = ProficiencyLevel(current_level)
            except ValueError:
                return Result.failure(f"Trình độ '{current_level}' không hợp lệ. Chỉ chấp nhận: A1, A2, B1, B2, C1, C2")

        if target_level is not None:
            try:
                profile.target_level = ProficiencyLevel(target_level)
            except ValueError:
                return Result.failure(f"Trình độ '{target_level}' không hợp lệ. Chỉ chấp nhận: A1, A2, B1, B2, C1, C2")

        if is_active is not None:
            profile.is_active = is_active

        self._repo.update(profile)

        return Result.success({
            "user_id": profile.user_id,
            "email": profile.email,
            "display_name": profile.display_name,
            "avatar_url": profile.avatar_url,
            "current_level": profile.current_level.value,
            "target_level": profile.target_level.value,
            "is_active": profile.is_active,
            "is_new_user": profile.is_new_user,
            "current_streak": profile.current_streak,
            "total_words_learned": profile.total_words_learned,
        })
