import json
import os

from application.repositories.flash_card_repository import FlashCardRepository
from application.use_cases.flashcard.create_flashcard_uc import CreateFlashCardUC
from infrastructure.persistence.dynamo_flashcard_repo import DynamoFlashCardRepository
from interfaces.controllers.flashcard_controller import FlashCardController


# Khởi tạo dependencies
flashcard_repo: FlashCardRepository = DynamoFlashCardRepository()
create_flashcard_uc = CreateFlashCardUC(flashcard_repo)
flashcard_controller = FlashCardController(create_flashcard_uc)


def handler(event, context):
    """
    Lambda handler cho endpoint POST /flashcards.
    
    Tạo flashcard mới cho người dùng.
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

    return flashcard_controller.create(event, user_id)
