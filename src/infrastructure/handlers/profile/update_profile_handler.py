"""
Lambda handler for PATCH /profile.
"""
import logging
from typing import Any

from application.use_cases.user_profile_use_cases import GetProfileUseCase, UpdateProfileUseCase
from infrastructure.repository_factory import RepositoryFactory
from infrastructure.logging.config import configure_logging
from infrastructure.handlers.base_handler import BaseHandler
from interfaces.controllers.profile_controller import ProfileController

# Configure logging
configure_logging("lambda")
logger = logging.getLogger(__name__)


class UpdateProfileHandler(BaseHandler[ProfileController]):
    """Handler for updating user profile."""

    def build_dependencies(self) -> ProfileController:
        """Build profile controller with dependencies."""
        user_repo = RepositoryFactory.create_user_repository()
        get_profile_uc = GetProfileUseCase(user_repo)
        update_profile_uc = UpdateProfileUseCase(user_repo)
        return ProfileController(get_profile_uc, update_profile_uc)

    def handle(self, user_id: str, event: dict, context: Any) -> dict:
        """Handle profile update."""
        controller = self.get_dependencies()
        body_str = event.get("body")
        result = controller.update_profile(user_id, body_str)
        
        if result.is_success:
            return self.presenter.present_success(result.value)
        else:
            return self.presenter.present_bad_request(result.error)


# Module-level handler instance (singleton)
_handler = UpdateProfileHandler()


def handler(event, context):
    """Lambda handler entry point."""
    return _handler(event, context)
