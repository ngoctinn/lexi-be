import json
from functools import lru_cache

from application.repositories.flash_card_repository import FlashCardRepository
from application.use_cases.flashcard.create_flashcard_uc import CreateFlashCardUC
from infrastructure.persistence.dynamo_flashcard_repo import DynamoFlashCardRepository
from interfaces.controllers.flashcard_controller import FlashCardController


def build_flashcard_controller() -> FlashCardController:
    """Build flashcard controller with dependencies."""
    flashcard_repo: FlashCardRepository = DynamoFlashCardRepository()
    create_flashcard_uc = CreateFlashCardUC(flashcard_repo)
    return FlashCardController(create_flashcard_uc)


@lru_cache(maxsize=1)
def get_flashcard_controller() -> FlashCardController:
    """Get cached flashcard controller (reuse across invocations)."""
    return build_flashcard_controller()


def _unauthorized_response():
    return {
        "statusCode": 401,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps({"error": "Unauthorized"}),
    }


def handler(event, context):
    """Lambda handler for POST /flashcards."""
    try:
        user_id = event.get("requestContext", {}).get("authorizer", {}).get("claims", {}).get("sub")
        if not user_id:
            return _unauthorized_response()
    except Exception:
        return _unauthorized_response()

    controller = get_flashcard_controller()
    return controller.create(event, user_id)
