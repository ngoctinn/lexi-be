from typing import Optional
from application.repositories.user_profile_repository import UserProfileRepository
from domain.value_objects.enums import ProficiencyLevel
from shared.result import Result


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
