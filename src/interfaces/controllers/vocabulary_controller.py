import json
from typing import Any, Dict

from pydantic import ValidationError

from application.exceptions.vocabulary_errors import (
    VocabularyLookupError,
    VocabularyNotFoundError,
    VocabularyPersistenceError,
)
from application.use_cases.vocabulary.translate_vocabulary import TranslateVocabularyUC
from interfaces.mapper.vocabulary_mapper import VocabularyMapper


class VocabularyController:
    """
    Điều phối các request liên quan đến tra cứu từ vựng.

    Tầng này chỉ lo parse request, gọi use case và map HTTP response.
    """

    def __init__(self, translate_use_case: TranslateVocabularyUC):
        self._translate_use_case = translate_use_case

    def _response(self, status: int, body: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "statusCode": status,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(body),
        }

    def translate(self, body_str: str | None) -> Dict[str, Any]:
        try:
            body = json.loads(body_str or "{}")
        except json.JSONDecodeError:
            return self._response(400, {"error": "Định dạng JSON không hợp lệ."})

        try:
            command = VocabularyMapper.to_translate_command(body)
            result = self._translate_use_case.execute(command)

            if not result.is_success:
                error = result.error
                if isinstance(error, VocabularyNotFoundError):
                    return self._response(404, {"error": str(error)})
                if isinstance(error, VocabularyLookupError):
                    return self._response(502, {"error": str(error)})
                if isinstance(error, VocabularyPersistenceError):
                    return self._response(500, {"error": str(error)})
                return self._response(422, {"error": str(error)})

            return self._response(200, result.value.model_dump())

        except ValidationError as exc:
            return self._response(400, {"error": "Dữ liệu yêu cầu không hợp lệ.", "details": exc.errors()})
        except Exception as exc:
            return self._response(500, {"error": f"Lỗi hệ thống: {str(exc)}"})
