"""Unit tests for batch translation logic in TranslateVocabularyUseCase."""

from pathlib import Path
import sys
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from application.use_cases.vocabulary_use_cases import TranslateVocabularyUseCase
from application.dtos.vocabulary_dtos import TranslateVocabularyCommand
from domain.entities.vocabulary import Vocabulary, Meaning


class TestBatchTranslationLogic:
    """Tests for batch translation logic in TranslateVocabularyUseCase."""

    def test_batch_collection_word_plus_first_definition_and_example(self):
        """Test that batch collects word + FIRST definition + FIRST example per meaning."""
        # Arrange
        mock_dictionary_service = Mock()
        mock_dictionary_service.get_word_definition.return_value = Vocabulary(
            word="hello",
            translate_vi="",  # Will be filled by translation
            phonetic="/həˈloʊ/",
            audio_url="https://example.com/hello.mp3",
            meanings=[
                Meaning(
                    part_of_speech="interjection",
                    definition="used as a greeting",
                    example="Hello, how are you?"
                ),
                Meaning(
                    part_of_speech="noun",
                    definition="an utterance of hello",
                    example="she gave a cheerful hello"
                )
            ]
        )
        
        mock_translation_service = Mock()
        # Expect: word + 2 definitions + 2 examples = 5 items
        mock_translation_service.translate_batch.return_value = [
            "xin chào",  # word
            "được dùng để chào hỏi",  # definition 1
            "Xin chào, bạn khỏe không?",  # example 1
            "lời chào",  # definition 2
            "cô ấy nói lời chào vui vẻ"  # example 2
        ]
        
        use_case = TranslateVocabularyUseCase(mock_dictionary_service, mock_translation_service)
        command = TranslateVocabularyCommand(word="hello")
        
        # Act
        result = use_case.execute(command)
        
        # Assert
        assert result.is_success
        # Verify translate_batch was called with exactly 5 items
        mock_translation_service.translate_batch.assert_called_once()
        call_args = mock_translation_service.translate_batch.call_args[0][0]
        assert len(call_args) == 5
        assert call_args[0] == "hello"
        assert call_args[1] == "used as a greeting"
        assert call_args[2] == "Hello, how are you?"
        assert call_args[3] == "an utterance of hello"
        assert call_args[4] == "she gave a cheerful hello"

    def test_single_aws_translate_call(self):
        """Test that only ONE AWS Translate call is made for all items."""
        # Arrange
        mock_dictionary_service = Mock()
        mock_dictionary_service.get_word_definition.return_value = Vocabulary(
            word="run",
            translate_vi="",
            phonetic="/rʌn/",
            meanings=[
                Meaning(part_of_speech="verb", definition="move fast", example="I run daily"),
                Meaning(part_of_speech="noun", definition="act of running", example="go for a run")
            ]
        )
        
        mock_translation_service = Mock()
        mock_translation_service.translate_batch.return_value = [
            "chạy", "di chuyển nhanh", "Tôi chạy hàng ngày",
            "hành động chạy", "đi chạy"
        ]
        
        use_case = TranslateVocabularyUseCase(mock_dictionary_service, mock_translation_service)
        command = TranslateVocabularyCommand(word="run")
        
        # Act
        result = use_case.execute(command)
        
        # Assert
        assert result.is_success
        # Verify translate_batch was called EXACTLY ONCE
        assert mock_translation_service.translate_batch.call_count == 1

    def test_proper_mapping_of_translations_to_items(self):
        """Test that translations are correctly mapped back to original items."""
        # Arrange
        mock_dictionary_service = Mock()
        mock_dictionary_service.get_word_definition.return_value = Vocabulary(
            word="test",
            translate_vi="",
            phonetic="/test/",
            meanings=[
                Meaning(part_of_speech="noun", definition="a procedure", example="take a test"),
                Meaning(part_of_speech="verb", definition="to examine", example="test the water")
            ]
        )
        
        mock_translation_service = Mock()
        mock_translation_service.translate_batch.return_value = [
            "kiểm tra",  # word
            "một thủ tục",  # definition 1
            "làm bài kiểm tra",  # example 1
            "để kiểm tra",  # definition 2
            "kiểm tra nước"  # example 2
        ]
        
        use_case = TranslateVocabularyUseCase(mock_dictionary_service, mock_translation_service)
        command = TranslateVocabularyCommand(word="test")
        
        # Act
        result = use_case.execute(command)
        
        # Assert
        assert result.is_success
        response = result.value
        
        # Verify word translation
        assert response.translation_vi == "kiểm tra"
        
        # Verify meaning 1 translations
        assert response.meanings[0].definition_vi == "một thủ tục"
        assert response.meanings[0].example_vi == "làm bài kiểm tra"
        
        # Verify meaning 2 translations
        assert response.meanings[1].definition_vi == "để kiểm tra"
        assert response.meanings[1].example_vi == "kiểm tra nước"

    def test_partial_failure_handling_some_items_translated(self):
        """Test handling when some items are translated but not all."""
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
        
        mock_translation_service = Mock()
        # Return fewer translations than requested (partial failure)
        mock_translation_service.translate_batch.return_value = [
            "xin chào",  # word translated
            "lời chào"  # definition translated, but example missing
        ]
        
        use_case = TranslateVocabularyUseCase(mock_dictionary_service, mock_translation_service)
        command = TranslateVocabularyCommand(word="hello")
        
        # Act
        result = use_case.execute(command)
        
        # Assert
        assert result.is_success
        response = result.value
        assert response.translation_vi == "xin chào"
        assert response.meanings[0].definition_vi == "lời chào"
        # Example should fallback to empty string when translation missing
        assert response.meanings[0].example_vi == ""

    def test_fallback_to_english_on_translation_failure(self):
        """Test that original English text is returned when translation fails."""
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
        
        mock_translation_service = Mock()
        # Simulate translation failure - translate_batch raises exception
        mock_translation_service.translate_batch.side_effect = Exception("Translation service unavailable")
        
        use_case = TranslateVocabularyUseCase(mock_dictionary_service, mock_translation_service)
        command = TranslateVocabularyCommand(word="hello")
        
        # Act
        result = use_case.execute(command)
        
        # Assert
        assert result.is_success
        response = result.value
        # Should fallback to original English text (graceful degradation)
        assert response.translation_vi == "hello"
        assert response.meanings[0].definition_vi == "greeting"
        assert response.meanings[0].example_vi == "hello there"

    def test_batch_with_meanings_without_examples(self):
        """Test batch translation when some meanings have no examples."""
        # Arrange
        mock_dictionary_service = Mock()
        mock_dictionary_service.get_word_definition.return_value = Vocabulary(
            word="test",
            translate_vi="",
            phonetic="/test/",
            meanings=[
                Meaning(part_of_speech="noun", definition="a procedure", example="take a test"),
                Meaning(part_of_speech="verb", definition="to examine", example="")  # No example
            ]
        )
        
        mock_translation_service = Mock()
        # Only 4 items: word + def1 + ex1 + def2 (no ex2)
        mock_translation_service.translate_batch.return_value = [
            "kiểm tra",  # word
            "một thủ tục",  # definition 1
            "làm bài kiểm tra",  # example 1
            "để kiểm tra"  # definition 2 (no example)
        ]
        
        use_case = TranslateVocabularyUseCase(mock_dictionary_service, mock_translation_service)
        command = TranslateVocabularyCommand(word="test")
        
        # Act
        result = use_case.execute(command)
        
        # Assert
        assert result.is_success
        # Verify only 4 items were sent for translation
        call_args = mock_translation_service.translate_batch.call_args[0][0]
        assert len(call_args) == 4
        
        # Verify mapping
        response = result.value
        assert response.meanings[0].example_vi == "làm bài kiểm tra"
        assert response.meanings[1].example_vi == ""  # No example to translate

    def test_empty_items_list_handling(self):
        """Test handling of empty items list (edge case)."""
        # Arrange
        mock_dictionary_service = Mock()
        mock_dictionary_service.get_word_definition.return_value = Vocabulary(
            word="test",
            translate_vi="",
            phonetic="/test/",
            meanings=[]  # No meanings
        )
        
        mock_translation_service = Mock()
        mock_translation_service.translate_batch.return_value = ["kiểm tra"]  # Only word
        
        use_case = TranslateVocabularyUseCase(mock_dictionary_service, mock_translation_service)
        command = TranslateVocabularyCommand(word="test")
        
        # Act
        result = use_case.execute(command)
        
        # Assert
        assert result.is_success
        response = result.value
        assert response.translation_vi == "kiểm tra"
        assert len(response.meanings) == 0

