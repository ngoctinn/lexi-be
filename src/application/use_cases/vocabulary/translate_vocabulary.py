from application.dtos.vocabulary.translate.translate_vocabulary_command import TranslateVocabularyCommand
from application.dtos.vocabulary.translate.translate_vocabulary_response import TranslateVocabularyResponse
from application.services.translation_service import TranslationService
from shared.result import Result


class TranslateVocabularyUC:
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
