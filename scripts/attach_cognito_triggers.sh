#!/bin/bash

# Script to attach Lambda triggers to Cognito User Pool
# This completes the setup after CloudFormation deployment

set -e

# Get stack outputs
echo "Getting CloudFormation stack outputs..."
AUTH_STACK_NAME="lexi-be-AuthModule-14XXR3EEHSPTM"

USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name "$AUTH_STACK_NAME" \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text \
  --region ap-southeast-1)

PRE_SIGNUP_ARN=$(aws cloudformation describe-stacks \
  --stack-name "$AUTH_STACK_NAME" \
  --query 'Stacks[0].Outputs[?OutputKey==`PreSignUpLambdaArn`].OutputValue' \
  --output text \
  --region ap-southeast-1)

POST_CONFIRMATION_ARN=$(aws cloudformation describe-stacks \
  --stack-name "$AUTH_STACK_NAME" \
  --query 'Stacks[0].Outputs[?OutputKey==`PostConfirmationLambdaArn`].OutputValue' \
  --output text \
  --region ap-southeast-1)

echo "User Pool ID: $USER_POOL_ID"
echo "PreSignUp Lambda ARN: $PRE_SIGNUP_ARN"
echo "PostConfirmation Lambda ARN: $POST_CONFIRMATION_ARN"

# Attach Lambda triggers to Cognito User Pool
echo "Attaching Lambda triggers to Cognito User Pool..."
aws cognito-idp update-user-pool \
  --user-pool-id "$USER_POOL_ID" \
  --lambda-config PreSignUp="$PRE_SIGNUP_ARN",PostConfirmation="$POST_CONFIRMATION_ARN" \
  --region ap-southeast-1

echo "✅ Lambda triggers attached successfully!"

# Verify the configuration
echo "Verifying configuration..."
aws cognito-idp describe-user-pool \
  --user-pool-id "$USER_POOL_ID" \
  --query 'UserPool.LambdaConfig' \
  --region ap-southeast-1

echo "✅ Setup complete!"