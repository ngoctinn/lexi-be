from application.dtos.base_dto import BaseDTO

class CreateFlashCardResponse(BaseDTO):
    """DTO đầu ra cho CreateFlashCardUC."""
    flashcard_id: str
    word: str
    message: str
