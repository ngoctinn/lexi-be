"""Integration tests for batch translation with mocked AWS Translate."""

from pathlib import Path
import sys
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from application.use_cases.vocabulary_use_cases import TranslateVocabularyUseCase
from application.dtos.vocabulary_dtos import TranslateVocabularyCommand
from domain.entities.vocabulary import Vocabulary, Meaning
from infrastructure.services.aws_translate_service import AwsTranslateService


class TestBatchTranslationIntegration:
    """Integration tests for batch translation with mocked AWS Translate."""

    def test_integration_with_aws_translate_service(self):
        """Test integration with AwsTranslateService (mocked boto3)."""
        # Arrange
        mock_dictionary_service = Mock()
        mock_dictionary_service.get_word_definition.return_value = Vocabulary(
            word="hello",
            translate_vi="",
            phonetic="/həˈloʊ/",
            audio_url="https://example.com/hello.mp3",
            meanings=[
                Meaning(
                    part_of_speech="interjection",
                    definition="used as a greeting",
                    example="Hello, how are you?"
                )
            ]
        )
        
        # Mock boto3 translate client
        with patch('infrastructure.services.aws_translate_service._get_client') as mock_get_client:
            mock_translate_client = Mock()
            mock_get_client.return_value = mock_translate_client
            
            # Mock single translate_text response with delimiter-separated translations
            delimiter = "\n###TRANSLATE_DELIMITER###\n"
            combined_translation = delimiter.join([
                'xin chào',  # word
                'được dùng để chào hỏi',  # definition
                'Xin chào, bạn khỏe không?'  # example
            ])
            mock_translate_client.translate_text.return_value = {
                'TranslatedText': combined_translation
            }
            
            translation_service = AwsTranslateService()
            use_case = TranslateVocabularyUseCase(mock_dictionary_service, translation_service)
            command = TranslateVocabularyCommand(word="hello")
            
            # Act
            result = use_case.execute(command)
            
            # Assert
            assert result.is_success
            response = result.value
            assert response.word == "hello"
            assert response.translation_vi == "xin chào"
            assert response.meanings[0].definition_vi == "được dùng để chào hỏi"
            assert response.meanings[0].example_vi == "Xin chào, bạn khỏe không?"
            
            # Verify translate_text was called ONCE (batch translation)
            assert mock_translate_client.translate_text.call_count == 1

    def test_integration_batch_translation_multiple_meanings(self):
        """Test integration with multiple meanings (mocked AWS Translate)."""
        # Arrange
        mock_dictionary_service = Mock()
        mock_dictionary_service.get_word_definition.return_value = Vocabulary(
            word="run",
            translate_vi="",
            phonetic="/rʌn/",
            meanings=[
                Meaning(part_of_speech="verb", definition="move fast", example="I run daily"),
                Meaning(part_of_speech="noun", definition="act of running", example="go for a run"),
                Meaning(part_of_speech="verb", definition="operate", example="run a business")
            ]
        )
        
        # Mock boto3 translate client
        with patch('infrastructure.services.aws_translate_service._get_client') as mock_get_client:
            mock_translate_client = Mock()
            mock_get_client.return_value = mock_translate_client
            
            # Mock single translate_text response with 7 items
            delimiter = "\n###TRANSLATE_DELIMITER###\n"
            combined_translation = delimiter.join([
                'chạy',  # word
                'di chuyển nhanh',  # def 1
                'Tôi chạy hàng ngày',  # ex 1
                'hành động chạy',  # def 2
                'đi chạy',  # ex 2
                'vận hành',  # def 3
                'điều hành doanh nghiệp'  # ex 3
            ])
            mock_translate_client.translate_text.return_value = {
                'TranslatedText': combined_translation
            }
            
            translation_service = AwsTranslateService()
            use_case = TranslateVocabularyUseCase(mock_dictionary_service, translation_service)
            command = TranslateVocabularyCommand(word="run")
            
            # Act
            result = use_case.execute(command)
            
            # Assert
            assert result.is_success
            response = result.value
            assert len(response.meanings) == 3
            
            # Verify all meanings are translated
            assert response.meanings[0].definition_vi == "di chuyển nhanh"
            assert response.meanings[0].example_vi == "Tôi chạy hàng ngày"
            
            assert response.meanings[1].definition_vi == "hành động chạy"
            assert response.meanings[1].example_vi == "đi chạy"
            
            assert response.meanings[2].definition_vi == "vận hành"
            assert response.meanings[2].example_vi == "điều hành doanh nghiệp"
            
            # Verify translate_text was called ONCE (batch translation)
            assert mock_translate_client.translate_text.call_count == 1

    def test_integration_aws_translate_failure_graceful_degradation(self):
        """Test graceful degradation when AWS Translate fails."""
        # Arrange
        mock_dictionary_service = Mock()
        mock_dictionary_service.get_word_definition.return_value = Vocabulary(
            word="hello",
            translate_vi="",
            phonetic="/həˈloʊ/",
            meanings=[
                Meaning(part_of_speech="interjection", definition="greeting", example="hello there")
            ]
        )
        
        # Mock boto3 translate client to raise exception
        with patch('infrastructure.services.aws_translate_service._get_client') as mock_get_client:
            mock_translate_client = Mock()
            mock_get_client.return_value = mock_translate_client
            
            # Simulate AWS Translate failure
            mock_translate_client.translate_text.side_effect = Exception("AWS Translate unavailable")
            
            translation_service = AwsTranslateService()
            use_case = TranslateVocabularyUseCase(mock_dictionary_service, translation_service)
            command = TranslateVocabularyCommand(word="hello")
            
            # Act
            result = use_case.execute(command)
            
            # Assert
            assert result.is_success  # Should still succeed with graceful degradation
            response = result.value
            # Should return original English text (graceful degradation)
            assert response.translation_vi == "hello"
            assert response.meanings[0].definition_vi == "greeting"
            assert response.meanings[0].example_vi == "hello there"

    def test_integration_delimiter_mismatch_fallback(self):
        """Test fallback when delimiter split produces wrong number of items."""
        # Arrange
        mock_dictionary_service = Mock()
        mock_dictionary_service.get_word_definition.return_value = Vocabulary(
            word="test",
            translate_vi="",
            phonetic="/test/",
            meanings=[
                Meaning(part_of_speech="noun", definition="a procedure", example="take a test")
            ]
        )
        
        # Mock boto3 translate client
        with patch('infrastructure.services.aws_translate_service._get_client') as mock_get_client:
            mock_translate_client = Mock()
            mock_get_client.return_value = mock_translate_client
            
            # Return wrong number of items (should be 3, but return 2)
            delimiter = "\n###TRANSLATE_DELIMITER###\n"
            combined_translation = delimiter.join([
                'kiểm tra',  # word
                'một thủ tục'  # definition (missing example)
            ])
            mock_translate_client.translate_text.return_value = {
                'TranslatedText': combined_translation
            }
            
            translation_service = AwsTranslateService()
            use_case = TranslateVocabularyUseCase(mock_dictionary_service, translation_service)
            command = TranslateVocabularyCommand(word="test")
            
            # Act
            result = use_case.execute(command)
            
            # Assert
            assert result.is_success
            response = result.value
            
            # Should fallback to original English text
            assert response.translation_vi == "test"
            assert response.meanings[0].definition_vi == "a procedure"
            assert response.meanings[0].example_vi == "take a test"

    def test_integration_with_context_for_phrasal_verbs(self):
        """Test integration with context parameter for phrasal verb detection."""
        # Arrange
        mock_dictionary_service = Mock()
        # Simulate phrasal verb detection: "get off" instead of "off"
        mock_dictionary_service.get_word_definition.return_value = Vocabulary(
            word="get off",  # Detected phrasal verb
            translate_vi="",
            phonetic="/ɡet ɒf/",
            meanings=[
                Meaning(
                    part_of_speech="phrasal verb",
                    definition="to leave a vehicle",
                    example="I get off the bus at the next stop"
                )
            ]
        )
        
        # Mock boto3 translate client
        with patch('infrastructure.services.aws_translate_service._get_client') as mock_get_client:
            mock_translate_client = Mock()
            mock_get_client.return_value = mock_translate_client
            
            delimiter = "\n###TRANSLATE_DELIMITER###\n"
            combined_translation = delimiter.join([
                'xuống xe',  # phrasal verb
                'rời khỏi phương tiện',  # definition
                'Tôi xuống xe buýt ở trạm tiếp theo'  # example
            ])
            mock_translate_client.translate_text.return_value = {
                'TranslatedText': combined_translation
            }
            
            translation_service = AwsTranslateService()
            use_case = TranslateVocabularyUseCase(mock_dictionary_service, translation_service)
            command = TranslateVocabularyCommand(
                word="off",
                context="I get off the bus at the next stop"
            )
            
            # Act
            result = use_case.execute(command)
            
            # Assert
            assert result.is_success
            response = result.value
            assert response.word == "get off"  # Detected phrasal verb
            assert response.translation_vi == "xuống xe"
            assert response.meanings[0].definition_vi == "rời khỏi phương tiện"
            
            # Verify dictionary service was called with context
            mock_dictionary_service.get_word_definition.assert_called_once_with(
                word="off",
                context="I get off the bus at the next stop"
            )

    def test_integration_empty_texts_handling(self):
        """Test handling of empty texts in batch translation."""
        # Arrange
        mock_dictionary_service = Mock()
        mock_dictionary_service.get_word_definition.return_value = Vocabulary(
            word="test",
            translate_vi="",
            phonetic="/test/",
            meanings=[
                Meaning(part_of_speech="noun", definition="a procedure", example="")  # Empty example
            ]
        )
        
        # Mock boto3 translate client
        with patch('infrastructure.services.aws_translate_service._get_client') as mock_get_client:
            mock_translate_client = Mock()
            mock_get_client.return_value = mock_translate_client
            
            # Only 2 items: word + definition (no example)
            delimiter = "\n###TRANSLATE_DELIMITER###\n"
            combined_translation = delimiter.join([
                'kiểm tra',  # word
                'một thủ tục'  # definition
            ])
            mock_translate_client.translate_text.return_value = {
                'TranslatedText': combined_translation
            }
            
            translation_service = AwsTranslateService()
            use_case = TranslateVocabularyUseCase(mock_dictionary_service, translation_service)
            command = TranslateVocabularyCommand(word="test")
            
            # Act
            result = use_case.execute(command)
            
            # Assert
            assert result.is_success
            response = result.value
            assert response.translation_vi == "kiểm tra"
            assert response.meanings[0].definition_vi == "một thủ tục"
            assert response.meanings[0].example_vi == ""  # Empty example remains empty

