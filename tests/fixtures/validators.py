"""
Response Validators - Validate API responses against schema

Provides validators for:
- Success/error response structure
- Pagination format
- Field presence and types
- Error codes
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class ResponseValidator:
    """Validate API responses against expected schema."""

    # ========================================================================
    # Basic Response Validation
    # ========================================================================

    @staticmethod
    def validate_success_response(response: Dict[str, Any], expected_keys: List[str] = None):
        """
        Validate success response structure.

        Args:
            response: Response dictionary
            expected_keys: List of expected keys in response["data"]

        Raises:
            AssertionError: Validation failed
        """
        assert response.get("success") == True, f"Expected success=true, got {response.get('success')}"
        # Note: 'message' field is optional - not all endpoints return it
        assert "data" in response, "Response missing 'data' field"

        if expected_keys:
            data = response.get("data", {})
            for key in expected_keys:
                assert key in data, f"Response data missing expected key: {key}"

        logger.debug(f"Success response validation passed")

    @staticmethod
    def validate_error_response(response: Dict[str, Any], expected_error_code: str = None):
        """
        Validate error response structure.
        
        Handles two formats:
        1. Standard format: {"success": false, "message": "...", "error": "..."}
        2. API Gateway format: {"message": "Unauthorized"} (for 401 errors)

        Args:
            response: Response dictionary
            expected_error_code: Expected error code (e.g., "NOT_FOUND")

        Raises:
            AssertionError: Validation failed
        """
        # Check if this is API Gateway 401 format (plain text)
        if "message" in response and "success" not in response and "error" not in response:
            # API Gateway unauthorized format: {"message": "Unauthorized"}
            assert "message" in response, "Error response missing 'message' field"
            logger.debug(f"Error response validation passed (API Gateway format): {response.get('message')}")
            return
        
        # Standard error format
        assert response.get("success") == False, f"Expected success=false, got {response.get('success')}"
        assert "message" in response, "Error response missing 'message' field"
        assert "error" in response, "Error response missing 'error' field"

        if expected_error_code:
            actual_error = response.get("error")
            assert actual_error == expected_error_code, \
                f"Expected error code '{expected_error_code}', got '{actual_error}'"

        logger.debug(f"Error response validation passed: {response.get('error')}")

    # ========================================================================
    # Pagination Validation
    # ========================================================================

    @staticmethod
    def validate_pagination(response: Dict[str, Any]):
        """
        Validate pagination structure in response.

        Args:
            response: Response dictionary with pagination

        Raises:
            AssertionError: Validation failed
        """
        data = response.get("data", {})

        # Check for pagination fields
        assert "next_key" in data or "last_key" in data, \
            "Response missing pagination fields (next_key or last_key)"

        # next_key should be string or None
        next_key = data.get("next_key")
        assert next_key is None or isinstance(next_key, str), \
            f"next_key should be string or None, got {type(next_key)}"

        logger.debug(f"Pagination validation passed")

    @staticmethod
    def validate_no_pagination_overlap(page1_ids: List[str], page2_ids: List[str]):
        """
        Validate that two pages have no overlapping IDs.

        Args:
            page1_ids: List of IDs from first page
            page2_ids: List of IDs from second page

        Raises:
            AssertionError: Pages have overlapping IDs
        """
        overlap = set(page1_ids) & set(page2_ids)
        assert len(overlap) == 0, f"Pages have overlapping IDs: {overlap}"

        logger.debug(f"No pagination overlap detected")

    # ========================================================================
    # Field Validation
    # ========================================================================

    @staticmethod
    def validate_field_type(data: Dict[str, Any], field: str, expected_type: type):
        """
        Validate field type.

        Args:
            data: Data dictionary
            field: Field name
            expected_type: Expected type (str, int, bool, list, dict, etc.)

        Raises:
            AssertionError: Field type doesn't match
        """
        value = data.get(field)
        assert isinstance(value, expected_type), \
            f"Field '{field}' should be {expected_type.__name__}, got {type(value).__name__}"

        logger.debug(f"Field type validation passed: {field} is {expected_type.__name__}")

    @staticmethod
    def validate_field_not_empty(data: Dict[str, Any], field: str):
        """
        Validate field is not empty.

        Args:
            data: Data dictionary
            field: Field name

        Raises:
            AssertionError: Field is empty
        """
        value = data.get(field)
        assert value, f"Field '{field}' is empty: {value}"

        logger.debug(f"Field not empty validation passed: {field}")

    @staticmethod
    def validate_field_in_list(data: Dict[str, Any], field: str, allowed_values: List[str]):
        """
        Validate field value is in allowed list.

        Args:
            data: Data dictionary
            field: Field name
            allowed_values: List of allowed values

        Raises:
            AssertionError: Field value not in allowed list
        """
        value = data.get(field)
        assert value in allowed_values, \
            f"Field '{field}' value '{value}' not in allowed values: {allowed_values}"

        logger.debug(f"Field in list validation passed: {field}={value}")

    # ========================================================================
    # Entity Validation
    # ========================================================================

    @staticmethod
    def validate_profile(profile: Dict[str, Any]):
        """Validate profile entity structure."""
        required_fields = [
            "user_id", "email", "display_name", "current_level",
            "target_level", "current_streak", "total_words_learned",
            "role", "is_active", "is_new_user"
        ]

        for field in required_fields:
            assert field in profile, f"Profile missing field: {field}"

        # Validate field types
        ResponseValidator.validate_field_type(profile, "user_id", str)
        ResponseValidator.validate_field_type(profile, "email", str)
        ResponseValidator.validate_field_type(profile, "current_level", str)
        ResponseValidator.validate_field_type(profile, "is_active", bool)

        logger.debug("Profile validation passed")

    @staticmethod
    def validate_flashcard(flashcard: Dict[str, Any]):
        """Validate flashcard entity structure."""
        required_fields = [
            "flashcard_id", "word", "translation_vi", "phonetic",
            "example_sentence", "review_count", "interval_days"
        ]

        for field in required_fields:
            assert field in flashcard, f"Flashcard missing field: {field}"

        # Validate field types
        ResponseValidator.validate_field_type(flashcard, "flashcard_id", str)
        ResponseValidator.validate_field_type(flashcard, "word", str)
        ResponseValidator.validate_field_type(flashcard, "review_count", int)

        logger.debug("Flashcard validation passed")

    @staticmethod
    def validate_session(session: Dict[str, Any]):
        """Validate session entity structure."""
        required_fields = [
            "session_id", "scenario_id", "status", "created_at",
            "turn_count"
        ]

        for field in required_fields:
            assert field in session, f"Session missing field: {field}"

        # Validate field types
        ResponseValidator.validate_field_type(session, "session_id", str)
        ResponseValidator.validate_field_type(session, "scenario_id", str)
        ResponseValidator.validate_field_type(session, "status", str)

        logger.debug("Session validation passed")

    @staticmethod
    def validate_scenario(scenario: Dict[str, Any]):
        """Validate scenario entity structure."""
        required_fields = [
            "scenario_id", "scenario_title", "context", "roles",
            "goals", "is_active", "difficulty_level"
        ]

        for field in required_fields:
            assert field in scenario, f"Scenario missing field: {field}"

        # Validate field types
        ResponseValidator.validate_field_type(scenario, "scenario_id", str)
        ResponseValidator.validate_field_type(scenario, "roles", list)
        ResponseValidator.validate_field_type(scenario, "goals", list)

        # Validate roles has exactly 2 elements
        assert len(scenario["roles"]) == 2, \
            f"Scenario roles should have 2 elements, got {len(scenario['roles'])}"

        logger.debug("Scenario validation passed")

    # ========================================================================
    # Error Code Validation
    # ========================================================================

    @staticmethod
    def validate_error_code(response: Dict[str, Any], expected_code: str):
        """
        Validate error code matches expected.

        Args:
            response: Error response dictionary
            expected_code: Expected error code

        Raises:
            AssertionError: Error code doesn't match
        """
        actual_code = response.get("error")
        assert actual_code == expected_code, \
            f"Expected error code '{expected_code}', got '{actual_code}'"

        logger.debug(f"Error code validation passed: {expected_code}")

    @staticmethod
    def validate_http_status(status_code: int, expected_status: int):
        """
        Validate HTTP status code.

        Args:
            status_code: Actual status code
            expected_status: Expected status code

        Raises:
            AssertionError: Status code doesn't match
        """
        assert status_code == expected_status, \
            f"Expected status {expected_status}, got {status_code}"

        logger.debug(f"HTTP status validation passed: {expected_status}")

    # ========================================================================
    # WebSocket Event Validation
    # ========================================================================

    @staticmethod
    def validate_websocket_event(event: Dict[str, Any], expected_event_type: str):
        """
        Validate WebSocket event structure.

        Args:
            event: Event dictionary
            expected_event_type: Expected event type

        Raises:
            AssertionError: Event validation failed
        """
        assert "event" in event, "WebSocket event missing 'event' field"

        actual_event = event.get("event")
        assert actual_event == expected_event_type, \
            f"Expected event '{expected_event_type}', got '{actual_event}'"

        logger.debug(f"WebSocket event validation passed: {expected_event_type}")

    @staticmethod
    def validate_hint_event(event: Dict[str, Any]):
        """Validate HINT_TEXT event structure."""
        ResponseValidator.validate_websocket_event(event, "HINT_TEXT")

        assert "hint" in event, "HINT_TEXT event missing 'hint' field"
        hint = event["hint"]

        required_hint_fields = ["level", "type", "markdown"]
        for field in required_hint_fields:
            assert field in hint, f"Hint missing field: {field}"

        # Validate markdown has vi and en
        markdown = hint["markdown"]
        assert "vi" in markdown, "Hint markdown missing 'vi' field"
        assert "en" in markdown, "Hint markdown missing 'en' field"

        logger.debug("Hint event validation passed")

    @staticmethod
    def validate_turn_analysis_event(event: Dict[str, Any]):
        """Validate TURN_ANALYSIS event structure."""
        ResponseValidator.validate_websocket_event(event, "TURN_ANALYSIS")

        assert "analysis" in event, "TURN_ANALYSIS event missing 'analysis' field"
        analysis = event["analysis"]

        assert "markdown" in analysis, "Analysis missing 'markdown' field"
        markdown = analysis["markdown"]

        assert "vi" in markdown, "Analysis markdown missing 'vi' field"
        assert "en" in markdown, "Analysis markdown missing 'en' field"

        logger.debug("Turn analysis event validation passed")
