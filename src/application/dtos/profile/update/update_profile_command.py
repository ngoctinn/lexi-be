from typing import Optional
from application.dtos.base_dto import BaseDTO

class UpdateProfileCommand(BaseDTO):
    """DTO đầu vào (Command) cho UpdateProfileUseCase."""
    user_id: str
    display_name: Optional[str] = None
    current_level: Optional[str] = None
    learning_goal: Optional[str] = None



