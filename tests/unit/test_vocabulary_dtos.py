"""Unit tests for vocabulary DTOs."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pytest
from pydantic import ValidationError

from application.dtos.vocabulary_dtos import (
    TranslateVocabularyCommand,
    MeaningDTO,
    TranslateVocabularyResponse,
    SynonymDTO,
    DefinitionDTO
)


class TestTranslateVocabularyCommand:
    """Tests for TranslateVocabularyCommand DTO."""

    def test_valid_command_with_word_only(self):
        """Test creating command with only word field."""
        command = TranslateVocabularyCommand(word="hello")
        
        assert command.word == "hello"
        assert command.sentence is None
        assert command.context is None

    def test_valid_command_with_all_fields(self):
        """Test creating command with all fields."""
        command = TranslateVocabularyCommand(
            word="off",
            sentence="I got off the bus",
            context="I got off the bus"
        )
        
        assert command.word == "off"
        assert command.sentence == "I got off the bus"
        assert command.context == "I got off the bus"

    def test_word_normalization(self):
        """Test word is normalized to lowercase and trimmed."""
        command = TranslateVocabularyCommand(word="  HELLO  ")
        
        assert command.word == "hello"

    def test_phrasal_verb_with_space(self):
        """Test phrasal verb with space is accepted."""
        command = TranslateVocabularyCommand(word="get off")
        
        assert command.word == "get off"

    def test_word_with_hyphen(self):
        """Test word with hyphen is accepted."""
        command = TranslateVocabularyCommand(word="well-known")
        
        assert command.word == "well-known"

    def test_word_with_apostrophe(self):
        """Test word with apostrophe is accepted."""
        command = TranslateVocabularyCommand(word="don't")
        
        assert command.word == "don't"

    def test_empty_word_raises_error(self):
        """Test empty word raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            TranslateVocabularyCommand(word="")
        
        assert "word" in str(exc_info.value)

    def test_word_too_long_raises_error(self):
        """Test word exceeding max length raises validation error."""
        long_word = "a" * 101
        
        with pytest.raises(ValidationError) as exc_info:
            TranslateVocabularyCommand(word=long_word)
        
        assert "word" in str(exc_info.value)

    def test_word_with_numbers_raises_error(self):
        """Test word with numbers raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            TranslateVocabularyCommand(word="hello123")
        
        assert "Word should only contain letters" in str(exc_info.value)

    def test_word_with_special_chars_raises_error(self):
        """Test word with special characters raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            TranslateVocabularyCommand(word="hello@world")
        
        assert "Word should only contain letters" in str(exc_info.value)

    def test_context_max_length(self):
        """Test context field respects max length."""
        long_context = "a" * 500  # Exactly 500 chars
        command = TranslateVocabularyCommand(word="test", context=long_context)
        
        assert command.context == long_context
        assert len(command.context) == 500

    def test_context_too_long_raises_error(self):
        """Test context exceeding max length raises validation error."""
        long_context = "a" * 501
        
        with pytest.raises(ValidationError) as exc_info:
            TranslateVocabularyCommand(word="test", context=long_context)
        
        assert "context" in str(exc_info.value)


class TestMeaningDTO:
    """Tests for MeaningDTO."""

    def test_valid_meaning_with_all_fields(self):
        """Test creating MeaningDTO with all fields."""
        meaning = MeaningDTO(
            part_of_speech="noun",
            definition="a greeting",
            definition_vi="lời chào",
            example="Hello there!",
            example_vi="Xin chào!"
        )
        
        assert meaning.part_of_speech == "noun"
        assert meaning.definition == "a greeting"
        assert meaning.definition_vi == "lời chào"
        assert meaning.example == "Hello there!"
        assert meaning.example_vi == "Xin chào!"

    def test_valid_meaning_minimal_fields(self):
        """Test creating MeaningDTO with only required fields."""
        meaning = MeaningDTO(
            part_of_speech="verb",
            definition="to greet someone"
        )
        
        assert meaning.part_of_speech == "verb"
        assert meaning.definition == "to greet someone"
        assert meaning.definition_vi == ""
        assert meaning.example == ""
        assert meaning.example_vi == ""

    def test_empty_part_of_speech_raises_error(self):
        """Test empty part_of_speech raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            MeaningDTO(part_of_speech="", definition="test")
        
        assert "part_of_speech" in str(exc_info.value)

    def test_empty_definition_raises_error(self):
        """Test empty definition raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            MeaningDTO(part_of_speech="noun", definition="")
        
        assert "definition" in str(exc_info.value)

    def test_part_of_speech_too_long_raises_error(self):
        """Test part_of_speech exceeding max length raises validation error."""
        long_pos = "a" * 51
        
        with pytest.raises(ValidationError) as exc_info:
            MeaningDTO(part_of_speech=long_pos, definition="test")
        
        assert "part_of_speech" in str(exc_info.value)


class TestTranslateVocabularyResponse:
    """Tests for TranslateVocabularyResponse DTO."""

    def test_valid_response_with_all_fields(self):
        """Test creating response with all fields."""
        meanings = [
            MeaningDTO(
                part_of_speech="noun",
                definition="a greeting",
                definition_vi="lời chào"
            )
        ]
        
        response = TranslateVocabularyResponse(
            word="hello",
            translation_vi="xin chào",
            phonetic="/həˈləʊ/",
            audio_url="https://example.com/hello.mp3",
            meanings=meanings,
            response_time_ms=150,
            cached=True
        )
        
        assert response.word == "hello"
        assert response.translation_vi == "xin chào"
        assert response.phonetic == "/həˈləʊ/"
        assert response.audio_url == "https://example.com/hello.mp3"
        assert len(response.meanings) == 1
        assert response.response_time_ms == 150
        assert response.cached is True

    def test_valid_response_minimal_fields(self):
        """Test creating response with only required fields."""
        response = TranslateVocabularyResponse(
            word="test",
            translation_vi="kiểm tra"
        )
        
        assert response.word == "test"
        assert response.translation_vi == "kiểm tra"
        assert response.phonetic == ""
        assert response.audio_url is None
        assert response.meanings == []
        assert response.definitions == []
        assert response.synonyms == []
        assert response.response_time_ms == 0
        assert response.cached is False

    def test_backward_compatibility_fields(self):
        """Test backward compatibility fields are present."""
        response = TranslateVocabularyResponse(
            word="hello",
            translation_vi="xin chào"
        )
        
        # Backward compatibility fields
        assert hasattr(response, "word")
        assert hasattr(response, "translation_vi")
        
        # New fields
        assert hasattr(response, "phonetic")
        assert hasattr(response, "audio_url")
        assert hasattr(response, "meanings")

    def test_response_with_multiple_meanings(self):
        """Test response with multiple meanings."""
        meanings = [
            MeaningDTO(part_of_speech="noun", definition="def 1"),
            MeaningDTO(part_of_speech="verb", definition="def 2"),
            MeaningDTO(part_of_speech="adjective", definition="def 3")
        ]
        
        response = TranslateVocabularyResponse(
            word="run",
            translation_vi="chạy",
            meanings=meanings
        )
        
        assert len(response.meanings) == 3
        assert response.meanings[0].part_of_speech == "noun"
        assert response.meanings[1].part_of_speech == "verb"
        assert response.meanings[2].part_of_speech == "adjective"

    def test_response_with_empty_meanings(self):
        """Test response with empty meanings list."""
        response = TranslateVocabularyResponse(
            word="test",
            translation_vi="kiểm tra",
            meanings=[]
        )
        
        assert response.meanings == []

    def test_response_serialization(self):
        """Test response can be serialized to dict."""
        meaning = MeaningDTO(
            part_of_speech="noun",
            definition="a greeting",
            definition_vi="lời chào"
        )
        
        response = TranslateVocabularyResponse(
            word="hello",
            translation_vi="xin chào",
            phonetic="/həˈləʊ/",
            meanings=[meaning]
        )
        
        data = response.model_dump()
        
        assert data["word"] == "hello"
        assert data["translation_vi"] == "xin chào"
        assert data["phonetic"] == "/həˈləʊ/"
        assert len(data["meanings"]) == 1
        assert data["meanings"][0]["part_of_speech"] == "noun"


class TestSynonymDTO:
    """Tests for SynonymDTO."""

    def test_valid_synonym_with_translation(self):
        """Test creating SynonymDTO with translation."""
        synonym = SynonymDTO(en="hi", vi="chào")
        
        assert synonym.en == "hi"
        assert synonym.vi == "chào"

    def test_valid_synonym_without_translation(self):
        """Test creating SynonymDTO without translation."""
        synonym = SynonymDTO(en="greetings")
        
        assert synonym.en == "greetings"
        assert synonym.vi == ""


class TestDefinitionDTO:
    """Tests for DefinitionDTO (legacy)."""

    def test_valid_definition_with_all_fields(self):
        """Test creating DefinitionDTO with all fields."""
        definition = DefinitionDTO(
            part_of_speech="noun",
            definition_en="a greeting",
            definition_vi="lời chào",
            example_en="Hello there!",
            example_vi="Xin chào!"
        )
        
        assert definition.part_of_speech == "noun"
        assert definition.definition_en == "a greeting"
        assert definition.definition_vi == "lời chào"
        assert definition.example_en == "Hello there!"
        assert definition.example_vi == "Xin chào!"

    def test_valid_definition_minimal_fields(self):
        """Test creating DefinitionDTO with only required fields."""
        definition = DefinitionDTO(
            part_of_speech="verb",
            definition_en="to greet"
        )
        
        assert definition.part_of_speech == "verb"
        assert definition.definition_en == "to greet"
        assert definition.definition_vi == ""
        assert definition.example_en == ""
        assert definition.example_vi == ""
