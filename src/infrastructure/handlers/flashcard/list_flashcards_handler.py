import json
from shared.http_utils import dumps
import base64
import logging

from application.repositories.flash_card_repository import FlashCardRepository
from application.use_cases.flashcard_use_cases import ListUserFlashcardsUseCase
from infrastructure.persistence.dynamo_flashcard_repo import DynamoFlashCardRepository

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Module-level singleton (AWS best practice)
# Initialized once per Lambda container, reused across invocations
_list_flashcards_uc = None


def build_list_flashcards_uc():
    """Build list flashcards use case with dependencies."""
    flashcard_repo: FlashCardRepository = DynamoFlashCardRepository()
    return ListUserFlashcardsUseCase(flashcard_repo)


def _get_or_build_list_flashcards_uc():
    """
    Lazy initialization of list flashcards use case (singleton pattern).
    
    AWS best practice: Initialize SDK clients and dependencies outside handler
    to take advantage of execution environment reuse.
    
    Returns:
        ListUserFlashcardsUseCase: Reusable use case instance
    """
    global _list_flashcards_uc
    if _list_flashcards_uc is None:
        logger.info("Building list flashcards use case (first invocation in this container)")
        _list_flashcards_uc = build_list_flashcards_uc()
    return _list_flashcards_uc


def _unauthorized_response():
    return {
        "statusCode": 401,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": dumps({"error": "Unauthorized"}),
    }


def handler(event, context):
    """Lambda handler for GET /flashcards."""
    try:
        user_id = event.get("requestContext", {}).get("authorizer", {}).get("claims", {}).get("sub")
        if not user_id:
            return _unauthorized_response()
    except Exception:
        return _unauthorized_response()

    query_params = event.get("queryStringParameters") or {}
    
    try:
        limit = int(query_params.get("limit", "20"))
        limit = min(max(1, limit), 100)
    except ValueError:
        limit = 20
    
    last_key = None
    last_key_str = query_params.get("last_key")
    if last_key_str:
        try:
            last_key = json.loads(base64.b64decode(last_key_str).decode("utf-8"))
        except Exception as e:
            logger.warning(f"Invalid last_key format: {str(e)}")
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": dumps({"error": "Invalid last_key format"}),
            }

    logger.info(f"Listing flashcards for user_id: {user_id}, limit: {limit}")

    try:
        uc = _get_or_build_list_flashcards_uc()
        cards, next_key = uc.execute(user_id, last_key, limit)
        
        cards_data = [
            {
                "flashcard_id": card.flashcard_id,
                "word": card.word,
                "translation_vi": card.translation_vi,
                "phonetic": card.phonetic,
                "audio_url": card.audio_url,
                "example_sentence": card.example_sentence,
                "review_count": card.review_count,
                "interval_days": card.interval_days,
                "difficulty": card.difficulty,
                "next_review_at": card.next_review_at.isoformat(),
                "last_reviewed_at": card.last_reviewed_at.isoformat() if card.last_reviewed_at else None,
            }
            for card in cards
        ]
        
        next_key_encoded = None
        if next_key:
            next_key_encoded = base64.b64encode(dumps(next_key).encode("utf-8")).decode("utf-8")
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": dumps({
                "success": True,
                "data": {
                    "cards": cards_data,
                    "next_key": next_key_encoded,
                }
            }),
        }
    
    except Exception as e:
        logger.error(f"Error listing flashcards: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": dumps({"error": "Internal server error"}),
        }
