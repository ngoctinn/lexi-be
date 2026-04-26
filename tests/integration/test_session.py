"""
Task 11-15: Speaking Session APIs
- POST /sessions (create)
- GET /sessions (list)
- GET /sessions/{id} (get single)
- POST /sessions/{id}/turns (submit turn)
- POST /sessions/{id}/complete (complete)

Tests:
- Happy path for all operations
- Error cases (404, 422)
- Session state validation
- Turn submission and AI response
"""

import pytest
import logging
from tests.fixtures.test_data import TestDataFactory
from tests.fixtures.validators import ResponseValidator

logger = logging.getLogger(__name__)


class TestSessionCreate:
    """Test suite for Session Create API"""

    def test_create_session_success(self, api_client):
        """Test: POST /sessions with valid data returns 200"""
        payload = TestDataFactory.valid_session_data()
        response = api_client.post("/sessions", payload)

        assert response.status_code == 200
        data = response.json()

        ResponseValidator.validate_success_response(data, [
            "session_id", "user_id", "scenario_id", "status"
        ])

        assert data["data"]["status"] == "ACTIVE"
        assert data["data"]["scenario_id"] == payload["scenario_id"]
        logger.info("✓ Create session success")

    def test_create_session_missing_scenario_id(self, api_client):
        """Test: POST /sessions without scenario_id returns 400"""
        payload = {
            "learner_role_id": "customer",
            "ai_role_id": "waiter",
            "ai_gender": "female",
            "level": "B1",
            "selected_goal": "order food"
        }
        response = api_client.post("/sessions", payload)

        assert response.status_code == 400
        data = response.json()
        ResponseValidator.validate_error_response(data, "VALIDATION_ERROR")
        logger.info("✓ Create session missing scenario_id")

    def test_create_session_missing_level(self, api_client):
        """Test: POST /sessions without level returns 400"""
        payload = {
            "scenario_id": "restaurant-ordering",
            "learner_role_id": "customer",
            "ai_role_id": "waiter",
            "ai_gender": "female",
            "selected_goal": "order food"
        }
        response = api_client.post("/sessions", payload)

        assert response.status_code == 400
        data = response.json()
        ResponseValidator.validate_error_response(data, "VALIDATION_ERROR")
        logger.info("✓ Create session missing level")

    def test_create_session_invalid_level(self, api_client):
        """Test: POST /sessions with invalid level returns 400"""
        payload = {
            "scenario_id": "restaurant-ordering",
            "learner_role_id": "customer",
            "ai_role_id": "waiter",
            "ai_gender": "female",
            "level": "INVALID",
            "selected_goal": "order food"
        }
        response = api_client.post("/sessions", payload)

        assert response.status_code == 400
        data = response.json()
        ResponseValidator.validate_error_response(data, "VALIDATION_ERROR")
        logger.info("✓ Create session invalid level")

    def test_create_session_invalid_scenario_id(self, api_client):
        """Test: POST /sessions with invalid scenario_id returns 400"""
        payload = {
            "scenario_id": "invalid-scenario-12345",
            "learner_role_id": "customer",
            "ai_role_id": "waiter",
            "ai_gender": "female",
            "level": "B1",
            "selected_goal": "order food"
        }
        response = api_client.post("/sessions", payload)

        assert response.status_code == 400
        data = response.json()
        ResponseValidator.validate_error_response(data, "NOT_FOUND")
        logger.info("✓ Create session invalid scenario_id")

    def test_create_session_unauthorized(self, public_client):
        """Test: POST /sessions without token returns 401"""
        payload = TestDataFactory.valid_session_data()
        response = public_client.post("/sessions", payload)

        assert response.status_code == 401
        data = response.json()
        ResponseValidator.validate_error_response(data, "UNAUTHORIZED")
        logger.info("✓ Create session unauthorized")


class TestSessionList:
    """Test suite for Session List API"""

    def test_list_sessions_success(self, api_client):
        """Test: GET /sessions returns list of user's sessions"""
        response = api_client.get("/sessions")

        assert response.status_code == 200
        data = response.json()

        ResponseValidator.validate_success_response(data, [
            "sessions", "total"
        ])

        assert isinstance(data["data"]["sessions"], list)
        logger.info("✓ List sessions success")

    def test_list_sessions_with_limit(self, api_client):
        """Test: GET /sessions with limit parameter"""
        response = api_client.get("/sessions", params={"limit": 5})

        assert response.status_code == 200
        data = response.json()

        assert len(data["data"]["sessions"]) <= 5
        logger.info("✓ List sessions with limit")

    def test_list_sessions_unauthorized(self, public_client):
        """Test: GET /sessions without token returns 401"""
        response = public_client.get("/sessions")

        assert response.status_code == 401
        data = response.json()
        ResponseValidator.validate_error_response(data, "UNAUTHORIZED")
        logger.info("✓ List sessions unauthorized")


class TestSessionGet:
    """Test suite for Session Get Single API"""

    def test_get_session_success(self, api_client):
        """Test: GET /sessions/{id} returns session details"""
        # Create session first
        create_payload = TestDataFactory.valid_session_data()
        create_response = api_client.post("/sessions", create_payload)
        assert create_response.status_code == 201
        session_id = create_response.json()["data"]["session_id"]

        # Get session
        response = api_client.get(f"/sessions/{session_id}")

        assert response.status_code == 200
        data = response.json()

        ResponseValidator.validate_success_response(data, [
            "session_id", "scenario_id", "status", "turns"
        ])

        assert data["data"]["session_id"] == session_id
        assert isinstance(data["data"]["turns"], list)
        logger.info("✓ Get session success")

    def test_get_session_not_found(self, api_client):
        """Test: GET /sessions/{id} with invalid id returns 400"""
        response = api_client.get("/sessions/invalid-session-12345")

        assert response.status_code == 400
        data = response.json()
        ResponseValidator.validate_error_response(data, "NOT_FOUND")
        logger.info("✓ Get session not found")

    def test_get_session_unauthorized(self, public_client):
        """Test: GET /sessions/{id} without token returns 401"""
        response = public_client.get("/sessions/some-id")

        assert response.status_code == 401
        data = response.json()
        ResponseValidator.validate_error_response(data, "UNAUTHORIZED")
        logger.info("✓ Get session unauthorized")


class TestSessionSubmitTurn:
    """Test suite for Session Submit Turn API"""

    def test_submit_turn_success(self, api_client):
        """Test: POST /sessions/{id}/turns with valid data"""
        # Create session
        create_payload = TestDataFactory.valid_session_data()
        create_response = api_client.post("/sessions", create_payload)
        assert create_response.status_code == 200
        session_id = create_response.json()["data"]["session_id"]

        # Submit turn
        turn_payload = TestDataFactory.valid_session_turn_data()
        response = api_client.post(f"/sessions/{session_id}/turns", turn_payload)

        assert response.status_code == 200
        data = response.json()

        ResponseValidator.validate_success_response(data, [
            "session_id", "status", "user_turn", "ai_turn"
        ])

        assert data["data"]["user_turn"]["content"] == turn_payload["text"]
        assert data["data"]["ai_turn"]["content"]  # AI should respond
        logger.info("✓ Submit turn success")

    def test_submit_turn_missing_text(self, api_client):
        """Test: POST /sessions/{id}/turns without text returns 400"""
        # Create session
        create_payload = TestDataFactory.valid_session_data()
        create_response = api_client.post("/sessions", create_payload)
        assert create_response.status_code == 200
        session_id = create_response.json()["data"]["session_id"]

        # Submit turn without text
        turn_payload = {
            "audio_url": "s3://bucket/audio.mp3",
            "is_hint_used": False
        }
        response = api_client.post(f"/sessions/{session_id}/turns", turn_payload)

        assert response.status_code == 400
        data = response.json()
        ResponseValidator.validate_error_response(data, "VALIDATION_ERROR")
        logger.info("✓ Submit turn missing text")

    def test_submit_turn_session_not_found(self, api_client):
        """Test: POST /sessions/{id}/turns with invalid session_id returns 400"""
        turn_payload = TestDataFactory.valid_session_turn_data()
        response = api_client.post("/sessions/invalid-session-12345/turns", turn_payload)

        assert response.status_code == 400
        data = response.json()
        ResponseValidator.validate_error_response(data, "NOT_FOUND")
        logger.info("✓ Submit turn session not found")

    def test_submit_turn_unauthorized(self, public_client):
        """Test: POST /sessions/{id}/turns without token returns 401"""
        turn_payload = TestDataFactory.valid_session_turn_data()
        response = public_client.post("/sessions/some-id/turns", turn_payload)

        assert response.status_code == 401
        data = response.json()
        ResponseValidator.validate_error_response(data, "UNAUTHORIZED")
        logger.info("✓ Submit turn unauthorized")


class TestSessionComplete:
    """Test suite for Session Complete API"""

    def test_complete_session_success(self, api_client):
        """Test: POST /sessions/{id}/complete completes session"""
        # Create session
        create_payload = TestDataFactory.valid_session_data()
        create_response = api_client.post("/sessions", create_payload)
        assert create_response.status_code == 201
        session_id = create_response.json()["data"]["session_id"]

        # Complete session
        response = api_client.post(f"/sessions/{session_id}/complete")

        assert response.status_code == 200
        data = response.json()

        ResponseValidator.validate_success_response(data, [
            "session_id", "status", "scoring"
        ])

        assert data["data"]["status"] == "COMPLETED"
        assert "overall_score" in data["data"]["scoring"]
        logger.info("✓ Complete session success")

    def test_complete_session_not_found(self, api_client):
        """Test: POST /sessions/{id}/complete with invalid id returns 400"""
        response = api_client.post("/sessions/invalid-session-12345/complete")

        assert response.status_code == 400
        data = response.json()
        ResponseValidator.validate_error_response(data, "NOT_FOUND")
        logger.info("✓ Complete session not found")

    def test_complete_session_unauthorized(self, public_client):
        """Test: POST /sessions/{id}/complete without token returns 401"""
        response = public_client.post("/sessions/some-id/complete")

        assert response.status_code == 401
        data = response.json()
        ResponseValidator.validate_error_response(data, "UNAUTHORIZED")
        logger.info("✓ Complete session unauthorized")
