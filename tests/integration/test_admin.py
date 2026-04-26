"""
Task 22-26: Admin APIs
- GET /admin/users (list users)
- PATCH /admin/users/{id} (update user)
- GET /admin/scenarios (list scenarios)
- POST /admin/scenarios (create scenario)
- PATCH /admin/scenarios/{id} (update scenario)

Tests:
- Admin role required
- Happy path for all operations
- Error cases (404, 422, 403)
- Unauthorized (non-admin user)
"""

import pytest
import logging
from tests.fixtures.test_data import TestDataFactory
from tests.fixtures.validators import ResponseValidator

logger = logging.getLogger(__name__)


class TestAdminListUsers:
    """Test suite for Admin List Users API"""

    def test_list_admin_users_success(self, admin_client):
        """Test: GET /admin/users returns list of users (admin only)"""
        response = admin_client.get("/admin/users")

        assert response.status_code == 200
        data = response.json()

        ResponseValidator.validate_success_response(data, [
            "users", "total_count"
        ])

        assert isinstance(data["data"]["users"], list)
        logger.info("✓ List admin users success")

    def test_list_admin_users_with_limit(self, admin_client):
        """Test: GET /admin/users with limit parameter"""
        response = admin_client.get("/admin/users", params={"limit": 5})

        assert response.status_code == 200
        data = response.json()

        assert len(data["data"]["users"]) <= 5
        logger.info("✓ List admin users with limit")

    def test_list_admin_users_non_admin(self, api_client):
        """Test: GET /admin/users without admin role returns 403"""
        response = api_client.get("/admin/users")

        assert response.status_code == 403
        data = response.json()
        ResponseValidator.validate_error_response(data, "FORBIDDEN")
        logger.info("✓ List admin users non-admin")

    def test_list_admin_users_unauthorized(self, public_client):
        """Test: GET /admin/users without token returns 401"""
        response = public_client.get("/admin/users")

        assert response.status_code == 401
        data = response.json()
        ResponseValidator.validate_error_response(data, "UNAUTHORIZED")
        logger.info("✓ List admin users unauthorized")


class TestAdminUpdateUser:
    """Test suite for Admin Update User API"""

    def test_update_admin_user_success(self, admin_client):
        """Test: PATCH /admin/users/{id} updates user (admin only)"""
        # First get a user
        list_response = admin_client.get("/admin/users", params={"limit": 1})
        assert list_response.status_code == 200
        users = list_response.json()["data"]["users"]

        if users:
            user_id = users[0]["user_id"]

            # Update user
            payload = TestDataFactory.valid_admin_user_update()
            response = admin_client.patch(f"/admin/users/{user_id}", payload)

            assert response.status_code == 200
            data = response.json()

            ResponseValidator.validate_success_response(data, ["user_id"])
            logger.info("✓ Update admin user success")
        else:
            logger.warning("⊘ Update admin user (no users found)")

    def test_update_admin_user_not_found(self, admin_client):
        """Test: PATCH /admin/users/{id} with invalid id returns 400"""
        payload = TestDataFactory.valid_admin_user_update()
        response = admin_client.patch("/admin/users/invalid-user-12345", payload)

        assert response.status_code == 400
        data = response.json()
        ResponseValidator.validate_error_response(data, "NOT_FOUND")
        logger.info("✓ Update admin user not found")

    def test_update_admin_user_non_admin(self, api_client):
        """Test: PATCH /admin/users/{id} without admin role returns 403"""
        payload = TestDataFactory.valid_admin_user_update()
        response = api_client.patch("/admin/users/some-user-id", payload)

        assert response.status_code == 403
        data = response.json()
        ResponseValidator.validate_error_response(data, "FORBIDDEN")
        logger.info("✓ Update admin user non-admin")

    def test_update_admin_user_unauthorized(self, public_client):
        """Test: PATCH /admin/users/{id} without token returns 401"""
        payload = TestDataFactory.valid_admin_user_update()
        response = public_client.patch("/admin/users/some-user-id", payload)

        assert response.status_code == 401
        data = response.json()
        ResponseValidator.validate_error_response(data, "UNAUTHORIZED")
        logger.info("✓ Update admin user unauthorized")


class TestAdminListScenarios:
    """Test suite for Admin List Scenarios API"""

    def test_list_admin_scenarios_success(self, admin_client):
        """Test: GET /admin/scenarios returns list of scenarios (admin only)"""
        response = admin_client.get("/admin/scenarios")

        assert response.status_code == 200
        data = response.json()

        ResponseValidator.validate_success_response(data, [
            "scenarios", "total_count"
        ])

        assert isinstance(data["data"]["scenarios"], list)
        logger.info("✓ List admin scenarios success")

    def test_list_admin_scenarios_non_admin(self, api_client):
        """Test: GET /admin/scenarios without admin role returns 403"""
        response = api_client.get("/admin/scenarios")

        assert response.status_code == 403
        data = response.json()
        ResponseValidator.validate_error_response(data, "FORBIDDEN")
        logger.info("✓ List admin scenarios non-admin")

    def test_list_admin_scenarios_unauthorized(self, public_client):
        """Test: GET /admin/scenarios without token returns 401"""
        response = public_client.get("/admin/scenarios")

        assert response.status_code == 401
        data = response.json()
        ResponseValidator.validate_error_response(data, "UNAUTHORIZED")
        logger.info("✓ List admin scenarios unauthorized")


class TestAdminCreateScenario:
    """Test suite for Admin Create Scenario API"""

    def test_create_admin_scenario_success(self, admin_client):
        """Test: POST /admin/scenarios creates scenario (admin only)"""
        payload = TestDataFactory.valid_admin_scenario_data()
        response = admin_client.post("/admin/scenarios", payload)

        assert response.status_code == 200
        data = response.json()

        ResponseValidator.validate_success_response(data, [
            "scenario_id", "scenario_title"
        ])

        assert data["data"]["scenario_title"] == payload["scenario_title"]
        logger.info("✓ Create admin scenario success")

    def test_create_admin_scenario_missing_field(self, admin_client):
        """Test: POST /admin/scenarios without required field returns 400"""
        payload = {
            "scenario_title": "Test Scenario",
            "context": "hotel"
            # Missing: difficulty_level, roles, goals
        }
        response = admin_client.post("/admin/scenarios", payload)

        assert response.status_code == 400
        data = response.json()
        ResponseValidator.validate_error_response(data, "VALIDATION_ERROR")
        logger.info("✓ Create admin scenario missing field")

    def test_create_admin_scenario_invalid_roles(self, admin_client):
        """Test: POST /admin/scenarios with invalid roles (not 2) returns 400"""
        payload = {
            "scenario_title": "Test Scenario",
            "context": "hotel",
            "difficulty_level": "A2",
            "roles": ["guest"],  # Only 1 role, need 2
            "goals": ["book a room"],
            "order": 1,
            "is_active": True
        }
        response = admin_client.post("/admin/scenarios", payload)

        assert response.status_code == 400
        data = response.json()
        ResponseValidator.validate_error_response(data, "VALIDATION_ERROR")
        logger.info("✓ Create admin scenario invalid roles")

    def test_create_admin_scenario_non_admin(self, api_client):
        """Test: POST /admin/scenarios without admin role returns 403"""
        payload = TestDataFactory.valid_admin_scenario_data()
        response = api_client.post("/admin/scenarios", payload)

        assert response.status_code == 403
        data = response.json()
        ResponseValidator.validate_error_response(data, "FORBIDDEN")
        logger.info("✓ Create admin scenario non-admin")

    def test_create_admin_scenario_unauthorized(self, public_client):
        """Test: POST /admin/scenarios without token returns 401"""
        payload = TestDataFactory.valid_admin_scenario_data()
        response = public_client.post("/admin/scenarios", payload)

        assert response.status_code == 401
        data = response.json()
        ResponseValidator.validate_error_response(data, "UNAUTHORIZED")
        logger.info("✓ Create admin scenario unauthorized")


class TestAdminUpdateScenario:
    """Test suite for Admin Update Scenario API"""

    def test_update_admin_scenario_success(self, admin_client):
        """Test: PATCH /admin/scenarios/{id} updates scenario (admin only)"""
        # First create a scenario
        create_payload = TestDataFactory.valid_admin_scenario_data()
        create_response = admin_client.post("/admin/scenarios", create_payload)
        assert create_response.status_code == 201
        scenario_id = create_response.json()["data"]["scenario_id"]

        # Update scenario
        update_payload = TestDataFactory.valid_scenario_update()
        response = admin_client.patch(f"/admin/scenarios/{scenario_id}", update_payload)

        assert response.status_code == 200
        data = response.json()

        ResponseValidator.validate_success_response(data, ["scenario_id"])
        assert data["data"]["scenario_title"] == update_payload["scenario_title"]
        logger.info("✓ Update admin scenario success")

    def test_update_admin_scenario_partial(self, admin_client):
        """Test: PATCH /admin/scenarios/{id} with partial fields"""
        # First create a scenario
        create_payload = TestDataFactory.valid_admin_scenario_data()
        create_response = admin_client.post("/admin/scenarios", create_payload)
        assert create_response.status_code == 201
        scenario_id = create_response.json()["data"]["scenario_id"]

        # Update only is_active
        update_payload = {"is_active": False}
        response = admin_client.patch(f"/admin/scenarios/{scenario_id}", update_payload)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["is_active"] == False
        logger.info("✓ Update admin scenario partial")

    def test_update_admin_scenario_not_found(self, admin_client):
        """Test: PATCH /admin/scenarios/{id} with invalid id returns 400"""
        update_payload = TestDataFactory.valid_scenario_update()
        response = admin_client.patch("/admin/scenarios/invalid-scenario-12345", update_payload)

        assert response.status_code == 400
        data = response.json()
        ResponseValidator.validate_error_response(data, "NOT_FOUND")
        logger.info("✓ Update admin scenario not found")

    def test_update_admin_scenario_non_admin(self, api_client):
        """Test: PATCH /admin/scenarios/{id} without admin role returns 403"""
        update_payload = TestDataFactory.valid_scenario_update()
        response = api_client.patch("/admin/scenarios/some-scenario-id", update_payload)

        assert response.status_code == 403
        data = response.json()
        ResponseValidator.validate_error_response(data, "FORBIDDEN")
        logger.info("✓ Update admin scenario non-admin")

    def test_update_admin_scenario_unauthorized(self, public_client):
        """Test: PATCH /admin/scenarios/{id} without token returns 401"""
        update_payload = TestDataFactory.valid_scenario_update()
        response = public_client.patch("/admin/scenarios/some-scenario-id", update_payload)

        assert response.status_code == 401
        data = response.json()
        ResponseValidator.validate_error_response(data, "UNAUTHORIZED")
        logger.info("✓ Update admin scenario unauthorized")
