from application.repositories.user_profile_repository import UserProfileRepository
from application.dtos.onboarding.complete_onboarding_command import CompleteOnboardingCommand
from application.dtos.onboarding.complete_onboarding_response import CompleteOnboardingResponse
from application.validators.onboarding_validators import (
    validate_display_name,
    validate_cefr_level,
    validate_avatar_url,
)
from domain.value_objects.enums import ProficiencyLevel
from shared.result import Result


class CompleteOnboardingUseCase:
    """
    Ca sử dụng: Hoàn tất onboarding cho user mới.

    Quy trình:
    1. Lấy profile theo user_id.
    2. Validate từng field.
    3. Cập nhật profile và set is_new_user=False.
    4. Lưu vào DB.
    """

    def __init__(self, repo: UserProfileRepository):
        self._repo = repo

    def execute(self, command: CompleteOnboardingCommand) -> Result[CompleteOnboardingResponse, str]:
        # 1. Lấy profile
        profile = self._repo.get_by_user_id(command.user_id)
        if not profile:
            return Result.failure("Hồ sơ không tồn tại trong hệ thống.")

        # 2. Validate display_name
        ok, err = validate_display_name(command.display_name)
        if not ok:
            return Result.failure(err)

        # 3. Validate current_level
        ok, err = validate_cefr_level(command.current_level, "Trình độ hiện tại")
        if not ok:
            return Result.failure(err)
        current_level = ProficiencyLevel(command.current_level)

        # 4. Validate target_level
        ok, err = validate_cefr_level(command.target_level, "Trình độ mục tiêu")
        if not ok:
            return Result.failure(err)
        target_level = ProficiencyLevel(command.target_level)

        # 5. Validate avatar_url
        ok, err = validate_avatar_url(command.avatar_url)
        if not ok:
            return Result.failure(err)

        # 6. Cập nhật entity
        profile.update_profile_info(
            display_name=command.display_name.strip(),
            avatar_url=command.avatar_url,
            current_level=current_level,
            target_level=target_level,
            is_new_user=False,
        )

        # 7. Lưu vào DB
        try:
            self._repo.update(profile)
        except Exception as e:
            return Result.failure(f"Lỗi khi cập nhật cơ sở dữ liệu: {str(e)}")

        # 8. Trả về response
        profile_dict = {
            "user_id": profile.user_id,
            "display_name": profile.display_name,
            "avatar_url": profile.avatar_url,
            "current_level": profile.current_level.value,
            "target_level": profile.target_level.value,
            "is_new_user": profile.is_new_user,
            "role": profile.role.value,
            "is_active": profile.is_active,
            "current_streak": profile.current_streak,
            "total_words_learned": profile.total_words_learned,
        }
        return Result.success(
            CompleteOnboardingResponse(
                is_success=True,
                message="Onboarding hoàn tất",
                profile=profile_dict,
            )
        )
