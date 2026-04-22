import json
from typing import Any, Dict

from pydantic import ValidationError

from application.exceptions.vocabulary_errors import VocabularyLookupError
from application.use_cases.flashcard.create_flashcard_uc import CreateFlashCardUC
from interfaces.mapper.flashcard_mapper import FlashCardMapper


class FlashCardController:
    """Điều phối các request liên quan đến flashcard."""

    def __init__(self, create_flashcard_usecase: CreateFlashCardUC) -> None:
        self.create_flashcard_usecase = create_flashcard_usecase
        self.mapper = FlashCardMapper()

    def _response(self, status: int, body: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "statusCode": status,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(body),
        }

    def create(self, event: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Tạo flashcard mới từ request."""
        try:
            body = json.loads(event.get("body", "{}"))
        except json.JSONDecodeError:
            return self._response(400, {"error": "Định dạng JSON không hợp lệ."})

        try:
            command = self.mapper.to_create_command(body, user_id)
        except ValidationError as e:
            return self._response(400, {"error": f"Dữ liệu không hợp lệ: {str(e)}"})

        result = self.create_flashcard_usecase.execute(command)

        if result.is_failure():
            error_msg = str(result.error) if result.error else "Không thể tạo flashcard."
            return self._response(400, {"error": error_msg})

        response_data = result.value
        return self._response(
            201,
            {
                "flashcard_id": response_data.flashcard_id,
                "word": response_data.word,
                "message": response_data.message,
            },
        )
