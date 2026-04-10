from application.repositories.user_profile_repository import UserProfileRepository
from application.dtos.profile.update.update_profile_command import UpdateProfileCommand, UpdateProfileResponse
from shared.result import Result
from domain.value_objects.enums import ProficiencyLevel

class UpdateProfileUseCase:
    """Ca sử dụng: Cập nhật thông tin hồ sơ."""
    def __init__(self, repo: UserProfileRepository):
        self._repo = repo

    def execute(self, request: UpdateProfileCommand) -> Result[UpdateProfileResponse, str]:
        # 1. Lấy profile hiện tại
        profile = self._repo.get_by_user_id(request.user_id)
        if not profile:
            return Result.failure("Hồ sơ không tồn tại.")

        # 2. Xử lý validation kiểu dữ liệu trước khi đẩy vào Domain
        new_level = None
        new_goal = None
        
        try:
            if request.current_level:
                new_level = ProficiencyLevel(request.current_level)
            if request.learning_goal:
                new_goal = ProficiencyLevel(request.learning_goal)
        except ValueError as e:
            return Result.failure(f"Dữ liệu trình độ không hợp lệ.")

        # 3. Giao tiếp với Entity (Domain Logic nằm ở Entity)
        profile.update_profile_info(
            display_name=request.display_name,
            current_level=new_level,
            learning_goal=new_goal
        )

        # 4. Lưu lại
        try:
            self._repo.update(profile)
            return Result.success(UpdateProfileResponse(is_success=True, message="Cập nhật thành công"))
        except Exception as e:
            return Result.failure(f"Lỗi khi cập nhật DB: {str(e)}")
