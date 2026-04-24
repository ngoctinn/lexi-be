from application.dtos.vocabulary_dtos import (
    TranslateVocabularyCommand,
    TranslateVocabularyResponse,
    TranslateSentenceCommand,
    TranslateSentenceResponse,
)
from application.service_ports.translation_service import TranslationService
from shared.result import Result


class TranslateVocabularyUseCase:
    """
    Ca sử dụng dịch từ vựng EN→VI.
    Phụ thuộc vào TranslationService (port), không phụ thuộc trực tiếp vào AWS.
    """

    def __init__(self, translation_service: TranslationService):
        self._translation_service = translation_service

    def execute(self, command: TranslateVocabularyCommand) -> Result[TranslateVocabularyResponse, Exception]:
        translation_vi = self._translation_service.translate_en_to_vi(command.word)
        return Result.success(TranslateVocabularyResponse(
            word=command.word,
            translation_vi=translation_vi,
        ))


class TranslateSentenceUseCase:
    """
    Ca sử dụng dịch toàn bộ câu EN→VI.
    Phụ thuộc vào TranslationService (port), không phụ thuộc trực tiếp vào AWS.
    """

    def __init__(self, translation_service: TranslationService):
        self._translation_service = translation_service

    def execute(self, command: TranslateSentenceCommand) -> Result[TranslateSentenceResponse, Exception]:
        try:
            sentence_vi = self._translation_service.translate_en_to_vi(command.sentence)
            return Result.success(TranslateSentenceResponse(
                sentence_en=command.sentence,
                sentence_vi=sentence_vi,
            ))
        except Exception as exc:
            return Result.failure(exc)
