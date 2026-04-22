import json
import logging

from application.repositories.flash_card_repository import FlashCardRepository
from application.use_cases.flashcard.review_flashcard_uc import ReviewFlashcardUC
from infrastructure.persistence.dynamo_flashcard_repo import DynamoFlashCardRepository


# Khởi tạo dependencies
flashcard_repo: FlashCardRepository = DynamoFlashCardRepository()
review_flashcard_uc = ReviewFlashcardUC(flashcard_repo)

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """
    Lambda handler cho endpoint POST /flashcards/{flashcard_id}/review.
    
    Đánh giá mức độ nhớ flashcard và cập nhật lịch ôn tập.
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

    # Parse request body
    try:
        body = json.loads(event.get("body", "{}"))
        rating = body.get("rating")
        if not rating:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"error": "Missing rating"}),
            }
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": "Invalid JSON"}),
        }

    logger.info(f"Reviewing flashcard_id: {flashcard_id}, rating: {rating}, user_id: {user_id}")

    try:
        # Capture old_interval trước khi review (để log theo Requirement 12.2)
        card_before = flashcard_repo.get_by_user_and_id(user_id, flashcard_id)
        old_interval = card_before.interval_days if card_before else None
        
        # Gọi use case
        card = review_flashcard_uc.execute(user_id, flashcard_id, rating)
        
        logger.info(f"Review successful - flashcard_id: {flashcard_id}, "
                    f"old_interval: {old_interval}, new_interval: {card.interval_days}")
        
        # Trả về thẻ đã cập nhật
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({
                "flashcard_id": card.flashcard_id,
                "word": card.word,
                "interval_days": card.interval_days,
                "review_count": card.review_count,
                "last_reviewed_at": card.last_reviewed_at.isoformat() if card.last_reviewed_at else None,
                "next_review_at": card.next_review_at.isoformat(),
            }),
        }
    
    except ValueError as e:
        logger.error(f"Invalid rating: {str(e)}")
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": "Invalid rating. Must be one of: forgot, hard, good, easy"}),
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
        logger.error(f"Error reviewing flashcard: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": "Internal server error"}),
        }
