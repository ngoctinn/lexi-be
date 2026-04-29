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
    - PostConfirmation_ConfirmSignUp: After email/password sign-up confirmation
    - PostConfirmation_ExternalProvider: After federated sign-up (not triggered for Google)
    - PostAuthentication_Authentication: After successful login (used for Google OAuth users)
    """
    try:
        trigger_source = event.get('triggerSource')
        logger.info(f"PostConfirmation handler triggered with source: {trigger_source}")
        
        # Handle PostConfirmation triggers (email/password sign-up)
        if trigger_source in ["PostConfirmation_ConfirmSignUp", "PostConfirmation_ExternalProvider"]:
            logger.info("Processing PostConfirmation event", extra={"context": {"user_id": event.get('userName')}})
            
            # Execute business logic via controller
            result = auth_controller.handle_post_confirmation(event)
            
            # Log result but ALWAYS return event object for Cognito
            if result.is_success:
                logger.info("User profile created successfully", extra={"context": {"user_id": event.get('userName')}})
            else:
                logger.error("Failed to create user profile", extra={"context": {"error": result.error}})
            
            return event
        
        # Handle PostAuthentication trigger (for Google OAuth users)
        # This is needed because PostConfirmation doesn't run for external providers
        if trigger_source == "PostAuthentication_Authentication":
            user_attributes = event.get('request', {}).get('userAttributes', {})
            identities = user_attributes.get('identities')
            
            # Only create profile for federated users (Google, Facebook, etc.)
            if identities:
                logger.info(f"Creating profile for federated user via PostAuthentication: {event.get('userName')}")
                result = auth_controller.handle_post_confirmation(event)
                
                if result.is_success:
                    logger.info("User profile created successfully via PostAuthentication")
                else:
                    # Profile might already exist, that's OK
                    logger.info(f"Profile creation result: {result.error}")
            else:
                logger.info(f"Not a federated user, skipping profile creation: {event.get('userName')}")
            
            return event
        
        # Skip other triggers
        logger.info(f"Skipping non-PostConfirmation/PostAuthentication event: {trigger_source}")
        return event
        
    except Exception as e:
        logger.exception("Error in post_confirmation_handler", extra={"context": {"error": str(e)}})
        # Even on error, return event to not block user sign-up
        # User can still login, profile creation can be retried later
        return event
