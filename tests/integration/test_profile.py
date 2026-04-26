"""
Task 2: Profile APIs - GET /profile, PATCH /profile

Tests:
- GET /profile: retrieve user profile
- PATCH /profile: update fields
- Partial updates
- Invalid avatar_url format
- Unauthorized access
"""

import pytest
import logging
from tests.fixtures.test_data import TestDataFactory
from tests.fixtures.validators import ResponseValidator

logger = logging.getLogger(__name__)


class TestProfileAPI:
    """Test suite for Profile API"""

    def test_get_profile_success(self, api_client):
        """Test: GET /profile returns user profile"""
        response = api_client.get("/profile")

        assert response.status_code == 200
        data = response.json()

        ResponseValidator.validate_success_response(data, [
            "user_id", "email", "display_name", "current_level", "target_level"
        ])

        profile = data["data"]
        assert profile["user_id"]
        assert profile["email"]
        assert profile["display_name"]
        logger.info("✓ Get profile success")

    def test_get_profile_unauthorized(self, public_client):
        """Test: GET /profile without token returns 401"""
        response = public_client.get("/profile")

        assert response.status_code == 401
        data = response.json()
        ResponseValidator.validate_error_response(data, "UNAUTHORIZED")
        logger.info("✓ Get profile unauthorized")

    def test_patch_profile_update_display_name(self, api_client):
        """Test: PATCH /profile updates display_name"""
        payload = {
            "display_name": "Updated Test User"
        }
        response = api_client.patch("/profile", payload)

        assert response.status_code == 200
        data = response.json()

        ResponseValidator.validate_success_response(data, [
            "user_id", "email", "display_name"
        ])

        assert data["data"]["display_name"] == payload["display_name"]
        logger.info("✓ Patch profile update display_name")

    def test_patch_profile_update_target_level(self, api_client):
        """Test: PATCH /profile updates target_level"""
        payload = {
            "target_level": "C1"
        }
        response = api_client.patch("/profile", payload)

        assert response.status_code == 200
        data = response.json()

        ResponseValidator.validate_success_response(data, ["target_level"])
        assert data["data"]["target_level"] == "C1"
        logger.info("✓ Patch profile update target_level")

    def test_patch_profile_update_avatar_url(self, api_client):
        """Test: PATCH /profile updates avatar_url"""
        payload = {
            "avatar_url": "https://example.com/new-avatar.jpg"
        }
        response = api_client.patch("/profile", payload)

        assert response.status_code == 200
        data = response.json()

        ResponseValidator.validate_success_response(data, ["avatar_url"])
        assert data["data"]["avatar_url"] == payload["avatar_url"]
        logger.info("✓ Patch profile update avatar_url")

    def test_patch_profile_partial_update(self, api_client):
        """Test: PATCH /profile with partial fields"""
        payload = {
            "display_name": "Partial Update User",
            "target_level": "B2"
        }
        response = api_client.patch("/profile", payload)

        assert response.status_code == 200
        data = response.json()

        assert data["data"]["display_name"] == payload["display_name"]
        assert data["data"]["target_level"] == payload["target_level"]
        logger.info("✓ Patch profile partial update")

    def test_patch_profile_invalid_target_level(self, api_client):
        """Test: PATCH /profile with invalid target_level returns 400"""
        payload = {
            "target_level": "INVALID"
        }
        response = api_client.patch("/profile", payload)

        assert response.status_code == 400
        data = response.json()
        ResponseValidator.validate_error_response(data, "VALIDATION_ERROR")
        logger.info("✓ Patch profile invalid target_level")

    def test_patch_profile_invalid_avatar_url(self, api_client):
        """Test: PATCH /profile with invalid avatar_url returns 400"""
        payload = {
            "avatar_url": "not-a-valid-url"
        }
        response = api_client.patch("/profile", payload)

        assert response.status_code == 400
        data = response.json()
        ResponseValidator.validate_error_response(data, "VALIDATION_ERROR")
        logger.info("✓ Patch profile invalid avatar_url")

    def test_patch_profile_unauthorized(self, public_client):
        """Test: PATCH /profile without token returns 401"""
        payload = {"display_name": "Test"}
        response = public_client.patch("/profile", payload)

        assert response.status_code == 401
        data = response.json()
        ResponseValidator.validate_error_response(data, "UNAUTHORIZED")
        logger.info("✓ Patch profile unauthorized")

    def test_patch_profile_empty_payload(self, api_client):
        """Test: PATCH /profile with empty payload"""
        payload = {}
        response = api_client.patch("/profile", payload)

        # Should either succeed (no changes) or return 400
        assert response.status_code in [200, 400]
        logger.info("✓ Patch profile empty payload")
