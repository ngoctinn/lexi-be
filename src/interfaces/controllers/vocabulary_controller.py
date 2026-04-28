import json
import logging
from typing import Any, Dict

from pydantic import ValidationError

from application.exceptions.vocabulary_errors import (
    VocabularyLookupError,
    VocabularyNotFoundError,
    VocabularyPersistenceError,
)
from application.use_cases.vocabulary_use_cases import TranslateSentenceUseCase, TranslateVocabularyUseCase
from domain.exceptions.dictionary_exceptions import WordNotFoundError, DictionaryServiceError
from interfaces.mapper.vocabulary_mapper import VocabularyMapper
from interfaces.presenters.http_presenter import HttpPresenter
from shared.result import Result
from interfaces.view_models.vocabulary_vm import VocabularyTranslationViewModel, SentenceTranslationViewModel
from shared.http_utils import dumps

logger = logging.getLogger(__name__)


class VocabularyController:
    def __init__(
        self,
        translate_use_case: TranslateVocabularyUseCase | None = None,
        translate_sentence_use_case: TranslateSentenceUseCase | None = None,
        presenter: HttpPresenter | None = None,
    ):
        self._translate_use_case = translate_use_case
        self._translate_sentence_use_case = translate_sentence_use_case
        self._presenter = presenter or HttpPresenter()

    def translate(self, body_str: str | None) -> Result[VocabularyTranslationViewModel, str]:
        if not self._translate_use_case:
            logger.error("Translate use case not configured")
            return Result.failure("Translate use case not configured")
        
        try:
            body = json.loads(body_str or "{}")
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in translate request")
            return Result.failure("Invalid JSON format")
        
        try:
            logger.info("Translating vocabulary")
            command = VocabularyMapper.to_translate_command(body)
            result = self._translate_use_case.execute(command)
            
            if not result.is_success:
                error = result.error
                # Handle Dictionary API errors
                if isinstance(error, WordNotFoundError):
                    logger.warning("Word not found in dictionary", extra={"context": {"error": str(error)}})
                    return Result.failure("Word not found in dictionary")
                if isinstance(error, DictionaryServiceError):
                    logger.error("Dictionary service error", extra={"context": {"error": str(error)}})
                    return Result.failure("Dictionary service temporarily unavailable")
                # Handle legacy errors
                if isinstance(error, VocabularyNotFoundError):
                    logger.warning("Vocabulary not found", extra={"context": {"error": str(error)}})
                    return Result.failure(str(error))
                if isinstance(error, (VocabularyLookupError, VocabularyPersistenceError)):
                    logger.error("External service error", extra={"context": {"error": str(error)}})
                    return Result.failure(str(error))
                logger.warning("Translation failed", extra={"context": {"error": str(error)}})
                return Result.failure(str(error))
            
            # Chuyển đổi Response DTO → View Model
            response = result.value
            view_model = VocabularyMapper.response_to_view_model(response)
            
            logger.info("Translation successful")
            return Result.success(view_model)
        except ValidationError as exc:
            logger.warning("Validation error in translate request", extra={"context": {"errors": str(exc)}})
            return Result.failure(f"Invalid request data: {str(exc)}")
        except Exception as exc:
            logger.exception("Error in translate", extra={"context": {"error": str(exc)}})
            raise

    def translate_sentence(self, body_str: str | None) -> Result[SentenceTranslationViewModel, str]:
        if not self._translate_sentence_use_case:
            logger.error("Translate sentence use case not configured")
            return Result.failure("Translate sentence use case not configured")
        
        try:
            body = json.loads(body_str or "{}")
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in translate_sentence request")
            return Result.failure("Invalid JSON format")
        
        try:
            logger.info("Translating sentence")
            command = VocabularyMapper.to_translate_sentence_command(body)
            result = self._translate_sentence_use_case.execute(command)
            
            if not result.is_success:
                logger.error("Sentence translation failed", extra={"context": {"error": str(result.error)}})
                return Result.failure(str(result.error))
            
            # Chuyển đổi Response DTO → View Model
            response = result.value
            view_model = SentenceTranslationViewModel(
                sentence_en=response.sentence_en,
                sentence_vi=response.sentence_vi,
            )
            
            logger.info("Sentence translation successful")
            return Result.success(view_model)
        except ValidationError as exc:
            logger.warning("Validation error in translate_sentence request", extra={"context": {"errors": str(exc)}})
            return Result.failure(f"Invalid request data: {str(exc)}")
        except Exception as exc:
            logger.exception("Error in translate_sentence", extra={"context": {"error": str(exc)}})
            raise
