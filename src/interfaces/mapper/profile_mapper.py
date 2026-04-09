from typing import Dict, Any
from application.dtos.profile.update.update_profile_command import UpdateProfileCommand

class ProfileMapper:
    """Phiên dịch dữ liệu đầu vào (HTTP Body) sang Command DTO cho profile."""
    @staticmethod
    def to_update_command(user_id: str, body: Dict[str, Any]) -> UpdateProfileCommand:
        return UpdateProfileCommand(
            user_id=user_id,
            display_name=body.get("display_name"),
            current_level=body.get("current_level"),
            learning_goal=body.get("learning_goal")
        )
