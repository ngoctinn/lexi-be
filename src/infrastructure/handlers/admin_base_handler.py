"""
Base handler for admin endpoints.
Extends BaseHandler with admin authorization check.
"""
import logging
from typing import Any, Optional

from infrastructure.handlers.base_handler import BaseHandler, AuthorizationError
from infrastructure.persistence.dynamo_user_repo import DynamoDBUserRepo

logger = logging.getLogger(__name__)


class AdminBaseHandler(BaseHandler):
    """
    Base class for admin-only endpoints.
    
    Enforces:
    - User authentication (inherited from BaseHandler)
    - Admin role authorization
    - Consistent error handling
    
    Usage:
        class MyAdminHandler(AdminBaseHandler[MyController]):
            def build_dependencies(self) -> MyController:
                return MyController(...)
            
            def handle(self, user_id: str, event: dict, context: Any) -> dict:
                # Your admin logic here
                return self.presenter.present_success(result)
    """

    def __init__(self):
        super().__init__()
        self._user_repo: Optional[DynamoDBUserRepo] = None

    def get_user_repo(self) -> DynamoDBUserRepo:
        """Lazy-load user repository."""
        if self._user_repo is None:
            self._user_repo = DynamoDBUserRepo()
        return self._user_repo

    def check_admin_role(self, user_id: str) -> None:
        """
        Verify user has ADMIN role.
        
        Raises:
            AuthorizationError: If user is not admin
        """
        user_repo = self.get_user_repo()
        profile = user_repo.get_by_user_id(user_id)
        
        if not profile:
            raise AuthorizationError("User profile not found")
        
        role_value = profile.role.value if hasattr(profile.role, "value") else profile.role
        if role_value != "ADMIN":
            logger.warning(
                f"Non-admin user attempted admin operation",
                extra={"context": {"user_id": user_id, "role": role_value}}
            )
            raise AuthorizationError("Admin role required")

    def __call__(self, event: dict, context: Any) -> dict:
        """
        Main Lambda handler entry point.
        Adds admin authorization check.
        """
        try:
            user_id = self.extract_user_id(event)
            logger.info(
                f"{self.__class__.__name__} invoked",
                extra={"context": {"user_id": user_id}}
            )
        except Exception as e:
            logger.warning(f"Authentication failed: {str(e)}")
            return self.presenter.present_unauthorized(str(e))

        try:
            # Check admin role
            self.check_admin_role(user_id)
            
            # Call handle
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
            raise
