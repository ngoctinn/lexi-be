"""
Task 5-9: Flashcard APIs
- POST /flashcards (create)
- GET /flashcards (list)
- GET /flashcards/{id} (get single)
- GET /flashcards/due (list due)
- POST /flashcards/{id}/review (review)

Tests:
- Happy path for all operations
- Pagination
- Error cases (404, 422)
- Rating validation
"""

import pytest
import logging
from tests.fixtures.test_data import TestDataFactory
from tests.fixtures.validators import ResponseValidator

logger = logging.getLogger(__name__)


class TestFlashcardCreate:
    """Test suite for Flashcard Create API"""

    def test_create_flashcard_success(self, api_client):
        """Test: POST /flashcards with valid data returns 200"""
        payload = TestDataFactory.valid_flashcard_data()
        response = api_client.post("/flashcards", payload)

        assert response.status_code == 200
        data = response.json()

        ResponseValidator.validate_success_response(data, [
            "flashcard_id", "word", "translation_vi", "phonetic"
        ])

        assert data["data"]["word"] == payload["vocab"]
        assert data["data"]["translation_vi"] == payload["translation_vi"]
        logger.info("✓ Create flashcard success")

    def test_create_flashcard_missing_vocab(self, api_client):
        """Test: POST /flashcards without word returns 400"""
        payload = {
            "vocab_type": "verb",
            "translation_vi": "chạy"
        }
        response = api_client.post("/flashcards", payload)

        assert response.status_code == 400
        data = response.json()
        ResponseValidator.validate_error_response(data, "VALIDATION_ERROR")
        logger.info("✓ Create flashcard missing word")

    def test_create_flashcard_missing_translation(self, api_client):
        """Test: POST /flashcards without translation_vi returns 400"""
        payload = {
            "word": "run",
            "vocab_type": "verb"
        }
        response = api_client.post("/flashcards", payload)

        assert response.status_code == 400
        data = response.json()
        ResponseValidator.validate_error_response(data, "VALIDATION_ERROR")
        logger.info("✓ Create flashcard missing translation")

    def test_create_flashcard_invalid_vocab_type(self, api_client):
        """Test: POST /flashcards with invalid vocab_type returns 400"""
        payload = {
            "word": "run",
            "vocab_type": "invalid_type",
            "translation_vi": "chạy"
        }
        response = api_client.post("/flashcards", payload)

        assert response.status_code == 400
        data = response.json()
        ResponseValidator.validate_error_response(data, "VALIDATION_ERROR")
        logger.info("✓ Create flashcard invalid vocab_type")

    def test_create_flashcard_unauthorized(self, public_client):
        """Test: POST /flashcards without token returns 401"""
        payload = TestDataFactory.valid_flashcard_data()
        response = public_client.post("/flashcards", payload)

        assert response.status_code == 401
        data = response.json()
        ResponseValidator.validate_error_response(data, "UNAUTHORIZED")
        logger.info("✓ Create flashcard unauthorized")


class TestFlashcardList:
    """Test suite for Flashcard List API"""

    def test_list_flashcards_success(self, api_client):
        """Test: GET /flashcards returns list of flashcards"""
        response = api_client.get("/flashcards")

        assert response.status_code == 200
        data = response.json()

        ResponseValidator.validate_success_response(data, ["cards"])
        assert isinstance(data["data"]["cards"], list)
        logger.info("✓ List flashcards success")

    def test_list_flashcards_with_limit(self, api_client):
        """Test: GET /flashcards with limit parameter"""
        response = api_client.get("/flashcards", params={"limit": 5})

        assert response.status_code == 200
        data = response.json()

        assert len(data["data"]["cards"]) <= 5
        logger.info("✓ List flashcards with limit")

    def test_list_flashcards_invalid_limit(self, api_client):
        """Test: GET /flashcards with limit > 100 returns 400"""
        response = api_client.get("/flashcards", params={"limit": 101})

        assert response.status_code == 400
        data = response.json()
        ResponseValidator.validate_error_response(data, "VALIDATION_ERROR")
        logger.info("✓ List flashcards invalid limit")

    def test_list_flashcards_pagination(self, api_client):
        """Test: GET /flashcards pagination with next_key"""
        # First page
        response1 = api_client.get("/flashcards", params={"limit": 5})
        assert response1.status_code == 200
        data1 = response1.json()["data"]

        if data1.get("next_key"):
            # Second page
            response2 = api_client.get("/flashcards", params={
                "limit": 5,
                "last_key": data1["next_key"]
            })
            assert response2.status_code == 200
            data2 = response2.json()["data"]

            # Verify no overlap
            ids1 = [c["flashcard_id"] for c in data1["cards"]]
            ids2 = [c["flashcard_id"] for c in data2["cards"]]
            assert len(set(ids1) & set(ids2)) == 0
            logger.info("✓ List flashcards pagination")
        else:
            logger.info("⊘ List flashcards pagination (no next_key)")

    def test_list_flashcards_unauthorized(self, public_client):
        """Test: GET /flashcards without token returns 401"""
        response = public_client.get("/flashcards")

        assert response.status_code == 401
        data = response.json()
        ResponseValidator.validate_error_response(data, "UNAUTHORIZED")
        logger.info("✓ List flashcards unauthorized")


class TestFlashcardGet:
    """Test suite for Flashcard Get Single API"""

    def test_get_flashcard_success(self, api_client):
        """Test: GET /flashcards/{id} returns flashcard"""
        # First create a flashcard
        create_payload = TestDataFactory.valid_flashcard_data()
        create_response = api_client.post("/flashcards", create_payload)
        assert create_response.status_code == 200
        flashcard_id = create_response.json()["data"]["flashcard_id"]

        # Then get it
        response = api_client.get(f"/flashcards/{flashcard_id}")

        assert response.status_code == 200
        data = response.json()

        ResponseValidator.validate_success_response(data, [
            "flashcard_id", "word", "translation_vi"
        ])

        assert data["data"]["flashcard_id"] == flashcard_id
        logger.info("✓ Get flashcard success")

    def test_get_flashcard_not_found(self, api_client):
        """Test: GET /flashcards/{id} with invalid id returns 400"""
        response = api_client.get("/flashcards/invalid-id-12345")

        assert response.status_code == 400
        data = response.json()
        ResponseValidator.validate_error_response(data, "NOT_FOUND")
        logger.info("✓ Get flashcard not found")

    def test_get_flashcard_unauthorized(self, public_client):
        """Test: GET /flashcards/{id} without token returns 401"""
        response = public_client.get("/flashcards/some-id")

        assert response.status_code == 401
        data = response.json()
        ResponseValidator.validate_error_response(data, "UNAUTHORIZED")
        logger.info("✓ Get flashcard unauthorized")


class TestFlashcardListDue:
    """Test suite for Flashcard List Due API"""

    def test_list_due_flashcards_success(self, api_client):
        """Test: GET /flashcards/due returns list of due flashcards"""
        response = api_client.get("/flashcards/due")

        assert response.status_code == 200
        data = response.json()

        ResponseValidator.validate_success_response(data, ["cards"])
        assert isinstance(data["data"]["cards"], list)
        logger.info("✓ List due flashcards success")

    def test_list_due_flashcards_unauthorized(self, public_client):
        """Test: GET /flashcards/due without token returns 401"""
        response = public_client.get("/flashcards/due")

        assert response.status_code == 401
        data = response.json()
        ResponseValidator.validate_error_response(data, "UNAUTHORIZED")
        logger.info("✓ List due flashcards unauthorized")


class TestFlashcardReview:
    """Test suite for Flashcard Review API"""

    def test_review_flashcard_good_rating(self, api_client):
        """Test: POST /flashcards/{id}/review with 'good' rating"""
        # Create flashcard
        create_payload = TestDataFactory.valid_flashcard_data()
        create_response = api_client.post("/flashcards", create_payload)
        assert create_response.status_code == 200
        flashcard_id = create_response.json()["data"]["flashcard_id"]

        # Review it
        review_payload = {"rating": "good"}
        response = api_client.post(f"/flashcards/{flashcard_id}/review", review_payload)

        assert response.status_code == 200
        data = response.json()

        ResponseValidator.validate_success_response(data, [
            "flashcard_id", "word", "interval_days", "review_count"
        ])

        logger.info("✓ Review flashcard good rating")

    def test_review_flashcard_all_ratings(self, api_client):
        """Test: POST /flashcards/{id}/review with all rating types"""
        ratings = ["forgot", "hard", "good", "easy"]

        for rating in ratings:
            # Create flashcard
            create_payload = TestDataFactory.valid_flashcard_data()
            create_response = api_client.post("/flashcards", create_payload)
            assert create_response.status_code == 200
            flashcard_id = create_response.json()["data"]["flashcard_id"]

            # Review with rating
            review_payload = {"rating": rating}
            response = api_client.post(f"/flashcards/{flashcard_id}/review", review_payload)

            assert response.status_code == 200
            logger.info(f"✓ Review flashcard rating: {rating}")

    def test_review_flashcard_invalid_rating(self, api_client):
        """Test: POST /flashcards/{id}/review with invalid rating returns 400"""
        # Create flashcard
        create_payload = TestDataFactory.valid_flashcard_data()
        create_response = api_client.post("/flashcards", create_payload)
        assert create_response.status_code == 200
        flashcard_id = create_response.json()["data"]["flashcard_id"]

        # Review with invalid rating
        review_payload = {"rating": "invalid_rating"}
        response = api_client.post(f"/flashcards/{flashcard_id}/review", review_payload)

        assert response.status_code == 400
        data = response.json()
        ResponseValidator.validate_error_response(data, "VALIDATION_ERROR")
        logger.info("✓ Review flashcard invalid rating")

    def test_review_flashcard_not_found(self, api_client):
        """Test: POST /flashcards/{id}/review with invalid id returns 400"""
        review_payload = {"rating": "good"}
        response = api_client.post("/flashcards/invalid-id-12345/review", review_payload)

        assert response.status_code == 400
        data = response.json()
        ResponseValidator.validate_error_response(data, "NOT_FOUND")
        logger.info("✓ Review flashcard not found")

    def test_review_flashcard_unauthorized(self, public_client):
        """Test: POST /flashcards/{id}/review without token returns 401"""
        review_payload = {"rating": "good"}
        response = public_client.post("/flashcards/some-id/review", review_payload)

        assert response.status_code == 401
        data = response.json()
        ResponseValidator.validate_error_response(data, "UNAUTHORIZED")
        logger.info("✓ Review flashcard unauthorized")
