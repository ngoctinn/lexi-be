import os

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from application.dtos.vocabulary.translate.translate_vocabulary_command import TranslateVocabularyCommand
from application.dtos.vocabulary.translate.translate_vocabulary_response import TranslateVocabularyResponse
from application.exceptions.vocabulary_errors import (
    VocabularyLookupError,
    VocabularyNotFoundError,
    VocabularyPersistenceError,
)
from application.repositories.vocabulary_repository import VocabularyRepository
from application.services.phrasal_verb_detection_service import PhrasalVerbDetectionService
from application.services.vocabulary_lookup_service import VocabularyLookupService
from domain.entities.vocabulary import Vocabulary
from domain.value_objects.enums import VocabType
from shared.result import Result

# Particle words không nên cache vì nghĩa phụ thuộc hoàn toàn vào context
_PARTICLE_WORDS = {"up", "out", "in", "on", "off", "back", "down", "away", "over", "around", "through"}


class TranslateVocabularyUC:
    """
    Ca sử dụng dịch từ vựng.

    Luồng:
    1. Nếu có context, detect phrase trước
    2. Tra cache DynamoDB theo word (hoặc phrase nếu detect được)
    3. Nếu miss, gọi nguồn ngoài để lấy dữ liệu
    4. Lưu lại vào DynamoDB
    5. Trả response đã chuẩn hóa
    """

    def __init__(
        self,
        repo: VocabularyRepository,
        source_service: VocabularyLookupService,
        phrase_detector: PhrasalVerbDetectionService | None = None,
    ):
        self._repo = repo
        self._source_service = source_service
        self._phrase_detector = phrase_detector

    def execute(self, command: TranslateVocabularyCommand) -> Result[TranslateVocabularyResponse, Exception]:
        # Detect phrase từ context nếu có
        detected_phrase = None
        phrase_type = None
        lookup_word = command.word

        if command.context and self._phrase_detector:
            detected_phrase = self._detect_phrase_in_context(command.word, command.context)
            if detected_phrase:
                lookup_word = detected_phrase
                phrase_type = "phrase"

        # Particle words (up, out, in...) không cache vì nghĩa phụ thuộc context
        # Nếu không detect được phrase từ particle word → dùng AWS Translate trực tiếp
        is_particle = command.word.lower() in _PARTICLE_WORDS
        if is_particle and not detected_phrase:
            translation_vi = self._translate_direct(command.word)
            return Result.success(TranslateVocabularyResponse(
                word=command.word,
                translation_vi=translation_vi,
                part_of_speech="particle",
                definition_vi="",
                detected_phrase=None,
                phrase_type=None,
            ))

        # Tra cache (chỉ cache non-particle words)
        if not is_particle:
            cached = self._repo.find_by_word(lookup_word)
            if cached:
                if not cached.translation_vi:
                    try:
                        refreshed = self._source_service.lookup(lookup_word)
                        self._repo.save(refreshed)
                        return Result.success(self._to_response(refreshed, detected_phrase, phrase_type))
                    except (VocabularyNotFoundError, VocabularyLookupError):
                        return Result.success(self._to_response(cached, detected_phrase, phrase_type))
                return Result.success(self._to_response(cached, detected_phrase, phrase_type))

        # Lookup từ nguồn ngoài
        try:
            vocabulary = self._source_service.lookup(lookup_word)
        except (VocabularyNotFoundError, VocabularyLookupError):
            # Phrase không có trong dictionary → dùng AWS Translate trực tiếp
            # KHÔNG fallback về single word vì sẽ gây cache sai
            translation_vi = self._translate_direct(lookup_word)
            return Result.success(TranslateVocabularyResponse(
                word=lookup_word,
                translation_vi=translation_vi,
                part_of_speech="phrase" if detected_phrase else "word",
                definition_vi="",
                detected_phrase=detected_phrase,
                phrase_type=phrase_type,
            ))
        except Exception as exc:
            return Result.failure(VocabularyLookupError(str(exc)))

        # Lưu cache (không cache particle words)
        if not is_particle:
            try:
                self._repo.save(vocabulary)
            except Exception as exc:
                return Result.failure(VocabularyPersistenceError(f"Không thể lưu từ vựng: {str(exc)}"))

        return Result.success(self._to_response(vocabulary, detected_phrase, phrase_type))

    def _translate_direct(self, text: str) -> str:
        """Dùng AWS Translate trực tiếp, không qua dictionary."""
        try:
            region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
            client = boto3.client("translate", region_name=region) if region else boto3.client("translate")
            response = client.translate_text(
                Text=text,
                SourceLanguageCode="en",
                TargetLanguageCode="vi",
            )
            return response.get("TranslatedText", text)
        except (ClientError, BotoCoreError):
            return text

    def _detect_phrase_in_context(self, word: str, context: str) -> str | None:
        """
        Detect xem word có nằm trong phrase không.

        Logic:
        - Nếu word là VERB (woke, looking, showed): match phrase có verb đó
        - Nếu word là PARTICLE (up, out, in): match phrase có particle đó
          nhưng chỉ khi particle xuất hiện ngay sau verb trong context
        """
        if not self._phrase_detector:
            return None

        tokens = self._phrase_detector.analyze(context)
        word_lower = word.lower()
        is_particle = word_lower in _PARTICLE_WORDS

        for token in tokens:
            if token.token_type != "phrase":
                continue

            phrase_words = token.text.lower().split()

            if is_particle:
                # Particle: chỉ match nếu word là particle CUỐI của phrase
                # VD: "up" match "showed up" (particle cuối) nhưng không match "pick up the phone"
                if phrase_words and phrase_words[-1] == word_lower:
                    return token.base
            else:
                # Verb: chỉ match nếu word là VERB ĐẦU của phrase (sau khi lemmatize)
                # VD: "woke" match "woke up" (verb đầu)
                if phrase_words and phrase_words[0] == word_lower:
                    return token.base
                # Hoặc verb đầu trong phrase text khớp với word (inflected form)
                # VD: phrase text = "woke up", base = "wake up" → phrase_words[0] = "woke" = word_lower
                # Đã được cover ở trên, không cần thêm logic

        return None

    def _get_inflections(self, base_verb: str) -> set[str]:
        """Trả về các dạng inflection của verb."""
        from application.services.phrasal_verb_detection_service import PhrasalVerbDetectionService
        # Dùng lại logic candidate_lemmas từ phrase detector
        if hasattr(self._phrase_detector, '_candidate_lemmas'):
            # Reverse: từ base tìm inflections không cần thiết
            # Chỉ cần check xem word_lower có lemmatize về base_verb không
            pass
        return {base_verb}

    def _to_response(
        self,
        vocabulary: Vocabulary,
        detected_phrase: str | None = None,
        phrase_type: str | None = None,
    ) -> TranslateVocabularyResponse:
        from application.dtos.vocabulary.translate.translate_vocabulary_response import VocabMeaning
        part_of_speech = vocabulary.word_type.value if hasattr(vocabulary.word_type, "value") else str(vocabulary.word_type)
        meanings = [
            VocabMeaning(
                part_of_speech=m.get("part_of_speech", ""),
                definition_vi=m.get("definition_vi", ""),
                example_sentence=m.get("example_sentence", ""),
            )
            for m in (vocabulary.all_meanings or [])
        ]
        return TranslateVocabularyResponse(
            word=vocabulary.word,
            translation_vi=vocabulary.translation_vi,
            part_of_speech=part_of_speech,
            definition_vi=vocabulary.definition_vi,
            phonetic=vocabulary.phonetic,
            audio_url=vocabulary.audio_url,
            example_sentence=vocabulary.example_sentence,
            source_api=vocabulary.source_api or "",
            detected_phrase=detected_phrase,
            phrase_type=phrase_type,
            meanings=meanings,
        )
