"""
Lambda handler for DELETE /flashcards/{flashcard_id}.
"""
import logging
from typing import Any

from application.use_cases.flashcard_use_cases import DeleteFlashcardUseCase
from infrastructure.persistence.dynamo_flashcard_repo import DynamoFlashCardRepository
from infrastructure.logging.config import configure_logging
from infrastructure.handlers.base_handler import BaseHandler

# Configure logging
configure_logging("lambda")
logger = logging.getLogger(__name__)


class DeleteFlashcardHandler(BaseHandler[DeleteFlashcardUseCase]):
    """Handler for deleting a flashcard."""

    def build_dependencies(self) -> DeleteFlashcardUseCase:
        """Build delete flashcard use case with dependencies."""
        flashcard_repo = DynamoFlashCardRepository()
        return DeleteFlashcardUseCase(flashcard_repo)

    def handle(self, user_id: str, event: dict, context: Any) -> dict:
        """Handle flashcard deletion."""
        flashcard_id = self.extract_path_param(event, "flashcard_id")
        
        logger.info(
            f"Deleting flashcard",
            extra={"context": {"user_id": user_id, "flashcard_id": flashcard_id}}
        )

        uc = self.get_dependencies()
        
        try:
            success = uc.execute(user_id, flashcard_id)
            
            if success:
                logger.info(
                    f"Delete successful",
                    extra={"context": {"flashcard_id": flashcard_id}}
                )
                return {
                    "statusCode": 204,
                    "headers": {"Access-Control-Allow-Origin": "*"},
                }
            else:
                logger.error(
                    f"Delete failed",
                    extra={"context": {"flashcard_id": flashcard_id}}
                )
                return self.presenter._format_response(500, {
                    "error": "Failed to delete flashcard",
                    "code": "DELETE_FAILED"
                })
        
        except PermissionError:
            logger.warning(
                f"Permission denied",
                extra={"context": {"user_id": user_id, "flashcard_id": flashcard_id}}
            )
            return self.presenter._format_response(403, {
                "error": "Forbidden",
                "code": "FORBIDDEN"
            })
        
        except KeyError:
            logger.warning(
                f"Flashcard not found",
                extra={"context": {"flashcard_id": flashcard_id}}
            )
            return self.presenter._format_response(404, {
                "error": "Flashcard not found",
                "code": "NOT_FOUND"
            })


# Module-level handler instance (singleton)
_handler = DeleteFlashcardHandler()


def handler(event, context):
    """Lambda handler entry point."""
    return _handler(event, context)
