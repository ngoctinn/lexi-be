"""Unit tests for TranslateVocabularyUseCase."""

import pytest
from unittest.mock import Mock

from application.use_cases.vocabulary_use_cases import TranslateVocabularyUseCase
from application.dtos.vocabulary_dtos import TranslateVocabularyCommand
from domain.entities.vocabulary import Vocabulary, Meaning
from domain.exceptions.dictionary_exceptions import WordNotFoundError, DictionaryServiceError


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


class TestTranslateVocabularyUseCaseSuccess:
    """Test successful vocabulary translation."""
    
    def test_successful_translation_workflow(self, use_case, mock_dictionary_service, mock_translation_service):
        """Test successful end-to-end translation workflow."""
        # Setup mock dictionary service
        vocab = Vocabulary(
            word='hello',
            translate_vi='',  # Will be filled by translation service
            phonetic='həˈləʊ',
            audio_url='http://example.com/audio.mp3',
            meanings=[
                Meaning(
                    part_of_speech='exclamation',
                    definition='used as a greeting',
                    definition_vi='',
                    example='hello there',
                    example_vi=''
                )
            ]
        )
        mock_dictionary_service.get_word_definition.return_value = vocab
        
        # Setup mock translation service
        mock_translation_service.translate_batch.return_value = [
            'xin chào',  # word translation
            'được dùng để chào hỏi',  # definition translation
            'xin chào'  # example translation
        ]
        
        # Execute
        command = TranslateVocabularyCommand(word='hello')
        result = use_case.execute(command)
        
        # Verify
        assert result.is_success
        response = result.value
        assert response.word == 'hello'
        assert response.translation_vi == 'xin chào'
        assert response.phonetic == 'həˈləʊ'
        assert len(response.meanings) == 1
        assert response.meanings[0].definition_vi == 'được dùng để chào hỏi'
        assert response.meanings[0].example_vi == 'xin chào'
    
    def test_multiple_meanings_translated(self, use_case, mock_dictionary_service, mock_translation_service):
        """Test translation of multiple meanings."""
        vocab = Vocabulary(
            word='run',
            translate_vi='',
            phonetic='rʌn',
            meanings=[
                Meaning(
                    part_of_speech='verb',
                    definition='to move quickly',
                    example='I run fast'
                ),
                Meaning(
                    part_of_speech='noun',
                    definition='an act of running',
                    example='a morning run'
                )
            ]
        )
        mock_dictionary_service.get_word_definition.return_value = vocab
        
        mock_translation_service.translate_batch.return_value = [
            'chạy',  # word
            'chuyển động nhanh',  # meaning 1 definition
            'tôi chạy nhanh',  # meaning 1 example
            'hành động chạy',  # meaning 2 definition
            'một buổi chạy buổi sáng'  # meaning 2 example
        ]
        
        command = TranslateVocabularyCommand(word='run')
        result = use_case.execute(command)
        
        assert result.is_success
        response = result.value
        assert len(response.meanings) == 2
        assert response.meanings[0].definition_vi == 'chuyển động nhanh'
        assert response.meanings[1].definition_vi == 'hành động chạy'
    
    def test_meaning_without_example(self, use_case, mock_dictionary_service, mock_translation_service):
        """Test translation of meaning without example."""
        vocab = Vocabulary(
            word='hello',
            translate_vi='',
            phonetic='həˈləʊ',
            meanings=[
                Meaning(
                    part_of_speech='exclamation',
                    definition='used as a greeting',
                    example=''  # No example
                )
            ]
        )
        mock_dictionary_service.get_word_definition.return_value = vocab
        
        mock_translation_service.translate_batch.return_value = [
            'xin chào',  # word
            'được dùng để chào hỏi'  # definition
        ]
        
        command = TranslateVocabularyCommand(word='hello')
        result = use_case.execute(command)
        
        assert result.is_success
        response = result.value
        assert response.meanings[0].example == ''
        assert response.meanings[0].example_vi == ''


class TestTranslateVocabularyUseCaseErrors:
    """Test error handling."""
    
    def test_word_not_found_error(self, use_case, mock_dictionary_service):
        """Test handling of word not found error."""
        mock_dictionary_service.get_word_definition.side_effect = WordNotFoundError('Word not found')
        
        command = TranslateVocabularyCommand(word='nonexistent')
        result = use_case.execute(command)
        
        assert not result.is_success
        assert isinstance(result.error, WordNotFoundError)
    
    def test_dictionary_service_error(self, use_case, mock_dictionary_service):
        """Test handling of dictionary service error."""
        mock_dictionary_service.get_word_definition.side_effect = DictionaryServiceError('Service unavailable')
        
        command = TranslateVocabularyCommand(word='hello')
        result = use_case.execute(command)
        
        assert not result.is_success
        assert isinstance(result.error, DictionaryServiceError)
    
    def test_translation_failure_graceful_degradation(self, use_case, mock_dictionary_service, mock_translation_service):
        """Test graceful degradation when translation fails."""
        vocab = Vocabulary(
            word='hello',
            translate_vi='',
            phonetic='həˈləʊ',
            meanings=[
                Meaning(
                    part_of_speech='exclamation',
                    definition='used as a greeting',
                    example='hello there'
                )
            ]
        )
        mock_dictionary_service.get_word_definition.return_value = vocab
        
        # Translation service fails
        mock_translation_service.translate_batch.side_effect = Exception('Translation failed')
        
        command = TranslateVocabularyCommand(word='hello')
        result = use_case.execute(command)
        
        # Should still succeed with English text
        assert result.is_success
        response = result.value
        assert response.word == 'hello'
        # Translations should be empty (fallback to original)
        assert response.meanings[0].definition_vi == 'used as a greeting'


class TestTranslateVocabularyUseCaseBatchTranslation:
    """Test batch translation logic."""
    
    def test_batch_translation_single_call(self, use_case, mock_dictionary_service, mock_translation_service):
        """Test that all items are translated in single batch call."""
        vocab = Vocabulary(
            word='hello',
            translate_vi='',
            phonetic='həˈləʊ',
            meanings=[
                Meaning(
                    part_of_speech='exclamation',
                    definition='used as a greeting',
                    example='hello there'
                ),
                Meaning(
                    part_of_speech='noun',
                    definition='a greeting',
                    example='say hello'
                )
            ]
        )
        mock_dictionary_service.get_word_definition.return_value = vocab
        mock_translation_service.translate_batch.return_value = [
            'xin chào',
            'được dùng để chào hỏi',
            'xin chào',
            'một lời chào',
            'nói xin chào'
        ]
        
        command = TranslateVocabularyCommand(word='hello')
        result = use_case.execute(command)
        
        # Verify translate_batch was called once with all items
        mock_translation_service.translate_batch.assert_called_once()
        call_args = mock_translation_service.translate_batch.call_args
        items = call_args[0][0]
        
        # Should have: word + 2 definitions + 2 examples = 5 items
        assert len(items) == 5
        assert items[0] == 'hello'  # word
        assert items[1] == 'used as a greeting'  # definition 1
        assert items[2] == 'hello there'  # example 1
        assert items[3] == 'a greeting'  # definition 2
        assert items[4] == 'say hello'  # example 2
    
    def test_batch_translation_mapping(self, use_case, mock_dictionary_service, mock_translation_service):
        """Test that translations are correctly mapped back to meanings."""
        vocab = Vocabulary(
            word='test',
            translate_vi='',
            phonetic='test',
            meanings=[
                Meaning(
                    part_of_speech='verb',
                    definition='to check',
                    example='test the code'
                )
            ]
        )
        mock_dictionary_service.get_word_definition.return_value = vocab
        
        mock_translation_service.translate_batch.return_value = [
            'kiểm tra',  # word
            'để kiểm tra',  # definition
            'kiểm tra mã'  # example
        ]
        
        command = TranslateVocabularyCommand(word='test')
        result = use_case.execute(command)
        
        assert result.is_success
        response = result.value
        assert response.translation_vi == 'kiểm tra'
        assert response.meanings[0].definition_vi == 'để kiểm tra'
        assert response.meanings[0].example_vi == 'kiểm tra mã'


class TestTranslateVocabularyUseCaseContext:
    """Test context parameter for phrasal verbs."""
    
    def test_context_passed_to_dictionary_service(self, use_case, mock_dictionary_service, mock_translation_service):
        """Test that context is passed to dictionary service."""
        vocab = Vocabulary(
            word='get off',
            translate_vi='',
            phonetic='ɡet ɔːf',
            meanings=[
                Meaning(
                    part_of_speech='phrasal verb',
                    definition='to leave or exit',
                    example='I got off the bus'
                )
            ]
        )
        mock_dictionary_service.get_word_definition.return_value = vocab
        mock_translation_service.translate_batch.return_value = ['xuống xe', 'rời khỏi hoặc thoát ra', 'tôi xuống xe']
        
        command = TranslateVocabularyCommand(word='off', context='I got off the bus')
        result = use_case.execute(command)
        
        # Verify context was passed
        mock_dictionary_service.get_word_definition.assert_called_once_with(
            word='off',
            context='I got off the bus'
        )


class TestTranslateVocabularyUseCaseLogging:
    """Test logging functionality."""
    
    def test_logs_translation_start(self, use_case, mock_dictionary_service, mock_translation_service, caplog):
        """Test that translation start is logged."""
        vocab = Vocabulary(
            word='hello',
            translate_vi='',
            phonetic='həˈləʊ',
            meanings=[]
        )
        mock_dictionary_service.get_word_definition.return_value = vocab
        mock_translation_service.translate_batch.return_value = ['xin chào']
        
        command = TranslateVocabularyCommand(word='hello')
        result = use_case.execute(command)
        
        # Check that translation was logged
        assert any('translat' in record.message.lower() for record in caplog.records)
    
    def test_logs_response_time(self, use_case, mock_dictionary_service, mock_translation_service, caplog):
        """Test that response time is logged."""
        vocab = Vocabulary(
            word='hello',
            translate_vi='',
            phonetic='həˈləʊ',
            meanings=[]
        )
        mock_dictionary_service.get_word_definition.return_value = vocab
        mock_translation_service.translate_batch.return_value = ['xin chào']
        
        command = TranslateVocabularyCommand(word='hello')
        result = use_case.execute(command)
        
        assert result.is_success
        response = result.value
        assert response.response_time_ms > 0
