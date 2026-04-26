"""
Streaming Response Handler for Bedrock InvokeModelWithResponseStream

Handles:
- Streaming events from Bedrock
- Token collection
- TTFT (Time To First Token) tracking
- Timeout handling
- Error handling

AWS Reference:
https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-runtime_example_bedrock-runtime_InvokeModelWithResponseStream_AnthropicClaude_section.html
"""

import json
import logging
import time
from dataclasses import dataclass
from typing import Iterator, Optional, Dict, Any

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

    def __init__(self, timeout_seconds: float = 5.0, bedrock_client=None):
        """
        Initialize streaming response handler.
        
        Args:
            timeout_seconds: Maximum time to wait for first token (TTFT)
            bedrock_client: Optional boto3 Bedrock Runtime client
        """
        self.timeout_seconds = timeout_seconds
        self.bedrock_client = bedrock_client
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
                        
                        # Parse JSON to extract text (Anthropic Claude format)
                        # Reference: https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-runtime_example_bedrock-runtime_InvokeModelWithResponseStream_AnthropicClaude_section.html
                        try:
                            chunk_json = json.loads(chunk_text)
                            
                            # Anthropic Claude Messages API format
                            if chunk_json.get("type") == "content_block_delta":
                                token_text = chunk_json.get("delta", {}).get("text", "")
                                response_text += token_text
                                self.metrics.token_count += 1
                            # Legacy format fallback
                            elif "completion" in chunk_json:
                                token_text = chunk_json["completion"]
                                response_text += token_text
                                self.metrics.token_count += 1
                            elif "text" in chunk_json:
                                token_text = chunk_json["text"]
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
    
    def invoke_with_streaming(
        self,
        model_id: str,
        system_prompt: str | list[dict],
        user_message: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Invoke Bedrock model with streaming and return complete response with metrics.
        
        Supports both Amazon Nova (automatic caching) and Anthropic Claude formats.
        
        Args:
            model_id: Bedrock model ID (e.g., "amazon.nova-micro-v1:0" or "anthropic.claude-3-haiku-20240307-v1:0")
            system_prompt: System prompt (string for Nova, string or list with cache_control for Claude)
            user_message: User message text
            max_tokens: Maximum tokens to generate
            temperature: Temperature for sampling
            
        Returns:
            Dict with keys: text, ttft_ms, latency_ms, input_tokens, output_tokens
        """
        if self.bedrock_client is None:
            raise ValueError("bedrock_client is required for invoke_with_streaming")
        
        # Detect model family and build appropriate request format
        if "nova" in model_id.lower():
            # Amazon Nova format
            # Reference: https://docs.aws.amazon.com/nova/latest/userguide/complete-request-schema.html
            native_request = {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": user_message}],
                    }
                ],
                "inferenceConfig": {
                    "maxTokens": max_tokens,
                    "temperature": temperature,
                }
            }
            
            # Add system prompt (Nova format: list of {text} objects)
            if system_prompt:
                if isinstance(system_prompt, str):
                    # Single string — wrap in list for Nova
                    native_request["system"] = [{"text": system_prompt}]
                elif isinstance(system_prompt, list):
                    # Already a list — use as-is (backward compatibility)
                    native_request["system"] = [
                        {"text": block["text"]} for block in system_prompt if "text" in block
                    ]
        else:
            # Anthropic Claude format (fallback for compatibility)
            # Reference: https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages.html
            native_request = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": user_message}],
                    }
                ],
            }
            
            # Add system prompt (supports both string and list with cache checkpoint)
            if system_prompt:
                native_request["system"] = system_prompt
        
        # Convert to JSON
        request_body = json.dumps(native_request)
        
        # Invoke model with streaming
        # Reference: https://docs.aws.amazon.com/boto3/latest/reference/services/bedrock-runtime/client/invoke_model_with_response_stream.html
        streaming_response = self.bedrock_client.invoke_model_with_response_stream(
            modelId=model_id,
            body=request_body,
        )
        
        # Collect response using existing method
        response_text, metrics = self.collect_response(streaming_response["body"])
        
        # Extract token counts from final event (if available)
        # Note: Token counts are in the final metadata event, not in chunks
        input_tokens = 0
        output_tokens = 0
        
        # Return structured response
        return {
            "text": response_text,
            "ttft_ms": metrics.ttft_ms,
            "latency_ms": metrics.total_latency_ms,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "error_message": metrics.error_message,
            "is_timeout": metrics.is_timeout,
        }

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
                        
                        # Parse JSON to extract text (Anthropic Claude format)
                        try:
                            chunk_json = json.loads(chunk_text)
                            
                            # Anthropic Claude Messages API format
                            if chunk_json.get("type") == "content_block_delta":
                                token_text = chunk_json.get("delta", {}).get("text", "")
                                if token_text:
                                    self.metrics.token_count += 1
                                    yield token_text, self.metrics
                            # Legacy format fallback
                            elif "completion" in chunk_json:
                                token_text = chunk_json["completion"]
                                self.metrics.token_count += 1
                                yield token_text, self.metrics
                            elif "text" in chunk_json:
                                token_text = chunk_json["text"]
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
