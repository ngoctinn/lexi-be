#!/usr/bin/env python3
"""Invoke GetProfileFunction directly."""

import boto3
import json

client = boto3.client('lambda', region_name='ap-southeast-1')

# Create a mock event with Cognito claims
event = {
    "requestContext": {
        "authorizer": {
            "claims": {
                "sub": "299a95fc-3021-7050-5812-42fffa4971ec"
            }
        }
    }
}

response = client.invoke(
    FunctionName='lexi-be-GetProfileFunction-p1QgFvKl6dSX',
    InvocationType='RequestResponse',
    Payload=json.dumps(event)
)

print("Status Code:", response['StatusCode'])
print("Response:")
print(json.dumps(json.loads(response['Payload'].read()), indent=2))

if 'FunctionError' in response:
    print("\nFunction Error:", response['FunctionError'])
