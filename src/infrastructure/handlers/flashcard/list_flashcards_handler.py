import json
from functools import lru_cache
from shared.http_utils import dumps
import base64
import logging

from application.repositories.flash_card_repository import FlashCardRepository
from application.use_cases.flashcard.list_user_flashcards_uc import ListUserFlashcardsUC
from infrastructure.persistence.dynamo_flashcard_repo import DynamoFlashCardRepository

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def build_list_flashcards_uc():
    """Build list flashcards use case with dependencies."""
    flashcard_repo: FlashCardRepository = DynamoFlashCardRepository()
    return ListUserFlashcardsUC(flashcard_repo)


@lru_cache(maxsize=1)
def get_list_flashcards_uc():
    """Get cached use case (reuse across invocations)."""
    return build_list_flashcards_uc()


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
        uc = get_list_flashcards_uc()
        cards, next_key = uc.execute(user_id, last_key, limit)
        
        cards_data = [
            {
                "flashcard_id": card.flashcard_id,
                "word": card.word,
                "translation_vi": card.translation_vi,
                "definition_vi": card.definition_vi,
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
            next_key_encoded = base64.b64encode(json.dumps(next_key).encode("utf-8")).decode("utf-8")
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": dumps({
                "cards": cards_data,
                "next_key": next_key_encoded,
            }),
        }
    
    except Exception as e:
        logger.error(f"Error listing flashcards: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": dumps({"error": "Internal server error"}),
        }
