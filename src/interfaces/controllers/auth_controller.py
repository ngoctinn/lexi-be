from typing import Dict, Any
import logging
from pydantic import ValidationError

from interfaces.mapper.auth_mapper import AuthMapper
from interfaces.presenters.http_presenter import HttpPresenter
from interfaces.view_models.base import OperationResult
from interfaces.view_models.user_vm import UserProfileViewModel
from application.use_cases.user_profile_use_cases import CreateUserProfileUseCase

logger = logging.getLogger(__name__)


class AuthController:
    """
    Controller điều phối luồng xác thực (Auth) và các sự kiện từ hệ thống Identity (Cognito).
    
    Trách nhiệm:
    - Tiếp nhận sự kiện (Event) từ các triggers (vd: Post Confirmation).
    - Phối hợp với Mapper để chuyển đổi sang Command DTO.
    - Thực thi Use Case tạo hồ sơ người dùng.
    - Chuyển đổi Response DTO sang View Model.
    - Trả về OperationResult[ViewModel].
    """
    def __init__(self, use_case: CreateUserProfileUseCase, presenter: HttpPresenter | None = None):
        self._use_case = use_case
        self._presenter = presenter or HttpPresenter()

    def handle_post_confirmation(self, event: Dict[str, Any]) -> OperationResult[UserProfileViewModel]:
        """
        Xử lý sự kiện Cognito Post Confirmation sau khi người dùng xác nhận đăng ký.
        """
        try:
            # 1. Map dữ liệu từ Cognito Event sang Command DTO
            command = AuthMapper.to_create_command(event)
            
            # 2. Thực thi logic lõi (Tạo hồ sơ)
            result = self._use_case.execute(command)
            
            if not result.is_success:
                logger.warning("Failed to create user", extra={"context": {"error": result.error}})
                return OperationResult.fail(result.error, "CREATE_FAILED")
            
            # 3. Chuyển đổi Response DTO → View Model
            response = result.value
            view_model = UserProfileViewModel(
                user_id=response.user_id,
                email=response.email,
                display_name=response.email.split("@")[0],
                avatar_url="",
                current_level="A1",
                target_level="B2",
                current_streak=0,
                total_words_learned=0,
                role="LEARNER",
                is_active=True,
                is_new_user=True,
            )
            
            logger.info("User created successfully", extra={"context": {"user_id": response.user_id}})
            return OperationResult.succeed(view_model)
        
        except ValidationError as e:
            logger.warning("Invalid Cognito data", extra={"context": {"error": str(e)}})
            return OperationResult.fail(f"Invalid data: {str(e)}", "VALIDATION_ERROR")
        except Exception as e:
            logger.exception("System error in AuthController", extra={"context": {"error": str(e)}})
            raise
