"""Unit tests for CacheService (in-memory + DynamoDB caching)."""

import json
import time
from unittest.mock import Mock, patch, MagicMock
import pytest

from infrastructure.services.cache_service import CacheService
from domain.entities.vocabulary import Vocabulary, Meaning


@pytest.fixture
def mock_dynamodb():
    """Mock DynamoDB client."""
    return Mock()


@pytest.fixture
def cache_service(mock_dynamodb):
    """Create CacheService with mocked DynamoDB."""
    with patch('infrastructure.services.cache_service.boto3.client', return_value=mock_dynamodb):
        service = CacheService(table_name='test-table')
        return service


class TestCacheServiceInMemory:
    """Test in-memory cache operations."""
    
    def test_get_miss_returns_none(self, cache_service):
        """Test cache miss returns None."""
        result = cache_service.get('nonexistent-key')
        assert result is None
    
    def test_set_and_get_success(self, cache_service):
        """Test setting and getting value from cache."""
        vocab = Vocabulary(
            word='hello',
            translate_vi='xin chào',
            phonetic='həˈləʊ',
            audio_url='http://example.com/audio.mp3',
            meanings=[
                Meaning(
                    part_of_speech='exclamation',
                    definition='used as a greeting',
                    definition_vi='được dùng để chào hỏi',
                    example='hello there',
                    example_vi='xin chào'
                )
            ]
        )
        
        cache_service.set('vocabulary:definition:hello', vocab)
        result = cache_service.get('vocabulary:definition:hello')
        
        assert result is not None
        assert result.word == 'hello'
        assert result.translate_vi == 'xin chào'
    
    def test_cache_hit_returns_cached_value(self, cache_service):
        """Test cache hit returns previously cached value."""
        vocab = Vocabulary(
            word='test',
            translate_vi='kiểm tra',
            phonetic='test',
            meanings=[]
        )
        
        cache_service.set('vocabulary:definition:test', vocab)
        result1 = cache_service.get('vocabulary:definition:test')
        result2 = cache_service.get('vocabulary:definition:test')
        
        assert result1 == result2
        assert result1.word == 'test'


class TestCacheServiceDynamoDB:
    """Test DynamoDB fallback caching."""
    
    def test_set_stores_in_dynamodb(self, cache_service, mock_dynamodb):
        """Test that set() stores value in DynamoDB."""
        vocab = Vocabulary(
            word='hello',
            translate_vi='xin chào',
            phonetic='həˈləʊ',
            meanings=[]
        )
        
        cache_service.set('vocabulary:definition:hello', vocab, ttl_seconds=86400)
        
        # Verify DynamoDB put_item was called
        mock_dynamodb.put_item.assert_called_once()
        call_args = mock_dynamodb.put_item.call_args
        assert call_args[1]['TableName'] == 'test-table'
        assert 'Item' in call_args[1]
    
    def test_get_retrieves_from_dynamodb_on_miss(self, cache_service, mock_dynamodb):
        """Test that get() retrieves from DynamoDB on in-memory miss."""
        vocab_dict = {
            'word': 'hello',
            'translate_vi': 'xin chào',
            'phonetic': 'həˈləʊ',
            'audio_url': None,
            'meanings': [],
            'origin': None
        }
        
        mock_dynamodb.get_item.return_value = {
            'Item': {
                'definition_json': json.dumps(vocab_dict)
            }
        }
        
        # Clear in-memory cache
        cache_service._memory_cache.clear()
        
        result = cache_service.get('vocabulary:definition:hello')
        
        # Verify DynamoDB get_item was called
        mock_dynamodb.get_item.assert_called_once()
        assert result is not None
        assert result.word == 'hello'
    
    def test_dynamodb_failure_graceful_degradation(self, cache_service, mock_dynamodb):
        """Test graceful degradation when DynamoDB fails."""
        mock_dynamodb.put_item.side_effect = Exception('DynamoDB error')
        
        vocab = Vocabulary(
            word='hello',
            translate_vi='xin chào',
            phonetic='həˈləʊ',
            meanings=[]
        )
        
        # Should not raise exception
        cache_service.set('vocabulary:definition:hello', vocab)
        
        # Value should still be in in-memory cache
        result = cache_service.get('vocabulary:definition:hello')
        assert result is not None
        assert result.word == 'hello'


class TestCacheServiceTTL:
    """Test TTL (Time To Live) functionality."""
    
    def test_set_with_custom_ttl(self, cache_service, mock_dynamodb):
        """Test setting value with custom TTL."""
        vocab = Vocabulary(
            word='hello',
            translate_vi='xin chào',
            phonetic='həˈləʊ',
            meanings=[]
        )
        
        cache_service.set('vocabulary:definition:hello', vocab, ttl_seconds=3600)
        
        # Verify TTL was set in DynamoDB
        mock_dynamodb.put_item.assert_called_once()
        call_args = mock_dynamodb.put_item.call_args
        item = call_args[1]['Item']
        assert 'ttl' in item
        assert item['ttl'] > int(time.time())
    
    def test_default_ttl_24_hours(self, cache_service, mock_dynamodb):
        """Test default TTL is 24 hours."""
        vocab = Vocabulary(
            word='hello',
            translate_vi='xin chào',
            phonetic='həˈləʊ',
            meanings=[]
        )
        
        before_time = int(time.time())
        cache_service.set('vocabulary:definition:hello', vocab)
        after_time = int(time.time())
        
        # Verify TTL is approximately 24 hours
        mock_dynamodb.put_item.assert_called_once()
        call_args = mock_dynamodb.put_item.call_args
        item = call_args[1]['Item']
        ttl = item['ttl']
        
        # TTL should be between 24 hours from before_time and after_time
        assert ttl >= before_time + 86400 - 1
        assert ttl <= after_time + 86400 + 1


class TestCacheServiceLogging:
    """Test logging functionality."""
    
    def test_logs_cache_hit(self, cache_service, caplog):
        """Test that cache hits are logged."""
        vocab = Vocabulary(
            word='hello',
            translate_vi='xin chào',
            phonetic='həˈləʊ',
            meanings=[]
        )
        
        cache_service.set('vocabulary:definition:hello', vocab)
        cache_service.get('vocabulary:definition:hello')
        
        # Check that cache hit was logged
        assert any('cache hit' in record.message.lower() for record in caplog.records)
    
    def test_logs_cache_miss(self, cache_service, caplog):
        """Test that cache misses are logged."""
        cache_service.get('nonexistent-key')
        
        # Check that cache miss was logged
        assert any('cache miss' in record.message.lower() for record in caplog.records)
