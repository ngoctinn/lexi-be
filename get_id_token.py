#!/usr/bin/env python3
import boto3
import json

USER_POOL_ID = "ap-southeast-1_VhFl3NxNy"
CLIENT_ID = "4krhiauplon0iei1f5r4cgpq7i"
USERNAME = "ngoctin.work@gmail.com"
PASSWORD = "Ngoctin1703@"
REGION = "ap-southeast-1"

client = boto3.client('cognito-idp', region_name=REGION)

response = client.admin_initiate_auth(
    UserPoolId=USER_POOL_ID,
    ClientId=CLIENT_ID,
    AuthFlow='ADMIN_USER_PASSWORD_AUTH',
    AuthParameters={
        'USERNAME': USERNAME,
        'PASSWORD': PASSWORD,
    }
)

id_token = response['AuthenticationResult']['IdToken']
print(f"ID Token:\n{id_token}\n")

with open('id_token.txt', 'w') as f:
    f.write(id_token)
print("✅ ID Token saved to id_token.txt")
