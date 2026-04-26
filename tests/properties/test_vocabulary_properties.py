"""Property-based tests for vocabulary translation using Hypothesis."""

import pytest
from hypothesis import given, strategies as st, assume
from unittest.mock import Mock
import json

from application.use_cases.vocabulary_use_cases import TranslateVocabularyUseCase
from application.dtos.vocabulary_dtos import TranslateVocabularyCommand, TranslateVocabularyResponse, MeaningDTO
from domain.entities.vocabulary import Vocabulary, Meaning


# Strategies for generating test data
word_strategy = st.text(
    alphabet=st.characters(blacklist_categories=('Cc', 'Cs')),
    min_size=1,
    max_size=100
).filter(lambda x: x.strip() and not any(c.isdigit() for c in x))

definition_strategy = st.text(
    alphabet=st.characters(blacklist_categories=('Cc', 'Cs')),
    min_size=5,
    max_size=500
).filter(lambda x: x.strip())

part_of_speech_strategy = st.sampled_from([
    'noun', 'verb', 'adjective', 'adverb', 'exclamation', 'phrasal verb'
])


@pytest.fixture
def mock_dictionary_service():
    """Mock DictionaryService."""
    return Mock()


@pytest.fixture
def mock_translation_service():
    """Mock TranslationService."""
    return Mock()


@pytest.fixture
def use_case(mock_dictionary_service, mock_translation_service):
    """Create TranslateVocabularyUseCase with mocked services."""
    return TranslateVocabularyUseCase(
        dictionary_service=mock_dictionary_service,
        translation_service=mock_translation_service
    )


class TestVocabularyResponseProperties:
    """Property-based tests for vocabulary response structure."""
    
    @given(word_strategy)
    def test_response_contains_word_field(self, word, use_case, mock_dictionary_service, mock_translation_service):
        """Property: Response always contains the requested word."""
        vocab = Vocabulary(
            word=word,
            translate_vi='translation',
            phonetic='phonetic',
            meanings=[]
        )
        mock_dictionary_service.get_word_definition.return_value = vocab
        mock_translation_service.translate_batch.return_value = ['translation']
        
        command = TranslateVocabularyCommand(word=word)
        result = use_case.execute(command)
        
        assert result.is_success
        assert result.value.word == word
    
    @given(word_strategy)
    def test_response_contains_translation_vi_field(self, word, use_case, mock_dictionary_service, mock_translation_service):
        """Property: Response always contains translation_vi field."""
        vocab = Vocabulary(
            word=word,
            translate_vi='',
            phonetic='phonetic',
            meanings=[]
        )
        mock_dictionary_service.get_word_definition.return_value = vocab
        mock_translation_service.translate_batch.return_value = ['translation_vi']
        
        command = TranslateVocabularyCommand(word=word)
        result = use_case.execute(command)
        
        assert result.is_success
        assert hasattr(result.value, 'translation_vi')
        assert result.value.translation_vi is not None
    
    @given(st.lists(part_of_speech_strategy, min_size=1, max_size=5))
    def test_response_contains_all_meanings(self, parts_of_speech, use_case, mock_dictionary_service, mock_translation_service):
        """Property: Response contains all meanings from dictionary."""
        meanings = [
            Meaning(
                part_of_speech=pos,
                definition=f'definition for {pos}',
                example=f'example for {pos}'
            )
            for pos in parts_of_speech
        ]
        
        vocab = Vocabulary(
            word='test',
            translate_vi='',
            phonetic='test',
            meanings=meanings
        )
        mock_dictionary_service.get_word_definition.return_value = vocab
        
        # Mock translations
        translations = ['test'] + [f'trans_{i}' for i in range(len(meanings) * 2)]
        mock_translation_service.translate_batch.return_value = translations
        
        command = TranslateVocabularyCommand(word='test')
        result = use_case.execute(command)
        
        assert result.is_success
        assert len(result.value.meanings) == len(meanings)


class TestBatchTranslationProperties:
    """Property-based tests for batch translation."""
    
    @given(st.lists(definition_strategy, min_size=1, max_size=10))
    def test_batch_translation_completes_all_items(self, definitions, use_case, mock_dictionary_service, mock_translation_service):
        """Property: Batch translation translates all items."""
        meanings = [
            Meaning(
                part_of_speech='noun',
                definition=defn,
                example=f'example for {defn[:20]}'
            )
            for defn in definitions
        ]
        
        vocab = Vocabulary(
            word='test',
            translate_vi='',
            phonetic='test',
            meanings=meanings
        )
        mock_dictionary_service.get_word_definition.return_value = vocab
        
        # Mock translations - should have same count as items
        translations = [f'trans_{i}' for i in range(1 + len(meanings) * 2)]
        mock_translation_service.translate_batch.return_value = translations
        
        command = TranslateVocabularyCommand(word='test')
        result = use_case.execute(command)
        
        assert result.is_success
        # All meanings should have translations
        for meaning in result.value.meanings:
            assert meaning.definition_vi is not None
    
    @given(st.lists(definition_strategy, min_size=1, max_size=5))
    def test_batch_translation_preserves_order(self, definitions, use_case, mock_dictionary_service, mock_translation_service):
        """Property: Batch translation preserves order of items."""
        meanings = [
            Meaning(
                part_of_speech='noun',
                definition=defn,
                example=f'example {i}'
            )
            for i, defn in enumerate(definitions)
        ]
        
        vocab = Vocabulary(
            word='test',
            translate_vi='',
            phonetic='test',
            meanings=meanings
        )
        mock_dictionary_service.get_word_definition.return_value = vocab
        
        # Mock translations with identifiable values
        translations = [f'trans_{i}' for i in range(1 + len(meanings) * 2)]
        mock_translation_service.translate_batch.return_value = translations
        
        command = TranslateVocabularyCommand(word='test')
        result = use_case.execute(command)
        
        assert result.is_success
        # Verify order is preserved
        for i, meaning in enumerate(result.value.meanings):
            assert meaning.definition == definitions[i]


class TestGracefulDegradationProperties:
    """Property-based tests for graceful degradation."""
    
    @given(word_strategy)
    def test_translation_failure_returns_english_text(self, word, use_case, mock_dictionary_service, mock_translation_service):
        """Property: Translation failure returns English text as fallback."""
        vocab = Vocabulary(
            word=word,
            translate_vi='',
            phonetic='phonetic',
            meanings=[
                Meaning(
                    part_of_speech='noun',
                    definition='test definition',
                    example='test example'
                )
            ]
        )
        mock_dictionary_service.get_word_definition.return_value = vocab
        mock_translation_service.translate_batch.side_effect = Exception('Translation failed')
        
        command = TranslateVocabularyCommand(word=word)
        result = use_case.execute(command)
        
        # Should still succeed with English text
        assert result.is_success
        assert result.value.meanings[0].definition == 'test definition'
        assert result.value.meanings[0].example == 'test example'


class TestCachingIdempotenceProperties:
    """Property-based tests for caching idempotence."""
    
    @given(word_strategy)
    def test_repeated_translation_returns_same_result(self, word, use_case, mock_dictionary_service, mock_translation_service):
        """Property: Repeated translation of same word returns identical result."""
        vocab = Vocabulary(
            word=word,
            translate_vi='translation',
            phonetic='phonetic',
            meanings=[
                Meaning(
                    part_of_speech='noun',
                    definition='definition',
                    example='example'
                )
            ]
        )
        mock_dictionary_service.get_word_definition.return_value = vocab
        mock_translation_service.translate_batch.return_value = ['translation', 'def_trans', 'ex_trans']
        
        command = TranslateVocabularyCommand(word=word)
        result1 = use_case.execute(command)
        result2 = use_case.execute(command)
        
        assert result1.is_success
        assert result2.is_success
        assert result1.value.word == result2.value.word
        assert result1.value.translation_vi == result2.value.translation_vi


class TestBackwardCompatibilityProperties:
    """Property-based tests for backward compatibility."""
    
    @given(word_strategy)
    def test_response_has_word_and_translation_vi_fields(self, word, use_case, mock_dictionary_service, mock_translation_service):
        """Property: Response always has word and translation_vi fields for backward compatibility."""
        vocab = Vocabulary(
            word=word,
            translate_vi='',
            phonetic='phonetic',
            meanings=[]
        )
        mock_dictionary_service.get_word_definition.return_value = vocab
        mock_translation_service.translate_batch.return_value = ['translation']
        
        command = TranslateVocabularyCommand(word=word)
        result = use_case.execute(command)
        
        assert result.is_success
        response = result.value
        # Backward compatibility: must have these fields
        assert hasattr(response, 'word')
        assert hasattr(response, 'translation_vi')
        assert response.word == word


class TestErrorResponseProperties:
    """Property-based tests for error responses."""
    
    @given(word_strategy)
    def test_error_response_has_error_field(self, word, use_case, mock_dictionary_service):
        """Property: Error response always has error field."""
        from domain.exceptions.dictionary_exceptions import WordNotFoundError
        
        mock_dictionary_service.get_word_definition.side_effect = WordNotFoundError('Not found')
        
        command = TranslateVocabularyCommand(word=word)
        result = use_case.execute(command)
        
        assert not result.is_success
        assert result.error is not None


class TestPerformanceProperties:
    """Property-based tests for performance."""
    
    @given(st.lists(definition_strategy, min_size=1, max_size=10))
    def test_response_time_recorded(self, definitions, use_case, mock_dictionary_service, mock_translation_service):
        """Property: Response time is always recorded."""
        meanings = [
            Meaning(
                part_of_speech='noun',
                definition=defn,
                example='example'
            )
            for defn in definitions
        ]
        
        vocab = Vocabulary(
            word='test',
            translate_vi='',
            phonetic='test',
            meanings=meanings
        )
        mock_dictionary_service.get_word_definition.return_value = vocab
        translations = [f'trans_{i}' for i in range(1 + len(meanings) * 2)]
        mock_translation_service.translate_batch.return_value = translations
        
        command = TranslateVocabularyCommand(word='test')
        result = use_case.execute(command)
        
        assert result.is_success
        assert result.value.response_time_ms >= 0


class TestOptionalFieldsProperties:
    """Property-based tests for optional fields handling."""
    
    @given(word_strategy)
    def test_optional_fields_handled_correctly(self, word, use_case, mock_dictionary_service, mock_translation_service):
        """Property: Optional fields are handled correctly."""
        vocab = Vocabulary(
            word=word,
            translate_vi='',
            phonetic='',  # Optional
            audio_url=None,  # Optional
            meanings=[
                Meaning(
                    part_of_speech='noun',
                    definition='definition',
                    example=''  # Optional
                )
            ]
        )
        mock_dictionary_service.get_word_definition.return_value = vocab
        mock_translation_service.translate_batch.return_value = ['translation', 'def_trans']
        
        command = TranslateVocabularyCommand(word=word)
        result = use_case.execute(command)
        
        assert result.is_success
        response = result.value
        # Optional fields should be handled gracefully
        assert response.phonetic is not None
        assert response.meanings[0].example == ''
