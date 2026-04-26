import logging
import time

from application.dtos.vocabulary_dtos import (
    TranslateVocabularyCommand,
    TranslateVocabularyResponse,
    TranslateSentenceCommand,
    TranslateSentenceResponse,
    MeaningDTO,
)
from application.service_ports.translation_service import TranslationService
from application.service_ports.dictionary_service import DictionaryService
from domain.exceptions.dictionary_exceptions import WordNotFoundError, DictionaryServiceError
from shared.result import Result

logger = logging.getLogger(__name__)


class TranslateVocabularyUseCase:
    """
    Use case for translating vocabulary EN→VI with Dictionary API.
    Orchestrates DictionaryService and TranslationService.
    
    Workflow:
    1. Fetch word definition from DictionaryService (with context for phrasal verbs)
    2. Collect items to translate: word + definitions + examples
    3. Batch translate using TranslationService
    4. Map translations back to Vocabulary entity
    5. Return TranslateVocabularyResponse
    """

    def __init__(
        self,
        dictionary_service: DictionaryService,
        translation_service: TranslationService
    ):
        self._dictionary_service = dictionary_service
        self._translation_service = translation_service

    def execute(self, command: TranslateVocabularyCommand) -> Result[TranslateVocabularyResponse, Exception]:
        """
        Execute vocabulary translation workflow.
        
        Args:
            command: TranslateVocabularyCommand with word and optional context
        
        Returns:
            Result with TranslateVocabularyResponse or Exception
        """
        start_time = time.time()
        
        try:
            # Step 1: Fetch word definition from DictionaryService (with context for phrasal verbs)
            logger.info(f"Fetching definition for word: {command.word}")
            vocabulary = self._dictionary_service.get_word_definition(
                word=command.word,
                context=command.context
            )
            logger.info(f"Fetched definition for word: {vocabulary.word}")
            
            # Step 2: Collect items to translate
            items_to_translate = []
            item_indices = []  # Track which item belongs to which meaning
            
            # Add word itself
            items_to_translate.append(vocabulary.word)
            item_indices.append(("word", None))
            
            # Add definitions and examples from meanings
            for idx, meaning in enumerate(vocabulary.meanings):
                # Add definition
                items_to_translate.append(meaning.definition)
                item_indices.append(("definition", idx))
                
                # Add example if available
                if meaning.example:
                    items_to_translate.append(meaning.example)
                    item_indices.append(("example", idx))
            
            # Step 3: Translate each item individually
            logger.info(f"Translating {len(items_to_translate)} items")
            translations = [
                self._translation_service.translate_en_to_vi(item) if item else ""
                for item in items_to_translate
            ]
            
            # Step 4: Map translations back to vocabulary
            translation_map = {}
            for i, (item_type, idx) in enumerate(item_indices):
                if item_type == "word":
                    translation_map["word"] = translations[i] if i < len(translations) else vocabulary.word
                else:
                    if idx not in translation_map:
                        translation_map[idx] = {}
                    translation_map[idx][item_type] = translations[i] if i < len(translations) else ""
            
            # Build MeaningDTOs with translations
            meanings_dto = []
            for idx, meaning in enumerate(vocabulary.meanings):
                trans = translation_map.get(idx, {})
                meanings_dto.append(MeaningDTO(
                    part_of_speech=meaning.part_of_speech,
                    definition=meaning.definition,
                    definition_vi=trans.get("definition", ""),
                    example=meaning.example,
                    example_vi=trans.get("example", "")
                ))
            
            # Step 5: Return response
            response_time_ms = int((time.time() - start_time) * 1000)
            logger.info(f"Translation completed in {response_time_ms}ms")
            
            return Result.success(TranslateVocabularyResponse(
                word=vocabulary.word,
                translate_vi=translation_map.get("word", vocabulary.word),
                phonetic=vocabulary.phonetic,
                audio_url=vocabulary.audio_url,
                meanings=meanings_dto,
                response_time_ms=response_time_ms,
                cached=False  # Will be set by adapter if cached
            ))
        
        except WordNotFoundError as e:
            logger.warning(f"Word not found: {command.word}")
            return Result.failure(e)
        except DictionaryServiceError as e:
            logger.error(f"Dictionary service error for word {command.word}: {e}")
            return Result.failure(e)
        except Exception as e:
            logger.error(f"Unexpected error translating vocabulary {command.word}: {e}", exc_info=True)
            return Result.failure(e)


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
