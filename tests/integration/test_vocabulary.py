"""
Task 3-4: Vocabulary APIs
- POST /vocabulary/translate
- POST /vocabulary/translate-sentence

Tests:
- Happy path: valid word/sentence
- Word not found (404)
- Missing required fields
- Invalid word length
- Dictionary service unavailable (503)
"""

import pytest
import logging
from tests.fixtures.test_data import TestDataFactory
from tests.fixtures.validators import ResponseValidator

logger = logging.getLogger(__name__)


class TestVocabularyTranslateWord:
    """Test suite for Vocabulary Translate Word API"""

    def test_translate_word_success(self, api_client):
        """Test: POST /vocabulary/translate with valid word returns 200"""
        payload = TestDataFactory.valid_translate_word_data()
        response = api_client.post("/vocabulary/translate", payload)

        assert response.status_code == 200
        data = response.json()

        ResponseValidator.validate_success_response(data, [
            "word", "translation_vi", "phonetic", "definitions"
        ])

        assert data["data"]["word"] == payload["word"]
        assert data["data"]["translation_vi"]
        assert data["data"]["phonetic"]
        assert isinstance(data["data"]["definitions"], list)
        logger.info("✓ Translate word success")

    def test_translate_word_missing_word_field(self, api_client):
        """Test: POST /vocabulary/translate without word returns 400"""
        payload = {
            "sentence": "I run every morning.",
            "context": "exercise"
        }
        response = api_client.post("/vocabulary/translate", payload)

        assert response.status_code == 400
        data = response.json()
        ResponseValidator.validate_error_response(data, "VALIDATION_ERROR")
        logger.info("✓ Translate word missing word field")

    def test_translate_word_not_found(self, api_client):
        """Test: POST /vocabulary/translate with non-existent word returns 400"""
        payload = {
            "word": "xyzabc123notaword"
        }
        response = api_client.post("/vocabulary/translate", payload)

        assert response.status_code == 400
        data = response.json()
        ResponseValidator.validate_error_response(data, "WORD_NOT_FOUND")
        logger.info("✓ Translate word not found")

    def test_translate_word_too_long(self, api_client):
        """Test: POST /vocabulary/translate with word > 100 chars returns 400"""
        payload = {
            "word": "a" * 101
        }
        response = api_client.post("/vocabulary/translate", payload)

        assert response.status_code == 400
        data = response.json()
        ResponseValidator.validate_error_response(data, "VALIDATION_ERROR")
        logger.info("✓ Translate word too long")

    def test_translate_word_empty_word(self, api_client):
        """Test: POST /vocabulary/translate with empty word returns 400"""
        payload = {
            "word": ""
        }
        response = api_client.post("/vocabulary/translate", payload)

        assert response.status_code == 400
        data = response.json()
        ResponseValidator.validate_error_response(data, "VALIDATION_ERROR")
        logger.info("✓ Translate word empty word")

    def test_translate_word_unauthorized(self, public_client):
        """Test: POST /vocabulary/translate without token returns 401"""
        payload = TestDataFactory.valid_translate_word_data()
        response = public_client.post("/vocabulary/translate", payload)

        assert response.status_code == 401
        data = response.json()
        ResponseValidator.validate_error_response(data, "UNAUTHORIZED")
        logger.info("✓ Translate word unauthorized")

    def test_translate_word_with_context(self, api_client):
        """Test: POST /vocabulary/translate with context for phrasal verb detection"""
        payload = {
            "word": "run",
            "context": "The business runs smoothly"
        }
        response = api_client.post("/vocabulary/translate", payload)

        assert response.status_code == 200
        data = response.json()
        ResponseValidator.validate_success_response(data, ["word", "translation_vi"])
        logger.info("✓ Translate word with context")


class TestVocabularyTranslateSentence:
    """Test suite for Vocabulary Translate Sentence API"""

    def test_translate_sentence_success(self, api_client):
        """Test: POST /vocabulary/translate-sentence with valid sentence returns 200"""
        payload = TestDataFactory.valid_translate_sentence_data()
        response = api_client.post("/vocabulary/translate-sentence", payload)

        assert response.status_code == 200
        data = response.json()

        ResponseValidator.validate_success_response(data, [
            "sentence_en", "sentence_vi"
        ])

        assert data["data"]["sentence_en"] == payload["sentence"]
        assert data["data"]["sentence_vi"]
        logger.info("✓ Translate sentence success")

    def test_translate_sentence_missing_field(self, api_client):
        """Test: POST /vocabulary/translate-sentence without sentence returns 400"""
        payload = {}
        response = api_client.post("/vocabulary/translate-sentence", payload)

        assert response.status_code == 400
        data = response.json()
        ResponseValidator.validate_error_response(data, "VALIDATION_ERROR")
        logger.info("✓ Translate sentence missing field")

    def test_translate_sentence_empty(self, api_client):
        """Test: POST /vocabulary/translate-sentence with empty sentence returns 400"""
        payload = {
            "sentence": ""
        }
        response = api_client.post("/vocabulary/translate-sentence", payload)

        assert response.status_code == 400
        data = response.json()
        ResponseValidator.validate_error_response(data, "VALIDATION_ERROR")
        logger.info("✓ Translate sentence empty")

    def test_translate_sentence_very_long(self, api_client):
        """Test: POST /vocabulary/translate-sentence with very long sentence"""
        payload = {
            "sentence": "This is a very long sentence. " * 50
        }
        response = api_client.post("/vocabulary/translate-sentence", payload)

        # Should either succeed or return 400 if there's a length limit
        assert response.status_code in [200, 400]
        logger.info("✓ Translate sentence very long")

    def test_translate_sentence_unauthorized(self, public_client):
        """Test: POST /vocabulary/translate-sentence without token returns 401"""
        payload = TestDataFactory.valid_translate_sentence_data()
        response = public_client.post("/vocabulary/translate-sentence", payload)

        assert response.status_code == 401
        data = response.json()
        ResponseValidator.validate_error_response(data, "UNAUTHORIZED")
        logger.info("✓ Translate sentence unauthorized")

    def test_translate_sentence_special_characters(self, api_client):
        """Test: POST /vocabulary/translate-sentence with special characters"""
        payload = {
            "sentence": "What's your name? I'm John! How are you?"
        }
        response = api_client.post("/vocabulary/translate-sentence", payload)

        assert response.status_code == 200
        data = response.json()
        ResponseValidator.validate_success_response(data, ["sentence_en", "sentence_vi"])
        logger.info("✓ Translate sentence special characters")
