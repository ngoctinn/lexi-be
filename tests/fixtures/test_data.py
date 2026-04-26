"""
Test Data Factory - Generate test data for API testing

Provides factory methods to create valid test data for all API endpoints.
"""

import uuid
from datetime import datetime, timedelta


class TestDataFactory:
    """Generate test data for API testing."""

    # ========================================================================
    # Onboarding Data
    # ========================================================================

    @staticmethod
    def valid_onboarding_data():
        """Generate valid onboarding data."""
        return {
            "display_name": f"Test User {uuid.uuid4().hex[:8]}",
            "current_level": "A1",
            "target_level": "B2",
            "preferred_topics": ["business", "travel"]
        }

    @staticmethod
    def invalid_onboarding_data_missing_field():
        """Generate onboarding data missing required field."""
        return {
            "display_name": "Test User",
            "current_level": "A1"
            # Missing: target_level
        }

    @staticmethod
    def invalid_onboarding_data_invalid_level():
        """Generate onboarding data with invalid level."""
        return {
            "display_name": "Test User",
            "current_level": "INVALID",
            "target_level": "B2",
            "preferred_topics": []
        }

    # ========================================================================
    # Profile Data
    # ========================================================================

    @staticmethod
    def valid_profile_update():
        """Generate valid profile update data."""
        return {
            "display_name": f"Updated User {uuid.uuid4().hex[:8]}",
            "avatar_url": "https://example.com/avatar.jpg",
            "target_level": "C1"
        }

    @staticmethod
    def invalid_profile_update_invalid_url():
        """Generate profile update with invalid avatar URL."""
        return {
            "display_name": "Test User",
            "avatar_url": "not-a-valid-url"
        }

    # ========================================================================
    # Vocabulary Data
    # ========================================================================

    @staticmethod
    def valid_translate_word_data():
        """Generate valid translate word request."""
        return {
            "word": "run",
            "sentence": "I run every morning.",
            "context": "I run every morning for exercise."
        }

    @staticmethod
    def invalid_translate_word_missing_field():
        """Generate translate word request missing required field."""
        return {
            "sentence": "I run every morning."
            # Missing: word
        }

    @staticmethod
    def invalid_translate_word_too_long():
        """Generate translate word request with word too long."""
        return {
            "word": "a" * 101,  # Max 100 chars
            "context": "test"
        }

    @staticmethod
    def valid_translate_sentence_data():
        """Generate valid translate sentence request."""
        return {
            "sentence": "How are you today?"
        }

    @staticmethod
    def invalid_translate_sentence_empty():
        """Generate translate sentence request with empty sentence."""
        return {
            "sentence": ""
        }

    # ========================================================================
    # Flashcard Data
    # ========================================================================

    @staticmethod
    def valid_flashcard_data():
        """Generate valid flashcard creation data."""
        return {
            "vocab": f"word_{uuid.uuid4().hex[:8]}",
            "vocab_type": "verb",
            "translation_vi": "chạy",
            "example_sentence": "She runs five miles every day.",
            "phonetic": "/rʌn/",
            "audio_url": "https://example.com/audio.mp3"
        }

    @staticmethod
    def invalid_flashcard_missing_field():
        """Generate flashcard data missing required field."""
        return {
            "vocab": "run",
            "vocab_type": "verb"
            # Missing: translation_vi
        }

    @staticmethod
    def invalid_flashcard_invalid_type():
        """Generate flashcard data with invalid vocab_type."""
        return {
            "vocab": "run",
            "vocab_type": "invalid_type",
            "translation_vi": "chạy"
        }

    @staticmethod
    def valid_flashcard_review_data(rating="good"):
        """Generate valid flashcard review data."""
        return {
            "rating": rating
        }

    @staticmethod
    def invalid_flashcard_review_invalid_rating():
        """Generate flashcard review with invalid rating."""
        return {
            "rating": "invalid_rating"
        }

    # ========================================================================
    # Scenario Data
    # ========================================================================

    @staticmethod
    def valid_scenario_data():
        """Generate valid scenario creation data."""
        return {
            "scenario_title": f"Test Scenario {uuid.uuid4().hex[:8]}",
            "context": "restaurant",
            "difficulty_level": "A1",
            "roles": ["customer", "waiter"],
            "goals": ["order food", "ask for recommendations"],
            "order": 1,
            "notes": "Test scenario",
            "is_active": True
        }

    @staticmethod
    def invalid_scenario_invalid_roles():
        """Generate scenario data with invalid roles (not exactly 2)."""
        return {
            "scenario_title": "Test Scenario",
            "context": "restaurant",
            "difficulty_level": "A1",
            "roles": ["customer"],  # Only 1 role, need 2
            "goals": ["order food"],
            "order": 1,
            "is_active": True
        }

    @staticmethod
    def valid_scenario_update():
        """Generate valid scenario update data."""
        return {
            "scenario_title": f"Updated Scenario {uuid.uuid4().hex[:8]}",
            "is_active": False,
            "order": 2
        }

    # ========================================================================
    # Session Data
    # ========================================================================

    @staticmethod
    def valid_session_data(scenario_id="restaurant-ordering"):
        """Generate valid session creation data."""
        return {
            "scenario_id": scenario_id,
            "learner_role_id": "customer",
            "ai_role_id": "waiter",
            "ai_gender": "female",
            "level": "B1",
            "selected_goal": "order food"
        }

    @staticmethod
    def invalid_session_missing_field():
        """Generate session data missing required field."""
        return {
            "scenario_id": "restaurant-ordering",
            "learner_role_id": "customer"
            # Missing: ai_role_id, level, etc.
        }

    @staticmethod
    def invalid_session_invalid_level():
        """Generate session data with invalid level."""
        return {
            "scenario_id": "restaurant-ordering",
            "learner_role_id": "customer",
            "ai_role_id": "waiter",
            "ai_gender": "female",
            "level": "INVALID",
            "selected_goal": "order food"
        }

    @staticmethod
    def valid_session_turn_data():
        """Generate valid session turn submission data."""
        return {
            "text": "Hello, I would like to order a coffee please.",
            "audio_url": "s3://bucket/audio.mp3",
            "is_hint_used": False
        }

    @staticmethod
    def invalid_session_turn_missing_text():
        """Generate session turn data missing text."""
        return {
            "audio_url": "s3://bucket/audio.mp3",
            "is_hint_used": False
            # Missing: text
        }

    # ========================================================================
    # WebSocket Data
    # ========================================================================

    @staticmethod
    def valid_websocket_start_session(session_id):
        """Generate valid WebSocket start_session action."""
        return {
            "action": "start_session",
            "session_id": session_id
        }

    @staticmethod
    def valid_websocket_audio_uploaded(session_id, s3_key):
        """Generate valid WebSocket audio_uploaded action."""
        return {
            "action": "audio_uploaded",
            "session_id": session_id,
            "s3_key": s3_key
        }

    @staticmethod
    def valid_websocket_use_hint(session_id):
        """Generate valid WebSocket use_hint action."""
        return {
            "action": "use_hint",
            "session_id": session_id
        }

    @staticmethod
    def valid_websocket_send_message_turn(session_id, text="Hello"):
        """Generate valid WebSocket send_message_turn action."""
        return {
            "action": "send_message_turn",
            "session_id": session_id,
            "text": text,
            "is_hint_used": False
        }

    @staticmethod
    def valid_websocket_end_session(session_id):
        """Generate valid WebSocket end_session action."""
        return {
            "action": "end_session",
            "session_id": session_id
        }

    @staticmethod
    def valid_websocket_analyze_turn(session_id, turn_index=1):
        """Generate valid WebSocket ANALYZE_TURN action."""
        return {
            "action": "ANALYZE_TURN",
            "session_id": session_id,
            "turn_index": turn_index
        }

    # ========================================================================
    # Admin Data
    # ========================================================================

    @staticmethod
    def valid_admin_user_update():
        """Generate valid admin user update data."""
        return {
            "is_active": False,
            "current_level": "B1",
            "target_level": "C1"
        }

    @staticmethod
    def valid_admin_scenario_data():
        """Generate valid admin scenario creation data."""
        return {
            "scenario_title": f"Admin Scenario {uuid.uuid4().hex[:8]}",
            "context": "hotel",
            "difficulty_level": "A2",
            "roles": ["guest", "receptionist"],
            "goals": ["book a room", "ask about amenities"],
            "order": 2,
            "notes": "Admin test scenario",
            "is_active": True
        }

    @staticmethod
    def invalid_admin_scenario_invalid_roles():
        """Generate admin scenario with invalid roles."""
        return {
            "scenario_title": "Test Scenario",
            "context": "hotel",
            "difficulty_level": "A2",
            "roles": ["guest", "receptionist", "manager"],  # 3 roles, need 2
            "goals": ["book a room"],
            "order": 2,
            "is_active": True
        }

    # ========================================================================
    # Error Test Data
    # ========================================================================

    @staticmethod
    def invalid_json():
        """Generate invalid JSON for testing."""
        return "{ invalid json }"

    @staticmethod
    def empty_payload():
        """Generate empty payload."""
        return {}

    @staticmethod
    def very_long_string(length=1000):
        """Generate very long string."""
        return "a" * length
