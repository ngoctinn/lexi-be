"""Unit tests for updated TranslateVocabularyUseCase with Dictionary API integration."""

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
from domain.exceptions.dictionary_exceptions import WordNotFoundError, DictionaryServiceError


class TestTranslateVocabularyUseCase:
    """Tests for updated TranslateVocabularyUseCase."""

    def test_successful_translation_workflow(self):
        """Test successful translation workflow (fetch + translate)."""
        # Mock services
        mock_dictionary_service = Mock()
        mock_dictionary_service.get_word_definition.return_value = Vocabulary(
            word="hello",
            translate_vi="",  # Empty, will be filled by translation
            phonetic="həˈləʊ",
            audio_url="//ssl.gstatic.com/dictionary/static/sounds/20200429/hello--_gb_1.mp3",
            meanings=[
                Meaning(
                    part_of_speech="exclamation",
                    definition="used as a greeting or to begin a phone conversation",
                    definition_vi="",
                    example="hello there, Katie!",
                    example_vi=""
                )
            ]
        )
        
        mock_translation_service = Mock()
        mock_translation_service.translate_batch.return_value = [
            "xin chào",  # word translation
            "được dùng để chào hỏi hoặc bắt đầu cuộc gọi điện thoại",  # definition translation
            "xin chào Katie!"  # example translation
        ]
        
        use_case = TranslateVocabularyUseCase(mock_dictionary_service, mock_translation_service)
        command = TranslateVocabularyCommand(word="hello")
        
        result = use_case.execute(command)
        
        assert result.is_success
        assert result.value.word == "hello"
        assert result.value.translation_vi == "xin chào"
        assert result.value.phonetic == "həˈləʊ"
        assert len(result.value.meanings) == 1
        assert result.value.meanings[0].definition == "used as a greeting or to begin a phone conversation"
        assert result.value.meanings[0].definition_vi == "được dùng để chào hỏi hoặc bắt đầu cuộc gọi điện thoại"
        assert result.value.meanings[0].example_vi == "xin chào Katie!"

    def test_word_not_found_error(self):
        """Test handling of word not found error."""
        mock_dictionary_service = Mock()
        mock_dictionary_service.get_word_definition.side_effect = WordNotFoundError("Word not found")
        
        mock_translation_service = Mock()
        
        use_case = TranslateVocabularyUseCase(mock_dictionary_service, mock_translation_service)
        command = TranslateVocabularyCommand(word="xyzabc")
        
        result = use_case.execute(command)
        
        assert not result.is_success
        assert isinstance(result.error, WordNotFoundError)

    def test_dictionary_service_error(self):
        """Test handling of dictionary service error."""
        mock_dictionary_service = Mock()
        mock_dictionary_service.get_word_definition.side_effect = DictionaryServiceError("Service unavailable")
        
        mock_translation_service = Mock()
        
        use_case = TranslateVocabularyUseCase(mock_dictionary_service, mock_translation_service)
        command = TranslateVocabularyCommand(word="hello")
        
        result = use_case.execute(command)
        
        assert not result.is_success
        assert isinstance(result.error, DictionaryServiceError)

    def test_translation_failure_graceful_degradation(self):
        """Test graceful degradation when translation fails."""
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
                    example="Hello, how are you?",
                    example_vi=""
                )
            ]
        )
        
        mock_translation_service = Mock()
        # Simulate translation failure by raising exception
        mock_translation_service.translate_batch.side_effect = Exception("Translation failed")
        
        use_case = TranslateVocabularyUseCase(mock_dictionary_service, mock_translation_service)
        command = TranslateVocabularyCommand(word="hello")
        
        result = use_case.execute(command)
        
        # Should still succeed with original English text
        assert result.is_success
        assert result.value.meanings[0].definition_vi == "used as a greeting"
        assert result.value.meanings[0].example_vi == "Hello, how are you?"

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
        
        assert result.is_success
        assert len(result.value.meanings) == 2
        assert result.value.meanings[0].definition_vi == "chuyển động nhanh"
        assert result.value.meanings[1].definition_vi == "một lần chạy"

    def test_empty_example(self):
        """Test handling of empty example."""
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
                )
            ]
        )
        
        mock_translation_service = Mock()
        mock_translation_service.translate_batch.return_value = [
            "xin chào",  # word
            "lời chào"  # definition
        ]
        
        use_case = TranslateVocabularyUseCase(mock_dictionary_service, mock_translation_service)
        command = TranslateVocabularyCommand(word="hello")
        
        result = use_case.execute(command)
        
        assert result.is_success
        assert result.value.meanings[0].example == ""
        assert result.value.meanings[0].example_vi == ""

    def test_response_time_tracking(self):
        """Test response time is tracked."""
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
                    example="",
                    example_vi=""
                )
            ]
        )
        
        mock_translation_service = Mock()
        mock_translation_service.translate_batch.return_value = ["xin chào", "lời chào"]
        
        use_case = TranslateVocabularyUseCase(mock_dictionary_service, mock_translation_service)
        command = TranslateVocabularyCommand(word="hello")
        
        result = use_case.execute(command)
        
        assert result.is_success
        assert result.value.response_time_ms >= 0

    def test_context_passed_to_dictionary_service(self):
        """Test that context is passed to dictionary service for phrasal verb detection."""
        mock_dictionary_service = Mock()
        mock_dictionary_service.get_word_definition.return_value = Vocabulary(
            word="get off",
            translate_vi="",
            phonetic="ɡet ɒf",
            meanings=[
                Meaning(
                    part_of_speech="phrasal verb",
                    definition="to leave a bus, train, etc.",
                    definition_vi="",
                    example="I got off the bus",
                    example_vi=""
                )
            ]
        )
        
        mock_translation_service = Mock()
        mock_translation_service.translate_batch.return_value = [
            "xuống xe",
            "rời khỏi xe buýt, tàu hỏa, v.v.",
            "Tôi xuống xe buýt"
        ]
        
        use_case = TranslateVocabularyUseCase(mock_dictionary_service, mock_translation_service)
        command = TranslateVocabularyCommand(word="off", context="I got off the bus")
        
        result = use_case.execute(command)
        
        # Verify context was passed to dictionary service
        mock_dictionary_service.get_word_definition.assert_called_once_with(
            word="off",
            context="I got off the bus"
        )
        
        assert result.is_success
        assert result.value.word == "get off"
