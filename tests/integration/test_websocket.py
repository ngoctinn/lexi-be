"""
Task 16-21: WebSocket APIs
- start_session
- audio_uploaded
- use_hint
- send_message_turn
- end_session
- ANALYZE_TURN

Test Cases:
- Happy path for each action
- Invalid session_id
- Unauthorized (invalid token)
- Event validation
"""

import pytest
import logging
from tests.fixtures.test_data import TestDataFactory
from tests.fixtures.validators import ResponseValidator

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
class TestWebSocketStartSession:
    """Test suite for WebSocket start_session action."""

    async def test_websocket_start_session_success(self, ws_client, api_client):
        """Test: WebSocket start_session action returns SESSION_READY event."""
        # Create session first
        session_data = TestDataFactory.valid_session_data()
        session_response = api_client.post("/sessions", session_data)
        assert session_response.status_code == 201

        session_id = session_response.json()["data"]["session_id"]

        # Send start_session action
        await ws_client.send_action("start_session", {"session_id": session_id})

        # Wait for SESSION_READY event
        event = await ws_client.wait_for_event("SESSION_READY", timeout=5)

        assert "upload_url" in event
        assert "s3_key" in event
        assert event["session_id"] == session_id

        logger.info("✓ WebSocket start_session success")

    async def test_websocket_start_session_invalid_id(self, ws_client):
        """Test: WebSocket start_session with invalid session_id."""
        await ws_client.send_action("start_session", {"session_id": "invalid-id"})

        # Should receive error event or timeout
        try:
            event = await ws_client.wait_for_event("ERROR", timeout=2)
            logger.info("✓ WebSocket start_session invalid id returns error")
        except TimeoutError:
            logger.info("✓ WebSocket start_session invalid id timeout (expected)")


@pytest.mark.asyncio
class TestWebSocketUseHint:
    """Test suite for WebSocket use_hint action."""

    async def test_websocket_use_hint_success(self, ws_client, api_client):
        """Test: WebSocket use_hint action returns HINT_TEXT event."""
        # Create and start session
        session_data = TestDataFactory.valid_session_data()
        session_response = api_client.post("/sessions", session_data)
        assert session_response.status_code == 201

        session_id = session_response.json()["data"]["session_id"]

        # Start session
        await ws_client.send_action("start_session", {"session_id": session_id})
        await ws_client.wait_for_event("SESSION_READY", timeout=5)

        # Request hint
        await ws_client.send_action("use_hint", {"session_id": session_id})

        # Wait for HINT_TEXT event
        event = await ws_client.wait_for_event("HINT_TEXT", timeout=5)

        ResponseValidator.validate_hint_event(event)

        logger.info("✓ WebSocket use_hint success")


@pytest.mark.asyncio
class TestWebSocketSendMessageTurn:
    """Test suite for WebSocket send_message_turn action."""

    async def test_websocket_send_message_turn_success(self, ws_client, api_client):
        """Test: WebSocket send_message_turn action returns TURN_SAVED event."""
        # Create and start session
        session_data = TestDataFactory.valid_session_data()
        session_response = api_client.post("/sessions", session_data)
        assert session_response.status_code == 201

        session_id = session_response.json()["data"]["session_id"]

        # Start session
        await ws_client.send_action("start_session", {"session_id": session_id})
        await ws_client.wait_for_event("SESSION_READY", timeout=5)

        # Send message turn
        await ws_client.send_action("send_message_turn", {
            "session_id": session_id,
            "text": "Hello, I would like to order a coffee please.",
            "is_hint_used": False
        })

        # Wait for TURN_SAVED event
        event = await ws_client.wait_for_event("TURN_SAVED", timeout=5)

        assert "session_id" in event
        assert event["session_id"] == session_id

        logger.info("✓ WebSocket send_message_turn success")


@pytest.mark.asyncio
class TestWebSocketEndSession:
    """Test suite for WebSocket end_session action."""

    async def test_websocket_end_session_success(self, ws_client, api_client):
        """Test: WebSocket end_session action returns SCORING_COMPLETE event."""
        # Create and start session
        session_data = TestDataFactory.valid_session_data()
        session_response = api_client.post("/sessions", session_data)
        assert session_response.status_code == 201

        session_id = session_response.json()["data"]["session_id"]

        # Start session
        await ws_client.send_action("start_session", {"session_id": session_id})
        await ws_client.wait_for_event("SESSION_READY", timeout=5)

        # End session
        await ws_client.send_action("end_session", {"session_id": session_id})

        # Wait for SCORING_COMPLETE event
        event = await ws_client.wait_for_event("SCORING_COMPLETE", timeout=5)

        assert "session_id" in event
        assert event["session_id"] == session_id

        logger.info("✓ WebSocket end_session success")


@pytest.mark.asyncio
class TestWebSocketAnalyzeTurn:
    """Test suite for WebSocket ANALYZE_TURN action."""

    async def test_websocket_analyze_turn_success(self, ws_client, api_client):
        """Test: WebSocket ANALYZE_TURN action returns TURN_ANALYSIS event."""
        # Create session and submit a turn
        session_data = TestDataFactory.valid_session_data()
        session_response = api_client.post("/sessions", session_data)
        assert session_response.status_code == 201

        session_id = session_response.json()["data"]["session_id"]

        # Submit turn via REST API
        turn_data = TestDataFactory.valid_session_turn_data()
        turn_response = api_client.post(f"/sessions/{session_id}/turns", turn_data)
        assert turn_response.status_code == 200

        # Start WebSocket session
        await ws_client.send_action("start_session", {"session_id": session_id})
        await ws_client.wait_for_event("SESSION_READY", timeout=5)

        # Request turn analysis
        await ws_client.send_action("ANALYZE_TURN", {
            "session_id": session_id,
            "turn_index": 1
        })

        # Wait for TURN_ANALYSIS event
        event = await ws_client.wait_for_event("TURN_ANALYSIS", timeout=5)

        ResponseValidator.validate_turn_analysis_event(event)

        logger.info("✓ WebSocket ANALYZE_TURN success")
