from typing import Dict, Any
import logging
from pydantic import ValidationError
from interfaces.mapper.auth_mapper import AuthMapper
from application.use_cases.user_profile_use_cases import CreateUserProfileUseCase

logger = logging.getLogger(__name__)

class AuthController:
    """
    Controller điều phối luồng xác thực (Auth) và các sự kiện từ hệ thống Identity (Cognito).
    
    Trách nhiệm:
    - Tiếp nhận sự kiện (Event) từ các triggers (vd: Post Confirmation).
    - Phối hợp với Mapper để chuyển đổi sang Command DTO.
    - Thực thi Use Case tạo hồ sơ người dùng.
    """
    def __init__(self, use_case: CreateUserProfileUseCase):
        self._use_case = use_case

    def handle_post_confirmation(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Xử lý sự kiện Cognito Post Confirmation sau khi người dùng xác nhận đăng ký.
        """
        try:
            # 1. Map dữ liệu từ Cognito Event sang Command DTO
            command = AuthMapper.to_create_command(event)
            
            # 2. Thực thi logic lõi (Tạo hồ sơ)
            result = self._use_case.execute(command)
            
            # 3. Ghi log kết quả (Sử dụng cho CloudWatch)
            if result.is_success:
                logger.info("%s - User: %s", result.value.message, result.value.user_id)
            else:
                logger.warning("%s", result.error)
        
        except ValidationError as e:
            logger.warning("Dữ liệu từ Cognito không hợp lệ: %s", str(e))
        except Exception as e:
            logger.exception("Lỗi hệ thống trong AuthController: %s", str(e))
            
        return event  # AWS Cognito yêu cầu trả lại nguyên vẹn event để tiếp tục luồng
