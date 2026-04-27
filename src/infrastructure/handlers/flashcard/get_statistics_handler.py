import json
from shared.http_utils import dumps
import logging

from application.repositories.flash_card_repository import FlashCardRepository
from application.use_cases.flashcard_use_cases import GetStatisticsUseCase
from infrastructure.persistence.dynamo_flashcard_repo import DynamoFlashCardRepository

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Module-level singleton (AWS best practice)
_get_statistics_uc = None


def build_get_statistics_uc():
    """Build get statistics use case with dependencies."""
    flashcard_repo: FlashCardRepository = DynamoFlashCardRepository()
    return GetStatisticsUseCase(flashcard_repo)


def _get_or_build_get_statistics_uc():
    """
    Lazy initialization of get statistics use case (singleton pattern).
    
    AWS best practice: Initialize SDK clients and dependencies outside handler
    to take advantage of execution environment reuse.
    
    Returns:
        GetStatisticsUseCase: Reusable use case instance
    """
    global _get_statistics_uc
    if _get_statistics_uc is None:
        logger.info("Building get statistics use case (first invocation in this container)")
        _get_statistics_uc = build_get_statistics_uc()
    return _get_statistics_uc


def _unauthorized_response():
    return {
        "statusCode": 401,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": dumps({"error": "Unauthorized"}),
    }


def handler(event, context):
    """Lambda handler for GET /flashcards/statistics."""
    try:
        user_id = event.get("requestContext", {}).get("authorizer", {}).get("claims", {}).get("sub")
        if not user_id:
            return _unauthorized_response()
    except Exception:
        return _unauthorized_response()

    logger.info(f"Getting statistics for user_id: {user_id}")

    try:
        uc = _get_or_build_get_statistics_uc()
        statistics = uc.execute(user_id)
        
        logger.info(f"Statistics retrieved - total: {statistics['total_count']}, due: {statistics['due_today_count']}")
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": dumps({
                "success": True,
                "data": statistics
            }),
        }
    
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": dumps({"error": "Internal server error"}),
        }
