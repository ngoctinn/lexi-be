from typing import Dict, Any
from interfaces.mapper.auth_mapper import AuthMapper
from application.use_cases.auth.create_user_profile import CreateUserProfileUseCase

class AuthController:
    """
    Controller điều phối luồng xác thực (Auth).
    Tiếp nhận dữ liệu, gọi Use Case và trả kết quả format chuẩn (hoặc giao tiếp hạ tầng).
    """
    def __init__(self, use_case: CreateUserProfileUseCase):
        self._use_case = use_case

    def handle_post_confirmation(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Xử lý kiện Cognito Post Confirmation."""
        # 1. Map dữ liệu
        command = AuthMapper.to_create_command(event)
        
        # 2. Thực thi logic lõi
        result = self._use_case.execute(command)
        
        # 3. Định dạng kết quả (Presenter logic tích hợp)
        if result.is_success:
            print(f"BÁO CÁO: {result.value.message} - User: {result.value.user_id}")
        else:
            print(f"CẢNH BÁO: {result.error}")
            
        return event  # AWS Cognito yêu cầu trả lại nguyên vẹn event
