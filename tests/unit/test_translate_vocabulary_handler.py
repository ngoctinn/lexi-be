"""
Unit tests for translate_vocabulary_handler.
Tests HTTP status code mapping and error handling.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import json
import pytest
from unittest.mock import Mock, patch

from application.dtos.vocabulary_dtos import TranslateVocabularyResponse, MeaningDTO
from domain.exceptions.dictionary_exceptions import WordNotFoundError, DictionaryServiceError
from interfaces.view_models.base import OperationResult
from interfaces.view_models.vocabulary_vm import VocabularyTranslationViewModel


class TestTranslateVocabularyHandler:
    """Test handler HTTP status code mapping."""

    @patch('src.infrastructure.handlers.vocabulary.translate_vocabulary_handler.vocabulary_controller')
    def test_handler_returns_200_on_success(self, mock_controller):
        """Test handler returns 200 for successful translation."""
        # Arrange
        from src.infrastructure.handlers.vocabulary.translate_vocabulary_handler import handler
        
        view_model = VocabularyTranslationViewModel(
            word="hello",
            translation_vi="xin chào",
            phonetic="həˈləʊ",
            definitions=[],
            synonyms=[],
            response_time_ms=100,
            cached=False
        )
        mock_controller.translate.return_value = OperationResult.succeed(view_model)
        
        event = {
            "body": json.dumps({"word": "hello"}),
            "requestContext": {
                "authorizer": {
                    "claims": {"sub": "user123"}
                }
            }
        }
        
        # Act
        response = handler(event, None)
        
        # Assert
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["data"]["word"] == "hello"

    @patch('src.infrastructure.handlers.vocabulary.translate_vocabulary_handler.vocabulary_controller')
    def test_handler_returns_404_for_word_not_found(self, mock_controller):
        """Test handler returns 404 when word not found."""
        # Arrange
        from src.infrastructure.handlers.vocabulary.translate_vocabulary_handler import handler
        
        mock_controller.translate.return_value = OperationResult.fail(
            "Word not found in dictionary",
            "WORD_NOT_FOUND"
        )
        
        event = {
            "body": json.dumps({"word": "xyz"}),
            "requestContext": {
                "authorizer": {
                    "claims": {"sub": "user123"}
                }
            }
        }
        
        # Act
        response = handler(event, None)
        
        # Assert
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert body["success"] is False
        assert body["error"] == "WORD_NOT_FOUND"

    @patch('src.infrastructure.handlers.vocabulary.translate_vocabulary_handler.vocabulary_controller')
    def test_handler_returns_503_for_dictionary_service_error(self, mock_controller):
        """Test handler returns 503 when dictionary service unavailable."""
        # Arrange
        from src.infrastructure.handlers.vocabulary.translate_vocabulary_handler import handler
        
        mock_controller.translate.return_value = OperationResult.fail(
            "Dictionary service temporarily unavailable",
            "DICTIONARY_SERVICE_ERROR"
        )
        
        event = {
            "body": json.dumps({"word": "hello"}),
            "requestContext": {
                "authorizer": {
                    "claims": {"sub": "user123"}
                }
            }
        }
        
        # Act
        response = handler(event, None)
        
        # Assert
        assert response["statusCode"] == 503
        body = json.loads(response["body"])
        assert body["success"] is False
        assert body["error"] == "DICTIONARY_SERVICE_ERROR"

    @patch('src.infrastructure.handlers.vocabulary.translate_vocabulary_handler.vocabulary_controller')
    def test_handler_returns_400_for_validation_error(self, mock_controller):
        """Test handler returns 400 for validation errors."""
        # Arrange
        from src.infrastructure.handlers.vocabulary.translate_vocabulary_handler import handler
        
        mock_controller.translate.return_value = OperationResult.fail(
            "Invalid request data",
            "VALIDATION_ERROR"
        )
        
        event = {
            "body": json.dumps({"word": ""}),
            "requestContext": {
                "authorizer": {
                    "claims": {"sub": "user123"}
                }
            }
        }
        
        # Act
        response = handler(event, None)
        
        # Assert
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["success"] is False
        assert body["error"] == "VALIDATION_ERROR"

    def test_handler_returns_401_for_missing_auth(self):
        """Test handler returns 401 when Cognito claims missing."""
        # Arrange
        from src.infrastructure.handlers.vocabulary.translate_vocabulary_handler import handler
        
        event = {
            "body": json.dumps({"word": "hello"}),
            "requestContext": {}  # Missing authorizer
        }
        
        # Act
        response = handler(event, None)
        
        # Assert
        assert response["statusCode"] == 401
        body = json.loads(response["body"])
        assert "Unauthorized" in body["error"]
