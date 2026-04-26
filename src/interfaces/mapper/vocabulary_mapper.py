from typing import Any, Dict

from application.dtos.vocabulary_dtos import (
    TranslateSentenceCommand,
    TranslateVocabularyCommand,
    TranslateVocabularyResponse,
    DefinitionDTO,
    SynonymDTO,
)
from interfaces.view_models.vocabulary_vm import (
    VocabularyTranslationViewModel,
    DefinitionVM,
    SynonymVM,
)


class VocabularyMapper:
    """Phiên dịch dữ liệu HTTP sang command của application."""

    @staticmethod
    def to_translate_command(body: Dict[str, Any]) -> TranslateVocabularyCommand:
        return TranslateVocabularyCommand(
            word=body.get("word", ""),
            sentence=body.get("sentence"),
            context=body.get("context"),
        )

    @staticmethod
    def to_translate_sentence_command(body: Dict[str, Any]) -> TranslateSentenceCommand:
        from application.dtos.vocabulary_dtos import TranslateSentenceCommand
        return TranslateSentenceCommand(sentence=body.get("sentence", ""))

    @staticmethod
    def response_to_view_model(response: TranslateVocabularyResponse) -> VocabularyTranslationViewModel:
        """Convert TranslateVocabularyResponse DTO to VocabularyTranslationViewModel."""
        # Convert meanings (new format) to definitions (legacy format) for backward compatibility
        definitions_vm = []
        
        # If meanings exist (new format), convert them
        if response.meanings:
            for meaning in response.meanings:
                definitions_vm.append(DefinitionVM(
                    part_of_speech=meaning.part_of_speech,
                    definition_en=meaning.definition,
                    definition_vi=meaning.definition_vi,
                    example_en=meaning.example,
                    example_vi=meaning.example_vi,
                ))
        # Otherwise use legacy definitions field
        elif response.definitions:
            for d in response.definitions:
                definitions_vm.append(DefinitionVM(
                    part_of_speech=d.part_of_speech,
                    definition_en=d.definition_en,
                    definition_vi=d.definition_vi,
                    example_en=d.example_en,
                    example_vi=d.example_vi,
                ))
        
        synonyms_vm = [
            SynonymVM(en=s.en, vi=s.vi)
            for s in response.synonyms
        ]
        
        return VocabularyTranslationViewModel(
            word=response.word,
            translation_vi=response.translate_vi,
            phonetic=response.phonetic,
            audio_url=response.audio_url,
            definitions=definitions_vm,
            synonyms=synonyms_vm,
            response_time_ms=response.response_time_ms,
            cached=response.cached,
        )
