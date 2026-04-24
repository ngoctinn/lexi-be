"""User Profile Use Cases - Consolidated from auth and profile modules."""

from application.repositories.user_profile_repository import UserProfileRepository
from application.dtos.auth_dtos import CreateUserProfileCommand, CreateUserProfileResponse
from application.dtos.profile_dtos import GetProfileResponse, UpdateProfileCommand, UpdateProfileResponse
from domain.entities.user_profile import UserProfile
from domain.value_objects.enums import ProficiencyLevel
from shared.result import Result


def _enum_to_str(value: object) -> str:
    """Helper function to convert enum to string value."""
    return value.value if hasattr(value, 'value') else str(value)

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
            display_name=profile.display_name,
            avatar_url=profile.avatar_url,
            current_level=_enum_to_str(profile.current_level),
            target_level=_enum_to_str(profile.target_level),
            current_streak=profile.current_streak,
            total_words_learned=profile.total_words_learned,
            role=_enum_to_str(profile.role),
            is_active=profile.is_active,
            is_new_user=profile.is_new_user,
        )
        return Result.success(response)


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
            avatar_url=profile.avatar_url,
            current_level=_enum_to_str(profile.current_level),
            target_level=_enum_to_str(profile.target_level),
            current_streak=profile.current_streak,
            total_words_learned=profile.total_words_learned,
            role=_enum_to_str(profile.role),
            is_active=profile.is_active,
            is_new_user=profile.is_new_user
        )
        return Result.success(response)


class UpdateProfileUseCase:
    """
    Ca sử dụng: Cập nhật thông tin hồ sơ người dùng.
    
    Quy trình:
    1. Kiểm tra tồn tại của hồ sơ.
    2. Chuyển đổi và validate dữ liệu trình độ (Domain Enums).
    3. Cập nhật thông tin qua thực thể Domain (Fat Entity).
    4. Lưu trữ thay đổi qua Repository.
    """
    def __init__(self, repo: UserProfileRepository):
        self._repo = repo

    def execute(self, request: UpdateProfileCommand) -> Result[UpdateProfileResponse, str]:
        """
        Thực thi trình tự cập nhật hồ sơ.
        """
        # 1. Lấy profile hiện tại
        profile = self._repo.get_by_user_id(request.user_id)
        if not profile:
            return Result.failure("Hồ sơ không tồn tại trong hệ thống.")

        # 2. Xử lý validation kiểu dữ liệu trước khi đẩy vào Domain
        new_level = None
        new_target_level = None
        
        try:
            if request.current_level:
                new_level = ProficiencyLevel(request.current_level)
            if request.target_level:
                new_target_level = ProficiencyLevel(request.target_level)
        except ValueError:
            return Result.failure(f"Dữ liệu trình độ không hợp lệ.")

        # 3. Giao tiếp với Entity (Domain Logic nằm ở Entity)
        profile.update_profile_info(
            display_name=request.display_name,
            avatar_url=request.avatar_url,
            current_level=new_level,
            target_level=new_target_level,
            is_new_user=request.is_new_user
        )

        # 4. Lưu lại
        try:
            self._repo.update(profile)
            response = UpdateProfileResponse(
                is_success=True,
                message="Cập nhật thành công",
                user_id=profile.user_id,
                email=profile.email,
                display_name=profile.display_name,
                avatar_url=profile.avatar_url,
                current_level=_enum_to_str(profile.current_level),
                target_level=_enum_to_str(profile.target_level),
                current_streak=profile.current_streak,
                total_words_learned=profile.total_words_learned,
                role=_enum_to_str(profile.role),
                is_active=profile.is_active,
                is_new_user=profile.is_new_user,
            )
            return Result.success(response)
        except Exception as e:
            return Result.failure(f"Lỗi khi cập nhật cơ sở dữ liệu: {str(e)}")
