import json
import logging

from application.use_cases.flashcard_use_cases import CreateFlashCardUseCase
from infrastructure.repository_factory import RepositoryFactory
from infrastructure.logging.config import configure_logging
from interfaces.controllers.flashcard_controller import FlashCardController
from interfaces.presenters.http_presenter import HttpPresenter
from shared.http_utils import dumps

# Configure logging
configure_logging("lambda")
logger = logging.getLogger(__name__)

# Module-level singleton (AWS best practice)
# Initialized once per Lambda container, reused across invocations
_flashcard_controller = None


def build_flashcard_controller() -> FlashCardController:
    """Build flashcard controller with dependencies."""
    flashcard_repo = RepositoryFactory.create_flashcard_repository()
    create_flashcard_uc = CreateFlashCardUseCase(flashcard_repo)
    return FlashCardController(create_flashcard_uc)


def _get_or_build_flashcard_controller() -> FlashCardController:
    """
    Lazy initialization of flashcard controller (singleton pattern).
    
    AWS best practice: Initialize SDK clients and dependencies outside handler
    to take advantage of execution environment reuse.
    
    Returns:
        FlashCardController: Reusable controller instance
    """
    global _flashcard_controller
    if _flashcard_controller is None:
        logger.info("Building flashcard controller (first invocation in this container)")
        _flashcard_controller = build_flashcard_controller()
    return _flashcard_controller


def _unauthorized_response():
    return {
        "statusCode": 401,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": dumps({"error": "Unauthorized"}),
    }


def handler(event, context):
    """Lambda handler for POST /flashcards."""
    try:
        user_id = event.get("requestContext", {}).get("authorizer", {}).get("claims", {}).get("sub")
        if not user_id:
            logger.warning("Unauthorized flashcard creation attempt")
            return _unauthorized_response()
        logger.info("Creating flashcard", extra={"context": {"user_id": user_id}})
    except Exception as e:
        logger.exception("Error extracting user_id", extra={"context": {"error": str(e)}})
        return _unauthorized_response()

    try:
        controller = _get_or_build_flashcard_controller()
        presenter = HttpPresenter()
        
        result = controller.create(event, user_id)
        
        if result.is_success:
            return presenter.present_created(result.value)
        else:
            error = result.error
            return presenter._format_response(400, {
                "error": error.message,
                "code": error.code or "ERROR"
            })
    except Exception as e:
        logger.exception("Error creating flashcard", extra={"context": {"user_id": user_id, "error": str(e)}})
        raise
