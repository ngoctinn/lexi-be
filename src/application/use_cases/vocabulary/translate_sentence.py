from application.dtos.vocabulary.translate.translate_sentence_command import TranslateSentenceCommand
from application.dtos.vocabulary.translate.translate_sentence_response import TranslateSentenceResponse
from application.exceptions.vocabulary_errors import VocabularyLookupError
from shared.result import Result


class TranslateSentenceUC:
    """
    Ca sử dụng dịch toàn bộ câu.

    Luồng:
    1. Nhận câu tiếng Anh
    2. Dùng AWS Translate để dịch sang tiếng Việt
    3. Trả về câu gốc + câu dịch
    """

    def __init__(self, translate_client=None):
        self._translate_client = translate_client

    def execute(self, command: TranslateSentenceCommand) -> Result[TranslateSentenceResponse, Exception]:
        try:
            sentence_vi = self._translate(command.sentence)
            return Result.success(TranslateSentenceResponse(
                sentence_en=command.sentence,
                sentence_vi=sentence_vi,
            ))
        except Exception as exc:
            return Result.failure(VocabularyLookupError(f"Không thể dịch câu: {str(exc)}"))

    def _translate(self, text: str) -> str:
        client = self._get_client()
        response = client.translate_text(
            Text=text,
            SourceLanguageCode="en",
            TargetLanguageCode="vi",
        )
        return response["TranslatedText"]

    def _get_client(self):
        if self._translate_client is None:
            import os
            import boto3
            region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
            self._translate_client = boto3.client("translate", region_name=region) if region else boto3.client("translate")
        return self._translate_client
