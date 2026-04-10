from application.dtos.base_dto import BaseDTO

class GetProfileResponse(BaseDTO):
    """DTO đầu ra cho GetProfileUseCase."""
    user_id: str
    email: str
    display_name: str
    current_level: str
    learning_goal: str
    current_streak: int
    total_words_learned: int
    role: str
    is_active: bool

