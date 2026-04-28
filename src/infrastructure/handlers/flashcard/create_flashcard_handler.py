"""
Lambda handler for POST /flashcards (create flashcard).
"""
import logging
from typing import Any

from application.use_cases.flashcard_use_cases import CreateFlashCardUseCase
from infrastructure.repository_factory import RepositoryFactory
from infrastructure.logging.config import configure_logging
from infrastructure.handlers.base_handler import BaseHandler
from interfaces.controllers.flashcard_controller import FlashCardController

# Configure logging
configure_logging("lambda")
logger = logging.getLogger(__name__)


class CreateFlashcardHandler(BaseHandler[FlashCardController]):
    """Handler for creating a flashcard."""

    def build_dependencies(self) -> FlashCardController:
        """Build flashcard controller with dependencies."""
        flashcard_repo = RepositoryFactory.create_flashcard_repository()
        create_flashcard_uc = CreateFlashCardUseCase(flashcard_repo)
        return FlashCardController(create_flashcard_uc)

    def handle(self, user_id: str, event: dict, context: Any) -> dict:
        """Handle flashcard creation."""
        controller = self.get_dependencies()
        result = controller.create(event, user_id)
        
        if result.is_success:
            return self.presenter.present_created(result.value)
        else:
            return self.presenter._format_response(400, {
                "error": result.error
            })


# Module-level handler instance (singleton)
_handler = CreateFlashcardHandler()


def handler(event, context):
    """Lambda handler entry point."""
    return _handler(event, context)
