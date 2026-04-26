import logging
import time
from typing import Callable, Any, List

logger = logging.getLogger(__name__)


class RetryService:
    """Exponential backoff retry logic for transient failures."""

    def __init__(self):
        self._retry_on_status_codes = [429, 500, 502, 503, 504]
        self._no_retry_on_status_codes = [400, 401, 403, 404]

    def execute_with_retry(
        self,
        func: Callable,
        max_retries: int = 2,
        backoff_delays: List[int] = None
    ) -> Any:
        """
        Execute function with exponential backoff retry logic.
        
        Args:
            func: Callable to execute
            max_retries: Maximum number of retries (default: 2)
            backoff_delays: List of delays in seconds between retries (default: [1, 2])
        
        Returns:
            Result from func() if successful
        
        Raises:
            Exception: Original exception if all retries exhausted
        """
        if backoff_delays is None:
            backoff_delays = [1, 2]

        for attempt in range(max_retries + 1):
            try:
                logger.debug(f"Attempt {attempt + 1}/{max_retries + 1}")
                return func()
            except Exception as e:
                # Check if this is a transient error worth retrying
                if not self._is_transient_error(e):
                    logger.debug(f"Permanent error, not retrying: {e}")
                    raise

                # If we've exhausted retries, raise the error
                if attempt >= max_retries:
                    logger.error(f"Max retries ({max_retries}) exhausted, raising error")
                    raise

                # Calculate backoff delay
                delay = backoff_delays[attempt] if attempt < len(backoff_delays) else backoff_delays[-1]
                logger.warning(f"Transient error on attempt {attempt + 1}, retrying after {delay}s: {e}")
                time.sleep(delay)

    def _is_transient_error(self, error: Exception) -> bool:
        """
        Determine if error is transient (worth retrying).
        
        Args:
            error: Exception to check
        
        Returns:
            True if transient, False if permanent
        """
        # Check for HTTP status code in error
        if hasattr(error, "response"):
            status_code = error.response.get("status_code") if isinstance(error.response, dict) else None
            if status_code:
                if status_code in self._retry_on_status_codes:
                    return True
                if status_code in self._no_retry_on_status_codes:
                    return False

        # Check for timeout errors (transient)
        if isinstance(error, TimeoutError):
            return True
        if "timeout" in str(error).lower():
            return True

        # Check for connection errors (transient)
        if "connection" in str(error).lower():
            return True

        # Default: treat as transient to be safe
        return True
