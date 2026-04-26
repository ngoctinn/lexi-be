#!/usr/bin/env python3
"""
Get Cognito JWT token for testing
"""
import boto3
import json
from botocore.exceptions import ClientError

# From .env.test
USER_POOL_ID = "ap-southeast-1_VhFl3NxNy"
CLIENT_ID = "4krhiauplon0iei1f5r4cgpq7i"
USERNAME = "ngoctin.work@gmail.com"
PASSWORD = "Ngoctin1703@"
REGION = "ap-southeast-1"

client = boto3.client('cognito-idp', region_name=REGION)

try:
    # Try admin auth flow (server-side, doesn't require client secret)
    response = client.admin_initiate_auth(
        UserPoolId=USER_POOL_ID,
        ClientId=CLIENT_ID,
        AuthFlow='ADMIN_USER_PASSWORD_AUTH',
        AuthParameters={
            'USERNAME': USERNAME,
            'PASSWORD': PASSWORD,
        }
    )
    
    access_token = response['AuthenticationResult']['AccessToken']
    print("✅ Token obtained successfully!\n")
    print(f"Access Token:\n{access_token}\n")
    print(f"Token Type: Bearer")
    print(f"Expires In: {response['AuthenticationResult']['ExpiresIn']} seconds")
    
    # Save to file for easy copy-paste
    with open('token.txt', 'w') as f:
        f.write(access_token)
    print("\n✅ Token saved to token.txt")
    
except ClientError as e:
    print(f"❌ Error: {e.response['Error']['Code']}")
    print(f"Message: {e.response['Error']['Message']}")
