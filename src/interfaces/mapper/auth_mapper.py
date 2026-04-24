from typing import Dict, Any
from application.dtos.auth_dtos import CreateUserProfileCommand

class AuthMapper:
    """Phiên dịch dữ liệu đầu vào từ AWS Cognito Event sang Command DTO của Application."""
    @staticmethod
    def to_create_command(event: Dict[str, Any]) -> CreateUserProfileCommand:
        user_attrs = event.get('request', {}).get('userAttributes', {})
        return CreateUserProfileCommand(
            user_id=event.get('userName', ''),
            email=user_attrs.get('email', ''),
            display_name=user_attrs.get('name', ''),
            avatar_url=user_attrs.get('picture', '')
        )
