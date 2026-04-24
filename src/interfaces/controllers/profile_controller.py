import json
import logging
from typing import Dict, Any
from pydantic import ValidationError

from interfaces.mapper.profile_mapper import ProfileMapper
from interfaces.presenters.http_presenter import HttpPresenter
from interfaces.view_models.base import OperationResult
from interfaces.view_models.user_vm import UserProfileViewModel
from application.use_cases.user_profile_use_cases import GetProfileUseCase, UpdateProfileUseCase
from shared.http_utils import dumps

logger = logging.getLogger(__name__)


class ProfileController:
    """
    Điều phối logic cho các yêu cầu liên quan đến Hồ sơ người dùng (Profile).
    
    Trách nhiệm:
    - Tiếp nhận yêu cầu từ Lambda Handler.
    - Chuyển đổi dữ liệu thô sang DTO thông qua Mapper.
    - Gọi Use Case tương ứng.
    - Chuyển đổi Response DTO sang View Model.
    - Trả về OperationResult[ViewModel].
    """
    def __init__(self, get_use_case: GetProfileUseCase, update_use_case: UpdateProfileUseCase, presenter: HttpPresenter | None = None):
        self._get_use_case = get_use_case
        self._update_use_case = update_use_case
        self._presenter = presenter or HttpPresenter()

    def get_profile(self, user_id: str) -> OperationResult[UserProfileViewModel]:
        """
        Xử lý yêu cầu lấy thông tin hồ sơ.
        """
        try:
            logger.info("Getting profile", extra={"context": {"user_id": user_id}})
            result = self._get_use_case.execute(user_id)
            
            if not result.is_success:
                logger.warning("Profile not found", extra={"context": {"user_id": user_id}})
                return OperationResult.fail("Profile not found", "NOT_FOUND")
            
            # Chuyển đổi Response DTO → View Model
            response = result.value
            view_model = UserProfileViewModel(
                user_id=response.user_id,
                email=response.email,
                display_name=response.display_name,
                avatar_url=response.avatar_url,
                current_level=response.current_level,
                target_level=response.target_level,
                current_streak=response.current_streak,
                total_words_learned=response.total_words_learned,
                role=response.role,
                is_active=response.is_active,
                is_new_user=response.is_new_user,
            )
            
            logger.info("Profile retrieved successfully", extra={"context": {"user_id": user_id}})
            return OperationResult.succeed(view_model)
            
        except Exception as e:
            logger.exception("Error getting profile", extra={"context": {"user_id": user_id, "error": str(e)}})
            raise

    def update_profile(self, user_id: str, body_str: str) -> OperationResult[UserProfileViewModel]:
        """
        Xử lý yêu cầu cập nhật thông tin hồ sơ.
        """
        try:
            body = json.loads(body_str or "{}")
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in update request")
            return OperationResult.fail("Invalid JSON format", "BAD_REQUEST")

        try:
            logger.info("Updating profile", extra={"context": {"user_id": user_id}})
            # 1. Map dữ liệu thô sang Command DTO
            command = ProfileMapper.to_update_command(user_id, body)
            
            # 2. Thực thi nghiệp vụ
            result = self._update_use_case.execute(command)
            
            if not result.is_success:
                logger.warning("Profile update failed", extra={"context": {"user_id": user_id, "error": result.error}})
                return OperationResult.fail(result.error, "UPDATE_FAILED")

            # 3. Chuyển đổi Response DTO → View Model
            response = result.value
            view_model = UserProfileViewModel(
                user_id=response.user_id,
                email=response.email,
                display_name=response.display_name,
                avatar_url=response.avatar_url,
                current_level=response.current_level,
                target_level=response.target_level,
                current_streak=response.current_streak,
                total_words_learned=response.total_words_learned,
                role=response.role,
                is_active=response.is_active,
                is_new_user=response.is_new_user,
            )
            
            logger.info("Profile updated successfully", extra={"context": {"user_id": user_id}})
            return OperationResult.succeed(view_model)
            
        except ValidationError as e:
            logger.warning("Validation error in update request", extra={"context": {"user_id": user_id, "errors": str(e)}})
            return OperationResult.fail(f"Invalid request data: {str(e)}", "VALIDATION_ERROR")
        except Exception as e:
            logger.exception("Error updating profile", extra={"context": {"user_id": user_id, "error": str(e)}})
            raise
