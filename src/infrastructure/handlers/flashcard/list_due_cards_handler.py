import json
from functools import lru_cache
from shared.http_utils import dumps
import logging

from application.repositories.flash_card_repository import FlashCardRepository
from application.use_cases.flashcard.list_due_cards_uc import ListDueCardsUC
from infrastructure.persistence.dynamo_flashcard_repo import DynamoFlashCardRepository

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def build_list_due_cards_uc():
    """Build list due cards use case with dependencies."""
    flashcard_repo: FlashCardRepository = DynamoFlashCardRepository()
    return ListDueCardsUC(flashcard_repo)


@lru_cache(maxsize=1)
def get_list_due_cards_uc():
    """Get cached use case (reuse across invocations)."""
    return build_list_due_cards_uc()


def _unauthorized_response():
    return {
        "statusCode": 401,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": dumps({"error": "Unauthorized"}),
    }


def handler(event, context):
    """Lambda handler for GET /flashcards/due."""
    try:
        user_id = event.get("requestContext", {}).get("authorizer", {}).get("claims", {}).get("sub")
        if not user_id:
            return _unauthorized_response()
    except Exception:
        return _unauthorized_response()

    logger.info(f"Listing due cards for user_id: {user_id}")

    try:
        uc = get_list_due_cards_uc()
        cards = uc.execute(user_id)
        
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
                "next_review_at": card.next_review_at.isoformat(),
                "last_reviewed_at": card.last_reviewed_at.isoformat() if card.last_reviewed_at else None,
            }
            for card in cards
        ]
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": dumps({"cards": cards_data}),
        }
    
    except Exception as e:
        logger.error(f"Error listing due cards: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": dumps({"error": "Internal server error"}),
        }
