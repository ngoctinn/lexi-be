"""
Synchronous wrapper for StreamingSTTService.

Lambda handlers cannot be async, but can run async code using asyncio.run().
Uses a single shared event loop to avoid conflicts with long-running streams.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from infrastructure.services.streaming_stt_service import StreamingSTTService, TranscriptResult

logger = logging.getLogger(__name__)

# Shared event loop for all async operations (reused across Lambda invocations)
_event_loop: Optional[asyncio.AbstractEventLoop] = None


def _get_or_create_loop() -> asyncio.AbstractEventLoop:
    """Get existing event loop or create new one."""
    global _event_loop
    
    if _event_loop is None or _event_loop.is_closed():
        _event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_event_loop)
        logger.info("Created new event loop for streaming")
    
    return _event_loop


class StreamingSTTServiceSync:
    """
    Synchronous wrapper around StreamingSTTService.
    
    Uses a shared event loop to run async methods from sync Lambda handler.
    The loop persists across invocations to support long-running streams.
    """

    def __init__(self, region: str = "ap-southeast-1"):
        self._service = StreamingSTTService(region=region)
        self._loop = _get_or_create_loop()

    def start_stream(
        self,
        stream_id: str,
        language_code: str = "en-US",
        sample_rate: int = 16000,
        media_encoding: str = "opus",
    ) -> str:
        """
        Start a new Transcribe streaming session (sync wrapper).
        
        Args:
            stream_id: Unique identifier for this stream
            language_code: Language code (e.g., "en-US")
            sample_rate: Audio sample rate in Hz (16000 for 16kHz)
            media_encoding: Audio encoding ("opus" or "pcm")
        
        Returns:
            stream_id for subsequent operations
        """
        return self._loop.run_until_complete(
            self._service.start_stream(
                stream_id=stream_id,
                language_code=language_code,
                sample_rate=sample_rate,
                media_encoding=media_encoding,
            )
        )

    def send_audio_chunk(self, stream_id: str, audio_bytes: bytes) -> None:
        """
        Send audio chunk to active stream (sync wrapper).
        
        Args:
            stream_id: Stream identifier
            audio_bytes: Audio data bytes
        """
        self._loop.run_until_complete(
            self._service.send_audio_chunk(stream_id=stream_id, audio_bytes=audio_bytes)
        )

    def get_transcripts(self, stream_id: str) -> list[TranscriptResult]:
        """
        Get accumulated transcripts since last call (non-blocking, already sync).
        
        Args:
            stream_id: Stream identifier
        
        Returns:
            List of TranscriptResult objects (partial and final)
        """
        return self._service.get_transcripts(stream_id=stream_id)

    def close_stream(self, stream_id: str) -> Optional[TranscriptResult]:
        """
        Close stream and return final transcript (sync wrapper).
        
        Args:
            stream_id: Stream identifier
        
        Returns:
            Final TranscriptResult or None if no final transcript
        """
        return self._loop.run_until_complete(self._service.close_stream(stream_id=stream_id))
