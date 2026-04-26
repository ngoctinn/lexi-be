"""Unit tests for RetryService."""

from pathlib import Path
import sys
import time
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from infrastructure.services.retry_service import RetryService


class TestRetryService:
    """Tests for RetryService."""

    def test_successful_execution_no_retry(self):
        """Test successful execution without retry."""
        retry_service = RetryService()
        mock_func = Mock(return_value="success")
        
        result = retry_service.execute_with_retry(mock_func)
        
        assert result == "success"
        assert mock_func.call_count == 1

    def test_retry_on_transient_error(self):
        """Test retry on transient error (timeout)."""
        retry_service = RetryService()
        mock_func = Mock(side_effect=[TimeoutError("timeout"), "success"])
        
        result = retry_service.execute_with_retry(mock_func, max_retries=2, backoff_delays=[0.01, 0.01])
        
        assert result == "success"
        assert mock_func.call_count == 2

    def test_no_retry_on_permanent_error(self):
        """Test no retry on permanent error (404)."""
        retry_service = RetryService()
        error = Exception("404 Not Found")
        error.response = {"status_code": 404}
        mock_func = Mock(side_effect=error)
        
        try:
            retry_service.execute_with_retry(mock_func)
            assert False, "Should have raised exception"
        except Exception as e:
            assert mock_func.call_count == 1

    def test_exponential_backoff(self):
        """Test exponential backoff delays."""
        retry_service = RetryService()
        call_times = []
        
        def track_calls():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise TimeoutError("timeout")
            return "success"
        
        mock_func = Mock(side_effect=track_calls)
        
        result = retry_service.execute_with_retry(mock_func, max_retries=2, backoff_delays=[0.05, 0.05])
        
        assert result == "success"
        assert mock_func.call_count == 3
        
        # Check backoff delays (with some tolerance)
        if len(call_times) >= 2:
            delay1 = call_times[1] - call_times[0]
            assert delay1 >= 0.04  # Allow some tolerance

    def test_max_retries_exhausted(self):
        """Test error raised after max retries exhausted."""
        retry_service = RetryService()
        mock_func = Mock(side_effect=TimeoutError("timeout"))
        
        try:
            retry_service.execute_with_retry(mock_func, max_retries=2, backoff_delays=[0.01, 0.01])
            assert False, "Should have raised exception"
        except TimeoutError:
            assert mock_func.call_count == 3  # 1 initial + 2 retries

    def test_retry_on_http_429(self):
        """Test retry on HTTP 429 (rate limit)."""
        retry_service = RetryService()
        error = Exception("429 Rate Limit")
        error.response = {"status_code": 429}
        mock_func = Mock(side_effect=[error, "success"])
        
        result = retry_service.execute_with_retry(mock_func, max_retries=2, backoff_delays=[0.01, 0.01])
        
        assert result == "success"
        assert mock_func.call_count == 2

    def test_retry_on_http_5xx(self):
        """Test retry on HTTP 5xx (server error)."""
        retry_service = RetryService()
        error = Exception("503 Service Unavailable")
        error.response = {"status_code": 503}
        mock_func = Mock(side_effect=[error, "success"])
        
        result = retry_service.execute_with_retry(mock_func, max_retries=2, backoff_delays=[0.01, 0.01])
        
        assert result == "success"
        assert mock_func.call_count == 2

    def test_no_retry_on_http_400(self):
        """Test no retry on HTTP 400 (client error)."""
        retry_service = RetryService()
        error = Exception("400 Bad Request")
        error.response = {"status_code": 400}
        mock_func = Mock(side_effect=error)
        
        try:
            retry_service.execute_with_retry(mock_func)
            assert False, "Should have raised exception"
        except Exception:
            assert mock_func.call_count == 1

    def test_retry_on_connection_error(self):
        """Test retry on connection error."""
        retry_service = RetryService()
        mock_func = Mock(side_effect=[ConnectionError("connection failed"), "success"])
        
        result = retry_service.execute_with_retry(mock_func, max_retries=2, backoff_delays=[0.01, 0.01])
        
        assert result == "success"
        assert mock_func.call_count == 2
