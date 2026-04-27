import json
from shared.http_utils import dumps
import logging

from application.repositories.flash_card_repository import FlashCardRepository
from application.use_cases.flashcard_use_cases import ExportFlashcardsUseCase
from infrastructure.persistence.dynamo_flashcard_repo import DynamoFlashCardRepository

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Module-level singleton (AWS best practice)
_export_flashcards_uc = None


def build_export_flashcards_uc():
    """Build export flashcards use case with dependencies."""
    flashcard_repo: FlashCardRepository = DynamoFlashCardRepository()
    return ExportFlashcardsUseCase(flashcard_repo)


def _get_or_build_export_flashcards_uc():
    """
    Lazy initialization of export flashcards use case (singleton pattern).
    
    AWS best practice: Initialize SDK clients and dependencies outside handler
    to take advantage of execution environment reuse.
    
    Returns:
        ExportFlashcardsUseCase: Reusable use case instance
    """
    global _export_flashcards_uc
    if _export_flashcards_uc is None:
        logger.info("Building export flashcards use case (first invocation in this container)")
        _export_flashcards_uc = build_export_flashcards_uc()
    return _export_flashcards_uc


def _unauthorized_response():
    return {
        "statusCode": 401,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": dumps({"error": "Unauthorized"}),
    }


def handler(event, context):
    """Lambda handler for GET /flashcards/export."""
    try:
        user_id = event.get("requestContext", {}).get("authorizer", {}).get("claims", {}).get("sub")
        if not user_id:
            return _unauthorized_response()
    except Exception:
        return _unauthorized_response()

    try:
        # Parse query parameters
        query_params = event.get("queryStringParameters", {}) or {}
        cursor = query_params.get("cursor")
        limit = int(query_params.get("limit", 1000))
        
        # Validate limit
        if limit > 1000:
            limit = 1000
        if limit < 1:
            limit = 1
    except (ValueError, TypeError):
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": dumps({"error": "Invalid query parameters"}),
        }

    logger.info(f"Exporting flashcards for user_id: {user_id}, limit: {limit}, cursor: {cursor}")

    try:
        uc = _get_or_build_export_flashcards_uc()
        flashcards, next_cursor = uc.execute(user_id, cursor, limit)
        
        logger.info(f"Export successful - exported {len(flashcards)} flashcards")
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": dumps({
                "success": True,
                "data": {
                    "flashcards": flashcards,
                    "next_cursor": next_cursor,
                    "count": len(flashcards),
                }
            }),
        }
    
    except Exception as e:
        logger.error(f"Error exporting flashcards: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": dumps({"error": "Internal server error"}),
        }
