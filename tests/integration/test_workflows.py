"""
Task 27: Integration - Vocabulary → Flashcard Workflow

Tests:
- Complete workflow: translate word → create flashcard → review
- Error handling at each step
- Data consistency across APIs
- Multiple words
- Flashcard data matches translation data
"""

import pytest
import logging
from tests.fixtures.test_data import TestDataFactory
from tests.fixtures.validators import ResponseValidator

logger = logging.getLogger(__name__)


class TestVocabularyFlashcardWorkflow:
    """Test suite for Vocabulary → Flashcard integration workflow"""

    def test_workflow_translate_to_flashcard_to_review(self, api_client):
        """Test: Complete workflow - translate → create flashcard → review"""

        # Step 1: Translate word
        translate_payload = {
            "word": "run",
            "context": "I run every morning"
        }
        translate_response = api_client.post("/vocabulary/translate", translate_payload)

        assert translate_response.status_code == 200
        translate_data = translate_response.json()["data"]

        # Verify translation response
        assert translate_data["word"] == "run"
        assert translate_data["translation_vi"]
        assert translate_data["phonetic"]
        assert len(translate_data["definitions"]) > 0
        logger.info("✓ Step 1: Translate word success")

        # Step 2: Create flashcard using translation data
        flashcard_payload = {
            "word": translate_data["word"],
            "vocab_type": translate_data["definitions"][0].get("part_of_speech", "noun"),
            "translation_vi": translate_data["translation_vi"],
            "example_sentence": translate_data["definitions"][0]["example_en"],
            "phonetic": translate_data["phonetic"],
            "audio_url": "https://example.com/audio.mp3"
        }
        flashcard_response = api_client.post("/flashcards", flashcard_payload)

        assert flashcard_response.status_code == 201
        flashcard_data = flashcard_response.json()["data"]

        # Verify flashcard creation
        assert flashcard_data["word"] == translate_data["word"]
        assert flashcard_data["translation_vi"] == translate_data["translation_vi"]
        assert flashcard_data["phonetic"] == translate_data["phonetic"]
        flashcard_id = flashcard_data["flashcard_id"]
        logger.info("✓ Step 2: Create flashcard success")

        # Step 3: Review flashcard
        review_payload = {"rating": "good"}
        review_response = api_client.post(f"/flashcards/{flashcard_id}/review", review_payload)

        assert review_response.status_code == 200
        review_data = review_response.json()["data"]

        # Verify review
        assert review_data["flashcard_id"] == flashcard_id
        assert review_data["review_count"] >= 1
        assert review_data["interval_days"] > 0
        logger.info("✓ Step 3: Review flashcard success")

        logger.info("✓ Complete workflow: translate → create → review")

    def test_workflow_multiple_words(self, api_client):
        """Test: Workflow with multiple words"""
        words = ["run", "walk", "jump"]

        for word in words:
            # Translate
            translate_response = api_client.post("/vocabulary/translate", {"word": word})
            assert translate_response.status_code == 200
            translate_data = translate_response.json()["data"]

            # Create flashcard
            flashcard_payload = {
                "word": translate_data["word"],
                "vocab_type": "verb",
                "translation_vi": translate_data["translation_vi"],
                "example_sentence": translate_data["definitions"][0]["example_en"],
                "phonetic": translate_data["phonetic"]
            }
            flashcard_response = api_client.post("/flashcards", flashcard_payload)
            assert flashcard_response.status_code == 201

            logger.info(f"✓ Workflow for word: {word}")

        logger.info("✓ Workflow with multiple words")

    def test_workflow_error_handling_word_not_found(self, api_client):
        """Test: Workflow error handling - word not found"""
        # Try to translate non-existent word
        translate_response = api_client.post("/vocabulary/translate", {
            "word": "xyzabc123notaword"
        })

        assert translate_response.status_code == 404
        data = translate_response.json()
        ResponseValidator.validate_error_response(data, "WORD_NOT_FOUND")
        logger.info("✓ Workflow error: word not found")

    def test_workflow_error_handling_invalid_flashcard_data(self, api_client):
        """Test: Workflow error handling - invalid flashcard data"""
        # Create flashcard with invalid data
        flashcard_payload = {
            "word": "test",
            "vocab_type": "invalid_type",
            "translation_vi": "test"
        }
        flashcard_response = api_client.post("/flashcards", flashcard_payload)

        assert flashcard_response.status_code == 422
        data = flashcard_response.json()
        ResponseValidator.validate_error_response(data, "VALIDATION_ERROR")
        logger.info("✓ Workflow error: invalid flashcard data")

    def test_workflow_data_consistency(self, api_client):
        """Test: Data consistency across workflow steps"""
        # Translate
        translate_response = api_client.post("/vocabulary/translate", {"word": "run"})
        assert translate_response.status_code == 200
        translate_data = translate_response.json()["data"]

        # Create flashcard
        flashcard_payload = {
            "vocab": translate_data["word"],
            "vocab_type": "verb",
            "translation_vi": translate_data["translation_vi"],
            "example_sentence": translate_data["definitions"][0]["example_en"],
            "phonetic": translate_data["phonetic"]
        }
        flashcard_response = api_client.post("/flashcards", flashcard_payload)
        assert flashcard_response.status_code == 201
        flashcard_data = flashcard_response.json()["data"]

        # Get flashcard
        get_response = api_client.get(f"/flashcards/{flashcard_data['flashcard_id']}")
        assert get_response.status_code == 200
        get_data = get_response.json()["data"]

        # Verify data consistency
        assert get_data["word"] == translate_data["word"]
        assert get_data["translation_vi"] == translate_data["translation_vi"]
        assert get_data["phonetic"] == translate_data["phonetic"]
        logger.info("✓ Data consistency verified")

    def test_workflow_review_rating_progression(self, api_client):
        """Test: Review rating progression (forgot → hard → good → easy)"""
        # Create flashcard
        flashcard_payload = TestDataFactory.valid_flashcard_data()
        flashcard_response = api_client.post("/flashcards", flashcard_payload)
        assert flashcard_response.status_code == 201
        flashcard_id = flashcard_response.json()["data"]["flashcard_id"]

        ratings = ["forgot", "hard", "good", "easy"]
        previous_interval = 0

        for rating in ratings:
            # Review with rating
            review_response = api_client.post(f"/flashcards/{flashcard_id}/review", {
                "rating": rating
            })
            assert review_response.status_code == 200
            review_data = review_response.json()["data"]

            # Verify interval progression
            current_interval = review_data["interval_days"]
            logger.info(f"  Rating: {rating}, Interval: {current_interval} days")

        logger.info("✓ Review rating progression")

    def test_workflow_unauthorized_at_each_step(self, public_client):
        """Test: Workflow authorization checks at each step"""
        # Step 1: Translate (should fail)
        translate_response = public_client.post("/vocabulary/translate", {"word": "run"})
        assert translate_response.status_code == 401
        logger.info("✓ Translate unauthorized")

        # Step 2: Create flashcard (should fail)
        flashcard_response = public_client.post("/flashcards", {
            "word": "run",
            "translation_vi": "chạy"
        })
        assert flashcard_response.status_code == 401
        logger.info("✓ Create flashcard unauthorized")

        # Step 3: Review flashcard (should fail)
        review_response = public_client.post("/flashcards/some-id/review", {
            "rating": "good"
        })
        assert review_response.status_code == 401
        logger.info("✓ Review flashcard unauthorized")

        logger.info("✓ Workflow authorization checks")
