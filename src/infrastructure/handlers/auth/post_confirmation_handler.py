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

    This handler supports:
    - PostConfirmation_ConfirmSignUp: After sign-up confirmation (local users and first federated sign-in)
    - PostConfirmation_ConfirmForgotPassword: After password reset confirmation (ignored here)
    """
    try:
        trigger_source = event.get('triggerSource')
        user_id = event.get('userName', 'unknown')
        logger.info(f"PostConfirmation handler triggered", extra={"context": {"trigger_source": trigger_source, "user_id": user_id}})

        # Handle PostConfirmation for successful sign-up confirmation.
        # AWS docs: for federated users, the post confirmation triggerSource is also PostConfirmation_ConfirmSignUp.
        if trigger_source == "PostConfirmation_ConfirmSignUp":
            logger.info("Processing PostConfirmation event", extra={"context": {"user_id": user_id, "trigger_source": trigger_source}})

            # Validate required fields
            user_attrs = event.get('request', {}).get('userAttributes', {})
            email = user_attrs.get('email', '')

            if not user_id:
                logger.error("Missing userName in Cognito event", extra={"context": {"event": event}})
                return event

            if not email:
                logger.error("Missing email in userAttributes", extra={"context": {"user_id": user_id, "userAttributes": user_attrs}})
                return event

            # Execute business logic via controller
            try:
                result = auth_controller.handle_post_confirmation(event)

                # Log result but ALWAYS return event object for Cognito
                if result.is_success:
                    logger.info("User profile created successfully", extra={"context": {"user_id": user_id, "email": email}})
                else:
                    logger.error("Failed to create user profile", extra={"context": {"user_id": user_id, "error": result.error}})
            except Exception as e:
                logger.exception("Exception in handle_post_confirmation", extra={"context": {"user_id": user_id, "error": str(e)}})

            return event

        # Skip other triggers
        logger.info(f"Skipping non-PostConfirmation/PostAuthentication event", extra={"context": {"trigger_source": trigger_source, "user_id": user_id}})
        return event

    except Exception as e:
        logger.exception("Error in post_confirmation_handler", extra={"context": {"error": str(e), "event": event}})
        # Even on error, return event to not block user sign-up
        # User can still login, profile creation can be retried later
        return event
