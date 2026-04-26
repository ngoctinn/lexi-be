"""Unit tests for delimiter-based batch translation."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from infrastructure.services.aws_translate_service import AwsTranslateService, BATCH_DELIMITER


class TestBatchTranslationDelimiter:
    """Test delimiter-based batch translation logic."""

    def test_empty_list_returns_empty(self):
        """Empty list should return empty list."""
        service = AwsTranslateService()
        result = service.translate_batch([])
        assert result == []

    def test_single_item_translates_directly(self):
        """Single item should use translate_en_to_vi directly."""
        service = AwsTranslateService()
        
        with patch.object(service, 'translate_en_to_vi', return_value='xin chào') as mock_translate:
            result = service.translate_batch(['hello'])
            
            assert result == ['xin chào']
            mock_translate.assert_called_once_with('hello')

    @patch('infrastructure.services.aws_translate_service._get_client')
    def test_multiple_items_single_api_call(self, mock_get_client):
        """Multiple items should make single API call with delimiter."""
        # Mock boto3 client
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock response: translated text with delimiter
        texts = ['hello', 'world', 'test']
        translated = ['xin chào', 'thế giới', 'kiểm tra']
        combined_response = BATCH_DELIMITER.join(translated)
        
        mock_client.translate_text.return_value = {
            'TranslatedText': combined_response
        }
        
        service = AwsTranslateService()
        result = service.translate_batch(texts)
        
        # Verify single API call
        assert mock_client.translate_text.call_count == 1
        
        # Verify correct input (joined with delimiter)
        call_args = mock_client.translate_text.call_args
        assert call_args[1]['Text'] == BATCH_DELIMITER.join(texts)
        assert call_args[1]['SourceLanguageCode'] == 'en'
        assert call_args[1]['TargetLanguageCode'] == 'vi'
        
        # Verify result
        assert result == translated

    @patch('infrastructure.services.aws_translate_service._get_client')
    def test_batch_with_empty_strings(self, mock_get_client):
        """Batch should handle empty strings correctly."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        texts = ['hello', '', 'world']
        translated = ['xin chào', '', 'thế giới']
        combined_response = BATCH_DELIMITER.join(translated)
        
        mock_client.translate_text.return_value = {
            'TranslatedText': combined_response
        }
        
        service = AwsTranslateService()
        result = service.translate_batch(texts)
        
        assert result == translated

    @patch('infrastructure.services.aws_translate_service._get_client')
    def test_batch_split_mismatch_fallback(self, mock_get_client):
        """If split result doesn't match input count, fallback to original texts."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        texts = ['hello', 'world', 'test']
        # Response missing delimiter (split will fail)
        mock_client.translate_text.return_value = {
            'TranslatedText': 'xin chào thế giới kiểm tra'
        }
        
        service = AwsTranslateService()
        result = service.translate_batch(texts)
        
        # Should fallback to original texts
        assert result == texts

    @patch('infrastructure.services.aws_translate_service._get_client')
    def test_batch_api_error_fallback(self, mock_get_client):
        """API error should fallback to original texts."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Simulate API error
        from botocore.exceptions import ClientError
        mock_client.translate_text.side_effect = ClientError(
            {'Error': {'Code': 'ServiceUnavailable', 'Message': 'Service unavailable'}},
            'TranslateText'
        )
        
        texts = ['hello', 'world']
        service = AwsTranslateService()
        result = service.translate_batch(texts)
        
        # Should fallback to original texts
        assert result == texts

    @patch('infrastructure.services.aws_translate_service._get_client')
    def test_batch_with_special_characters(self, mock_get_client):
        """Batch should handle special characters correctly."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        texts = ['hello!', 'world?', 'test@123']
        translated = ['xin chào!', 'thế giới?', 'kiểm tra@123']
        combined_response = BATCH_DELIMITER.join(translated)
        
        mock_client.translate_text.return_value = {
            'TranslatedText': combined_response
        }
        
        service = AwsTranslateService()
        result = service.translate_batch(texts)
        
        assert result == translated

    @patch('infrastructure.services.aws_translate_service._get_client')
    def test_batch_with_long_texts(self, mock_get_client):
        """Batch should handle longer texts (but within 10KB limit)."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Create texts that are reasonably long but under 10KB total
        texts = [
            'The quick brown fox jumps over the lazy dog' * 5,
            'Lorem ipsum dolor sit amet' * 5,
            'Hello world test' * 5
        ]
        translated = [
            'Con cáo nâu nhanh nhảy qua con chó lười' * 5,
            'Lorem ipsum dolor sit amet' * 5,
            'Xin chào thế giới kiểm tra' * 5
        ]
        combined_response = BATCH_DELIMITER.join(translated)
        
        mock_client.translate_text.return_value = {
            'TranslatedText': combined_response
        }
        
        service = AwsTranslateService()
        result = service.translate_batch(texts)
        
        assert result == translated
        assert len(result) == len(texts)

    @patch('infrastructure.services.aws_translate_service._get_client')
    def test_batch_preserves_order(self, mock_get_client):
        """Batch translation should preserve order of items."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        texts = ['first', 'second', 'third', 'fourth', 'fifth']
        translated = ['thứ nhất', 'thứ hai', 'thứ ba', 'thứ tư', 'thứ năm']
        combined_response = BATCH_DELIMITER.join(translated)
        
        mock_client.translate_text.return_value = {
            'TranslatedText': combined_response
        }
        
        service = AwsTranslateService()
        result = service.translate_batch(texts)
        
        assert result == translated
        for i, (original, translation) in enumerate(zip(texts, result)):
            assert translation == translated[i]
