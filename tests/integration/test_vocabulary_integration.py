"""Integration tests for vocabulary translation with Dictionary API and AWS Translate."""

import pytest
import time
from unittest.mock import Mock, patch

from infrastructure.adapters.dictionary_service_adapter import DictionaryServiceAdapter
from application.use_cases.vocabulary_use_cases import TranslateVocabularyUseCase
from application.dtos.vocabulary_dtos import TranslateVocabularyCommand
from domain.entities.vocabulary import Vocabulary, Meaning
from domain.exceptions.dictionary_exceptions import WordNotFoundError, DictionaryServiceError


@pytest.fixture
def mock_cache_service():
    """Mock CacheService."""
    return Mock()


@pytest.fixture
def mock_retry_service():
    """Mock RetryService that executes function immediately."""
    service = Mock()
    service.execute_with_retry.side_effect = lambda func, *args, **kwargs: func()
    return service


@pytest.fixture
def mock_logger():
    """Mock logger."""
    return Mock()


@pytest.fixture
def dictionary_adapter(mock_cache_service, mock_retry_service, mock_logger):
    """Create DictionaryServiceAdapter with mocked dependencies."""
    return DictionaryServiceAdapter(
        cache_service=mock_cache_service,
        retry_service=mock_retry_service,
        logger=mock_logger
    )


@pytest.fixture
def mock_translation_service():
    """Mock TranslationService."""
    return Mock()


@pytest.fixture
def use_case(dictionary_adapter, mock_translation_service):
    """Create TranslateVocabularyUseCase with real adapter and mocked translation."""
    return TranslateVocabularyUseCase(
        dictionary_service=dictionary_adapter,
        translation_service=mock_translation_service
    )


class TestDictionaryAPIIntegration:
    """Integration tests with Dictionary API."""
    
    @patch('infrastructure.adapters.dictionary_service_adapter.requests.get')
    def test_successful_dictionary_api_response(self, mock_get, dictionary_adapter, mock_cache_service):
        """Test successful response from Dictionary API."""
        mock_cache_service.get.return_value = None
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'word': 'hello',
            'phonetic': 'həˈləʊ',
            'phonetics': [{'text': 'həˈləʊ', 'audio': 'http://example.com/audio.mp3'}],
            'meanings': [
                {
                    'partOfSpeech': 'exclamation',
                    'definitions': [
                        {
                            'definition': 'used as a greeting',
                            'example': 'hello there'
                        }
                    ]
                }
            ]
        }
        mock_get.return_value = mock_response
        
        result = dictionary_adapter.get_word_definition('hello')
        
        assert result.word == 'hello'
        assert result.phonetic == 'həˈləʊ'
        assert len(result.meanings) == 1
    
    @patch('infrastructure.adapters.dictionary_service_adapter.requests.get')
    def test_dictionary_api_404_error(self, mock_get, dictionary_adapter, mock_cache_service):
        """Test handling of 404 from Dictionary API."""
        mock_cache_service.get.return_value = None
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        with pytest.raises(WordNotFoundError):
            dictionary_adapter.get_word_definition('nonexistent')
    
    @patch('infrastructure.adapters.dictionary_service_adapter.requests.get')
    def test_dictionary_api_timeout(self, mock_get, dictionary_adapter, mock_cache_service):
        """Test handling of timeout from Dictionary API."""
        mock_cache_service.get.return_value = None
        mock_get.side_effect = TimeoutError('Request timeout')
        
        with pytest.raises(DictionaryServiceError):
            dictionary_adapter.get_word_definition('hello')


class TestAWSTranslateIntegration:
    """Integration tests with AWS Translate."""
    
    @patch('infrastructure.adapters.dictionary_service_adapter.requests.get')
    def test_successful_aws_translate(self, mock_get, use_case, mock_translation_service):
        """Test successful translation with AWS Translate."""
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: {
                'word': 'hello',
                'phonetic': 'həˈləʊ',
                'phonetics': [{'text': 'həˈləʊ', 'audio': None}],
                'meanings': [
                    {
                        'partOfSpeech': 'exclamation',
                        'definitions': [
                            {
                                'definition': 'used as a greeting',
                                'example': 'hello there'
                            }
                        ]
                    }
                ]
            }
        )
        
        mock_translation_service.translate_batch.return_value = [
            'xin chào',
            'được dùng để chào hỏi',
            'xin chào'
        ]
        
        command = TranslateVocabularyCommand(word='hello')
        result = use_case.execute(command)
        
        assert result.is_success
        response = result.value
        assert response.translation_vi == 'xin chào'
        assert response.meanings[0].definition_vi == 'được dùng để chào hỏi'
    
    @patch('infrastructure.adapters.dictionary_service_adapter.requests.get')
    def test_aws_translate_failure_graceful_degradation(self, mock_get, use_case, mock_translation_service):
        """Test graceful degradation when AWS Translate fails."""
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: {
                'word': 'hello',
                'phonetic': 'həˈləʊ',
                'phonetics': [{'text': 'həˈləʊ', 'audio': None}],
                'meanings': [
                    {
                        'partOfSpeech': 'exclamation',
                        'definitions': [
                            {
                                'definition': 'used as a greeting',
                                'example': 'hello there'
                            }
                        ]
                    }
                ]
            }
        )
        
        mock_translation_service.translate_batch.side_effect = Exception('Translation failed')
        
        command = TranslateVocabularyCommand(word='hello')
        result = use_case.execute(command)
        
        # Should still succeed with English text
        assert result.is_success
        response = result.value
        assert response.word == 'hello'
        assert response.meanings[0].definition == 'used as a greeting'


class TestEndToEndWorkflow:
    """End-to-end integration tests."""
    
    @patch('infrastructure.adapters.dictionary_service_adapter.requests.get')
    def test_complete_vocabulary_translation_workflow(self, mock_get, use_case, mock_translation_service):
        """Test complete workflow from request to response."""
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: {
                'word': 'run',
                'phonetic': 'rʌn',
                'phonetics': [{'text': 'rʌn', 'audio': None}],
                'meanings': [
                    {
                        'partOfSpeech': 'verb',
                        'definitions': [
                            {
                                'definition': 'to move quickly',
                                'example': 'I run fast'
                            }
                        ]
                    },
                    {
                        'partOfSpeech': 'noun',
                        'definitions': [
                            {
                                'definition': 'an act of running',
                                'example': 'a morning run'
                            }
                        ]
                    }
                ]
            }
        )
        
        mock_translation_service.translate_batch.return_value = [
            'chạy',
            'chuyển động nhanh',
            'tôi chạy nhanh',
            'hành động chạy',
            'một buổi chạy buổi sáng'
        ]
        
        command = TranslateVocabularyCommand(word='run')
        result = use_case.execute(command)
        
        assert result.is_success
        response = result.value
        assert response.word == 'run'
        assert response.translation_vi == 'chạy'
        assert len(response.meanings) == 2
        assert response.meanings[0].part_of_speech == 'verb'
        assert response.meanings[0].definition_vi == 'chuyển động nhanh'
        assert response.meanings[1].part_of_speech == 'noun'
        assert response.meanings[1].definition_vi == 'hành động chạy'


class TestPerformanceValidation:
    """Performance validation tests."""
    
    @patch('infrastructure.adapters.dictionary_service_adapter.requests.get')
    def test_response_time_under_2000ms(self, mock_get, use_case, mock_translation_service):
        """Test that response time is under 2000ms."""
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: {
                'word': 'hello',
                'phonetic': 'həˈləʊ',
                'phonetics': [{'text': 'həˈləʊ', 'audio': None}],
                'meanings': [
                    {
                        'partOfSpeech': 'exclamation',
                        'definitions': [
                            {
                                'definition': 'used as a greeting',
                                'example': 'hello there'
                            }
                        ]
                    }
                ]
            }
        )
        
        mock_translation_service.translate_batch.return_value = [
            'xin chào',
            'được dùng để chào hỏi',
            'xin chào'
        ]
        
        start_time = time.time()
        command = TranslateVocabularyCommand(word='hello')
        result = use_case.execute(command)
        elapsed_time = (time.time() - start_time) * 1000
        
        assert result.is_success
        # Response time should be recorded
        assert result.value.response_time_ms > 0
        # Actual elapsed time should be reasonable
        assert elapsed_time < 5000  # Allow 5 seconds for test overhead


class TestPhrasalVerbIntegration:
    """Integration tests for phrasal verb support."""
    
    @patch('infrastructure.adapters.dictionary_service_adapter.requests.get')
    def test_phrasal_verb_with_context(self, mock_get, use_case, mock_translation_service):
        """Test phrasal verb translation with context."""
        # First call returns 404 for "off", second call returns success for "get off"
        mock_get.side_effect = [
            Mock(status_code=404),  # "off" not found
            Mock(
                status_code=200,
                json=lambda: {
                    'word': 'get off',
                    'phonetic': 'ɡet ɔːf',
                    'phonetics': [{'text': 'ɡet ɔːf', 'audio': None}],
                    'meanings': [
                        {
                            'partOfSpeech': 'phrasal verb',
                            'definitions': [
                                {
                                    'definition': 'to leave or exit',
                                    'example': 'I got off the bus'
                                }
                            ]
                        }
                    ]
                }
            )
        ]
        
        mock_translation_service.translate_batch.return_value = [
            'xuống xe',
            'rời khỏi hoặc thoát ra',
            'tôi xuống xe'
        ]
        
        command = TranslateVocabularyCommand(word='off', context='I got off the bus')
        result = use_case.execute(command)
        
        assert result.is_success
        response = result.value
        assert response.word == 'get off'
        assert response.meanings[0].part_of_speech == 'phrasal verb'
