import json
import logging

from application.use_cases.onboarding_use_cases import CompleteOnboardingUseCase
from infrastructure.repository_factory import RepositoryFactory
from infrastructure.logging.config import configure_logging
from interfaces.controllers.onboarding_controller import OnboardingController
from interfaces.presenters.http_presenter import HttpPresenter
from shared.http_utils import dumps

# Configure logging
configure_logging("lambda")
logger = logging.getLogger(__name__)

# DI - khởi tạo một lần khi Lambda cold start
_user_repo = RepositoryFactory.create_user_repository()
_complete_onboarding_uc = CompleteOnboardingUseCase(_user_repo)
_controller = OnboardingController(_complete_onboarding_uc)


def handler(event, context):
    """Handler cho POST /onboarding/complete."""
    # 1. Lấy user_id từ JWT claims
    try:
        user_id = event["requestContext"]["authorizer"]["claims"]["sub"]
        logger.info("Processing onboarding", extra={"context": {"user_id": user_id}})
    except KeyError:
        logger.warning("Unauthorized onboarding attempt")
        return {
            "statusCode": 401,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": dumps({"error": "Unauthorized"}),
        }

    try:
        presenter = HttpPresenter()
        body_str = event.get("body")
        
        # Get OperationResult from controller
        result = _controller.complete(user_id, body_str)
        
        # Convert OperationResult to HTTP response
        if result.is_success:
            return presenter.present_success(result.success)
        else:
            error = result.error
            return presenter._format_response(400, {
                "error": error.message,
                "code": error.code or "ERROR"
            })
    except Exception as e:
        logger.exception("Error in onboarding handler", extra={"context": {"user_id": user_id, "error": str(e)}})
        raise
