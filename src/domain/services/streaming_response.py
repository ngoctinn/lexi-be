"""
Streaming Response Handler for Bedrock InvokeModelWithResponseStream

Handles:
- Streaming events from Bedrock
- Token collection
- TTFT (Time To First Token) tracking
- Timeout handling
- Error handling
"""

import json
import logging
import time
from dataclasses import dataclass
from typing import Iterator, Optional

logger = logging.getLogger(__name__)


@dataclass
class StreamingMetrics:
    """Metrics collected during streaming."""
    ttft_ms: Optional[float] = None  # Time to first token in milliseconds
    total_latency_ms: Optional[float] = None  # Total latency in milliseconds
    token_count: int = 0  # Number of tokens received
    is_timeout: bool = False  # Whether streaming timed out
    error_message: Optional[str] = None  # Error message if any


class StreamingResponse:
    """Handles streaming responses from Bedrock."""

    def __init__(self, timeout_seconds: float = 5.0):
        """
        Initialize streaming response handler.
        
        Args:
            timeout_seconds: Maximum time to wait for first token (TTFT)
        """
        self.timeout_seconds = timeout_seconds
        self.metrics = StreamingMetrics()
        self._start_time = None
        self._first_token_time = None

    def collect_response(self, event_stream) -> tuple[str, StreamingMetrics]:
        """
        Collect complete response from event stream.
        
        Args:
            event_stream: EventStream from invoke_model_with_response_stream
            
        Returns:
            Tuple of (complete_response_text, metrics)
        """
        self._start_time = time.time()
        response_text = ""
        
        try:
            for event in event_stream:
                # Check for timeout on first token
                if self._first_token_time is None:
                    elapsed = time.time() - self._start_time
                    if elapsed > self.timeout_seconds:
                        self.metrics.is_timeout = True
                        self.metrics.error_message = f"TTFT timeout: {elapsed:.2f}s > {self.timeout_seconds}s"
                        logger.warning(self.metrics.error_message)
                        break
                
                # Handle chunk event
                if "chunk" in event:
                    chunk = event["chunk"]
                    if "bytes" in chunk:
                        # Record TTFT on first token
                        if self._first_token_time is None:
                            self._first_token_time = time.time()
                            self.metrics.ttft_ms = (self._first_token_time - self._start_time) * 1000
                            logger.debug(f"TTFT: {self.metrics.ttft_ms:.2f}ms")
                        
                        # Decode chunk bytes
                        chunk_bytes = chunk["bytes"]
                        chunk_text = chunk_bytes.decode("utf-8")
                        
                        # Parse JSON to extract text
                        try:
                            chunk_json = json.loads(chunk_text)
                            # Different models have different response formats
                            # Try common fields: completion, text, output, content
                            if "completion" in chunk_json:
                                token_text = chunk_json["completion"]
                            elif "text" in chunk_json:
                                token_text = chunk_json["text"]
                            elif "output" in chunk_json:
                                token_text = chunk_json["output"]
                            elif "content" in chunk_json:
                                token_text = chunk_json["content"]
                            else:
                                # If no recognized field, use entire chunk
                                token_text = chunk_text
                            
                            response_text += token_text
                            self.metrics.token_count += 1
                        except json.JSONDecodeError:
                            # If not JSON, treat as raw text
                            response_text += chunk_text
                            self.metrics.token_count += 1
                
                # Handle error events
                elif "internalServerException" in event:
                    error = event["internalServerException"]
                    self.metrics.error_message = f"Internal server error: {error.get('message', 'Unknown')}"
                    logger.error(self.metrics.error_message)
                    break
                
                elif "modelStreamErrorException" in event:
                    error = event["modelStreamErrorException"]
                    self.metrics.error_message = f"Model stream error: {error.get('message', 'Unknown')}"
                    logger.error(self.metrics.error_message)
                    break
                
                elif "modelTimeoutException" in event:
                    error = event["modelTimeoutException"]
                    self.metrics.error_message = f"Model timeout: {error.get('message', 'Unknown')}"
                    self.metrics.is_timeout = True
                    logger.error(self.metrics.error_message)
                    break
                
                elif "validationException" in event:
                    error = event["validationException"]
                    self.metrics.error_message = f"Validation error: {error.get('message', 'Unknown')}"
                    logger.error(self.metrics.error_message)
                    break
                
                elif "throttlingException" in event:
                    error = event["throttlingException"]
                    self.metrics.error_message = f"Throttling error: {error.get('message', 'Unknown')}"
                    logger.error(self.metrics.error_message)
                    break
                
                elif "serviceUnavailableException" in event:
                    error = event["serviceUnavailableException"]
                    self.metrics.error_message = f"Service unavailable: {error.get('message', 'Unknown')}"
                    logger.error(self.metrics.error_message)
                    break
        
        except Exception as e:
            self.metrics.error_message = f"Streaming error: {str(e)}"
            logger.exception(self.metrics.error_message)
        
        finally:
            # Calculate total latency
            if self._start_time:
                self.metrics.total_latency_ms = (time.time() - self._start_time) * 1000
        
        return response_text, self.metrics

    def stream_tokens(self, event_stream) -> Iterator[tuple[str, StreamingMetrics]]:
        """
        Stream tokens incrementally (for real-time display).
        
        Yields:
            Tuple of (token_text, current_metrics) for each token
        """
        self._start_time = time.time()
        
        try:
            for event in event_stream:
                # Check for timeout on first token
                if self._first_token_time is None:
                    elapsed = time.time() - self._start_time
                    if elapsed > self.timeout_seconds:
                        self.metrics.is_timeout = True
                        self.metrics.error_message = f"TTFT timeout: {elapsed:.2f}s > {self.timeout_seconds}s"
                        logger.warning(self.metrics.error_message)
                        break
                
                # Handle chunk event
                if "chunk" in event:
                    chunk = event["chunk"]
                    if "bytes" in chunk:
                        # Record TTFT on first token
                        if self._first_token_time is None:
                            self._first_token_time = time.time()
                            self.metrics.ttft_ms = (self._first_token_time - self._start_time) * 1000
                            logger.debug(f"TTFT: {self.metrics.ttft_ms:.2f}ms")
                        
                        # Decode chunk bytes
                        chunk_bytes = chunk["bytes"]
                        chunk_text = chunk_bytes.decode("utf-8")
                        
                        # Parse JSON to extract text
                        try:
                            chunk_json = json.loads(chunk_text)
                            if "completion" in chunk_json:
                                token_text = chunk_json["completion"]
                            elif "text" in chunk_json:
                                token_text = chunk_json["text"]
                            elif "output" in chunk_json:
                                token_text = chunk_json["output"]
                            elif "content" in chunk_json:
                                token_text = chunk_json["content"]
                            else:
                                token_text = chunk_text
                            
                            self.metrics.token_count += 1
                            yield token_text, self.metrics
                        except json.JSONDecodeError:
                            self.metrics.token_count += 1
                            yield chunk_text, self.metrics
                
                # Handle error events
                elif "internalServerException" in event:
                    error = event["internalServerException"]
                    self.metrics.error_message = f"Internal server error: {error.get('message', 'Unknown')}"
                    logger.error(self.metrics.error_message)
                    break
                
                elif "modelStreamErrorException" in event:
                    error = event["modelStreamErrorException"]
                    self.metrics.error_message = f"Model stream error: {error.get('message', 'Unknown')}"
                    logger.error(self.metrics.error_message)
                    break
                
                elif "modelTimeoutException" in event:
                    error = event["modelTimeoutException"]
                    self.metrics.error_message = f"Model timeout: {error.get('message', 'Unknown')}"
                    self.metrics.is_timeout = True
                    logger.error(self.metrics.error_message)
                    break
                
                elif "validationException" in event:
                    error = event["validationException"]
                    self.metrics.error_message = f"Validation error: {error.get('message', 'Unknown')}"
                    logger.error(self.metrics.error_message)
                    break
                
                elif "throttlingException" in event:
                    error = event["throttlingException"]
                    self.metrics.error_message = f"Throttling error: {error.get('message', 'Unknown')}"
                    logger.error(self.metrics.error_message)
                    break
                
                elif "serviceUnavailableException" in event:
                    error = event["serviceUnavailableException"]
                    self.metrics.error_message = f"Service unavailable: {error.get('message', 'Unknown')}"
                    logger.error(self.metrics.error_message)
                    break
        
        except Exception as e:
            self.metrics.error_message = f"Streaming error: {str(e)}"
            logger.exception(self.metrics.error_message)
        
        finally:
            # Calculate total latency
            if self._start_time:
                self.metrics.total_latency_ms = (time.time() - self._start_time) * 1000
