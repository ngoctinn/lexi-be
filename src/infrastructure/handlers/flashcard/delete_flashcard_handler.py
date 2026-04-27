import json
from shared.http_utils import dumps
import logging

from application.repositories.flash_card_repository import FlashCardRepository
from application.use_cases.flashcard_use_cases import DeleteFlashcardUseCase
from infrastructure.persistence.dynamo_flashcard_repo import DynamoFlashCardRepository

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Module-level singleton (AWS best practice)
_delete_flashcard_uc = None


def build_delete_flashcard_uc():
    """Build delete flashcard use case with dependencies."""
    flashcard_repo: FlashCardRepository = DynamoFlashCardRepository()
    return DeleteFlashcardUseCase(flashcard_repo)


def _get_or_build_delete_flashcard_uc():
    """
    Lazy initialization of delete flashcard use case (singleton pattern).
    
    AWS best practice: Initialize SDK clients and dependencies outside handler
    to take advantage of execution environment reuse.
    
    Returns:
        DeleteFlashcardUseCase: Reusable use case instance
    """
    global _delete_flashcard_uc
    if _delete_flashcard_uc is None:
        logger.info("Building delete flashcard use case (first invocation in this container)")
        _delete_flashcard_uc = build_delete_flashcard_uc()
    return _delete_flashcard_uc


def _unauthorized_response():
    return {
        "statusCode": 401,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": dumps({"error": "Unauthorized"}),
    }


def handler(event, context):
    """Lambda handler for DELETE /flashcards/{flashcard_id}."""
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

    logger.info(f"Deleting flashcard_id: {flashcard_id}, user_id: {user_id}")

    try:
        uc = _get_or_build_delete_flashcard_uc()
        success = uc.execute(user_id, flashcard_id)
        
        if success:
            logger.info(f"Delete successful - flashcard_id: {flashcard_id}")
            return {
                "statusCode": 204,
                "headers": {"Access-Control-Allow-Origin": "*"},
            }
        else:
            logger.error(f"Delete failed - flashcard_id: {flashcard_id}")
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": dumps({"error": "Failed to delete flashcard"}),
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
        logger.error(f"Error deleting flashcard: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": dumps({"error": "Internal server error"}),
        }
