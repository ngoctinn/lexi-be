"""Unit tests for StreamingResponse."""

import json
import pytest
from domain.services.streaming_response import StreamingResponse, StreamingMetrics


class TestStreamingResponse:
    """Test StreamingResponse streaming logic."""

    def test_streaming_metrics_initialization(self):
        """Test StreamingMetrics initialization."""
        metrics = StreamingMetrics()
        assert metrics.ttft_ms is None
        assert metrics.total_latency_ms is None
        assert metrics.token_count == 0
        assert metrics.is_timeout is False
        assert metrics.error_message is None

    def test_streaming_response_initialization(self):
        """Test StreamingResponse initialization."""
        response = StreamingResponse(timeout_seconds=5.0)
        assert response.timeout_seconds == 5.0
        assert response.metrics.token_count == 0

    def test_collect_response_empty_stream(self):
        """Test collecting response from empty stream."""
        response = StreamingResponse()
        event_stream = []
        
        text, metrics = response.collect_response(event_stream)
        assert text == ""
        assert metrics.token_count == 0
        assert metrics.total_latency_ms is not None

    def test_collect_response_single_chunk(self):
        """Test collecting response with single chunk."""
        response = StreamingResponse()
        
        # Simulate Bedrock streaming response
        chunk_data = {"completion": "Hello world"}
        chunk_bytes = json.dumps(chunk_data).encode("utf-8")
        
        event_stream = [
            {"chunk": {"bytes": chunk_bytes}}
        ]
        
        text, metrics = response.collect_response(event_stream)
        assert text == "Hello world"
        assert metrics.token_count == 1
        assert metrics.ttft_ms is not None
        assert metrics.total_latency_ms is not None

    def test_collect_response_multiple_chunks(self):
        """Test collecting response with multiple chunks."""
        response = StreamingResponse()
        
        chunks = [
            {"completion": "Hello "},
            {"completion": "world"},
            {"completion": "!"},
        ]
        
        event_stream = [
            {"chunk": {"bytes": json.dumps(chunk).encode("utf-8")}}
            for chunk in chunks
        ]
        
        text, metrics = response.collect_response(event_stream)
        assert text == "Hello world!"
        assert metrics.token_count == 3

    def test_collect_response_with_text_field(self):
        """Test collecting response with 'text' field instead of 'completion'."""
        response = StreamingResponse()
        
        chunk_data = {"text": "Alternative format"}
        chunk_bytes = json.dumps(chunk_data).encode("utf-8")
        
        event_stream = [
            {"chunk": {"bytes": chunk_bytes}}
        ]
        
        text, metrics = response.collect_response(event_stream)
        assert text == "Alternative format"
        assert metrics.token_count == 1

    def test_collect_response_with_output_field(self):
        """Test collecting response with 'output' field."""
        response = StreamingResponse()
        
        chunk_data = {"output": "Output format"}
        chunk_bytes = json.dumps(chunk_data).encode("utf-8")
        
        event_stream = [
            {"chunk": {"bytes": chunk_bytes}}
        ]
        
        text, metrics = response.collect_response(event_stream)
        assert text == "Output format"
        assert metrics.token_count == 1

    def test_collect_response_with_content_field(self):
        """Test collecting response with 'content' field."""
        response = StreamingResponse()
        
        chunk_data = {"content": "Content format"}
        chunk_bytes = json.dumps(chunk_data).encode("utf-8")
        
        event_stream = [
            {"chunk": {"bytes": chunk_bytes}}
        ]
        
        text, metrics = response.collect_response(event_stream)
        assert text == "Content format"
        assert metrics.token_count == 1

    def test_collect_response_raw_text(self):
        """Test collecting response with raw text (not JSON)."""
        response = StreamingResponse()
        
        raw_text = "Raw text response"
        chunk_bytes = raw_text.encode("utf-8")
        
        event_stream = [
            {"chunk": {"bytes": chunk_bytes}}
        ]
        
        text, metrics = response.collect_response(event_stream)
        assert text == "Raw text response"
        assert metrics.token_count == 1

    def test_collect_response_internal_server_error(self):
        """Test collecting response with internal server error."""
        response = StreamingResponse()
        
        event_stream = [
            {"internalServerException": {"message": "Server error"}}
        ]
        
        text, metrics = response.collect_response(event_stream)
        assert text == ""
        assert "Internal server error" in metrics.error_message

    def test_collect_response_model_stream_error(self):
        """Test collecting response with model stream error."""
        response = StreamingResponse()
        
        event_stream = [
            {"modelStreamErrorException": {"message": "Stream error"}}
        ]
        
        text, metrics = response.collect_response(event_stream)
        assert text == ""
        assert "Model stream error" in metrics.error_message

    def test_collect_response_model_timeout(self):
        """Test collecting response with model timeout."""
        response = StreamingResponse()
        
        event_stream = [
            {"modelTimeoutException": {"message": "Timeout"}}
        ]
        
        text, metrics = response.collect_response(event_stream)
        assert text == ""
        assert metrics.is_timeout is True
        assert "Model timeout" in metrics.error_message

    def test_collect_response_validation_error(self):
        """Test collecting response with validation error."""
        response = StreamingResponse()
        
        event_stream = [
            {"validationException": {"message": "Validation failed"}}
        ]
        
        text, metrics = response.collect_response(event_stream)
        assert text == ""
        assert "Validation error" in metrics.error_message

    def test_collect_response_throttling_error(self):
        """Test collecting response with throttling error."""
        response = StreamingResponse()
        
        event_stream = [
            {"throttlingException": {"message": "Too many requests"}}
        ]
        
        text, metrics = response.collect_response(event_stream)
        assert text == ""
        assert "Throttling error" in metrics.error_message

    def test_collect_response_service_unavailable(self):
        """Test collecting response with service unavailable error."""
        response = StreamingResponse()
        
        event_stream = [
            {"serviceUnavailableException": {"message": "Service down"}}
        ]
        
        text, metrics = response.collect_response(event_stream)
        assert text == ""
        assert "Service unavailable" in metrics.error_message

    def test_stream_tokens_single_token(self):
        """Test streaming tokens one by one."""
        response = StreamingResponse()
        
        chunks = [
            {"completion": "Hello "},
            {"completion": "world"},
            {"completion": "!"},
        ]
        
        event_stream = [
            {"chunk": {"bytes": json.dumps(chunk).encode("utf-8")}}
            for chunk in chunks
        ]
        
        tokens = list(response.stream_tokens(event_stream))
        assert len(tokens) == 3
        assert tokens[0][0] == "Hello "
        assert tokens[1][0] == "world"
        assert tokens[2][0] == "!"
        
        # Check metrics
        assert tokens[2][1].token_count == 3
        assert tokens[0][1].ttft_ms is not None

    def test_stream_tokens_with_error(self):
        """Test streaming tokens with error in middle."""
        response = StreamingResponse()
        
        event_stream = [
            {"chunk": {"bytes": json.dumps({"completion": "Hello"}).encode("utf-8")}},
            {"modelStreamErrorException": {"message": "Error"}},
        ]
        
        tokens = list(response.stream_tokens(event_stream))
        assert len(tokens) == 1
        assert tokens[0][0] == "Hello"
        assert response.metrics.error_message is not None

    def test_ttft_tracking(self):
        """Test TTFT (Time To First Token) tracking."""
        response = StreamingResponse()
        
        chunk_data = {"completion": "First token"}
        chunk_bytes = json.dumps(chunk_data).encode("utf-8")
        
        event_stream = [
            {"chunk": {"bytes": chunk_bytes}}
        ]
        
        text, metrics = response.collect_response(event_stream)
        assert metrics.ttft_ms is not None
        assert metrics.ttft_ms >= 0  # Should be very small for test

    def test_total_latency_tracking(self):
        """Test total latency tracking."""
        response = StreamingResponse()
        
        chunks = [
            {"completion": "Token 1"},
            {"completion": "Token 2"},
        ]
        
        event_stream = [
            {"chunk": {"bytes": json.dumps(chunk).encode("utf-8")}}
            for chunk in chunks
        ]
        
        text, metrics = response.collect_response(event_stream)
        assert metrics.total_latency_ms is not None
        assert metrics.total_latency_ms >= metrics.ttft_ms
