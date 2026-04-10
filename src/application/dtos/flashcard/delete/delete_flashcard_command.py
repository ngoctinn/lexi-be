from pydantic import Field

from application.dtos.base_dto import BaseDTO

class DeleteFlashCardCommand(BaseDTO):
    flashcard_id: str