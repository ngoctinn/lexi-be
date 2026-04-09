import json
import dataclasses
from typing import Dict, Any
from interfaces.mapper.profile_mapper import ProfileMapper
from application.use_cases.profile.get_profile import GetProfileUseCase
from application.use_cases.profile.update_profile import UpdateProfileUseCase

class ProfileController:
    """Điều phối logic, xử lý HTTP request và định dạng response (Presenter)."""
    def __init__(self, get_use_case: GetProfileUseCase, update_use_case: UpdateProfileUseCase):
        self._get_use_case = get_use_case
        self._update_use_case = update_use_case

    def _response(self, status: int, body: Dict[str, Any]) -> Dict[str, Any]:
        """Đóng gói Presenter logic đơn giản cho HTTP response."""
        return {
            "statusCode": status, 
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            }, 
            "body": json.dumps(body)
        }

    def get_profile(self, user_id: str) -> Dict[str, Any]:
        result = self._get_use_case.execute(user_id)
        if not result.is_success:
            return self._response(404, {"error": result.error})
        return self._response(200, dataclasses.asdict(result.value))

    def update_profile(self, user_id: str, body_str: str) -> Dict[str, Any]:
        try:
            body = json.loads(body_str or "{}")
        except json.JSONDecodeError:
            return self._response(400, {"error": "Invalid JSON body"})

        command = ProfileMapper.to_update_command(user_id, body)
        result = self._update_use_case.execute(command)
        
        if not result.is_success:
            return self._response(400, {"error": result.error})

        return self._response(200, dataclasses.asdict(result.value))
