import json
from shared.http_utils import dumps
import logging

from application.repositories.flash_card_repository import FlashCardRepository
from application.use_cases.flashcard_use_cases import ImportFlashcardsUseCase
from infrastructure.persistence.dynamo_flashcard_repo import DynamoFlashCardRepository

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Module-level singleton (AWS best practice)
_import_flashcards_uc = None


def build_import_flashcards_uc():
    """Build import flashcards use case with dependencies."""
    flashcard_repo: FlashCardRepository = DynamoFlashCardRepository()
    return ImportFlashcardsUseCase(flashcard_repo)


def _get_or_build_import_flashcards_uc():
    """
    Lazy initialization of import flashcards use case (singleton pattern).
    
    AWS best practice: Initialize SDK clients and dependencies outside handler
    to take advantage of execution environment reuse.
    
    Returns:
        ImportFlashcardsUseCase: Reusable use case instance
    """
    global _import_flashcards_uc
    if _import_flashcards_uc is None:
        logger.info("Building import flashcards use case (first invocation in this container)")
        _import_flashcards_uc = build_import_flashcards_uc()
    return _import_flashcards_uc


def _unauthorized_response():
    return {
        "statusCode": 401,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": dumps({"error": "Unauthorized"}),
    }


def handler(event, context):
    """Lambda handler for POST /flashcards/import."""
    try:
        user_id = event.get("requestContext", {}).get("authorizer", {}).get("claims", {}).get("sub")
        if not user_id:
            return _unauthorized_response()
    except Exception:
        return _unauthorized_response()

    try:
        body = json.loads(event.get("body", "{}"))
        flashcards_data = body.get("flashcards", [])
        
        if not isinstance(flashcards_data, list):
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": dumps({"error": "flashcards must be an array"}),
            }
        
        if len(flashcards_data) == 0:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": dumps({"error": "flashcards array cannot be empty"}),
            }
    
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": dumps({"error": "Invalid JSON"}),
        }

    logger.info(f"Importing {len(flashcards_data)} flashcards for user_id: {user_id}")

    try:
        uc = _get_or_build_import_flashcards_uc()
        result = uc.execute(user_id, flashcards_data)
        
        logger.info(f"Import completed - imported: {result['imported']}, skipped: {result['skipped']}, failed: {result['failed']}")
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": dumps({
                "success": True,
                "data": result
            }),
        }
    
    except Exception as e:
        logger.error(f"Error importing flashcards: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": dumps({"error": "Internal server error"}),
        }
