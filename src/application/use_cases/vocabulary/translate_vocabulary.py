from application.dtos.vocabulary.translate.translate_vocabulary_command import TranslateVocabularyCommand
from application.dtos.vocabulary.translate.translate_vocabulary_response import TranslateVocabularyResponse
from application.exceptions.vocabulary_errors import (
    VocabularyLookupError,
    VocabularyNotFoundError,
    VocabularyPersistenceError,
)
from application.repositories.vocabulary_repository import VocabularyRepository
from application.services.vocabulary_lookup_service import VocabularyLookupService
from domain.entities.vocabulary import Vocabulary
from shared.result import Result


class TranslateVocabularyUC:
    """
    Ca sử dụng dịch từ vựng.

    Luồng:
    1. Tra cache DynamoDB theo word.
    2. Nếu miss, gọi nguồn ngoài để lấy dữ liệu.
    3. Lưu lại vào DynamoDB.
    4. Trả response đã chuẩn hóa.
    """

    def __init__(self, repo: VocabularyRepository, source_service: VocabularyLookupService):
        self._repo = repo
        self._source_service = source_service

    def execute(self, command: TranslateVocabularyCommand) -> Result[TranslateVocabularyResponse, Exception]:
        cached = self._repo.find_by_word(command.word)
        if cached:
            if not cached.translation_vi:
                try:
                    refreshed = self._source_service.lookup(command.word)
                    self._repo.save(refreshed)
                    return Result.success(self._to_response(refreshed))
                except (VocabularyNotFoundError, VocabularyLookupError):
                    return Result.success(self._to_response(cached))

            return Result.success(self._to_response(cached))

        try:
            vocabulary = self._source_service.lookup(command.word)
        except (VocabularyNotFoundError, VocabularyLookupError) as exc:
            return Result.failure(exc)
        except Exception as exc:
            return Result.failure(VocabularyLookupError(str(exc)))

        try:
            self._repo.save(vocabulary)
        except Exception as exc:
            return Result.failure(VocabularyPersistenceError(f"Không thể lưu từ vựng: {str(exc)}"))

        return Result.success(self._to_response(vocabulary))

    def _to_response(self, vocabulary: Vocabulary) -> TranslateVocabularyResponse:
        part_of_speech = vocabulary.word_type.value if hasattr(vocabulary.word_type, "value") else str(vocabulary.word_type)
        return TranslateVocabularyResponse(
            word=vocabulary.word,
            translation_vi=vocabulary.translation_vi,
            part_of_speech=part_of_speech,
            definition_vi=vocabulary.definition_vi,
            phonetic=vocabulary.phonetic,
            audio_url=vocabulary.audio_url,
            example_sentence=vocabulary.example_sentence,
            source_api=vocabulary.source_api or "",
        )
