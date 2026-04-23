import json
from shared.http_utils import dumps
import logging

from application.repositories.flash_card_repository import FlashCardRepository
from application.use_cases.flashcard.list_due_cards_uc import ListDueCardsUC
from infrastructure.persistence.dynamo_flashcard_repo import DynamoFlashCardRepository


# Khởi tạo dependencies
flashcard_repo: FlashCardRepository = DynamoFlashCardRepository()
list_due_cards_uc = ListDueCardsUC(flashcard_repo)

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """
    Lambda handler cho endpoint GET /flashcards/due.
    
    Lấy danh sách flashcard đến hạn ôn tập.
    """
    # Lấy user_id từ authorizer context
    try:
        user_id = event.get("requestContext", {}).get("authorizer", {}).get("claims", {}).get("sub")
        if not user_id:
            return {
                "statusCode": 401,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": dumps({"error": "Unauthorized"}),
            }
    except Exception:
        return {
            "statusCode": 401,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": dumps({"error": "Unauthorized"}),
        }

    logger.info(f"Listing due cards for user_id: {user_id}")

    try:
        # Gọi use case
        cards = list_due_cards_uc.execute(user_id)
        
        # Chuyển đổi sang JSON response
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
