"""Unit tests for RetryService (exponential backoff retry logic)."""

import time
from unittest.mock import Mock, patch
import pytest

from infrastructure.services.retry_service import RetryService


@pytest.fixture
def retry_service():
    """Create RetryService instance."""
    return RetryService()


class TestRetryServiceSuccess:
    """Test successful execution without retries."""
    
    def test_execute_success_first_try(self, retry_service):
        """Test successful execution on first try."""
        mock_func = Mock(return_value='success')
        
        result = retry_service.execute_with_retry(mock_func)
        
        assert result == 'success'
        assert mock_func.call_count == 1
    
    def test_execute_with_args_and_kwargs(self, retry_service):
        """Test execution with arguments and keyword arguments."""
        mock_func = Mock(return_value='result')
        
        result = retry_service.execute_with_retry(
            mock_func,
            'arg1',
            'arg2',
            kwarg1='value1',
            kwarg2='value2'
        )
        
        assert result == 'result'
        mock_func.assert_called_once_with('arg1', 'arg2', kwarg1='value1', kwarg2='value2')


class TestRetryServiceTransientErrors:
    """Test retry logic for transient errors."""
    
    def test_retry_on_http_429(self, retry_service):
        """Test retry on HTTP 429 (rate limit)."""
        mock_func = Mock(side_effect=[
            Exception('HTTP 429: Too Many Requests'),
            'success'
        ])
        
        result = retry_service.execute_with_retry(mock_func, max_retries=2)
        
        assert result == 'success'
        assert mock_func.call_count == 2
    
    def test_retry_on_http_5xx(self, retry_service):
        """Test retry on HTTP 5xx (server error)."""
        mock_func = Mock(side_effect=[
            Exception('HTTP 500: Internal Server Error'),
            Exception('HTTP 503: Service Unavailable'),
            'success'
        ])
        
        result = retry_service.execute_with_retry(mock_func, max_retries=2)
        
        assert result == 'success'
        assert mock_func.call_count == 3
    
    def test_no_retry_on_http_404(self, retry_service):
        """Test no retry on HTTP 404 (not found)."""
        mock_func = Mock(side_effect=Exception('HTTP 404: Not Found'))
        
        with pytest.raises(Exception):
            retry_service.execute_with_retry(mock_func, max_retries=2)
        
        # Should only try once (no retries)
        assert mock_func.call_count == 1
    
    def test_no_retry_on_http_4xx(self, retry_service):
        """Test no retry on HTTP 4xx (client error)."""
        mock_func = Mock(side_effect=Exception('HTTP 400: Bad Request'))
        
        with pytest.raises(Exception):
            retry_service.execute_with_retry(mock_func, max_retries=2)
        
        # Should only try once (no retries)
        assert mock_func.call_count == 1


class TestRetryServiceExponentialBackoff:
    """Test exponential backoff delays."""
    
    @patch('time.sleep')
    def test_backoff_delays_1s_2s(self, mock_sleep, retry_service):
        """Test exponential backoff with 1s, 2s delays."""
        mock_func = Mock(side_effect=[
            Exception('HTTP 429'),
            Exception('HTTP 429'),
            'success'
        ])
        
        result = retry_service.execute_with_retry(
            mock_func,
            max_retries=2,
            backoff_delays=[1, 2]
        )
        
        assert result == 'success'
        # Verify sleep was called with correct delays
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(1)
        mock_sleep.assert_any_call(2)
    
    @patch('time.sleep')
    def test_custom_backoff_delays(self, mock_sleep, retry_service):
        """Test custom backoff delays."""
        mock_func = Mock(side_effect=[
            Exception('HTTP 429'),
            Exception('HTTP 429'),
            'success'
        ])
        
        result = retry_service.execute_with_retry(
            mock_func,
            max_retries=2,
            backoff_delays=[0.5, 1.5]
        )
        
        assert result == 'success'
        mock_sleep.assert_any_call(0.5)
        mock_sleep.assert_any_call(1.5)


class TestRetryServiceMaxRetries:
    """Test max retries limit."""
    
    def test_max_retries_exceeded(self, retry_service):
        """Test that exception is raised after max retries exceeded."""
        mock_func = Mock(side_effect=Exception('HTTP 429'))
        
        with pytest.raises(Exception):
            retry_service.execute_with_retry(mock_func, max_retries=2)
        
        # Should try 1 initial + 2 retries = 3 times
        assert mock_func.call_count == 3
    
    def test_zero_retries(self, retry_service):
        """Test with zero retries (no retry)."""
        mock_func = Mock(side_effect=Exception('HTTP 429'))
        
        with pytest.raises(Exception):
            retry_service.execute_with_retry(mock_func, max_retries=0)
        
        # Should only try once
        assert mock_func.call_count == 1


class TestRetryServiceLogging:
    """Test logging functionality."""
    
    def test_logs_retry_attempts(self, retry_service, caplog):
        """Test that retry attempts are logged."""
        mock_func = Mock(side_effect=[
            Exception('HTTP 429'),
            'success'
        ])
        
        result = retry_service.execute_with_retry(mock_func, max_retries=2)
        
        assert result == 'success'
        # Check that retry was logged
        assert any('retry' in record.message.lower() for record in caplog.records)
    
    def test_logs_backoff_delay(self, retry_service, caplog):
        """Test that backoff delays are logged."""
        mock_func = Mock(side_effect=[
            Exception('HTTP 429'),
            'success'
        ])
        
        with patch('time.sleep'):
            result = retry_service.execute_with_retry(
                mock_func,
                max_retries=2,
                backoff_delays=[1]
            )
        
        assert result == 'success'
        # Check that backoff delay was logged
        assert any('backoff' in record.message.lower() or 'delay' in record.message.lower() 
                   for record in caplog.records)


class TestRetryServiceEdgeCases:
    """Test edge cases."""
    
    def test_timeout_error_is_retried(self, retry_service):
        """Test that timeout errors are retried."""
        mock_func = Mock(side_effect=[
            TimeoutError('Request timeout'),
            'success'
        ])
        
        result = retry_service.execute_with_retry(mock_func, max_retries=2)
        
        assert result == 'success'
        assert mock_func.call_count == 2
    
    def test_connection_error_is_retried(self, retry_service):
        """Test that connection errors are retried."""
        mock_func = Mock(side_effect=[
            ConnectionError('Connection refused'),
            'success'
        ])
        
        result = retry_service.execute_with_retry(mock_func, max_retries=2)
        
        assert result == 'success'
        assert mock_func.call_count == 2
