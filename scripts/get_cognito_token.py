#!/usr/bin/env python3
"""
Get JWT token from Cognito for testing
"""

import boto3
import json
from datetime import datetime

REGION = "ap-southeast-1"
USER_POOL_ID = "ap-southeast-1_VhFl3NxNy"
CLIENT_ID = "4krhiauplon0iei1f5r4cgpq7i"

def get_test_user_credentials():
    """Get test user credentials from Cognito"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching test user from Cognito...")
    
    cognito = boto3.client('cognito-idp', region_name=REGION)
    
    try:
        # List users
        response = cognito.list_users(UserPoolId=USER_POOL_ID, Limit=5)
        
        if not response['Users']:
            print("❌ No users found in Cognito User Pool")
            return None
        
        # Show available users
        print(f"\n✅ Found {len(response['Users'])} users:")
        for i, user in enumerate(response['Users']):
            username = user['Username']
            status = user['UserStatus']
            print(f"  {i+1}. {username} (Status: {status})")
        
        # Use first user
        test_user = response['Users'][0]
        username = test_user['Username']
        
        print(f"\n✅ Using user: {username}")
        print(f"   User ID (sub): {test_user['Attributes'][0]['Value']}")
        
        return username
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        return None

def get_admin_token(username):
    """Get JWT token using admin auth flow"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Getting JWT token for {username}...")
    
    cognito = boto3.client('cognito-idp', region_name=REGION)
    
    try:
        # Use admin auth flow (requires admin permissions)
        response = cognito.admin_initiate_auth(
            UserPoolId=USER_POOL_ID,
            ClientId=CLIENT_ID,
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': 'TempPassword123!'  # Default temp password
            }
        )
        
        if 'AuthenticationResult' in response:
            token = response['AuthenticationResult']['IdToken']
            print(f"✅ Got JWT token!")
            print(f"\nToken (first 50 chars): {token[:50]}...")
            return token
        else:
            print(f"⚠️  No token in response: {response}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        return None

def main():
    print(f"\n{'='*60}")
    print(f"Cognito Token Generator")
    print(f"Region: {REGION}")
    print(f"User Pool: {USER_POOL_ID}")
    print(f"{'='*60}\n")
    
    # Get test user
    username = get_test_user_credentials()
    if not username:
        return 1
    
    # Get token
    token = get_admin_token(username)
    if not token:
        return 1
    
    print(f"\n{'='*60}")
    print(f"✅ Ready to test!")
    print(f"{'='*60}")
    print(f"\nUse this token in API calls:")
    print(f"  Authorization: Bearer {token}")
    
    return 0

if __name__ == "__main__":
    exit(main())
