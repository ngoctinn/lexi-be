from datetime import datetime, timezone
from typing import List, Optional
import os

import boto3

from application.repositories.vocabulary_repository import VocabularyRepository
from domain.entities.vocabulary import Vocabulary
from domain.value_objects.enums import VocabType


class DynamoVocabularyRepo(VocabularyRepository):
    def __init__(self, table=None):
        self._table = table or boto3.resource("dynamodb").Table(os.environ["LEXI_TABLE_NAME"])

    def find_by_word(self, word: str) -> Optional[Vocabulary]:
        normalized_word = word.strip().lower()
        response = self._table.get_item(
            Key={
                "PK": f"VOCAB#{normalized_word}",
                "SK": "META",
            }
        )
        item = response.get("Item")
        if not item:
            return None

        return self._to_entity(item)

    def save(self, vocabulary: Vocabulary) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._table.put_item(
            Item={
                "PK": f"VOCAB#{vocabulary.word}",
                "SK": "META",
                "EntityType": "VOCABULARY",
                "word": vocabulary.word,
                "word_type": vocabulary.word_type.value if hasattr(vocabulary.word_type, "value") else vocabulary.word_type,
                "translation_vi": vocabulary.translation_vi,
                "definition_vi": vocabulary.definition_vi,
                "phonetic": vocabulary.phonetic,
                "audio_url": vocabulary.audio_url,
                "example_sentence": vocabulary.example_sentence,
                "source_api": vocabulary.source_api or "",
                "created_at": now,
                "updated_at": now,
            }
        )

    def list_by_level(self, level: str, limit: int = 20) -> List[Vocabulary]:
        raise NotImplementedError("Chưa hỗ trợ truy vấn vocabulary theo level.")

    def _to_entity(self, item: dict) -> Vocabulary:
        return Vocabulary(
            word=item.get("word", ""),
            word_type=self._to_vocab_type(item.get("word_type", "noun")),
            translation_vi=item.get("translation_vi", ""),
            definition_vi=item.get("definition_vi", ""),
            phonetic=item.get("phonetic", ""),
            audio_url=item.get("audio_url", ""),
            example_sentence=item.get("example_sentence", ""),
            source_api=item.get("source_api", ""),
        )

    def _to_vocab_type(self, value: str) -> VocabType:
        normalized = str(value).strip().lower()
        mapping = {
            "noun": VocabType.NOUN,
            "verb": VocabType.VERB,
            "adjective": VocabType.ADJECTIVE,
            "adverb": VocabType.ADVERB,
            "pronoun": VocabType.PRONOUN,
            "preposition": VocabType.PREPOSITION,
            "conjunction": VocabType.CONJUNCTION,
            "interjection": VocabType.INTERJECTION,
            "exclamation": VocabType.INTERJECTION,
            "phrase": VocabType.PHRASE,
            "idiom": VocabType.IDIOM,
        }
        return mapping.get(normalized, VocabType.NOUN)
