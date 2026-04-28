"""
Lambda handler for vocabulary translation API.
"""
import logging
from typing import Any

from application.use_cases.vocabulary_use_cases import TranslateVocabularyUseCase
from infrastructure.service_factory import ServiceFactory
from infrastructure.logging.config import configure_logging
from infrastructure.handlers.base_handler import BaseHandler
from interfaces.controllers.vocabulary_controller import VocabularyController

# Configure logging
configure_logging("lambda")
logger = logging.getLogger(__name__)


class TranslateVocabularyHandler(BaseHandler[VocabularyController]):
    """Handler for vocabulary translation."""

    def build_dependencies(self) -> VocabularyController:
        """Build vocabulary controller with dependencies."""
        translate_service = ServiceFactory.create_translation_service()
        dictionary_service = ServiceFactory.create_dictionary_service()
        translate_vocabulary_uc = TranslateVocabularyUseCase(dictionary_service, translate_service)
        return VocabularyController(translate_vocabulary_uc)

    def handle(self, user_id: str, event: dict, context: Any) -> dict:
        """Handle vocabulary translation."""
        controller = self.get_dependencies()
        body_str = event.get("body")
        result = controller.translate(body_str)
        
        if result.is_success:
            return self.presenter.present_success(result.value)
        else:
            # Map error_code to HTTP status codes
            error_code = result.error or "ERROR"
            
            if error_code == "WORD_NOT_FOUND":
                return self.presenter._format_response(404, {
                    "success": False,
                    "message": error_code,
                    "error": error_code
                })
            elif error_code == "DICTIONARY_SERVICE_ERROR":
                return self.presenter._format_response(503, {
                    "success": False,
                    "message": error_code,
                    "error": error_code
                })
            else:
                # Default to 400 for validation errors and other client errors
                return self.presenter._format_response(400, {
                    "success": False,
                    "message": error_code,
                    "error": error_code
                })


# Module-level handler instance (singleton)
_handler = TranslateVocabularyHandler()


def handler(event, context):
    """Lambda handler entry point."""
    return _handler(event, context)
