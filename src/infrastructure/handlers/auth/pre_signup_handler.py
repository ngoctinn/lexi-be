import logging
import os
import boto3
from botocore.exceptions import ClientError

from infrastructure.logging.config import configure_logging

# Configure logging
configure_logging("lambda")
logger = logging.getLogger(__name__)

# Initialize Cognito client
cognito_client = boto3.client('cognito-idp')
USER_POOL_ID = os.environ.get('COGNITO_USER_POOL_ID')


def handler(event, context):
    """
    Pre Sign-up Lambda Trigger - Link federated users to existing local users.
    
    AWS Best Practice: Automatically link Google/Facebook users to existing 
    email/password accounts to prevent duplicate users.
    
    For federated sign-ins (Google/Facebook), you can auto-confirm and
    auto-verify email/phone in `event.response`.
    
    Refs:
    - https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-identity-federation-consolidate-users.html
    - https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-pre-sign-up.html
    """
    try:
        trigger_source = event.get('triggerSource')
        logger.info(f"Pre sign-up trigger invoked: {trigger_source}")
        
        # Only process federated sign-ups (Google, Facebook, etc.)
        if trigger_source != 'PreSignUp_ExternalProvider':
            logger.info(f"Skipping non-federated sign-up: {trigger_source}")
            # For regular email/password sign-ups, return event unchanged
            # Cognito will send OTP verification email automatically
            return event
        
        # Extract user info
        user_attributes = event['request'].get('userAttributes', {})
        email = user_attributes.get('email')
        provider_name = event['userName'].split('_')[0]  # e.g., "Google_123456" -> "Google"
        provider_user_id = event['userName'].split('_', 1)[1]  # e.g., "Google_123456" -> "123456"
        
        if not email:
            logger.warning("No email found in federated user attributes")
            return event

        # AWS docs: PreSignUp trigger can set response flags.
        # For external providers, we can safely auto-confirm and auto-verify
        # to avoid any OTP requirement in the federated flow.
        event.setdefault('response', {})
        event['response']['autoConfirmUser'] = True
        event['response']['autoVerifyEmail'] = True
        if 'phone_number' in user_attributes:
            event['response']['autoVerifyPhone'] = True
        
        logger.info(f"Checking for existing user with email: {email}")
        
        # Search for existing user with this email
        existing_user = _find_user_by_email(email)
        
        if existing_user:
            logger.info(f"Found existing user: {existing_user['Username']}")
            
            # Link federated identity to existing user
            _link_provider_for_user(
                existing_username=existing_user['Username'],
                provider_name=provider_name,
                provider_user_id=provider_user_id
            )
            
            logger.info(f"Successfully linked {provider_name} identity to user {existing_user['Username']}")
        else:
            logger.info(f"No existing user found for {email}, will create new user")
        
        # MUST return event object unchanged
        return event
        
    except Exception as e:
        logger.exception(f"Error in pre_signup_handler: {str(e)}")
        # Don't block sign-up on errors - fail open for better UX
        # AWS will create new user if we return event normally
        return event


def _find_user_by_email(email: str) -> dict | None:
    """
    Search for existing user by email in Cognito User Pool.
    
    Returns:
        User dict if found, None otherwise
    """
    try:
        response = cognito_client.list_users(
            UserPoolId=USER_POOL_ID,
            Filter=f'email = "{email}"',
            Limit=1
        )
        
        users = response.get('Users', [])
        if users:
            return users[0]
        return None
        
    except ClientError as e:
        logger.error(f"Error searching for user: {e}")
        return None


def _link_provider_for_user(
    existing_username: str,
    provider_name: str,
    provider_user_id: str
) -> None:
    """
    Link federated identity to existing Cognito user.
    
    Uses AdminLinkProviderForUser API to consolidate user identities.
    """
    try:
        cognito_client.admin_link_provider_for_user(
            UserPoolId=USER_POOL_ID,
            DestinationUser={
                'ProviderName': 'Cognito',
                'ProviderAttributeValue': existing_username
            },
            SourceUser={
                'ProviderName': provider_name,
                'ProviderAttributeName': 'Cognito_Subject',
                'ProviderAttributeValue': provider_user_id
            }
        )
        logger.info(f"AdminLinkProviderForUser succeeded")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AliasExistsException':
            logger.warning(f"User already linked: {e}")
        else:
            logger.error(f"Error linking provider: {e}")
            raise
