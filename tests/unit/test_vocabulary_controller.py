"""
Unit tests for VocabularyController.
Tests HTTP request handling, error mapping, and response formatting.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import json
import pytest
from unittest.mock import Mock, MagicMock

from application.dtos.vocabulary_dtos import (
    TranslateVocabularyResponse,
    MeaningDTO,
)
from domain.exceptions.dictionary_exceptions import WordNotFoundError, DictionaryServiceError
from interfaces.controllers.vocabulary_controller import VocabularyController
from shared.result import Result


class TestVocabularyController:
    """Test VocabularyController request handling and error mapping."""

    def test_translate_success(self):
        """Test successful vocabulary translation returns 200 with data."""
        # Arrange
        mock_use_case = Mock()
        response = TranslateVocabularyResponse(
            word="hello",
            translation_vi="xin chào",
            phonetic="həˈləʊ",
            audio_url="https://example.com/hello.mp3",
            meanings=[
                MeaningDTO(
                    part_of_speech="exclamation",
                    definition="used as a greeting",
                    definition_vi="được dùng để chào hỏi",
                    example="hello there!",
                    example_vi="xin chào!"
                )
            ],
            response_time_ms=150,
            cached=False
        )
        mock_use_case.execute.return_value = Result.success(response)
        
        controller = VocabularyController(translate_use_case=mock_use_case)
        body_str = json.dumps({"word": "hello", "context": "hello there!"})
        
        # Act
        result = controller.translate(body_str)
        
        # Assert
        assert result.is_success
        assert result.success.word == "hello"
        assert result.success.translation_vi == "xin chào"
        assert result.success.phonetic == "həˈləʊ"
        assert len(result.success.definitions) == 0  # Mapper converts meanings to definitions

    def test_translate_word_not_found_returns_404_error(self):
        """Test word not found returns NOT_FOUND error code."""
        # Arrange
        mock_use_case = Mock()
        mock_use_case.execute.return_value = Result.failure(
            WordNotFoundError("Word 'xyz' not found in dictionary")
        )
        
        controller = VocabularyController(translate_use_case=mock_use_case)
        body_str = json.dumps({"word": "xyz"})
        
        # Act
        result = controller.translate(body_str)
        
        # Assert
        assert not result.is_success
        assert result.error.code == "WORD_NOT_FOUND"
        assert "not found" in result.error.message.lower()

    def test_translate_dictionary_service_error_returns_503_error(self):
        """Test dictionary service unavailable returns SERVICE_ERROR code."""
        # Arrange
        mock_use_case = Mock()
        mock_use_case.execute.return_value = Result.failure(
            DictionaryServiceError("Dictionary API timeout")
        )
        
        controller = VocabularyController(translate_use_case=mock_use_case)
        body_str = json.dumps({"word": "hello"})
        
        # Act
        result = controller.translate(body_str)
        
        # Assert
        assert not result.is_success
        assert result.error.code == "DICTIONARY_SERVICE_ERROR"
        assert "unavailable" in result.error.message.lower()

    def test_translate_invalid_json_returns_400_error(self):
        """Test invalid JSON returns BAD_REQUEST error."""
        # Arrange
        controller = VocabularyController(translate_use_case=Mock())
        body_str = "invalid json"
        
        # Act
        result = controller.translate(body_str)
        
        # Assert
        assert not result.is_success
        assert result.error.code == "BAD_REQUEST"
        assert "json" in result.error.message.lower()

    def test_translate_validation_error_returns_400_error(self):
        """Test validation error (empty word) returns VALIDATION_ERROR."""
        # Arrange
        mock_use_case = Mock()
        controller = VocabularyController(translate_use_case=mock_use_case)
        body_str = json.dumps({"word": ""})  # Empty word should fail validation
        
        # Act
        result = controller.translate(body_str)
        
        # Assert
        assert not result.is_success
        assert result.error.code == "VALIDATION_ERROR"

    def test_translate_with_context_passes_context_to_use_case(self):
        """Test that context field is passed to use case for phrasal verb detection."""
        # Arrange
        mock_use_case = Mock()
        response = TranslateVocabularyResponse(
            word="get off",
            translation_vi="xuống xe",
            phonetic="",
            meanings=[],
            response_time_ms=100,
            cached=False
        )
        mock_use_case.execute.return_value = Result.success(response)
        
        controller = VocabularyController(translate_use_case=mock_use_case)
        body_str = json.dumps({"word": "off", "context": "I got off the bus"})
        
        # Act
        result = controller.translate(body_str)
        
        # Assert
        assert result.is_success
        # Verify use case was called with command containing context
        call_args = mock_use_case.execute.call_args[0][0]
        assert call_args.word == "off"
        assert call_args.context == "I got off the bus"

    def test_translate_without_use_case_returns_error(self):
        """Test controller without use case returns NOT_CONFIGURED error."""
        # Arrange
        controller = VocabularyController(translate_use_case=None)
        body_str = json.dumps({"word": "hello"})
        
        # Act
        result = controller.translate(body_str)
        
        # Assert
        assert not result.is_success
        assert result.error.code == "NOT_CONFIGURED"

    def test_translate_logs_all_requests(self, caplog):
        """Test that all translation requests are logged."""
        # Arrange
        mock_use_case = Mock()
        response = TranslateVocabularyResponse(
            word="hello",
            translation_vi="xin chào",
            phonetic="",
            meanings=[],
            response_time_ms=100,
            cached=False
        )
        mock_use_case.execute.return_value = Result.success(response)
        
        controller = VocabularyController(translate_use_case=mock_use_case)
        body_str = json.dumps({"word": "hello"})
        
        # Act
        with caplog.at_level("INFO"):
            result = controller.translate(body_str)
        
        # Assert
        assert "Translating vocabulary" in caplog.text
        assert "Translation successful" in caplog.text
