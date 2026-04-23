from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent

logger = logging.getLogger(__name__)


@dataclass
class TranscriptResult:
    """Represents a transcription result (partial or final)."""
    text: str
    confidence: float
    is_partial: bool


class StreamingSTTService:
    """
    Real-time speech-to-text using Amazon Transcribe Streaming API.
    
    Uses amazon-transcribe-streaming-sdk (async Python SDK).
    Boto3 does NOT support Transcribe Streaming.
    
    Docs: https://github.com/awslabs/amazon-transcribe-streaming-sdk
    API Reference: https://docs.aws.amazon.com/transcribe/latest/APIReference/API_streaming_StartStreamTranscription.html
    """

    def __init__(self, region: str = "ap-southeast-1"):
        self._region = region
        self._active_streams: Dict[str, TranscribeStreamingClient] = {}
        self._transcript_buffers: Dict[str, List[TranscriptResult]] = {}
        self._stream_handlers: Dict[str, StreamHandler] = {}

    async def start_stream(
        self,
        stream_id: str,
        language_code: str = "en-US",
        sample_rate: int = 16000,
        media_encoding: str = "opus",
    ) -> str:
        """
        Start a new Transcribe streaming session.
        
        Args:
            stream_id: Unique identifier for this stream
            language_code: Language code (e.g., "en-US")
            sample_rate: Audio sample rate in Hz (16000 for 16kHz)
            media_encoding: Audio encoding ("opus" or "pcm")
        
        Returns:
            stream_id for subsequent operations
        
        Raises:
            ValueError: If stream_id already exists
        """
        if stream_id in self._active_streams:
            raise ValueError(f"Stream {stream_id} already exists")

        try:
            # Create streaming client
            client = TranscribeStreamingClient(region=self._region)

            # Create event handler
            handler = StreamHandler(stream_id, self._transcript_buffers)

            # Start stream with event handler
            stream = await client.start_stream_transcription(
                language_code=language_code,
                media_sample_rate_hz=sample_rate,
                media_encoding=media_encoding,
                transcript_result_stream_handler=handler,
            )

            # Store stream and handler
            self._active_streams[stream_id] = stream
            self._stream_handlers[stream_id] = handler
            self._transcript_buffers[stream_id] = []

            logger.info(
                "Transcribe stream started",
                extra={
                    "stream_id": stream_id,
                    "language_code": language_code,
                    "sample_rate": sample_rate,
                    "media_encoding": media_encoding,
                },
            )

            return stream_id

        except Exception as exc:
            logger.exception("Failed to start Transcribe stream", extra={"stream_id": stream_id})
            raise

    async def send_audio_chunk(self, stream_id: str, audio_bytes: bytes) -> None:
        """
        Send audio chunk to active stream.
        
        Args:
            stream_id: Stream identifier
            audio_bytes: Audio data bytes
        
        Raises:
            ValueError: If stream_id doesn't exist
        """
        if stream_id not in self._active_streams:
            raise ValueError(f"No active stream: {stream_id}")

        try:
            stream = self._active_streams[stream_id]
            # Send audio to stream (non-blocking)
            await stream.input_stream.send_audio_event(audio_chunk=audio_bytes)
        except Exception as exc:
            logger.exception(
                "Failed to send audio chunk",
                extra={"stream_id": stream_id, "chunk_size": len(audio_bytes)},
            )
            raise

    def get_transcripts(self, stream_id: str) -> List[TranscriptResult]:
        """
        Get accumulated transcripts since last call (non-blocking).
        
        Args:
            stream_id: Stream identifier
        
        Returns:
            List of TranscriptResult objects (partial and final)
        """
        if stream_id not in self._transcript_buffers:
            return []

        transcripts = self._transcript_buffers[stream_id]
        self._transcript_buffers[stream_id] = []  # Clear buffer
        return transcripts

    async def close_stream(self, stream_id: str) -> Optional[TranscriptResult]:
        """
        Close stream and return final transcript.
        
        Args:
            stream_id: Stream identifier
        
        Returns:
            Final TranscriptResult or None if no final transcript
        """
        if stream_id not in self._active_streams:
            logger.warning("Stream not found", extra={"stream_id": stream_id})
            return None

        try:
            stream = self._active_streams[stream_id]

            # Signal end of audio
            await stream.input_stream.end_stream()

            # Wait for handler to finish processing
            handler = self._stream_handlers.get(stream_id)
            if handler:
                await handler.wait_for_completion()

            # Get final transcript from buffer
            transcripts = self._transcript_buffers.get(stream_id, [])
            final = next((t for t in reversed(transcripts) if not t.is_partial), None)

            logger.info(
                "Transcribe stream closed",
                extra={
                    "stream_id": stream_id,
                    "has_final_transcript": final is not None,
                    "final_confidence": final.confidence if final else 0.0,
                },
            )

            return final

        except Exception as exc:
            logger.exception("Error closing stream", extra={"stream_id": stream_id})
            raise

        finally:
            # Cleanup
            self._active_streams.pop(stream_id, None)
            self._stream_handlers.pop(stream_id, None)
            self._transcript_buffers.pop(stream_id, None)


class StreamHandler(TranscriptResultStreamHandler):
    """
    Event handler for Transcribe streaming results.
    
    Processes transcript events and stores them in a buffer.
    """

    def __init__(self, stream_id: str, buffers: Dict[str, List[TranscriptResult]]):
        self._stream_id = stream_id
        self._buffers = buffers
        self._completion_event = asyncio.Event()

    async def handle_transcript_event(self, transcript_event: TranscriptEvent) -> None:
        """
        Handle transcript event from Transcribe stream.
        
        Extracts partial and final transcripts and stores in buffer.
        """
        try:
            results = transcript_event.transcript.results
            for result in results:
                if not result.alternatives:
                    continue

                alternative = result.alternatives[0]
                transcript_text = alternative.transcript

                # Calculate average confidence from items
                items = alternative.items or []
                confidences = [item.confidence for item in items if item.confidence is not None]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 1.0

                # Add to buffer
                transcript_result = TranscriptResult(
                    text=transcript_text,
                    confidence=avg_confidence,
                    is_partial=result.is_partial,
                )

                self._buffers[self._stream_id].append(transcript_result)

                log_level = "debug" if result.is_partial else "info"
                logger.log(
                    logging.DEBUG if log_level == "debug" else logging.INFO,
                    "Transcript received",
                    extra={
                        "stream_id": self._stream_id,
                        "is_partial": result.is_partial,
                        "text": transcript_text[:100],  # Log first 100 chars
                        "confidence": avg_confidence,
                    },
                )

        except Exception as exc:
            logger.exception(
                "Error handling transcript event",
                extra={"stream_id": self._stream_id},
            )

    async def handle_error(self, error: Exception) -> None:
        """Handle stream errors."""
        logger.error(
            "Transcribe stream error",
            extra={"stream_id": self._stream_id, "error": str(error)},
        )
        self._completion_event.set()

    async def handle_stream_termination(self) -> None:
        """Handle stream termination."""
        logger.info("Transcribe stream terminated", extra={"stream_id": self._stream_id})
        self._completion_event.set()

    async def wait_for_completion(self, timeout: float = 30.0) -> None:
        """
        Wait for stream to complete processing.
        
        Args:
            timeout: Maximum time to wait in seconds
        """
        try:
            await asyncio.wait_for(self._completion_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(
                "Stream completion timeout",
                extra={"stream_id": self._stream_id, "timeout": timeout},
            )
