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


class TestBatchTranslation:
    """Tests for batch translation optimization."""

    def test_single_translate_batch_call(self):
        """Test that batch translation uses a single translate_batch call."""
        mock_dictionary_service = Mock()
        mock_dictionary_service.get_word_definition.return_value = Vocabulary(
            word="hello",
            translate_vi="",
            phonetic="həˈləʊ",
            meanings=[
                Meaning(
                    part_of_speech="exclamation",
                    definition="used as a greeting",
                    definition_vi="",
                    example="hello there, Katie!",
                    example_vi=""
                )
            ]
        )
        
        mock_translation_service = Mock()
        # Mock translate_batch to return translations
        mock_translation_service.translate_batch.return_value = [
            "xin chào",  # word
            "được dùng để chào hỏi",  # definition
            "xin chào Katie!"  # example
        ]
        
        use_case = TranslateVocabularyUseCase(mock_dictionary_service, mock_translation_service)
        command = TranslateVocabularyCommand(word="hello")
        
        result = use_case.execute(command)
        
        # Verify translate_batch was called exactly once
        assert mock_translation_service.translate_batch.call_count == 1
        
        # Verify it was called with all items
        call_args = mock_translation_service.translate_batch.call_args[0][0]
        assert len(call_args) == 3
        assert call_args[0] == "hello"
        assert call_args[1] == "used as a greeting"
        assert call_args[2] == "hello there, Katie!"
        
        # Verify result
        assert result.is_success
        assert result.value.translation_vi == "xin chào"
        assert result.value.meanings[0].definition_vi == "được dùng để chào hỏi"
        assert result.value.meanings[0].example_vi == "xin chào Katie!"

    def test_batch_translation_multiple_meanings(self):
        """Test batch translation with multiple meanings."""
        mock_dictionary_service = Mock()
        mock_dictionary_service.get_word_definition.return_value = Vocabulary(
            word="run",
            translate_vi="",
            phonetic="rʌn",
            meanings=[
                Meaning(
                    part_of_speech="verb",
                    definition="to move fast",
                    definition_vi="",
                    example="I run every morning",
                    example_vi=""
                ),
                Meaning(
                    part_of_speech="noun",
                    definition="an act of running",
                    definition_vi="",
                    example="Let's go for a run",
                    example_vi=""
                )
            ]
        )
        
        mock_translation_service = Mock()
        mock_translation_service.translate_batch.return_value = [
            "chạy",  # word
            "chuyển động nhanh",  # def 1
            "Tôi chạy mỗi sáng",  # ex 1
            "một lần chạy",  # def 2
            "Hãy đi chạy"  # ex 2
        ]
        
        use_case = TranslateVocabularyUseCase(mock_dictionary_service, mock_translation_service)
        command = TranslateVocabularyCommand(word="run")
        
        result = use_case.execute(command)
        
        # Verify single batch call
        assert mock_translation_service.translate_batch.call_count == 1
        
        # Verify all items were batched
        call_args = mock_translation_service.translate_batch.call_args[0][0]
        assert len(call_args) == 5
        
        # Verify result
        assert result.is_success
        assert len(result.value.meanings) == 2
        assert result.value.meanings[0].definition_vi == "chuyển động nhanh"
        assert result.value.meanings[1].definition_vi == "một lần chạy"

    def test_batch_translation_with_empty_examples(self):
        """Test batch translation skips empty examples."""
        mock_dictionary_service = Mock()
        mock_dictionary_service.get_word_definition.return_value = Vocabulary(
            word="hello",
            translate_vi="",
            phonetic="həˈləʊ",
            meanings=[
                Meaning(
                    part_of_speech="exclamation",
                    definition="greeting",
                    definition_vi="",
                    example="",  # No example
                    example_vi=""
                ),
                Meaning(
                    part_of_speech="noun",
                    definition="a greeting",
                    definition_vi="",
                    example="she gave me a hello",
                    example_vi=""
                )
            ]
        )
        
        mock_translation_service = Mock()
        mock_translation_service.translate_batch.return_value = [
            "xin chào",  # word
            "lời chào",  # def 1 (no example)
            "một lời chào",  # def 2
            "cô ấy chào tôi"  # ex 2
        ]
        
        use_case = TranslateVocabularyUseCase(mock_dictionary_service, mock_translation_service)
        command = TranslateVocabularyCommand(word="hello")
        
        result = use_case.execute(command)
        
        # Verify batch call
        call_args = mock_translation_service.translate_batch.call_args[0][0]
        assert len(call_args) == 4  # word + 2 defs + 1 example
        
        # Verify result
        assert result.is_success
        assert result.value.meanings[0].example == ""
        assert result.value.meanings[0].example_vi == ""
        assert result.value.meanings[1].example_vi == "cô ấy chào tôi"

    def test_batch_translation_failure_graceful_degradation(self):
        """Test graceful degradation when batch translation fails."""
        mock_dictionary_service = Mock()
        mock_dictionary_service.get_word_definition.return_value = Vocabulary(
            word="hello",
            translate_vi="",
            phonetic="həˈləʊ",
            meanings=[
                Meaning(
                    part_of_speech="exclamation",
                    definition="greeting",
                    definition_vi="",
                    example="Hello!",
                    example_vi=""
                )
            ]
        )
        
        mock_translation_service = Mock()
        # Simulate batch translation failure
        mock_translation_service.translate_batch.side_effect = Exception("Translation service unavailable")
        
        use_case = TranslateVocabularyUseCase(mock_dictionary_service, mock_translation_service)
        command = TranslateVocabularyCommand(word="hello")
        
        result = use_case.execute(command)
        
        # Should still succeed with original English text
        assert result.is_success
        assert result.value.translation_vi == "hello"
        assert result.value.meanings[0].definition_vi == "greeting"
        assert result.value.meanings[0].example_vi == "Hello!"

    def test_batch_translation_partial_failure(self):
        """Test handling when translate_batch returns fewer items than expected."""
        mock_dictionary_service = Mock()
        mock_dictionary_service.get_word_definition.return_value = Vocabulary(
            word="hello",
            translate_vi="",
            phonetic="həˈləʊ",
            meanings=[
                Meaning(
                    part_of_speech="exclamation",
                    definition="greeting",
                    definition_vi="",
                    example="Hello!",
                    example_vi=""
                )
            ]
        )
        
        mock_translation_service = Mock()
        # Return fewer translations than expected
        mock_translation_service.translate_batch.return_value = [
            "xin chào",  # word
            "lời chào"  # definition (missing example)
        ]
        
        use_case = TranslateVocabularyUseCase(mock_dictionary_service, mock_translation_service)
        command = TranslateVocabularyCommand(word="hello")
        
        result = use_case.execute(command)
        
        # Should handle gracefully
        assert result.is_success
        assert result.value.translation_vi == "xin chào"
        assert result.value.meanings[0].definition_vi == "lời chào"
        # Example should fallback to empty string
        assert result.value.meanings[0].example_vi == ""
