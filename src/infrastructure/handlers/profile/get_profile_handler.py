import logging

from application.use_cases.user_profile_use_cases import GetProfileUseCase, UpdateProfileUseCase
from infrastructure.repository_factory import RepositoryFactory
from infrastructure.logging.config import configure_logging
from interfaces.controllers.profile_controller import ProfileController
from interfaces.presenters.http_presenter import HttpPresenter

# Configure logging
configure_logging("lambda")
logger = logging.getLogger(__name__)

# Module-level singleton (AWS best practice)
# Initialized once per Lambda container, reused across invocations
_profile_controller = None


def build_profile_controller() -> ProfileController:
    """Build profile controller with dependencies."""
    user_repo = RepositoryFactory.create_user_repository()
    get_profile_uc = GetProfileUseCase(user_repo)
    update_profile_uc = UpdateProfileUseCase(user_repo)
    return ProfileController(get_profile_uc, update_profile_uc)


def _get_or_build_profile_controller() -> ProfileController:
    """
    Lazy initialization of profile controller (singleton pattern).
    
    AWS best practice: Initialize SDK clients and dependencies outside handler
    to take advantage of execution environment reuse.
    
    Returns:
        ProfileController: Reusable controller instance
    """
    global _profile_controller
    if _profile_controller is None:
        logger.info("Building profile controller (first invocation in this container)")
        _profile_controller = build_profile_controller()
    return _profile_controller


def _unauthorized_response():
    return {
        "statusCode": 401,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": '{"error": "Unauthorized"}',
    }


def handler(event, context):
    """Lambda handler for GET /profile."""
    try:
        user_id = event["requestContext"]["authorizer"]["claims"]["sub"]
        logger.info("Getting profile", extra={"context": {"user_id": user_id}})
    except KeyError as e:
        logger.warning("Unauthorized access attempt", extra={"context": {"error": str(e)}})
        return _unauthorized_response()

    try:
        controller = _get_or_build_profile_controller()
        presenter = HttpPresenter()
        
        # Get OperationResult from controller
        result = controller.get_profile(user_id)
        
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
        logger.exception("Error getting profile", extra={"context": {"user_id": user_id, "error": str(e)}})
        raise
