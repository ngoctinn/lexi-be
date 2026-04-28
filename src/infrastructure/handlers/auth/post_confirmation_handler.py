import logging

from application.use_cases.user_profile_use_cases import CreateUserProfileUseCase
from infrastructure.repository_factory import RepositoryFactory
from infrastructure.logging.config import configure_logging
from interfaces.controllers.auth_controller import AuthController

# Configure logging
configure_logging("lambda")
logger = logging.getLogger(__name__)

# Initialize dependencies using factory
user_repo = RepositoryFactory.create_user_repository()
create_profile_use_case = CreateUserProfileUseCase(user_repo)
auth_controller = AuthController(create_profile_use_case)

def handler(event, context):
    """
    Handler mỏng (Thin Handler) - Chỉ đóng vai trò adapter hạ tầng.
    Logic Interface Adapter chuẩn nằm ở AuthController.
    
    CRITICAL: Cognito Lambda triggers MUST return the event object.
    Returning any other object will cause "Object of type X is not JSON serializable" error.
    """
    try:
        if event.get('triggerSource') != "PostConfirmation_ConfirmSignUp":
            logger.info("Skipping non-PostConfirmation event")
            return event

        logger.info("Processing PostConfirmation event", extra={"context": {"user_id": event.get('userName')}})
        
        # Execute business logic via controller
        result = auth_controller.handle_post_confirmation(event)
        
        # Log result but ALWAYS return event object for Cognito
        if result.is_success:
            logger.info("User profile created successfully", extra={"context": {"user_id": event.get('userName')}})
        else:
            logger.error("Failed to create user profile", extra={"context": {"error": result.error}})
        
        # MUST return event object - Cognito requirement
        return event
        
    except Exception as e:
        logger.exception("Error in post_confirmation_handler", extra={"context": {"error": str(e)}})
        # Even on error, return event to not block user sign-up
        # User can still login, profile creation can be retried later
        return event
