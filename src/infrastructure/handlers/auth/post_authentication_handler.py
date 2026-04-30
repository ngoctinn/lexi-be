import logging

from application.use_cases.user_profile_use_cases import CreateUserProfileUseCase
from application.dtos.auth_dtos import CreateUserProfileCommand
from infrastructure.repository_factory import RepositoryFactory
from infrastructure.logging.config import configure_logging

# Configure logging
configure_logging("lambda")
logger = logging.getLogger(__name__)

# Initialize dependencies using factory
user_repo = RepositoryFactory.create_user_repository()
create_profile_use_case = CreateUserProfileUseCase(user_repo)


def handler(event, context):
    """
    Post Authentication Lambda Trigger - Ensure user profile exists.
    
    This trigger runs AFTER successful authentication (including Google OAuth).
    PostConfirmation also runs for the first federated sign-in, but PostAuthentication
    is a reliable safety net if profile creation failed or was skipped.
    
    Refs:
    - https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-post-authentication.html
    """
    try:
        trigger_source = event.get('triggerSource')
        logger.info(f"PostAuthentication handler triggered with source: {trigger_source}")
        
        # PostAuthentication runs for successful authentications.
        if trigger_source != "PostAuthentication_Authentication":
            logger.info(f"Skipping non-authentication event: {trigger_source}")
            return event
        
        user_attributes = event.get('request', {}).get('userAttributes', {})
        user_id = event.get('userName')
        email = user_attributes.get('email')
        
        if not user_id or not email:
            logger.warning(f"Missing user_id or email: user_id={user_id}, email={email}")
            return event
        
        logger.info(f"Ensuring profile exists: {user_id}, email: {email}")
        
        # Create user profile
        try:
            command = CreateUserProfileCommand(
                user_id=user_id,
                email=email,
                display_name=user_attributes.get('name', ''),
                avatar_url=user_attributes.get('picture', '')
            )
            result = create_profile_use_case.execute(command)
            
            if result.is_success:
                logger.info(f"User profile created successfully: {user_id}")
            else:
                # Most common expected failure is "already exists" / conditional check.
                logger.info(f"Profile not created (likely already exists): {result.error}")
        except Exception as e:
            logger.exception(f"Exception creating user profile: {str(e)}")
        
        # MUST return event object - Cognito requirement
        return event
        
    except Exception as e:
        logger.exception(f"Error in post_authentication_handler: {str(e)}")
        # Even on error, return event to not block authentication
        return event
