from dataclasses import dataclass

@dataclass(frozen=True)
class UpdateProfileCommand:
    """DTO đầu vào (Command) cho UpdateProfileUseCase."""
    user_id: str
    display_name: str = None
    current_level: str = None
    learning_goal: str = None

@dataclass(frozen=True)
class UpdateProfileResponse:
    """DTO đầu ra cho UpdateProfileUseCase."""
    is_success: bool
    message: str
