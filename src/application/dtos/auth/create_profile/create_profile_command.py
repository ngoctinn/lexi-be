from pydantic import Field, EmailStr
from application.dtos.base_dto import BaseDTO

class CreateUserProfileCommand(BaseDTO):
    """DTO đầu vào (Command) từ UI/Cognito."""
    user_id: str = Field(min_length=1)
    email: EmailStr
    current_level: str = "A1"
    learning_goal: str = "B2"

class CreateUserProfileResponse(BaseDTO):
    """DTO đầu ra trả về cho Client."""
    user_id: str
    email: str
    is_created: bool
    message: str

