from application.dtos.vocabulary.translate.translate_sentence_command import TranslateSentenceCommand
from application.dtos.vocabulary.translate.translate_sentence_response import TranslateSentenceResponse
from application.services.translation_service import TranslationService
from shared.result import Result


class TranslateSentenceUC:
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
