"""Unit tests for CacheService."""

from pathlib import Path
import sys
import time
from unittest.mock import Mock, patch, MagicMock

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from infrastructure.services.cache_service import CacheService


class TestCacheService:
    """Tests for CacheService."""

    def test_cache_hit_in_memory(self):
        """Test cache hit from in-memory cache."""
        cache = CacheService()
        test_value = {"word": "hello", "phonetic": "/həˈloʊ/"}
        
        cache.set("vocabulary:definition:hello", test_value)
        result = cache.get("vocabulary:definition:hello")
        
        assert result == test_value

    def test_cache_miss(self):
        """Test cache miss returns None."""
        cache = CacheService()
        result = cache.get("vocabulary:definition:nonexistent")
        
        assert result is None

    def test_cache_expiration(self):
        """Test cache expiration after TTL."""
        cache = CacheService()
        test_value = {"word": "hello"}
        
        # Set with 1 second TTL
        cache.set("vocabulary:definition:hello", test_value, ttl_seconds=1)
        
        # Should be available immediately
        assert cache.get("vocabulary:definition:hello") == test_value
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired
        assert cache.get("vocabulary:definition:hello") is None

    def test_cache_clear(self):
        """Test clearing in-memory cache."""
        cache = CacheService()
        test_value = {"word": "hello"}
        
        cache.set("vocabulary:definition:hello", test_value)
        assert cache.get("vocabulary:definition:hello") == test_value
        
        cache.clear()
        assert cache.get("vocabulary:definition:hello") is None

    @patch("infrastructure.services.cache_service._get_dynamodb_client")
    def test_dynamodb_fallback_on_cache_miss(self, mock_get_client):
        """Test DynamoDB fallback when in-memory cache misses."""
        cache = CacheService()
        test_value = {"word": "hello", "phonetic": "/həˈloʊ/"}
        
        # Mock DynamoDB response
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        import json
        mock_client.get_item.return_value = {
            "Item": {
                "cache_key": {"S": "vocabulary:definition:hello"},
                "definition_json": {"S": json.dumps(test_value)},
                "ttl": {"N": str(int(time.time()) + 86400)}
            }
        }
        
        result = cache.get("vocabulary:definition:hello")
        
        assert result == test_value
        mock_client.get_item.assert_called_once()

    @patch("infrastructure.services.cache_service._get_dynamodb_client")
    def test_dynamodb_storage(self, mock_get_client):
        """Test storing value in DynamoDB."""
        cache = CacheService()
        test_value = {"word": "hello"}
        
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        cache.set("vocabulary:definition:hello", test_value)
        
        mock_client.put_item.assert_called_once()
        call_args = mock_client.put_item.call_args
        assert call_args[1]["TableName"] == "lexi-vocabulary-cache"
        assert call_args[1]["Item"]["cache_key"]["S"] == "vocabulary:definition:hello"

    def test_dynamodb_error_graceful_degradation(self):
        """Test graceful degradation when DynamoDB fails."""
        from botocore.exceptions import ClientError
        
        cache = CacheService()
        test_value = {"word": "hello"}
        
        # Mock the global _get_dynamodb_client to raise error
        with patch("infrastructure.services.cache_service._get_dynamodb_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            # Use ClientError which is caught by the code
            mock_client.put_item.side_effect = ClientError(
                {"Error": {"Code": "ServiceUnavailable"}},
                "PutItem"
            )
            
            # Should not raise, just log warning
            cache.set("vocabulary:definition:hello", test_value)
        
        # In-memory cache should still work
        assert cache.get("vocabulary:definition:hello") == test_value
