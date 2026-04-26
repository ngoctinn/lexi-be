"""
Task 10: Scenario API - GET /scenarios (Public)

Tests:
- Happy path: list all scenarios
- Filter by level (A1-C2)
- Pagination
- NO auth header required (public endpoint)
"""

import pytest
import logging
from tests.fixtures.validators import ResponseValidator

logger = logging.getLogger(__name__)


class TestScenarioAPI:
    """Test suite for Scenario API (Public)"""

    def test_list_scenarios_success(self, public_client):
        """Test: GET /scenarios returns list of scenarios (no auth required)"""
        response = public_client.get("/scenarios")

        assert response.status_code == 200
        data = response.json()

        ResponseValidator.validate_success_response(data, [
            "scenarios", "total"
        ])

        assert isinstance(data["data"]["scenarios"], list)
        assert isinstance(data["data"]["total"], int)
        logger.info("✓ List scenarios success (public)")

    def test_list_scenarios_with_limit(self, public_client):
        """Test: GET /scenarios with limit parameter"""
        response = public_client.get("/scenarios", params={"limit": 5})

        assert response.status_code == 200
        data = response.json()

        assert len(data["data"]["scenarios"]) <= 5
        logger.info("✓ List scenarios with limit")

    def test_list_scenarios_filter_by_level_a1(self, public_client):
        """Test: GET /scenarios filtered by level A1"""
        response = public_client.get("/scenarios", params={"level": "A1"})

        assert response.status_code == 200
        data = response.json()

        # All scenarios should be A1
        for scenario in data["data"]["scenarios"]:
            assert scenario["difficulty_level"] == "A1"
        logger.info("✓ List scenarios filter by level A1")

    def test_list_scenarios_filter_by_level_b1(self, public_client):
        """Test: GET /scenarios filtered by level B1"""
        response = public_client.get("/scenarios", params={"level": "B1"})

        assert response.status_code == 200
        data = response.json()

        # All scenarios should be B1
        for scenario in data["data"]["scenarios"]:
            assert scenario["difficulty_level"] == "B1"
        logger.info("✓ List scenarios filter by level B1")

    def test_list_scenarios_filter_by_level_c2(self, public_client):
        """Test: GET /scenarios filtered by level C2"""
        response = public_client.get("/scenarios", params={"level": "C2"})

        assert response.status_code == 200
        data = response.json()

        # All scenarios should be C2
        for scenario in data["data"]["scenarios"]:
            assert scenario["difficulty_level"] == "C2"
        logger.info("✓ List scenarios filter by level C2")

    def test_list_scenarios_invalid_level(self, public_client):
        """Test: GET /scenarios with invalid level returns 400"""
        response = public_client.get("/scenarios", params={"level": "INVALID"})

        assert response.status_code == 400
        data = response.json()
        ResponseValidator.validate_error_response(data, "VALIDATION_ERROR")
        logger.info("✓ List scenarios invalid level")

    def test_list_scenarios_pagination(self, public_client):
        """Test: GET /scenarios pagination"""
        # First page
        response1 = public_client.get("/scenarios", params={"limit": 2})
        assert response1.status_code == 200
        data1 = response1.json()["data"]

        # Verify structure
        assert "scenarios" in data1
        assert "total" in data1
        logger.info("✓ List scenarios pagination")

    def test_list_scenarios_response_structure(self, public_client):
        """Test: GET /scenarios response has correct structure"""
        response = public_client.get("/scenarios", params={"limit": 1})

        assert response.status_code == 200
        data = response.json()

        if data["data"]["scenarios"]:
            scenario = data["data"]["scenarios"][0]

            # Verify scenario fields
            assert "scenario_id" in scenario
            assert "scenario_title" in scenario
            assert "context" in scenario
            assert "roles" in scenario
            assert "goals" in scenario
            assert "is_active" in scenario
            assert "usage_count" in scenario
            assert "difficulty_level" in scenario
            assert "order" in scenario
            assert "created_at" in scenario

            # Verify roles is a list
            assert isinstance(scenario["roles"], list)
            assert len(scenario["roles"]) == 2  # learner and AI roles

            logger.info("✓ List scenarios response structure")

    def test_list_scenarios_no_auth_header(self, public_client):
        """Test: GET /scenarios works without Authorization header"""
        # public_client has no token, so no Authorization header
        response = public_client.get("/scenarios")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        logger.info("✓ List scenarios no auth header required")

    def test_list_scenarios_with_auth_header(self, api_client):
        """Test: GET /scenarios also works with Authorization header"""
        # api_client has token, so Authorization header is included
        response = api_client.get("/scenarios")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        logger.info("✓ List scenarios with auth header")
