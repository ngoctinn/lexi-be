from pydantic import Field, EmailStr
from application.dtos.base_dto import BaseDTO


class CreateUserProfileCommand(BaseDTO):
    """DTO đầu vào (Command) từ UI/Cognito."""
    user_id: str = Field(min_length=1)
    email: EmailStr
    display_name: str = ""
    avatar_url: str = ""
    current_level: str = "A1"
    target_level: str = "B2"


class CreateUserProfileResponse(BaseDTO):
    """DTO đầu ra trả về cho Client."""
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
    is_created: bool = True
    message: str = "Profile created successfully"
