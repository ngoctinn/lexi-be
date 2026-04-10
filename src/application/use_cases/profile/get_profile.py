from application.repositories.user_profile_repository import UserProfileRepository
from application.dtos.profile.get.get_profile_response import GetProfileResponse
from shared.result import Result

class GetProfileUseCase:
    """
    Ca sử dụng: Lấy thông tin hồ sơ người dùng.
    
    Quy trình:
    1. Truy vấn Repository theo User ID.
    2. Nếu không thấy, trả về lỗi.
    3. Nếu thấy, map Entity sang Response DTO.
    """
    def __init__(self, repo: UserProfileRepository):
        self._repo = repo

    def execute(self, user_id: str) -> Result[GetProfileResponse, str]:
        """
        Thực thi trình tự lấy hồ sơ.
        """
        profile = self._repo.get_by_user_id(user_id)
        if not profile:
            return Result.failure("Không tìm thấy hồ sơ người dùng.")
        
        response = GetProfileResponse(
            user_id=profile.user_id,
            email=profile.email,
            display_name=profile.display_name,
            current_level=profile.current_level.value if hasattr(profile.current_level, 'value') else profile.current_level,
            learning_goal=profile.learning_goal.value if hasattr(profile.learning_goal, 'value') else profile.learning_goal,
            current_streak=profile.current_streak,
            total_words_learned=profile.total_words_learned,
            role=profile.role.value if hasattr(profile.role, 'value') else profile.role,
            is_active=profile.is_active
        )
        return Result.success(response)
