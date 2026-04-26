"""
WebSocketClient - WebSocket wrapper for real-time API testing

Provides:
- JWT authentication
- Event queue for async message handling
- Timeout-based event waiting
- Connection lifecycle management
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketClient:
    """WebSocket client for real-time API testing with JWT auth and event handling."""

    def __init__(self, timeout: int = 5):
        """
        Initialize WebSocket client.

        Args:
            timeout: Default timeout for wait_for_event in seconds
        """
        self.timeout = timeout
        self.ws = None
        self.event_queue = asyncio.Queue()
        self.receive_task = None
        logger.info(f"WebSocketClient initialized with timeout={timeout}s")

    async def connect(self, url: str, token: str) -> None:
        """
        Connect to WebSocket with JWT token.

        Args:
            url: WebSocket URL (e.g., wss://...)
            token: JWT token for authentication

        Raises:
            ConnectionError: Failed to connect
        """
        try:
            import websockets
        except ImportError:
            raise ImportError("websockets library not installed. Install with: pip install websockets")

        try:
            # Connect with token in query string
            ws_url = f"{url}?token={token}"
            self.ws = await websockets.connect(ws_url)
            logger.info(f"Connected to {url}")

            # Start background task to receive messages
            self.receive_task = asyncio.create_task(self._receive_messages())
        except Exception as e:
            logger.error(f"Failed to connect to {url}: {e}")
            raise ConnectionError(f"WebSocket connection failed: {e}") from e

    async def send_action(self, action: str, payload: Dict[str, Any] = None) -> None:
        """
        Send action to WebSocket.

        Args:
            action: Action name (e.g., "start_session")
            payload: Optional action payload

        Raises:
            RuntimeError: Not connected
        """
        if not self.ws:
            raise RuntimeError("WebSocket not connected. Call connect() first.")

        message = {"action": action}
        if payload:
            message.update(payload)

        try:
            await self.ws.send(json.dumps(message))
            logger.debug(f"Sent action: {action}")
        except Exception as e:
            logger.error(f"Failed to send action {action}: {e}")
            raise

    async def wait_for_event(self, event_type: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Wait for specific event from WebSocket.

        Args:
            event_type: Event type to wait for (e.g., "SESSION_READY")
            timeout: Timeout in seconds (uses default if not specified)

        Returns:
            Event data as dictionary

        Raises:
            TimeoutError: Event not received within timeout
            RuntimeError: Not connected
        """
        if not self.ws:
            raise RuntimeError("WebSocket not connected. Call connect() first.")

        timeout = timeout or self.timeout

        try:
            # Wait for event with timeout
            while True:
                event = await asyncio.wait_for(self.event_queue.get(), timeout=timeout)

                # Check if this is the event we're looking for
                if event.get("event") == event_type:
                    logger.debug(f"Received event: {event_type}")
                    return event

                # If not, log and continue waiting
                logger.debug(f"Skipped event: {event.get('event')}, waiting for {event_type}")

        except asyncio.TimeoutError:
            logger.error(f"Timeout waiting for event: {event_type}")
            raise TimeoutError(f"Event '{event_type}' not received within {timeout}s")

    async def _receive_messages(self) -> None:
        """
        Background task to receive messages from WebSocket.
        Parses JSON and queues events.
        """
        try:
            async for message in self.ws:
                try:
                    event = json.loads(message)
                    await self.event_queue.put(event)
                    logger.debug(f"Queued event: {event.get('event', 'unknown')}")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse WebSocket message: {e}")
        except Exception as e:
            logger.error(f"WebSocket receive error: {e}")
        finally:
            logger.info("WebSocket receive task ended")

    async def close(self) -> None:
        """Close WebSocket connection and cleanup."""
        if self.receive_task:
            self.receive_task.cancel()
            try:
                await self.receive_task
            except asyncio.CancelledError:
                pass

        if self.ws:
            await self.ws.close()
            logger.info("WebSocket closed")
