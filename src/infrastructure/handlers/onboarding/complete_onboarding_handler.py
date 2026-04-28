"""
Lambda handler for POST /onboarding/complete.
"""
import logging
from typing import Any

from application.use_cases.onboarding_use_cases import CompleteOnboardingUseCase
from infrastructure.repository_factory import RepositoryFactory
from infrastructure.logging.config import configure_logging
from infrastructure.handlers.base_handler import BaseHandler
from interfaces.controllers.onboarding_controller import OnboardingController

# Configure logging
configure_logging("lambda")
logger = logging.getLogger(__name__)


class CompleteOnboardingHandler(BaseHandler[OnboardingController]):
    """Handler for completing onboarding."""

    def build_dependencies(self) -> OnboardingController:
        """Build onboarding controller with dependencies."""
        user_repo = RepositoryFactory.create_user_repository()
        complete_onboarding_uc = CompleteOnboardingUseCase(user_repo)
        return OnboardingController(complete_onboarding_uc)

    def handle(self, user_id: str, event: dict, context: Any) -> dict:
        """Handle onboarding completion."""
        controller = self.get_dependencies()
        body_str = event.get("body")
        
        result = controller.complete(user_id, body_str)
        
        if result.is_success:
            return self.presenter.present_success(result.value)
        else:
            return self.presenter._format_response(400, {
                "error": result.error
            })


# Module-level handler instance (singleton)
_handler = CompleteOnboardingHandler()


def handler(event, context):
    """Lambda handler entry point."""
    return _handler(event, context)
