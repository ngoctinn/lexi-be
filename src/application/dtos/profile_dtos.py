from typing import Optional
from application.dtos.base_dto import BaseDTO


class GetProfileResponse(BaseDTO):
    """DTO đầu ra cho GetProfileUseCase."""
    user_id: str
    email: str
    display_name: str
    avatar_url: str = ""
    current_level: str
    target_level: str
    current_streak: int
    total_words_learned: int
    role: str
    is_active: bool
    is_new_user: bool = True


class UpdateProfileCommand(BaseDTO):
    """DTO đầu vào (Command) cho UpdateProfileUseCase."""
    user_id: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    current_level: Optional[str] = None
    target_level: Optional[str] = None
    is_new_user: Optional[bool] = None


class UpdateProfileResponse(BaseDTO):
    """DTO đầu ra cho UpdateProfileUseCase."""
    is_success: bool
    message: str
    user_id: str
    email: str
    display_name: str
    avatar_url: str = ""
    current_level: str
    target_level: str
    current_streak: int = 0
    total_words_learned: int = 0
    role: str = "LEARNER"
    is_active: bool = True
    is_new_user: bool = True
