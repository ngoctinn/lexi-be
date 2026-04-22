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
        """
        Thực thi trình tự tạo hồ sơ người dùng.
        """
        # 1. Validation & Mapping (DTO -> Entity)
        try:
            current_level = ProficiencyLevel(request.current_level)
            target_level = ProficiencyLevel(request.target_level)
        except ValueError as e:
            return Result.failure(f"Dữ liệu trình độ không hợp lệ: {str(e)}")

        # 2. Tạo thực thể Domain
        profile = UserProfile(
            user_id=request.user_id,
            email=request.email,
            display_name=request.display_name or request.email.split("@")[0],
            avatar_url=request.avatar_url,
            current_level=current_level,
            target_level=target_level
        )

        # 3. Lưu trữ qua Port (Repository)
        try:
            is_new = self._repo.create(profile)
        except Exception as e:
            # Lưu ý: Ở đây ta bắt lỗi Infrastructure và trả về lỗi Domain
            return Result.failure(f"Lỗi khi lưu trữ hồ sơ: {str(e)}")

        # 4. Trả về kết quả qua ResponseDTO
        message = "Hồ sơ được tạo thành công" if is_new else "Hồ sơ đã tồn tại, bỏ qua bước tạo mới."
        
        response = CreateUserProfileResponse(
            user_id=profile.user_id,
            email=profile.email,
            is_created=is_new,
            message=message
        )
        return Result.success(response)
