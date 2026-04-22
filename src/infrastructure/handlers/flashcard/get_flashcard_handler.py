import json
import logging

from application.repositories.flash_card_repository import FlashCardRepository
from application.use_cases.flashcard.get_flashcard_detail_uc import GetFlashcardDetailUC
from infrastructure.persistence.dynamo_flashcard_repo import DynamoFlashCardRepository


# Khởi tạo dependencies
flashcard_repo: FlashCardRepository = DynamoFlashCardRepository()
get_flashcard_detail_uc = GetFlashcardDetailUC(flashcard_repo)

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """
    Lambda handler cho endpoint GET /flashcards/{flashcard_id}.
    
    Lấy thông tin chi tiết của một flashcard.
    """
    # Lấy user_id từ authorizer context
    try:
        user_id = event.get("requestContext", {}).get("authorizer", {}).get("claims", {}).get("sub")
        if not user_id:
            return {
                "statusCode": 401,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"error": "Unauthorized"}),
            }
    except Exception:
        return {
            "statusCode": 401,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": "Unauthorized"}),
        }

    # Lấy flashcard_id từ path parameters
    try:
        flashcard_id = event.get("pathParameters", {}).get("flashcard_id")
        if not flashcard_id:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"error": "Missing flashcard_id"}),
            }
    except Exception:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": "Invalid path parameters"}),
        }

    logger.info(f"Getting flashcard detail - flashcard_id: {flashcard_id}, user_id: {user_id}")

    try:
        # Gọi use case
        card = get_flashcard_detail_uc.execute(user_id, flashcard_id)
        
        # Trả về thông tin đầy đủ
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({
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
                "last_reviewed_at": card.last_reviewed_at.isoformat() if card.last_reviewed_at else None,
                "next_review_at": card.next_review_at.isoformat(),
                "source_session_id": card.source_session_id,
                "source_turn_index": card.source_turn_index,
            }),
        }
    
    except PermissionError:
        logger.error(f"Permission denied for flashcard_id: {flashcard_id}, user_id: {user_id}")
        return {
            "statusCode": 403,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": "Forbidden"}),
        }
    
    except KeyError:
        logger.error(f"Flashcard not found: {flashcard_id}")
        return {
            "statusCode": 404,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": "Flashcard not found"}),
        }
    
    except Exception as e:
        logger.error(f"Error getting flashcard detail: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": "Internal server error"}),
        }
