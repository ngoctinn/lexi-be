"""Integration tests for batch translation with vocabulary use case."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from application.use_cases.vocabulary_use_cases import TranslateVocabularyUseCase
from application.dtos.vocabulary_dtos import TranslateVocabularyCommand
from domain.entities.vocabulary import Vocabulary, Meaning
from infrastructure.services.aws_translate_service import AwsTranslateService, BATCH_DELIMITER


class TestBatchTranslationIntegration:
    """Integration tests for batch translation in vocabulary lookup."""

    @patch('infrastructure.services.aws_translate_service._get_client')
    def test_vocabulary_use_case_single_api_call(self, mock_get_client):
        """Vocabulary use case should make single API call for batch translation."""
        # Setup mock
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Create mock vocabulary with 3 meanings
        vocabulary = Vocabulary(
            word='run',
            translate_vi='chạy',
            phonetic='/rʌn/',
            audio_url='https://example.com/run.mp3',
            meanings=[
                Meaning(
                    part_of_speech='verb',
                    definition='to move quickly on foot',
                    example='I run every morning'
                ),
                Meaning(
                    part_of_speech='verb',
                    definition='to operate or manage',
                    example='She runs a business'
                ),
                Meaning(
                    part_of_speech='noun',
                    definition='an act of running',
                    example='Let\'s go for a run'
                )
            ]
        )
        
        # Mock dictionary service
        mock_dict_service = Mock()
        mock_dict_service.get_word_definition.return_value = vocabulary
        
        # Mock translations (7 items: word + 3 definitions + 3 examples)
        items = [
            'run',
            'to move quickly on foot',
            'I run every morning',
            'to operate or manage',
            'She runs a business',
            'an act of running',
            'Let\'s go for a run'
        ]
        translations = [
            'chạy',
            'di chuyển nhanh chóng trên bộ',
            'Tôi chạy mỗi sáng',
            'vận hành hoặc quản lý',
            'Cô ấy điều hành một doanh nghiệp',
            'một hành động chạy',
            'Hãy đi chạy'
        ]
        combined_response = BATCH_DELIMITER.join(translations)
        
        mock_client.translate_text.return_value = {
            'TranslatedText': combined_response
        }
        
        # Create use case
        translate_service = AwsTranslateService()
        use_case = TranslateVocabularyUseCase(mock_dict_service, translate_service)
        
        # Execute
        command = TranslateVocabularyCommand(word='run', context=None)
        result = use_case.execute(command)
        
        # Verify
        assert result.is_success
        
        # Verify single API call
        assert mock_client.translate_text.call_count == 1
        
        # Verify correct input
        call_args = mock_client.translate_text.call_args
        assert call_args[1]['Text'] == BATCH_DELIMITER.join(items)
        assert call_args[1]['SourceLanguageCode'] == 'en'
        assert call_args[1]['TargetLanguageCode'] == 'vi'
        
        # Verify response
        response = result.value
        assert response.word == 'run'
        assert response.translate_vi == 'chạy'
        assert len(response.meanings) == 3
        assert response.meanings[0].definition_vi == 'di chuyển nhanh chóng trên bộ'
        assert response.meanings[0].example_vi == 'Tôi chạy mỗi sáng'

    @patch('infrastructure.services.aws_translate_service._get_client')
    def test_vocabulary_with_missing_examples(self, mock_get_client):
        """Vocabulary with missing examples should still batch translate correctly."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Vocabulary with some missing examples
        vocabulary = Vocabulary(
            word='hello',
            translate_vi='xin chào',
            phonetic='/həˈloʊ/',
            audio_url='https://example.com/hello.mp3',
            meanings=[
                Meaning(
                    part_of_speech='interjection',
                    definition='used as a greeting',
                    example='Hello, how are you?'
                ),
                Meaning(
                    part_of_speech='noun',
                    definition='an act of greeting',
                    example=None  # Missing example
                )
            ]
        )
        
        mock_dict_service = Mock()
        mock_dict_service.get_word_definition.return_value = vocabulary
        
        # 4 items: word + 2 definitions + 1 example (second meaning has no example)
        items = [
            'hello',
            'used as a greeting',
            'Hello, how are you?',
            'an act of greeting'
        ]
        translations = [
            'xin chào',
            'được sử dụng như một lời chào',
            'Xin chào, bạn khỏe không?',
            'một hành động chào hỏi'
        ]
        combined_response = BATCH_DELIMITER.join(translations)
        
        mock_client.translate_text.return_value = {
            'TranslatedText': combined_response
        }
        
        translate_service = AwsTranslateService()
        use_case = TranslateVocabularyUseCase(mock_dict_service, translate_service)
        
        command = TranslateVocabularyCommand(word='hello', context=None)
        result = use_case.execute(command)
        
        assert result.is_success
        assert mock_client.translate_text.call_count == 1
        
        response = result.value
        assert response.meanings[0].example_vi == 'Xin chào, bạn khỏe không?'
        assert response.meanings[1].example_vi == ''  # No example

    @patch('infrastructure.services.aws_translate_service._get_client')
    def test_batch_translation_performance_reduction(self, mock_get_client):
        """Verify batch translation reduces API calls from N to 1."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Create vocabulary with 5 meanings (11 items total)
        meanings = [
            Meaning(
                part_of_speech='verb',
                definition=f'definition {i}',
                example=f'example {i}'
            )
            for i in range(5)
        ]
        
        vocabulary = Vocabulary(
            word='test',
            translate_vi='kiểm tra',
            phonetic='/test/',
            audio_url='https://example.com/test.mp3',
            meanings=meanings
        )
        
        mock_dict_service = Mock()
        mock_dict_service.get_word_definition.return_value = vocabulary
        
        # Mock translations
        items_count = 1 + (5 * 2)  # word + 5 definitions + 5 examples
        translations = [f'translation {i}' for i in range(items_count)]
        combined_response = BATCH_DELIMITER.join(translations)
        
        mock_client.translate_text.return_value = {
            'TranslatedText': combined_response
        }
        
        translate_service = AwsTranslateService()
        use_case = TranslateVocabularyUseCase(mock_dict_service, translate_service)
        
        command = TranslateVocabularyCommand(word='test', context=None)
        result = use_case.execute(command)
        
        assert result.is_success
        
        # Verify: 1 API call instead of 11
        assert mock_client.translate_text.call_count == 1
        
        # Before optimization: would be 11 calls
        # After optimization: 1 call
        # Reduction: 90%
        print(f"API calls reduced from {items_count} to {mock_client.translate_text.call_count}")

    @patch('infrastructure.services.aws_translate_service._get_client')
    def test_batch_translation_with_context(self, mock_get_client):
        """Batch translation should work with context parameter."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        vocabulary = Vocabulary(
            word='get off',
            translate_vi='xuống',
            phonetic='/ɡet ɔf/',
            audio_url='https://example.com/get-off.mp3',
            meanings=[
                Meaning(
                    part_of_speech='phrasal verb',
                    definition='to leave a vehicle',
                    example='Get off the bus at the next stop'
                )
            ]
        )
        
        mock_dict_service = Mock()
        mock_dict_service.get_word_definition.return_value = vocabulary
        
        items = [
            'get off',
            'to leave a vehicle',
            'Get off the bus at the next stop'
        ]
        translations = [
            'xuống',
            'rời khỏi một phương tiện',
            'Xuống xe buýt ở trạm tiếp theo'
        ]
        combined_response = BATCH_DELIMITER.join(translations)
        
        mock_client.translate_text.return_value = {
            'TranslatedText': combined_response
        }
        
        translate_service = AwsTranslateService()
        use_case = TranslateVocabularyUseCase(mock_dict_service, translate_service)
        
        # With context for phrasal verb detection
        command = TranslateVocabularyCommand(
            word='get off',
            context='I need to get off the bus'
        )
        result = use_case.execute(command)
        
        assert result.is_success
        assert mock_client.translate_text.call_count == 1
