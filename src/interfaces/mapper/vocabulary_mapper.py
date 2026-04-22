from typing import Any, Dict

from application.dtos.vocabulary.translate.translate_sentence_command import TranslateSentenceCommand
from application.dtos.vocabulary.translate.translate_vocabulary_command import TranslateVocabularyCommand


class VocabularyMapper:
    """Phiên dịch dữ liệu HTTP sang command của application."""

    @staticmethod
    def to_translate_command(body: Dict[str, Any]) -> TranslateVocabularyCommand:
        return TranslateVocabularyCommand(
            word=body.get("word", ""),
            sentence=body.get("sentence"),
        )

    @staticmethod
    def to_translate_sentence_command(body: Dict[str, Any]) -> TranslateSentenceCommand:
        return TranslateSentenceCommand(sentence=body.get("sentence", ""))
