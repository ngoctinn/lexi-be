"""
Base handler for all Lambda endpoints.
Standardizes: auth extraction, error handling, logging, DI pattern.
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional, TypeVar, Generic

from interfaces.presenters.http_presenter import HttpPresenter
from shared.http_utils import dumps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class AuthenticationError(Exception):
    """Raised when user authentication fails."""
    pass


class AuthorizationError(Exception):
    """Raised when user lacks required permissions."""
    pass


class BaseHandler(ABC, Generic[T]):
    """
    Base class for all Lambda handlers.
    
    Enforces:
    - Consistent auth extraction
    - Consistent error handling
    - Consistent logging
    - Lazy dependency initialization (singleton pattern)
    
    Usage:
        class MyHandler(BaseHandler[MyController]):
            def build_dependencies(self) -> MyController:
                return MyController(...)
            
            def handle(self, user_id: str, event: dict, context: Any) -> dict:
                # Your business logic here
                return self.presenter.present_success(result)
    """

    def __init__(self):
        self.presenter = HttpPresenter()
        self._dependencies: Optional[T] = None

    @abstractmethod
    def build_dependencies(self) -> T:
        """Build and return dependencies. Called once per container."""
        pass

    def get_dependencies(self) -> T:
        """Lazy-load dependencies (singleton pattern)."""
        if self._dependencies is None:
            logger.info(f"Building dependencies for {self.__class__.__name__}")
            self._dependencies = self.build_dependencies()
        return self._dependencies

    @staticmethod
    def extract_user_id(event: dict) -> str:
        """
        Extract user_id from Cognito claims.
        
        Raises:
            AuthenticationError: If user_id not found
        """
        try:
            user_id = event["requestContext"]["authorizer"]["claims"]["sub"]
            if not user_id:
                raise AuthenticationError("Empty user_id")
            return user_id
        except (KeyError, TypeError) as e:
            raise AuthenticationError(f"Missing Cognito claims: {str(e)}")

    @staticmethod
    def extract_path_param(event: dict, param_name: str) -> str:
        """
        Extract path parameter.
        
        Raises:
            ValueError: If parameter not found
        """
        try:
            value = event["pathParameters"][param_name]
            if not value:
                raise ValueError(f"Empty {param_name}")
            return value
        except (KeyError, TypeError) as e:
            raise ValueError(f"Missing path parameter '{param_name}': {str(e)}")

    @staticmethod
    def extract_query_param(event: dict, param_name: str, default: Optional[str] = None) -> Optional[str]:
        """Extract query parameter with optional default."""
        try:
            params = event.get("queryStringParameters") or {}
            return params.get(param_name, default)
        except (KeyError, TypeError):
            return default

    @abstractmethod
    def handle(self, user_id: str, event: dict, context: Any) -> dict:
        """
        Handle the request. Implement your business logic here.
        
        Args:
            user_id: Authenticated user ID
            event: Lambda event
            context: Lambda context
            
        Returns:
            HTTP response dict
        """
        pass

    def __call__(self, event: dict, context: Any) -> dict:
        """
        Main Lambda handler entry point.
        Handles auth, error handling, logging.
        """
        try:
            user_id = self.extract_user_id(event)
            logger.info(
                f"{self.__class__.__name__} invoked",
                extra={"context": {"user_id": user_id}}
            )
        except AuthenticationError as e:
            logger.warning(f"Authentication failed: {str(e)}")
            return self.presenter.present_unauthorized(str(e))

        try:
            return self.handle(user_id, event, context)
        except AuthorizationError as e:
            logger.warning(
                f"Authorization failed: {str(e)}",
                extra={"context": {"user_id": user_id}}
            )
            return self._format_response(403, {"error": str(e), "code": "FORBIDDEN"})
        except ValueError as e:
            logger.warning(
                f"Validation error: {str(e)}",
                extra={"context": {"user_id": user_id}}
            )
            return self.presenter.present_bad_request(str(e))
        except Exception as e:
            logger.exception(
                f"Unhandled error in {self.__class__.__name__}",
                extra={"context": {"user_id": user_id, "error": str(e)}}
            )
            return self._format_response(500, {
                "error": "Internal server error",
                "code": "INTERNAL_ERROR",
                "message": str(e)
            })

    def _format_response(self, status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
        """Format HTTP response."""
        return self.presenter._format_response(status_code, body)
