import json
from typing import Dict, Any
from pydantic import ValidationError

from interfaces.mapper.profile_mapper import ProfileMapper
from application.use_cases.profile.get_profile import GetProfileUseCase
from application.use_cases.profile.update_profile import UpdateProfileUseCase
from shared.http_utils import dumps

class ProfileController:
    """
    Điều phối logic cho các yêu cầu liên quan đến Hồ sơ người dùng (Profile).
    
    Trách nhiệm:
    - Tiếp nhận yêu cầu từ Lambda Handler.
    - Chuyển đổi dữ liệu thô sang DTO thông qua Mapper.
    - Gọi Use Case tương ứng.
    - Định dạng kết quả trả về cho Client (Presenter logic).
    """
    def __init__(self, get_use_case: GetProfileUseCase, update_use_case: UpdateProfileUseCase):
        self._get_use_case = get_use_case
        self._update_use_case = update_use_case

    def _response(self, status: int, body: Dict[str, Any]) -> Dict[str, Any]:
        """Đóng gói logic định dạng phản hồi HTTP."""
        return {
            "statusCode": status, 
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            }, 
            "body": dumps(body)
        }

    def get_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Xử lý yêu cầu lấy thông tin hồ sơ.
        """
        result = self._get_use_case.execute(user_id)
        if not result.is_success:
            return self._response(404, {"error": result.error})
        
        # Pydantic v2 dùng model_dump(), v1 dùng dict()
        return self._response(200, result.value.model_dump())

    def update_profile(self, user_id: str, body_str: str) -> Dict[str, Any]:
        """
        Xử lý yêu cầu cập nhật thông tin hồ sơ.
        """
        try:
            body = json.loads(body_str or "{}")
        except json.JSONDecodeError:
            return self._response(400, {"error": "Định dạng JSON không hợp lệ."})

        try:
            # 1. Map dữ liệu thô sang Command DTO
            command = ProfileMapper.to_update_command(user_id, body)
            
            # 2. Thực thi nghiệp vụ
            result = self._update_use_case.execute(command)
            
            if not result.is_success:
                return self._response(422, {"error": result.error})

            return self._response(200, result.value.model_dump())
            
        except ValidationError as e:
            # Xử lý lỗi validation từ Pydantic
            return self._response(400, {
                "error": "Dữ liệu yêu cầu không hợp lệ.",
                "details": e.errors()
            })
        except Exception as e:
            return self._response(500, {"error": f"Lỗi hệ thống: {str(e)}"})
