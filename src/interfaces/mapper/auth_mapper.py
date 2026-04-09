from typing import Dict, Any
from application.dtos.auth.create_profile.create_profile_command import CreateUserProfileCommand

class AuthMapper:
    """Phiên dịch dữ liệu đầu vào từ AWS Cognito Event sang Command DTO của Application."""
    @staticmethod
    def to_create_command(event: Dict[str, Any]) -> CreateUserProfileCommand:
        user_attrs = event.get('request', {}).get('userAttributes', {})
        return CreateUserProfileCommand(
            user_id=event.get('userName', ''),
            email=user_attrs.get('email', ''),
            current_level=user_attrs.get('custom:current_level', 'A1'),
            learning_goal=user_attrs.get('custom:learning_goal', 'B2')
        )
