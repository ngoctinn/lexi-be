"""Unit tests for DictionaryServiceAdapter."""

from pathlib import Path
import sys
from unittest.mock import Mock, patch, MagicMock
import json
import urllib.error

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from infrastructure.adapters.dictionary_service_adapter import DictionaryServiceAdapter
from domain.exceptions.dictionary_exceptions import (
    WordNotFoundError,
    DictionaryServiceError,
    DictionaryTimeoutError
)
from domain.entities.vocabulary import Vocabulary, Meaning


class TestDictionaryServiceAdapter:
    """Tests for DictionaryServiceAdapter."""

    @patch("infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen")
    def test_successful_response_parsing(self, mock_urlopen):
        """Test successful Dictionary API response parsing."""
        mock_response = Mock()
        mock_response.read.return_value = json.dumps([
            {
                "word": "hello",
                "phonetic": "/həˈloʊ/",
                "phonetics": [
                    {
                        "text": "/həˈloʊ/",
                        "audio": "https://api.dictionaryapi.dev/media/pronunciations/en/hello-us.mp3"
                    }
                ],
                "meanings": [
                    {
                        "partOfSpeech": "interjection",
                        "definitions": [
                            {
                                "definition": "used as a greeting",
                                "example": "Hello, how are you?"
                            }
                        ]
                    }
                ]
            }
        ]).encode('utf-8')
        mock_urlopen.return_value = mock_response
        
        adapter = DictionaryServiceAdapter()
        result = adapter.get_word_definition("hello")
        
        assert isinstance(result, Vocabulary)
        assert result.word == "hello"
        assert result.phonetic == "/həˈloʊ/"
        assert result.audio_url == "https://api.dictionaryapi.dev/media/pronunciations/en/hello-us.mp3"
        assert len(result.meanings) == 1
        assert result.meanings[0].part_of_speech == "interjection"
        assert result.meanings[0].definition == "used as a greeting"
        assert result.meanings[0].example == "Hello, how are you?"
        assert result.meanings[0].definition_vi == ""  # Not translated yet
        assert result.meanings[0].example_vi == ""  # Not translated yet

    @patch("infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen")
    def test_word_not_found_404(self, mock_urlopen):
        """Test handling of 404 (word not found)."""
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://api.dictionaryapi.dev/api/v2/entries/en/xyzabc",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None
        )
        
        adapter = DictionaryServiceAdapter()
        
        try:
            adapter.get_word_definition("xyzabc")
            assert False, "Should have raised WordNotFoundError"
        except WordNotFoundError as e:
            assert "not found" in str(e).lower()
            assert "xyzabc" in str(e)

    @patch("infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen")
    def test_server_error_5xx(self, mock_urlopen):
        """Test handling of 5xx server error."""
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://api.dictionaryapi.dev/api/v2/entries/en/hello",
            code=503,
            msg="Service Unavailable",
            hdrs={},
            fp=None
        )
        
        adapter = DictionaryServiceAdapter()
        
        try:
            adapter.get_word_definition("hello")
            assert False, "Should have raised DictionaryServiceError"
        except DictionaryServiceError as e:
            assert "503" in str(e) or "unavailable" in str(e).lower()

    @patch("infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen")
    def test_timeout_error(self, mock_urlopen):
        """Test handling of timeout."""
        mock_urlopen.side_effect = urllib.error.URLError(
            reason="timed out"
        )
        
        adapter = DictionaryServiceAdapter()
        
        try:
            adapter.get_word_definition("hello")
            assert False, "Should have raised DictionaryTimeoutError"
        except DictionaryTimeoutError as e:
            assert "timeout" in str(e).lower() or "timed out" in str(e).lower()

    @patch("infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen")
    def test_phrasal_verb_support(self, mock_urlopen):
        """Test support for phrasal verbs (multi-word expressions)."""
        mock_response = Mock()
        mock_response.read.return_value = json.dumps([
            {
                "word": "get off",
                "phonetic": "/ɡɛt ɔf/",
                "phonetics": [],
                "meanings": [
                    {
                        "partOfSpeech": "phrasal verb",
                        "definitions": [
                            {
                                "definition": "to leave a vehicle",
                                "example": "Get off the bus"
                            }
                        ]
                    }
                ]
            }
        ]).encode('utf-8')
        mock_urlopen.return_value = mock_response
        
        adapter = DictionaryServiceAdapter()
        result = adapter.get_word_definition("get off")
        
        assert result.word == "get off"
        assert result.meanings[0].part_of_speech == "phrasal verb"
        assert result.meanings[0].definition == "to leave a vehicle"

    @patch("infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen")
    def test_multiple_meanings_all_extracted(self, mock_urlopen):
        """Test extracting ALL meanings from API response."""
        mock_response = Mock()
        mock_response.read.return_value = json.dumps([
            {
                "word": "run",
                "phonetic": "/rʌn/",
                "phonetics": [],
                "meanings": [
                    {
                        "partOfSpeech": "verb",
                        "definitions": [
                            {"definition": "to move fast", "example": "I run every day"}
                        ]
                    },
                    {
                        "partOfSpeech": "noun",
                        "definitions": [
                            {"definition": "an act of running", "example": "a morning run"}
                        ]
                    },
                    {
                        "partOfSpeech": "adjective",
                        "definitions": [
                            {"definition": "flowing", "example": ""}
                        ]
                    }
                ]
            }
        ]).encode('utf-8')
        mock_urlopen.return_value = mock_response
        
        adapter = DictionaryServiceAdapter()
        result = adapter.get_word_definition("run")
        
        # Should extract ALL meanings (not limited to 3)
        assert len(result.meanings) == 3
        assert result.meanings[0].part_of_speech == "verb"
        assert result.meanings[1].part_of_speech == "noun"
        assert result.meanings[2].part_of_speech == "adjective"

    @patch("infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen")
    def test_first_definition_only_per_meaning(self, mock_urlopen):
        """Test extracting FIRST definition only per part of speech."""
        mock_response = Mock()
        mock_response.read.return_value = json.dumps([
            {
                "word": "run",
                "phonetic": "/rʌn/",
                "phonetics": [],
                "meanings": [
                    {
                        "partOfSpeech": "verb",
                        "definitions": [
                            {"definition": "to move fast", "example": "I run"},
                            {"definition": "to operate", "example": "The engine runs"},
                            {"definition": "to manage", "example": "She runs a business"}
                        ]
                    }
                ]
            }
        ]).encode('utf-8')
        mock_urlopen.return_value = mock_response
        
        adapter = DictionaryServiceAdapter()
        result = adapter.get_word_definition("run")
        
        # Should only extract FIRST definition
        assert len(result.meanings) == 1
        assert result.meanings[0].definition == "to move fast"
        assert result.meanings[0].example == "I run"

    @patch("infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen")
    def test_missing_example_handled(self, mock_urlopen):
        """Test handling of missing example in definition."""
        mock_response = Mock()
        mock_response.read.return_value = json.dumps([
            {
                "word": "hello",
                "phonetic": "/həˈloʊ/",
                "phonetics": [],
                "meanings": [
                    {
                        "partOfSpeech": "interjection",
                        "definitions": [
                            {
                                "definition": "used as a greeting"
                                # No example field
                            }
                        ]
                    }
                ]
            }
        ]).encode('utf-8')
        mock_urlopen.return_value = mock_response
        
        adapter = DictionaryServiceAdapter()
        result = adapter.get_word_definition("hello")
        
        assert result.meanings[0].example == ""

    @patch("infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen")
    def test_missing_audio_handled(self, mock_urlopen):
        """Test handling of missing audio URL."""
        mock_response = Mock()
        mock_response.read.return_value = json.dumps([
            {
                "word": "hello",
                "phonetic": "/həˈloʊ/",
                "phonetics": [
                    {"text": "/həˈloʊ/"}  # No audio field
                ],
                "meanings": [
                    {
                        "partOfSpeech": "interjection",
                        "definitions": [
                            {"definition": "used as a greeting"}
                        ]
                    }
                ]
            }
        ]).encode('utf-8')
        mock_urlopen.return_value = mock_response
        
        adapter = DictionaryServiceAdapter()
        result = adapter.get_word_definition("hello")
        
        assert result.audio_url is None

    @patch("infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen")
    def test_origin_field_extracted(self, mock_urlopen):
        """Test extraction of origin field if available."""
        mock_response = Mock()
        mock_response.read.return_value = json.dumps([
            {
                "word": "hello",
                "phonetic": "/həˈloʊ/",
                "phonetics": [],
                "origin": "early 19th century: variant of earlier hollo",
                "meanings": [
                    {
                        "partOfSpeech": "interjection",
                        "definitions": [
                            {"definition": "used as a greeting"}
                        ]
                    }
                ]
            }
        ]).encode('utf-8')
        mock_urlopen.return_value = mock_response
        
        adapter = DictionaryServiceAdapter()
        result = adapter.get_word_definition("hello")
        
        assert result.origin == "early 19th century: variant of earlier hollo"

    @patch("infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen")
    def test_url_encoding_for_special_characters(self, mock_urlopen):
        """Test URL encoding for words with spaces, hyphens, apostrophes."""
        mock_response = Mock()
        mock_response.read.return_value = json.dumps([
            {
                "word": "don't",
                "phonetic": "/doʊnt/",
                "phonetics": [],
                "meanings": [
                    {
                        "partOfSpeech": "contraction",
                        "definitions": [
                            {"definition": "do not"}
                        ]
                    }
                ]
            }
        ]).encode('utf-8')
        mock_urlopen.return_value = mock_response
        
        adapter = DictionaryServiceAdapter()
        result = adapter.get_word_definition("don't")
        
        assert result.word == "don't"
        
        # Verify URL was encoded
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        assert "don%27t" in request.full_url or "don't" in request.full_url

    @patch("infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen")
    def test_logging_on_success(self, mock_urlopen):
        """Test logging on successful API call."""
        mock_response = Mock()
        mock_response.read.return_value = json.dumps([
            {
                "word": "hello",
                "phonetic": "/həˈloʊ/",
                "phonetics": [],
                "meanings": [
                    {
                        "partOfSpeech": "interjection",
                        "definitions": [
                            {"definition": "used as a greeting"}
                        ]
                    }
                ]
            }
        ]).encode('utf-8')
        mock_urlopen.return_value = mock_response
        
        adapter = DictionaryServiceAdapter()
        
        with patch("infrastructure.adapters.dictionary_service_adapter.logger") as mock_logger:
            result = adapter.get_word_definition("hello")
            
            # Verify logging calls
            assert mock_logger.info.call_count >= 2
            # Check that word and response time are logged
            log_calls = [str(call) for call in mock_logger.info.call_args_list]
            assert any("hello" in str(call) for call in log_calls)
            assert any("response_time" in str(call) for call in log_calls)

    @patch("infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen")
    def test_logging_on_404(self, mock_urlopen):
        """Test logging on 404 error."""
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://api.dictionaryapi.dev/api/v2/entries/en/xyzabc",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None
        )
        
        adapter = DictionaryServiceAdapter()
        
        with patch("infrastructure.adapters.dictionary_service_adapter.logger") as mock_logger:
            try:
                adapter.get_word_definition("xyzabc")
            except WordNotFoundError:
                pass
            
            # Verify warning was logged
            assert mock_logger.warning.call_count >= 1
            log_call = str(mock_logger.warning.call_args_list[0])
            assert "404" in log_call or "xyzabc" in log_call


class TestCacheIntegration:
    """Tests for cache integration."""

    @patch("infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen")
    def test_cache_hit_returns_cached_data(self, mock_urlopen):
        """Test cache hit returns cached data without API call."""
        from infrastructure.services.cache_service import CacheService
        
        cache = CacheService()
        adapter = DictionaryServiceAdapter(cache_service=cache)
        
        # Pre-populate cache
        cached_vocab = {
            "word": "hello",
            "translate_vi": "",
            "phonetic": "/həˈloʊ/",
            "audio_url": "https://example.com/hello.mp3",
            "origin": None,
            "meanings": [
                {
                    "part_of_speech": "interjection",
                    "definition": "used as a greeting",
                    "definition_vi": "",
                    "example": "Hello!",
                    "example_vi": ""
                }
            ]
        }
        cache.set("vocabulary:definition:hello", cached_vocab)
        
        # Get word definition
        result = adapter.get_word_definition("hello")
        
        # Should return cached data
        assert result.word == "hello"
        assert result.phonetic == "/həˈloʊ/"
        
        # Should NOT call API
        assert mock_urlopen.call_count == 0

    @patch("infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen")
    def test_cache_miss_calls_api_and_caches(self, mock_urlopen):
        """Test cache miss calls API and caches result."""
        from infrastructure.services.cache_service import CacheService
        
        cache = CacheService()
        adapter = DictionaryServiceAdapter(cache_service=cache)
        
        # Mock API response
        mock_response = Mock()
        mock_response.read.return_value = json.dumps([
            {
                "word": "hello",
                "phonetic": "/həˈloʊ/",
                "phonetics": [],
                "meanings": [
                    {
                        "partOfSpeech": "interjection",
                        "definitions": [
                            {"definition": "used as a greeting"}
                        ]
                    }
                ]
            }
        ]).encode('utf-8')
        mock_urlopen.return_value = mock_response
        
        # Get word definition (cache miss)
        result = adapter.get_word_definition("hello")
        
        # Should call API
        assert mock_urlopen.call_count == 1
        
        # Should cache result
        cached = cache.get("vocabulary:definition:hello")
        assert cached is not None
        assert cached["word"] == "hello"
        
        # Second call should hit cache
        mock_urlopen.reset_mock()
        result2 = adapter.get_word_definition("hello")
        assert mock_urlopen.call_count == 0  # No API call

    @patch("infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen")
    def test_cache_failure_graceful_degradation(self, mock_urlopen):
        """Test graceful degradation when cache fails."""
        from infrastructure.services.cache_service import CacheService
        
        cache = CacheService()
        adapter = DictionaryServiceAdapter(cache_service=cache)
        
        # Mock cache.get to raise exception
        with patch.object(cache, 'get', side_effect=Exception("Cache error")):
            # Mock API response
            mock_response = Mock()
            mock_response.read.return_value = json.dumps([
                {
                    "word": "hello",
                    "phonetic": "/həˈloʊ/",
                    "phonetics": [],
                    "meanings": [
                        {
                            "partOfSpeech": "interjection",
                            "definitions": [
                                {"definition": "used as a greeting"}
                            ]
                        }
                    ]
                }
            ]).encode('utf-8')
            mock_urlopen.return_value = mock_response
            
            # Should still work despite cache failure
            result = adapter.get_word_definition("hello")
            assert result.word == "hello"

    @patch("infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen")
    def test_cache_storage_failure_graceful_degradation(self, mock_urlopen):
        """Test graceful degradation when cache storage fails."""
        from infrastructure.services.cache_service import CacheService
        
        cache = CacheService()
        adapter = DictionaryServiceAdapter(cache_service=cache)
        
        # Mock API response
        mock_response = Mock()
        mock_response.read.return_value = json.dumps([
            {
                "word": "hello",
                "phonetic": "/həˈloʊ/",
                "phonetics": [],
                "meanings": [
                    {
                        "partOfSpeech": "interjection",
                        "definitions": [
                            {"definition": "used as a greeting"}
                        ]
                    }
                ]
            }
        ]).encode('utf-8')
        mock_urlopen.return_value = mock_response
        
        # Mock cache.set to raise exception
        with patch.object(cache, 'set', side_effect=Exception("Cache error")):
            # Should still work despite cache storage failure
            result = adapter.get_word_definition("hello")
            assert result.word == "hello"

    @patch("infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen")
    def test_cache_key_format(self, mock_urlopen):
        """Test cache key format is vocabulary:definition:{word_lowercase}."""
        from infrastructure.services.cache_service import CacheService
        
        cache = CacheService()
        adapter = DictionaryServiceAdapter(cache_service=cache)
        
        # Mock API response
        mock_response = Mock()
        mock_response.read.return_value = json.dumps([
            {
                "word": "Hello",
                "phonetic": "/həˈloʊ/",
                "phonetics": [],
                "meanings": [
                    {
                        "partOfSpeech": "interjection",
                        "definitions": [
                            {"definition": "used as a greeting"}
                        ]
                    }
                ]
            }
        ]).encode('utf-8')
        mock_urlopen.return_value = mock_response
        
        # Get word definition with uppercase
        result = adapter.get_word_definition("Hello")
        
        # Cache key should be lowercase
        cached = cache.get("vocabulary:definition:hello")
        assert cached is not None
        
        # Uppercase key should not exist
        cached_upper = cache.get("vocabulary:definition:Hello")
        assert cached_upper is None

    @patch("infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen")
    def test_phrasal_verb_cache_key(self, mock_urlopen):
        """Test cache key for phrasal verbs."""
        from infrastructure.services.cache_service import CacheService
        
        cache = CacheService()
        adapter = DictionaryServiceAdapter(cache_service=cache)
        
        # Mock API response for "get off"
        mock_response = Mock()
        mock_response.read.return_value = json.dumps([
            {
                "word": "get off",
                "phonetic": "/ɡɛt ɒf/",
                "phonetics": [],
                "meanings": [
                    {
                        "partOfSpeech": "phrasal verb",
                        "definitions": [
                            {"definition": "to leave a vehicle"}
                        ]
                    }
                ]
            }
        ]).encode('utf-8')
        mock_urlopen.return_value = mock_response
        
        # Get phrasal verb definition
        result = adapter.get_word_definition("get off")
        
        # Cache key should include space
        cached = cache.get("vocabulary:definition:get off")
        assert cached is not None
        assert cached["word"] == "get off"


class TestRetryIntegration:
    """Tests for retry logic integration."""

    @patch("infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen")
    def test_retry_on_429_rate_limit(self, mock_urlopen):
        """Test retry on HTTP 429 (rate limit)."""
        from infrastructure.services.retry_service import RetryService
        
        # First call: 429, Second call: 429, Third call: success
        mock_response = Mock()
        mock_response.read.return_value = json.dumps([
            {
                "word": "hello",
                "phonetic": "/həˈloʊ/",
                "phonetics": [],
                "meanings": [
                    {
                        "partOfSpeech": "interjection",
                        "definitions": [
                            {"definition": "used as a greeting"}
                        ]
                    }
                ]
            }
        ]).encode('utf-8')
        
        mock_urlopen.side_effect = [
            urllib.error.HTTPError(
                url="https://api.dictionaryapi.dev/api/v2/entries/en/hello",
                code=429,
                msg="Too Many Requests",
                hdrs={},
                fp=None
            ),
            urllib.error.HTTPError(
                url="https://api.dictionaryapi.dev/api/v2/entries/en/hello",
                code=429,
                msg="Too Many Requests",
                hdrs={},
                fp=None
            ),
            mock_response
        ]
        
        retry_service = RetryService()
        adapter = DictionaryServiceAdapter(retry_service=retry_service)
        
        with patch("infrastructure.adapters.dictionary_service_adapter.logger") as mock_logger:
            result = adapter.get_word_definition("hello")
            
            # Should succeed after retries
            assert result.word == "hello"
            
            # Should have made 3 attempts
            assert mock_urlopen.call_count == 3
            
            # Should have logged retry attempts
            warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
            assert any("429" in str(call) for call in warning_calls)

    @patch("infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen")
    @patch("infrastructure.adapters.dictionary_service_adapter.time.sleep")
    def test_retry_with_exponential_backoff(self, mock_sleep, mock_urlopen):
        """Test exponential backoff delays (1s, 2s)."""
        from infrastructure.services.retry_service import RetryService
        
        # First call: 503, Second call: 503, Third call: success
        mock_response = Mock()
        mock_response.read.return_value = json.dumps([
            {
                "word": "hello",
                "phonetic": "/həˈloʊ/",
                "phonetics": [],
                "meanings": [
                    {
                        "partOfSpeech": "interjection",
                        "definitions": [
                            {"definition": "used as a greeting"}
                        ]
                    }
                ]
            }
        ]).encode('utf-8')
        
        mock_urlopen.side_effect = [
            urllib.error.HTTPError(
                url="https://api.dictionaryapi.dev/api/v2/entries/en/hello",
                code=503,
                msg="Service Unavailable",
                hdrs={},
                fp=None
            ),
            urllib.error.HTTPError(
                url="https://api.dictionaryapi.dev/api/v2/entries/en/hello",
                code=503,
                msg="Service Unavailable",
                hdrs={},
                fp=None
            ),
            mock_response
        ]
        
        retry_service = RetryService()
        adapter = DictionaryServiceAdapter(retry_service=retry_service)
        
        result = adapter.get_word_definition("hello")
        
        # Should succeed after retries
        assert result.word == "hello"
        
        # Should have slept with exponential backoff
        assert mock_sleep.call_count == 2
        assert mock_sleep.call_args_list[0][0][0] == 1  # First retry: 1s
        assert mock_sleep.call_args_list[1][0][0] == 2  # Second retry: 2s

    @patch("infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen")
    def test_retry_on_5xx_server_error(self, mock_urlopen):
        """Test retry on HTTP 5xx server errors."""
        from infrastructure.services.retry_service import RetryService
        
        # First call: 500, Second call: success
        mock_response = Mock()
        mock_response.read.return_value = json.dumps([
            {
                "word": "hello",
                "phonetic": "/həˈloʊ/",
                "phonetics": [],
                "meanings": [
                    {
                        "partOfSpeech": "interjection",
                        "definitions": [
                            {"definition": "used as a greeting"}
                        ]
                    }
                ]
            }
        ]).encode('utf-8')
        
        mock_urlopen.side_effect = [
            urllib.error.HTTPError(
                url="https://api.dictionaryapi.dev/api/v2/entries/en/hello",
                code=500,
                msg="Internal Server Error",
                hdrs={},
                fp=None
            ),
            mock_response
        ]
        
        retry_service = RetryService()
        adapter = DictionaryServiceAdapter(retry_service=retry_service)
        
        result = adapter.get_word_definition("hello")
        
        # Should succeed after retry
        assert result.word == "hello"
        assert mock_urlopen.call_count == 2

    @patch("infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen")
    def test_no_retry_on_404(self, mock_urlopen):
        """Test no retry on HTTP 404 (permanent error)."""
        from infrastructure.services.retry_service import RetryService
        
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://api.dictionaryapi.dev/api/v2/entries/en/xyzabc",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None
        )
        
        retry_service = RetryService()
        adapter = DictionaryServiceAdapter(retry_service=retry_service)
        
        try:
            adapter.get_word_definition("xyzabc")
            assert False, "Should have raised WordNotFoundError"
        except WordNotFoundError:
            pass
        
        # Should NOT retry on 404
        assert mock_urlopen.call_count == 1

    @patch("infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen")
    def test_no_retry_on_4xx_client_error(self, mock_urlopen):
        """Test no retry on HTTP 4xx client errors."""
        from infrastructure.services.retry_service import RetryService
        
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://api.dictionaryapi.dev/api/v2/entries/en/hello",
            code=400,
            msg="Bad Request",
            hdrs={},
            fp=None
        )
        
        retry_service = RetryService()
        adapter = DictionaryServiceAdapter(retry_service=retry_service)
        
        try:
            adapter.get_word_definition("hello")
            assert False, "Should have raised DictionaryServiceError"
        except DictionaryServiceError:
            pass
        
        # Should NOT retry on 4xx
        assert mock_urlopen.call_count == 1

    @patch("infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen")
    def test_max_retries_exhausted_raises_error(self, mock_urlopen):
        """Test error raised after max retries exhausted."""
        from infrastructure.services.retry_service import RetryService
        
        # All attempts fail with 503
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://api.dictionaryapi.dev/api/v2/entries/en/hello",
            code=503,
            msg="Service Unavailable",
            hdrs={},
            fp=None
        )
        
        retry_service = RetryService()
        adapter = DictionaryServiceAdapter(retry_service=retry_service)
        
        try:
            adapter.get_word_definition("hello")
            assert False, "Should have raised DictionaryServiceError"
        except DictionaryServiceError as e:
            assert "503" in str(e) or "unavailable" in str(e).lower()
        
        # Should have made 3 attempts (initial + 2 retries)
        assert mock_urlopen.call_count == 3

    @patch("infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen")
    def test_retry_logging(self, mock_urlopen):
        """Test logging of retry attempts."""
        from infrastructure.services.retry_service import RetryService
        
        # First call: 503, Second call: success
        mock_response = Mock()
        mock_response.read.return_value = json.dumps([
            {
                "word": "hello",
                "phonetic": "/həˈloʊ/",
                "phonetics": [],
                "meanings": [
                    {
                        "partOfSpeech": "interjection",
                        "definitions": [
                            {"definition": "used as a greeting"}
                        ]
                    }
                ]
            }
        ]).encode('utf-8')
        
        mock_urlopen.side_effect = [
            urllib.error.HTTPError(
                url="https://api.dictionaryapi.dev/api/v2/entries/en/hello",
                code=503,
                msg="Service Unavailable",
                hdrs={},
                fp=None
            ),
            mock_response
        ]
        
        retry_service = RetryService()
        adapter = DictionaryServiceAdapter(retry_service=retry_service)
        
        with patch("infrastructure.services.retry_service.logger") as mock_retry_logger:
            result = adapter.get_word_definition("hello")
            
            # Should log retry attempt
            warning_calls = [str(call) for call in mock_retry_logger.warning.call_args_list]
            assert len(warning_calls) >= 1
            assert any("retry" in str(call).lower() for call in warning_calls)

    @patch("infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen")
    def test_success_on_first_attempt_no_retry(self, mock_urlopen):
        """Test no retry when first attempt succeeds."""
        from infrastructure.services.retry_service import RetryService
        
        mock_response = Mock()
        mock_response.read.return_value = json.dumps([
            {
                "word": "hello",
                "phonetic": "/həˈloʊ/",
                "phonetics": [],
                "meanings": [
                    {
                        "partOfSpeech": "interjection",
                        "definitions": [
                            {"definition": "used as a greeting"}
                        ]
                    }
                ]
            }
        ]).encode('utf-8')
        mock_urlopen.return_value = mock_response
        
        retry_service = RetryService()
        adapter = DictionaryServiceAdapter(retry_service=retry_service)
        
        result = adapter.get_word_definition("hello")
        
        # Should succeed on first attempt
        assert result.word == "hello"
        assert mock_urlopen.call_count == 1
