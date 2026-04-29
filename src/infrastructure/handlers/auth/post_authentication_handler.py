import logging

from application.use_cases.user_profile_use_cases import CreateUserProfileUseCase
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
    Post Authentication Lambda Trigger - Create user profile for federated users.
    
    This trigger runs AFTER successful authentication, including Google OAuth.
    It ensures that federated users (Google, Facebook, etc.) have a profile
    in DynamoDB since PostConfirmation trigger doesn't run for them.
    
    Refs:
    - https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-post-authentication.html
    """
    try:
        trigger_source = event.get('triggerSource')
        logger.info(f"PostAuthentication handler triggered with source: {trigger_source}")
        
        # Only process for external provider logins (Google, Facebook, etc.)
        # PostAuthentication runs for ALL logins, we only want to create profile
        # for federated users who don't have one yet
        if trigger_source != "PostAuthentication_Authentication":
            logger.info(f"Skipping non-authentication event: {trigger_source}")
            return event
        
        user_attributes = event.get('request', {}).get('userAttributes', {})
        user_id = event.get('userName')
        email = user_attributes.get('email')
        
        if not user_id or not email:
            logger.warning(f"Missing user_id or email: user_id={user_id}, email={email}")
            return event
        
        # Check if this is a federated user (has identities attribute)
        identities = user_attributes.get('identities')
        if not identities:
            logger.info(f"Not a federated user, skipping profile creation: {user_id}")
            return event
        
        logger.info(f"Creating profile for federated user: {user_id}, email: {email}")
        
        # Create user profile
        try:
            profile = create_profile_use_case.execute(
                user_id=user_id,
                email=email,
                name=user_attributes.get('name'),
                picture=user_attributes.get('picture')
            )
            logger.info(f"User profile created successfully: {profile.user_id}")
        except Exception as e:
            # Profile might already exist, that's OK
            if "already exists" in str(e).lower():
                logger.info(f"User profile already exists: {user_id}")
            else:
                logger.error(f"Failed to create user profile: {e}")
                # Don't fail authentication, just log the error
        
        # MUST return event object - Cognito requirement
        return event
        
    except Exception as e:
        logger.exception(f"Error in post_authentication_handler: {str(e)}")
        # Even on error, return event to not block authentication
        return event
