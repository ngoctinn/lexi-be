import json
from shared.http_utils import dumps
import logging

from application.repositories.flash_card_repository import FlashCardRepository
from application.use_cases.flashcard_use_cases import UpdateFlashcardUseCase
from infrastructure.persistence.dynamo_flashcard_repo import DynamoFlashCardRepository

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Module-level singleton (AWS best practice)
_update_flashcard_uc = None


def build_update_flashcard_uc():
    """Build update flashcard use case with dependencies."""
    flashcard_repo: FlashCardRepository = DynamoFlashCardRepository()
    return UpdateFlashcardUseCase(flashcard_repo)


def _get_or_build_update_flashcard_uc():
    """
    Lazy initialization of update flashcard use case (singleton pattern).
    
    AWS best practice: Initialize SDK clients and dependencies outside handler
    to take advantage of execution environment reuse.
    
    Returns:
        UpdateFlashcardUseCase: Reusable use case instance
    """
    global _update_flashcard_uc
    if _update_flashcard_uc is None:
        logger.info("Building update flashcard use case (first invocation in this container)")
        _update_flashcard_uc = build_update_flashcard_uc()
    return _update_flashcard_uc


def _unauthorized_response():
    return {
        "statusCode": 401,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": dumps({"error": "Unauthorized"}),
    }


def handler(event, context):
    """Lambda handler for PATCH /flashcards/{flashcard_id}."""
    try:
        user_id = event.get("requestContext", {}).get("authorizer", {}).get("claims", {}).get("sub")
        if not user_id:
            return _unauthorized_response()
    except Exception:
        return _unauthorized_response()

    try:
        flashcard_id = event.get("pathParameters", {}).get("flashcard_id")
        if not flashcard_id:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": dumps({"error": "Missing flashcard_id"}),
            }
    except Exception:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": dumps({"error": "Invalid path parameters"}),
        }

    try:
        body = json.loads(event.get("body", "{}"))
        translation_vi = body.get("translation_vi")
        phonetic = body.get("phonetic")
        audio_url = body.get("audio_url")
        example_sentence = body.get("example_sentence")
        
        # At least one field must be provided
        if not any([translation_vi, phonetic, audio_url, example_sentence]):
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": dumps({"error": "At least one field must be provided for update"}),
            }
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": dumps({"error": "Invalid JSON"}),
        }

    logger.info(f"Updating flashcard_id: {flashcard_id}, user_id: {user_id}")

    try:
        uc = _get_or_build_update_flashcard_uc()
        card = uc.execute(
            user_id=user_id,
            flashcard_id=flashcard_id,
            translation_vi=translation_vi,
            phonetic=phonetic,
            audio_url=audio_url,
            example_sentence=example_sentence
        )
        
        logger.info(f"Update successful - flashcard_id: {flashcard_id}")
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": dumps({
                "success": True,
                "data": {
                    "flashcard_id": card.flashcard_id,
                    "word": card.word,
                    "translation_vi": card.translation_vi,
                    "phonetic": card.phonetic,
                    "audio_url": card.audio_url,
                    "example_sentence": card.example_sentence,
                    "ease_factor": card.ease_factor,
                    "repetition_count": card.repetition_count,
                    "interval_days": card.interval_days,
                    "next_review_at": card.next_review_at.isoformat(),
                }
            }),
        }
    
    except PermissionError:
        logger.error(f"Permission denied for flashcard_id: {flashcard_id}, user_id: {user_id}")
        return {
            "statusCode": 403,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": dumps({"error": "Forbidden"}),
        }
    
    except KeyError:
        logger.error(f"Flashcard not found: {flashcard_id}")
        return {
            "statusCode": 404,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": dumps({"error": "Flashcard not found"}),
        }
    
    except Exception as e:
        logger.error(f"Error updating flashcard: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": dumps({"error": "Internal server error"}),
        }
