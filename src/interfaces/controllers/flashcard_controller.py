import json
import logging
from typing import Any, Dict

from pydantic import ValidationError

from application.exceptions.vocabulary_errors import VocabularyLookupError
from application.use_cases.flashcard_use_cases import CreateFlashCardUseCase
from interfaces.mapper.flashcard_mapper import FlashCardMapper
from interfaces.presenters.http_presenter import HttpPresenter
from shared.result import Result
from interfaces.view_models.flashcard_vm import FlashcardViewModel
from shared.http_utils import dumps

logger = logging.getLogger(__name__)


class FlashCardController:
    """Điều phối các request liên quan đến flashcard."""

    def __init__(self, create_flashcard_usecase: CreateFlashCardUseCase, presenter: HttpPresenter | None = None) -> None:
        self.create_flashcard_usecase = create_flashcard_usecase
        self.mapper = FlashCardMapper()
        self._presenter = presenter or HttpPresenter()

    def create(self, event: Dict[str, Any], user_id: str) -> Result[FlashcardViewModel, str]:
        """Tạo flashcard mới từ request."""
        try:
            body = json.loads(event.get("body", "{}"))
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in flashcard creation")
            return Result.failure("Invalid JSON format")

        try:
            logger.info("Creating flashcard", extra={"context": {"user_id": user_id}})
            command = self.mapper.to_create_command(body, user_id)
        except ValidationError as e:
            logger.warning("Validation error in flashcard creation", extra={"context": {"error": str(e)}})
            return Result.failure(f"Invalid data: {str(e)}")

        try:
            result = self.create_flashcard_usecase.execute(command)

            if not result.is_success:
                error_msg = str(result.error) if result.error else "Cannot create flashcard"
                logger.warning("Flashcard creation failed", extra={"context": {"user_id": user_id, "error": error_msg}})
                return Result.failure(error_msg)

            # Chuyển đổi Response DTO → View Model
            response = result.value
            view_model = FlashcardViewModel(
                flashcard_id=response.flashcard_id,
                word=response.word,
                meaning=response.translation_vi,
                example=response.example_sentence,
                created_at=response.created_at,
                next_review_at=response.created_at,  # Set to created_at for new cards
            )
            
            logger.info("Flashcard created successfully", extra={"context": {"user_id": user_id, "flashcard_id": response.flashcard_id}})
            return Result.success(view_model)
        except Exception as e:
            logger.exception("Error creating flashcard", extra={"context": {"user_id": user_id, "error": str(e)}})
            raise
