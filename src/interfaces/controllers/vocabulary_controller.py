import json
from typing import Any, Dict

from pydantic import ValidationError

from application.exceptions.vocabulary_errors import (
    VocabularyLookupError,
    VocabularyNotFoundError,
    VocabularyPersistenceError,
)
from application.use_cases.vocabulary.analyze_sentence import AnalyzeSentenceUC
from application.use_cases.vocabulary.translate_sentence import TranslateSentenceUC
from application.use_cases.vocabulary.translate_vocabulary import TranslateVocabularyUC
from interfaces.mapper.vocabulary_mapper import VocabularyMapper


class VocabularyController:
    def __init__(
        self,
        translate_use_case: TranslateVocabularyUC | None = None,
        analyze_use_case: AnalyzeSentenceUC | None = None,
        translate_sentence_use_case: TranslateSentenceUC | None = None,
    ):
        self._translate_use_case = translate_use_case
        self._analyze_use_case = analyze_use_case
        self._translate_sentence_use_case = translate_sentence_use_case

    def _response(self, status: int, body: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "statusCode": status,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(body, ensure_ascii=False),
        }

    def translate(self, body_str: str | None) -> Dict[str, Any]:
        if not self._translate_use_case:
            return self._response(500, {"error": "Translate use case chưa được cấu hình."})
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
            error_details = [{"loc": list(e.get("loc", [])), "msg": e.get("msg", ""), "type": e.get("type", "")} for e in exc.errors()]
            return self._response(400, {"error": "Dữ liệu yêu cầu không hợp lệ.", "details": error_details})
        except Exception as exc:
            return self._response(500, {"error": f"Lỗi hệ thống: {str(exc)}"})

    def translate_sentence(self, body_str: str | None) -> Dict[str, Any]:
        if not self._translate_sentence_use_case:
            return self._response(500, {"error": "Translate sentence use case chưa được cấu hình."})
        try:
            body = json.loads(body_str or "{}")
        except json.JSONDecodeError:
            return self._response(400, {"error": "Định dạng JSON không hợp lệ."})
        try:
            command = VocabularyMapper.to_translate_sentence_command(body)
            result = self._translate_sentence_use_case.execute(command)
            if not result.is_success:
                return self._response(502, {"error": str(result.error)})
            return self._response(200, result.value.model_dump())
        except ValidationError as exc:
            error_details = [{"loc": list(e.get("loc", [])), "msg": e.get("msg", ""), "type": e.get("type", "")} for e in exc.errors()]
            return self._response(400, {"error": "Dữ liệu yêu cầu không hợp lệ.", "details": error_details})
        except Exception as exc:
            return self._response(500, {"error": f"Lỗi hệ thống: {str(exc)}"})

    def analyze(self, body_str: str | None) -> Dict[str, Any]:
        if not self._analyze_use_case:
            return self._response(500, {"error": "Analyze use case chưa được cấu hình."})
        try:
            body = json.loads(body_str or "{}")
        except json.JSONDecodeError:
            return self._response(400, {"error": "Định dạng JSON không hợp lệ."})
        try:
            command = VocabularyMapper.to_analyze_sentence_command(body)
            result = self._analyze_use_case.execute(command)
            if not result.is_success:
                return self._response(422, {"error": str(result.error)})
            return self._response(200, result.value.model_dump())
        except ValidationError as exc:
            return self._response(400, {"error": "Dữ liệu yêu cầu không hợp lệ.", "details": exc.errors()})
        except Exception as exc:
            return self._response(500, {"error": f"Lỗi hệ thống: {str(exc)}"})
