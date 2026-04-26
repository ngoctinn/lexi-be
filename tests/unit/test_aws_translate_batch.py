"""Unit tests for AWS Translate batch translation."""

from pathlib import Path
import sys
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from infrastructure.services.aws_translate_service import AwsTranslateService


class TestAwsTranslateBatch:
    """Tests for batch translation in AwsTranslateService."""

    @patch("infrastructure.services.aws_translate_service._get_client")
    def test_batch_translate_single_call(self, mock_get_client):
        """Test that batch translation makes a single AWS Translate call."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # Mock AWS Translate response
        mock_client.translate_text.return_value = {
            "TranslatedText": "xin chào\n###TRANSLATE_DELIMITER###\nlời chào\n###TRANSLATE_DELIMITER###\nví dụ"
        }
        
        service = AwsTranslateService()
        texts = ["hello", "greeting", "example"]
        
        result = service.translate_batch(texts)
        
        # Verify single call to AWS Translate
        assert mock_client.translate_text.call_count == 1
        
        # Verify result
        assert len(result) == 3
        assert result[0] == "xin chào"
        assert result[1] == "lời chào"
        assert result[2] == "ví dụ"

    @patch("infrastructure.services.aws_translate_service._get_client")
    def test_batch_translate_empty_list(self, mock_get_client):
        """Test batch translation with empty list."""
        service = AwsTranslateService()
        result = service.translate_batch([])
        
        assert result == []
        # Should not call AWS Translate
        mock_get_client.assert_not_called()

    @patch("infrastructure.services.aws_translate_service._get_client")
    def test_batch_translate_single_item(self, mock_get_client):
        """Test batch translation with single item."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        mock_client.translate_text.return_value = {
            "TranslatedText": "xin chào"
        }
        
        service = AwsTranslateService()
        result = service.translate_batch(["hello"])
        
        assert len(result) == 1
        assert result[0] == "xin chào"

    @patch("infrastructure.services.aws_translate_service._get_client")
    def test_batch_translate_with_empty_strings(self, mock_get_client):
        """Test batch translation with empty strings."""
        service = AwsTranslateService()
        result = service.translate_batch(["", "", ""])
        
        # Should return original empty strings without calling AWS
        assert result == ["", "", ""]
        mock_get_client.assert_not_called()

    @patch("infrastructure.services.aws_translate_service._get_client")
    def test_batch_translate_failure_returns_originals(self, mock_get_client):
        """Test that batch translation returns original texts on failure."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # Simulate AWS Translate failure
        from botocore.exceptions import ClientError
        mock_client.translate_text.side_effect = ClientError(
            {"Error": {"Code": "ServiceUnavailable", "Message": "Service unavailable"}},
            "TranslateText"
        )
        
        service = AwsTranslateService()
        texts = ["hello", "greeting", "example"]
        
        result = service.translate_batch(texts)
        
        # Should return original texts
        assert result == texts

    @patch("infrastructure.services.aws_translate_service._get_client")
    def test_batch_translate_mismatch_returns_originals(self, mock_get_client):
        """Test that batch translation returns originals when split count mismatches."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # Mock response with wrong number of items
        mock_client.translate_text.return_value = {
            "TranslatedText": "xin chào\n###TRANSLATE_DELIMITER###\nlời chào"  # Only 2 items
        }
        
        service = AwsTranslateService()
        texts = ["hello", "greeting", "example"]  # 3 items
        
        result = service.translate_batch(texts)
        
        # Should return original texts due to mismatch
        assert result == texts

    @patch("infrastructure.services.aws_translate_service._get_client")
    def test_batch_translate_preserves_order(self, mock_get_client):
        """Test that batch translation preserves order of items."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        mock_client.translate_text.return_value = {
            "TranslatedText": "một\n###TRANSLATE_DELIMITER###\nhai\n###TRANSLATE_DELIMITER###\nba\n###TRANSLATE_DELIMITER###\nbốn"
        }
        
        service = AwsTranslateService()
        texts = ["one", "two", "three", "four"]
        
        result = service.translate_batch(texts)
        
        assert len(result) == 4
        assert result[0] == "một"
        assert result[1] == "hai"
        assert result[2] == "ba"
        assert result[3] == "bốn"

    @patch("infrastructure.services.aws_translate_service._get_client")
    def test_batch_translate_uses_correct_parameters(self, mock_get_client):
        """Test that batch translation uses correct AWS Translate parameters."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        mock_client.translate_text.return_value = {
            "TranslatedText": "xin chào\n###TRANSLATE_DELIMITER###\nlời chào"
        }
        
        service = AwsTranslateService()
        service.translate_batch(["hello", "greeting"])
        
        # Verify call parameters
        call_args = mock_client.translate_text.call_args
        assert call_args[1]["SourceLanguageCode"] == "en"
        assert call_args[1]["TargetLanguageCode"] == "vi"
        assert "###TRANSLATE_DELIMITER###" in call_args[1]["Text"]
