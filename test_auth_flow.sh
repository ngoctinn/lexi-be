#!/bin/bash

# Test Auth Flow - Verify PostConfirmation Lambda fix

USER_POOL_ID="ap-southeast-1_6GzL5k9Fr"
CLIENT_ID="6r7npt973q3pbb48s1ied5lmb5"
REGION="ap-southeast-1"
TEST_EMAIL="test-$(date +%s)@example.com"
TEST_PASSWORD="TestPassword123!"

echo "=== Testing Auth Flow ==="
echo "Test Email: $TEST_EMAIL"
echo ""

# Step 1: Sign up
echo "1. Signing up user..."
SIGNUP_RESULT=$(aws cognito-idp sign-up \
  --client-id $CLIENT_ID \
  --username $TEST_EMAIL \
  --password $TEST_PASSWORD \
  --user-attributes Name=email,Value=$TEST_EMAIL \
  --region $REGION 2>&1)

if [ $? -eq 0 ]; then
  echo "✅ Sign-up successful"
  echo "$SIGNUP_RESULT" | jq -r '.UserConfirmed, .CodeDeliveryDetails'
else
  echo "❌ Sign-up failed"
  echo "$SIGNUP_RESULT"
  exit 1
fi

echo ""

# Step 2: Admin confirm (skip OTP for testing)
echo "2. Admin confirming user..."
aws cognito-idp admin-confirm-sign-up \
  --user-pool-id $USER_POOL_ID \
  --username $TEST_EMAIL \
  --region $REGION

if [ $? -eq 0 ]; then
  echo "✅ User confirmed"
else
  echo "❌ Confirmation failed"
  exit 1
fi

echo ""

# Step 3: Wait for PostConfirmation Lambda
echo "3. Waiting for PostConfirmation Lambda to execute..."
sleep 3

# Step 4: Check CloudWatch Logs
echo "4. Checking PostConfirmation Lambda logs..."
LOG_GROUP="/aws/lambda/lexi-be-AuthModule-14XXR3EE-PostConfirmationLambda-wxOTbJALGt7U"
aws logs tail $LOG_GROUP --since 1m --region $REGION | grep -E "(User profile created|Error|JSON serializable)" | tail -5

echo ""

# Step 5: Verify user in DynamoDB
echo "5. Verifying user profile in DynamoDB..."
aws dynamodb get-item \
  --table-name LexiApp \
  --key "{\"PK\":{\"S\":\"USER#$TEST_EMAIL\"},\"SK\":{\"S\":\"PROFILE\"}}" \
  --region $REGION \
  --query 'Item.{Email:email.S,UserID:user_id.S,Role:role.S,Active:is_active.BOOL}' \
  --output table

if [ $? -eq 0 ]; then
  echo "✅ User profile found in DynamoDB"
else
  echo "❌ User profile not found"
fi

echo ""
echo "=== Test Complete ==="
