from dataclasses import dataclass

@dataclass(frozen=True)
class CreateUserProfileCommand:
    """DTO đầu vào (Command) từ UI/Cognito."""
    user_id: str
    email: str
    current_level: str = "A1"
    learning_goal: str = "B2"

@dataclass(frozen=True)
class CreateUserProfileResponse:
    """DTO đầu ra trả về cho Client."""
    user_id: str
    email: str
    is_created: bool
    message: str
