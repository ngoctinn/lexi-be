from application.repositories.user_profile_repository import UserProfileRepository
from application.dtos.auth.create_profile.create_profile_command import CreateUserProfileCommand, CreateUserProfileResponse
from domain.entities.user_profile import UserProfile
from domain.value_objects.enums import ProficiencyLevel
from shared.result import Result


class CreateUserProfileUseCase:
    """
    Ca sử dụng: Tạo hồ sơ người dùng mới sau khi xác thực.
    Tuân thủ quy trình chuẩn Chương 5: Request -> Logic -> Save -> Result.
    """
    def __init__(self, repo: UserProfileRepository):
        self._repo = repo

    def execute(self, request: CreateUserProfileCommand) -> Result[CreateUserProfileResponse, str]:
        # 1. Validation & Mapping (DTO -> Entity)
        try:
            current_level = ProficiencyLevel(request.current_level)
            learning_goal = ProficiencyLevel(request.learning_goal)
        except ValueError as e:
            return Result.failure(f"Dữ liệu trình độ không hợp lệ: {str(e)}")

        # 2. Tạo thực thể Domain
        profile = UserProfile(
            user_id=request.user_id,
            email=request.email,
            display_name=request.email.split("@")[0],
            current_level=current_level,
            learning_goal=learning_goal
        )

        # 3. Lưu trữ qua Port (Repository)
        try:
            self._repo.create(profile)
        except Exception as e:
            # Lưu ý: Ở đây ta bắt lỗi Infrastructure và trả về lỗi Domain
            return Result.failure(f"Lỗi khi lưu trữ hồ sơ: {str(e)}")

        # 4. Trả về kết quả qua ResponseDTO
        response = CreateUserProfileResponse(
            user_id=profile.user_id,
            email=profile.email,
            is_created=True,
            message="Hồ sơ được tạo thành công"
        )
        return Result.success(response)
