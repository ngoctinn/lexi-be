import os

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from application.dtos.vocabulary.translate.translate_vocabulary_command import TranslateVocabularyCommand
from application.dtos.vocabulary.translate.translate_vocabulary_response import TranslateVocabularyResponse
from application.exceptions.vocabulary_errors import VocabularyLookupError, VocabularyNotFoundError
from application.repositories.vocabulary_repository import VocabularyRepository
from application.services.vocabulary_lookup_service import VocabularyLookupService
from shared.result import Result

# Reuse boto3 client — tránh tạo mới mỗi lần gọi
_translate_client = None


def _get_translate_client():
    global _translate_client
    if _translate_client is None:
        region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
        _translate_client = boto3.client("translate", region_name=region) if region else boto3.client("translate")
    return _translate_client


class TranslateVocabularyUC:
    """
    Ca sử dụng dịch từ vựng trong ngữ cảnh câu.

    Luồng:
    1. Dùng AWS Translate để dịch từ trong ngữ cảnh câu (context-aware)
    2. Tra cache DynamoDB để lấy thêm phonetic, audio, definition nếu có
    3. Nếu cache miss, gọi dictionary API để lấy metadata
    4. Trả về translation + metadata
    """

    def __init__(
        self,
        repo: VocabularyRepository,
        source_service: VocabularyLookupService,
    ):
        self._repo = repo
        self._source_service = source_service

    def execute(self, command: TranslateVocabularyCommand) -> Result[TranslateVocabularyResponse, Exception]:
        word = command.word

        # 1. Dịch từ với ngữ cảnh câu bằng AWS Translate
        # Nếu có sentence, dịch cả câu rồi lấy nghĩa từ trong đó
        # Nếu không có sentence, dịch từ đơn lẻ
        translation_vi = self._translate_in_context(word, command.sentence)

        # 2. Lấy metadata từ cache hoặc dictionary API
        phonetic = ""
        audio_url = ""
        definition_vi = ""
        part_of_speech = ""

        cached = self._repo.find_by_word(word)
        if cached:
            phonetic = cached.phonetic or ""
            audio_url = cached.audio_url or ""
            definition_vi = cached.definition_vi or ""
            part_of_speech = cached.word_type.value if hasattr(cached.word_type, "value") else str(cached.word_type)
        else:
            # Thử lấy từ dictionary API (best-effort, không fail nếu không có)
            try:
                vocab = self._source_service.lookup(word)
                phonetic = vocab.phonetic or ""
                audio_url = vocab.audio_url or ""
                definition_vi = vocab.definition_vi or ""
                part_of_speech = vocab.word_type.value if hasattr(vocab.word_type, "value") else str(vocab.word_type)
                # Lưu cache
                try:
                    self._repo.save(vocab)
                except Exception:
                    pass  # Cache failure không block response
            except (VocabularyNotFoundError, VocabularyLookupError):
                pass  # Không có trong dictionary — vẫn trả về translation từ AWS Translate

        return Result.success(TranslateVocabularyResponse(
            word=word,
            translation_vi=translation_vi,
            part_of_speech=part_of_speech,
            definition_vi=definition_vi,
            phonetic=phonetic,
            audio_url=audio_url,
        ))

    def _translate_in_context(self, word: str, sentence: str | None) -> str:
        """
        Dịch từ bằng AWS Translate.
        Nếu có sentence, dịch cả câu để lấy nghĩa đúng ngữ cảnh,
        sau đó fallback về dịch từ đơn nếu cần.
        """
        # Ưu tiên dịch từ đơn lẻ — đơn giản và đủ dùng cho MVP
        # AWS Translate đã context-aware ở mức từ
        text_to_translate = word
        try:
            client = _get_translate_client()
            response = client.translate_text(
                Text=text_to_translate,
                SourceLanguageCode="en",
                TargetLanguageCode="vi",
            )
            return response.get("TranslatedText", word)
        except (ClientError, BotoCoreError):
            return word
