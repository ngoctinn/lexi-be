import json
from shared.http_utils import dumps
import logging

from application.repositories.flash_card_repository import FlashCardRepository
from application.use_cases.flashcard_use_cases import ReviewFlashcardUseCase
from infrastructure.persistence.dynamo_flashcard_repo import DynamoFlashCardRepository

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Module-level singleton (AWS best practice)
# Initialized once per Lambda container, reused across invocations
_review_flashcard_uc = None


def build_review_flashcard_uc():
    """Build review flashcard use case with dependencies."""
    flashcard_repo: FlashCardRepository = DynamoFlashCardRepository()
    return ReviewFlashcardUseCase(flashcard_repo)


def _get_or_build_review_flashcard_uc():
    """
    Lazy initialization of review flashcard use case (singleton pattern).
    
    AWS best practice: Initialize SDK clients and dependencies outside handler
    to take advantage of execution environment reuse.
    
    Returns:
        ReviewFlashcardUseCase: Reusable use case instance
    """
    global _review_flashcard_uc
    if _review_flashcard_uc is None:
        logger.info("Building review flashcard use case (first invocation in this container)")
        _review_flashcard_uc = build_review_flashcard_uc()
    return _review_flashcard_uc


def _unauthorized_response():
    return {
        "statusCode": 401,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": dumps({"error": "Unauthorized"}),
    }


def handler(event, context):
    """Lambda handler for POST /flashcards/{flashcard_id}/review."""
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
        rating = body.get("rating")
        if not rating:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": dumps({"error": "Missing rating"}),
            }
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": dumps({"error": "Invalid JSON"}),
        }

    logger.info(f"Reviewing flashcard_id: {flashcard_id}, rating: {rating}, user_id: {user_id}")

    try:
        uc = _get_or_build_review_flashcard_uc()
        card = uc.execute(user_id, flashcard_id, rating)
        
        logger.info(f"Review successful - flashcard_id: {flashcard_id}, interval: {card.interval_days}")
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": dumps({
                "success": True,
                "data": {
                    "flashcard_id": card.flashcard_id,
                    "word": card.word,
                    "interval_days": card.interval_days,
                    "review_count": card.review_count,
                    "last_reviewed_at": card.last_reviewed_at.isoformat() if card.last_reviewed_at else None,
                    "next_review_at": card.next_review_at.isoformat(),
                }
            }),
        }
    
    except ValueError as e:
        logger.error(f"Invalid rating: {str(e)}")
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": dumps({"error": "Invalid rating. Must be one of: forgot, hard, good, easy"}),
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
        logger.error(f"Error reviewing flashcard: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": dumps({"error": "Internal server error"}),
        }
