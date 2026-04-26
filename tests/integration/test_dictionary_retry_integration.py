"""Integration tests for DictionaryServiceAdapter with RetryService."""

from pathlib import Path
import sys
from unittest.mock import Mock, patch
import json
import urllib.error

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from infrastructure.adapters.dictionary_service_adapter import DictionaryServiceAdapter
from infrastructure.services.retry_service import RetryService
from infrastructure.services.cache_service import CacheService
from domain.exceptions.dictionary_exceptions import (
    WordNotFoundError,
    DictionaryServiceError
)


class TestDictionaryRetryIntegration:
    """Integration tests for retry logic with cache."""

    @patch("infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen")
    @patch("infrastructure.adapters.dictionary_service_adapter.time.sleep")
    def test_retry_with_cache_and_eventual_success(self, mock_sleep, mock_urlopen):
        """Test complete flow: cache miss, retry on 503, eventual success, cache storage."""
        cache = CacheService()
        retry = RetryService()
        adapter = DictionaryServiceAdapter(cache_service=cache, retry_service=retry)
        
        # Mock API response
        mock_response = Mock()
        mock_response.read.return_value = json.dumps([
            {
                "word": "hello",
                "phonetic": "/həˈloʊ/",
                "phonetics": [
                    {
                        "text": "/həˈloʊ/",
                        "audio": "https://example.com/hello.mp3"
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
        
        # First call: 503, Second call: success
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
        
        # First request: cache miss, retry, success
        result = adapter.get_word_definition("hello")
        
        assert result.word == "hello"
        assert result.phonetic == "/həˈloʊ/"
        assert result.audio_url == "https://example.com/hello.mp3"
        assert len(result.meanings) == 1
        
        # Should have retried once
        assert mock_urlopen.call_count == 2
        assert mock_sleep.call_count == 1
        assert mock_sleep.call_args_list[0][0][0] == 1  # 1s backoff
        
        # Should be cached now
        cached = cache.get("vocabulary:definition:hello")
        assert cached is not None
        assert cached["word"] == "hello"
        
        # Second request: cache hit, no API call
        mock_urlopen.reset_mock()
        result2 = adapter.get_word_definition("hello")
        
        assert result2.word == "hello"
        assert mock_urlopen.call_count == 0  # No API call

    @patch("infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen")
    def test_retry_exhausted_with_cache_miss(self, mock_urlopen):
        """Test retry exhaustion doesn't cache failed result."""
        cache = CacheService()
        retry = RetryService()
        adapter = DictionaryServiceAdapter(cache_service=cache, retry_service=retry)
        
        # All attempts fail with 503
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://api.dictionaryapi.dev/api/v2/entries/en/hello",
            code=503,
            msg="Service Unavailable",
            hdrs={},
            fp=None
        )
        
        try:
            adapter.get_word_definition("hello")
            assert False, "Should have raised DictionaryServiceError"
        except DictionaryServiceError:
            pass
        
        # Should have made 3 attempts (initial + 2 retries)
        assert mock_urlopen.call_count == 3
        
        # Should NOT cache failed result
        cached = cache.get("vocabulary:definition:hello")
        assert cached is None

    @patch("infrastructure.adapters.dictionary_service_adapter.urllib.request.urlopen")
    def test_no_retry_on_404_with_cache(self, mock_urlopen):
        """Test 404 doesn't retry and doesn't cache."""
        cache = CacheService()
        retry = RetryService()
        adapter = DictionaryServiceAdapter(cache_service=cache, retry_service=retry)
        
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://api.dictionaryapi.dev/api/v2/entries/en/xyzabc",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None
        )
        
        try:
            adapter.get_word_definition("xyzabc")
            assert False, "Should have raised WordNotFoundError"
        except WordNotFoundError:
            pass
        
        # Should NOT retry on 404
        assert mock_urlopen.call_count == 1
        
        # Should NOT cache 404 result
        cached = cache.get("vocabulary:definition:xyzabc")
        assert cached is None
