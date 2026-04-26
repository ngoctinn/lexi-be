"""
APIClient - HTTP wrapper for API testing

Provides a simple, testable HTTP client with:
- Authentication header support
- Response validation
- Retry logic for transient errors
- Comprehensive logging
- Connection pooling via requests.Session
"""

import logging
import time
from typing import Optional, Dict, Any
from requests import Session, Response, RequestException, Timeout, ConnectionError
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry as UrllibRetry

logger = logging.getLogger(__name__)


class APIClient:
    """HTTP client for API testing with auth, validation, and retry logic."""

    def __init__(self, base_url: str, token: str = None, timeout: int = 10):
        """
        Initialize API client.

        Args:
            base_url: Base URL for all requests (e.g., https://api.example.com)
            token: Optional JWT token for authentication
            timeout: Request timeout in seconds (default: 10)
        """
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.session = self._create_session()
        logger.info(f"APIClient initialized: base_url={self.base_url}, token={'***' if token else 'None'}")

    def _create_session(self) -> Session:
        """
        Create a requests.Session with connection pooling and retry logic.

        Returns:
            Configured Session object
        """
        session = Session()

        # Configure retry strategy for transient errors
        retry_strategy = UrllibRetry(
            total=3,  # Total retries
            backoff_factor=0.5,  # Exponential backoff: 0.5s, 1s, 2s
            status_forcelist=[429, 500, 502, 503, 504],  # Retry on these status codes
            allowed_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _get_headers(self) -> Dict[str, str]:
        """
        Build request headers with auth if token provided.

        Returns:
            Dictionary of headers
        """
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _log_request(self, method: str, url: str, **kwargs):
        """Log outgoing request."""
        logger.debug(f"{method} {url}")
        if "json" in kwargs:
            logger.debug(f"  Payload: {kwargs['json']}")

    def _log_response(self, response: Response):
        """Log incoming response."""
        logger.debug(f"  Status: {response.status_code}")
        try:
            logger.debug(f"  Response: {response.json()}")
        except Exception:
            logger.debug(f"  Response: {response.text[:200]}")

    def get(self, endpoint: str, **kwargs) -> Response:
        """
        GET request with auth header.

        Args:
            endpoint: API endpoint (e.g., /profile)
            **kwargs: Additional arguments passed to requests.get (params, headers, etc.)

        Returns:
            Response object

        Raises:
            ConnectionError: Network connection failed
            Timeout: Request timed out
            RequestException: Other request errors
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        headers.update(kwargs.pop("headers", {}))

        self._log_request("GET", url, **kwargs)

        try:
            response = self.session.get(url, headers=headers, timeout=self.timeout, **kwargs)
            self._log_response(response)
            return response
        except (ConnectionError, Timeout) as e:
            logger.error(f"GET {url} failed: {e}")
            raise

    def post(self, endpoint: str, data: dict = None, **kwargs) -> Response:
        """
        POST request with auth header.

        Args:
            endpoint: API endpoint (e.g., /flashcards)
            data: Request body as dictionary
            **kwargs: Additional arguments passed to requests.post

        Returns:
            Response object

        Raises:
            ConnectionError: Network connection failed
            Timeout: Request timed out
            RequestException: Other request errors
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        headers.update(kwargs.pop("headers", {}))

        self._log_request("POST", url, json=data, **kwargs)

        try:
            response = self.session.post(url, json=data, headers=headers, timeout=self.timeout, **kwargs)
            self._log_response(response)
            return response
        except (ConnectionError, Timeout) as e:
            logger.error(f"POST {url} failed: {e}")
            raise

    def patch(self, endpoint: str, data: dict = None, **kwargs) -> Response:
        """
        PATCH request with auth header.

        Args:
            endpoint: API endpoint (e.g., /profile)
            data: Request body as dictionary
            **kwargs: Additional arguments passed to requests.patch

        Returns:
            Response object

        Raises:
            ConnectionError: Network connection failed
            Timeout: Request timed out
            RequestException: Other request errors
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        headers.update(kwargs.pop("headers", {}))

        self._log_request("PATCH", url, json=data, **kwargs)

        try:
            response = self.session.patch(url, json=data, headers=headers, timeout=self.timeout, **kwargs)
            self._log_response(response)
            return response
        except (ConnectionError, Timeout) as e:
            logger.error(f"PATCH {url} failed: {e}")
            raise

    def validate_response(self, response: Response, expected_status: int = 200) -> Dict[str, Any]:
        """
        Validate response status and JSON structure.

        Args:
            response: Response object to validate
            expected_status: Expected HTTP status code (default: 200)

        Returns:
            Parsed JSON response

        Raises:
            AssertionError: Status code doesn't match expected
            ValueError: Response is not valid JSON
            KeyError: Response missing required fields
        """
        # Check status code
        if response.status_code != expected_status:
            logger.error(
                f"Status code mismatch: expected {expected_status}, got {response.status_code}"
            )
            raise AssertionError(
                f"Expected status {expected_status}, got {response.status_code}: {response.text}"
            )

        # Parse JSON
        try:
            data = response.json()
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise ValueError(f"Response is not valid JSON: {response.text}") from e

        # Validate response structure
        if "success" not in data:
            raise KeyError("Response missing 'success' field")

        if data["success"]:
            # Success response should have: success, message, data
            if "message" not in data:
                raise KeyError("Success response missing 'message' field")
            if "data" not in data:
                raise KeyError("Success response missing 'data' field")
        else:
            # Error response should have: success, message, error
            if "message" not in data:
                raise KeyError("Error response missing 'message' field")
            if "error" not in data:
                raise KeyError("Error response missing 'error' field")

        logger.debug(f"Response validation passed: {data}")
        return data
