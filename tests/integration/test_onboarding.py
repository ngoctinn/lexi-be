"""
Task 1: Onboarding API - POST /onboarding/complete

Tests:
- Happy path: valid onboarding data
- Missing required fields
- Invalid level values
- Unauthorized (no token)
"""

import pytest
import logging
from tests.fixtures.test_data import TestDataFactory
from tests.fixtures.validators import ResponseValidator

logger = logging.getLogger(__name__)


class TestOnboardingAPI:
    """Test suite for Onboarding API"""

    def test_onboarding_complete_success(self, api_client):
        """Test: POST /onboarding/complete with valid data returns 200"""
        payload = TestDataFactory.valid_onboarding_data()
        response = api_client.post("/onboarding/complete", payload)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()

        ResponseValidator.validate_success_response(data, [
            "is_success", "message", "profile"
        ])

        profile = data["data"]["profile"]
        assert profile["display_name"] == payload["display_name"]
        assert profile["current_level"] == payload["current_level"]
        assert profile["target_level"] == payload["target_level"]
        logger.info("✓ Onboarding complete success")

    def test_onboarding_missing_display_name(self, api_client):
        """Test: POST /onboarding/complete without display_name returns 400"""
        payload = {
            "current_level": "A1",
            "target_level": "B2",
            "preferred_topics": ["business"]
        }
        response = api_client.post("/onboarding/complete", payload)

        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        data = response.json()
        ResponseValidator.validate_error_response(data, "VALIDATION_ERROR")
        logger.info("✓ Onboarding missing display_name")

    def test_onboarding_missing_current_level(self, api_client):
        """Test: POST /onboarding/complete without current_level returns 400"""
        payload = {
            "display_name": "Test User",
            "target_level": "B2",
            "preferred_topics": ["business"]
        }
        response = api_client.post("/onboarding/complete", payload)

        assert response.status_code == 400
        data = response.json()
        ResponseValidator.validate_error_response(data, "VALIDATION_ERROR")
        logger.info("✓ Onboarding missing current_level")

    def test_onboarding_missing_target_level(self, api_client):
        """Test: POST /onboarding/complete without target_level returns 400"""
        payload = {
            "display_name": "Test User",
            "current_level": "A1",
            "preferred_topics": ["business"]
        }
        response = api_client.post("/onboarding/complete", payload)

        assert response.status_code == 400
        data = response.json()
        ResponseValidator.validate_error_response(data, "VALIDATION_ERROR")
        logger.info("✓ Onboarding missing target_level")

    def test_onboarding_invalid_current_level(self, api_client):
        """Test: POST /onboarding/complete with invalid current_level returns 400"""
        payload = {
            "display_name": "Test User",
            "current_level": "INVALID",
            "target_level": "B2",
            "preferred_topics": ["business"]
        }
        response = api_client.post("/onboarding/complete", payload)

        assert response.status_code == 400
        data = response.json()
        ResponseValidator.validate_error_response(data, "VALIDATION_ERROR")
        logger.info("✓ Onboarding invalid current_level")

    def test_onboarding_invalid_target_level(self, api_client):
        """Test: POST /onboarding/complete with invalid target_level returns 400"""
        payload = {
            "display_name": "Test User",
            "current_level": "A1",
            "target_level": "INVALID",
            "preferred_topics": ["business"]
        }
        response = api_client.post("/onboarding/complete", payload)

        assert response.status_code == 400
        data = response.json()
        ResponseValidator.validate_error_response(data, "VALIDATION_ERROR")
        logger.info("✓ Onboarding invalid target_level")

    def test_onboarding_unauthorized(self, public_client):
        """Test: POST /onboarding/complete without token returns 401"""
        payload = TestDataFactory.valid_onboarding_data()
        response = public_client.post("/onboarding/complete", payload)

        assert response.status_code == 401
        data = response.json()
        ResponseValidator.validate_error_response(data, "UNAUTHORIZED")
        logger.info("✓ Onboarding unauthorized")

    def test_onboarding_invalid_json(self, api_client):
        """Test: POST /onboarding/complete with invalid JSON returns 400"""
        # Send raw invalid JSON
        response = api_client.session.post(
            f"{api_client.base_url}/onboarding/complete",
            data="{ invalid json }",
            headers=api_client._get_headers()
        )

        assert response.status_code == 400
        logger.info("✓ Onboarding invalid JSON")
