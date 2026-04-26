"""Unit tests for DictionaryServiceAdapter."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from infrastructure.adapters.dictionary_service_adapter import DictionaryServiceAdapter
from domain.exceptions.dictionary_exceptions import WordNotFoundError, DictionaryServiceError
from domain.entities.vocabulary import Vocabulary


@pytest.fixture
def mock_cache_service():
    """Mock CacheService."""
    return Mock()


@pytest.fixture
def mock_retry_service():
    """Mock RetryService."""
    return Mock()


@pytest.fixture
def mock_logger():
    """Mock logger."""
    return Mock()


@pytest.fixture
def adapter(mock_cache_service, mock_retry_service, mock_logger):
    """Create DictionaryServiceAdapter with mocked dependencies."""
    return DictionaryServiceAdapter(
        cache_service=mock_cache_service,
        retry_service=mock_retry_service,
        logger=mock_logger
    )


class TestDictionaryServiceAdapterSuccess:
    """Test successful Dictionary API responses."""
    
    @patch('infrastructure.adapters.dictionary_service_adapter.requests.get')
    def test_successful_response_parsing(self, mock_get, adapter, mock_cache_service):
        """Test successful parsing of Dictionary API response."""
        mock_cache_service.get.return_value = None  # Cache miss
        
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
        
        result = adapter.get_word_definition('hello')
        
        assert result.word == 'hello'
        assert result.phonetic == 'həˈləʊ'
        assert len(result.meanings) == 1
        assert result.meanings[0].part_of_speech == 'exclamation'
        assert result.meanings[0].definition == 'used as a greeting'
    
    @patch('infrastructure.adapters.dictionary_service_adapter.requests.get')
    def test_multiple_meanings_parsed(self, mock_get, adapter, mock_cache_service):
        """Test parsing multiple meanings."""
        mock_cache_service.get.return_value = None
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'word': 'run',
            'phonetic': 'rʌn',
            'phonetics': [{'text': 'rʌn', 'audio': None}],
            'meanings': [
                {
                    'partOfSpeech': 'verb',
                    'definitions': [{'definition': 'to move quickly', 'example': 'I run fast'}]
                },
                {
                    'partOfSpeech': 'noun',
                    'definitions': [{'definition': 'an act of running', 'example': 'a morning run'}]
                }
            ]
        }
        mock_get.return_value = mock_response
        
        result = adapter.get_word_definition('run')
        
        assert len(result.meanings) == 2
        assert result.meanings[0].part_of_speech == 'verb'
        assert result.meanings[1].part_of_speech == 'noun'


class TestDictionaryServiceAdapterErrors:
    """Test error handling."""
    
    @patch('infrastructure.adapters.dictionary_service_adapter.requests.get')
    def test_word_not_found_404(self, mock_get, adapter, mock_cache_service):
        """Test handling of 404 (word not found)."""
        mock_cache_service.get.return_value = None
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        with pytest.raises(WordNotFoundError):
            adapter.get_word_definition('nonexistentword')
    
    @patch('infrastructure.adapters.dictionary_service_adapter.requests.get')
    def test_server_error_5xx(self, mock_get, adapter, mock_cache_service):
        """Test handling of 5xx (server error)."""
        mock_cache_service.get.return_value = None
        
        mock_response = Mock()
        mock_response.status_code = 503
        mock_get.return_value = mock_response
        
        with pytest.raises(DictionaryServiceError):
            adapter.get_word_definition('hello')
    
    @patch('infrastructure.adapters.dictionary_service_adapter.requests.get')
    def test_timeout_error(self, mock_get, adapter, mock_cache_service):
        """Test handling of timeout."""
        mock_cache_service.get.return_value = None
        mock_get.side_effect = TimeoutError('Request timeout')
        
        with pytest.raises(DictionaryServiceError):
            adapter.get_word_definition('hello')


class TestDictionaryServiceAdapterCaching:
    """Test caching integration."""
    
    def test_cache_hit_returns_cached_value(self, adapter, mock_cache_service):
        """Test that cache hit returns cached value without API call."""
        cached_vocab = Mock(spec=Vocabulary)
        mock_cache_service.get.return_value = cached_vocab
        
        result = adapter.get_word_definition('hello')
        
        assert result == cached_vocab
        # Verify cache was checked
        mock_cache_service.get.assert_called_once()
    
    @patch('infrastructure.adapters.dictionary_service_adapter.requests.get')
    def test_cache_miss_stores_result(self, mock_get, adapter, mock_cache_service):
        """Test that cache miss stores result in cache."""
        mock_cache_service.get.return_value = None
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'word': 'hello',
            'phonetic': 'həˈləʊ',
            'phonetics': [{'text': 'həˈləʊ', 'audio': None}],
            'meanings': [
                {
                    'partOfSpeech': 'exclamation',
                    'definitions': [{'definition': 'used as a greeting'}]
                }
            ]
        }
        mock_get.return_value = mock_response
        
        result = adapter.get_word_definition('hello')
        
        # Verify cache.set was called
        mock_cache_service.set.assert_called_once()
        call_args = mock_cache_service.set.call_args
        assert 'hello' in call_args[0][0]  # Cache key contains word
    
    @patch('infrastructure.adapters.dictionary_service_adapter.requests.get')
    def test_cache_failure_graceful_degradation(self, mock_get, adapter, mock_cache_service):
        """Test graceful degradation when cache fails."""
        mock_cache_service.get.return_value = None
        mock_cache_service.set.side_effect = Exception('Cache error')
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'word': 'hello',
            'phonetic': 'həˈləʊ',
            'phonetics': [{'text': 'həˈləʊ', 'audio': None}],
            'meanings': [
                {
                    'partOfSpeech': 'exclamation',
                    'definitions': [{'definition': 'used as a greeting'}]
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Should not raise exception
        result = adapter.get_word_definition('hello')
        assert result.word == 'hello'


class TestDictionaryServiceAdapterRetry:
    """Test retry logic integration."""
    
    @patch('infrastructure.adapters.dictionary_service_adapter.requests.get')
    def test_retry_on_transient_error(self, mock_get, adapter, mock_cache_service, mock_retry_service):
        """Test that retry service is used for transient errors."""
        mock_cache_service.get.return_value = None
        
        # Configure retry service to call the function
        def retry_side_effect(func, *args, **kwargs):
            return func()
        
        mock_retry_service.execute_with_retry.side_effect = retry_side_effect
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'word': 'hello',
            'phonetic': 'həˈləʊ',
            'phonetics': [{'text': 'həˈləʊ', 'audio': None}],
            'meanings': [
                {
                    'partOfSpeech': 'exclamation',
                    'definitions': [{'definition': 'used as a greeting'}]
                }
            ]
        }
        mock_get.return_value = mock_response
        
        result = adapter.get_word_definition('hello')
        
        # Verify retry service was called
        mock_retry_service.execute_with_retry.assert_called_once()


class TestDictionaryServiceAdapterLogging:
    """Test logging functionality."""
    
    @patch('infrastructure.adapters.dictionary_service_adapter.requests.get')
    def test_logs_api_call(self, mock_get, adapter, mock_cache_service, mock_logger):
        """Test that API calls are logged."""
        mock_cache_service.get.return_value = None
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'word': 'hello',
            'phonetic': 'həˈləʊ',
            'phonetics': [{'text': 'həˈləʊ', 'audio': None}],
            'meanings': [
                {
                    'partOfSpeech': 'exclamation',
                    'definitions': [{'definition': 'used as a greeting'}]
                }
            ]
        }
        mock_get.return_value = mock_response
        
        adapter.get_word_definition('hello')
        
        # Verify logging was called
        assert mock_logger.info.called or mock_logger.debug.called
    
    @patch('infrastructure.adapters.dictionary_service_adapter.requests.get')
    def test_logs_error_on_failure(self, mock_get, adapter, mock_cache_service, mock_logger):
        """Test that errors are logged."""
        mock_cache_service.get.return_value = None
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        with pytest.raises(WordNotFoundError):
            adapter.get_word_definition('nonexistent')
        
        # Verify error logging was called
        assert mock_logger.warning.called or mock_logger.error.called


class TestDictionaryServiceAdapterPhrasalVerbs:
    """Test phrasal verb support."""
    
    @patch('infrastructure.adapters.dictionary_service_adapter.requests.get')
    def test_phrasal_verb_with_context(self, mock_get, adapter, mock_cache_service):
        """Test phrasal verb detection with context."""
        mock_cache_service.get.return_value = None
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'word': 'get off',
            'phonetic': 'ɡet ɔːf',
            'phonetics': [{'text': 'ɡet ɔːf', 'audio': None}],
            'meanings': [
                {
                    'partOfSpeech': 'phrasal verb',
                    'definitions': [{'definition': 'to leave or exit', 'example': 'I got off the bus'}]
                }
            ]
        }
        mock_get.return_value = mock_response
        
        result = adapter.get_word_definition('off', context='I got off the bus')
        
        assert result.word == 'get off'
        assert result.meanings[0].part_of_speech == 'phrasal verb'
