#!/bin/bash

# Test Bedrock API in Production
# This script tests the conversation endpoint to verify Bedrock is being called

API_URL="https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod"
REGION="ap-southeast-1"

echo "=========================================="
echo "Bedrock Production API Test"
echo "=========================================="
echo "API URL: $API_URL"
echo "Region: $REGION"
echo ""

# Step 1: Get test user ID from Cognito
echo "[1] Getting test user from Cognito..."
USER_ID=$(aws cognito-idp list-users \
  --user-pool-id ap-southeast-1_VhFl3NxNy \
  --region $REGION \
  --query 'Users[0].Attributes[?Name==`sub`].Value' \
  --output text)

if [ -z "$USER_ID" ]; then
  echo "❌ Failed to get user ID"
  exit 1
fi

echo "✅ User ID: $USER_ID"
echo ""

# Step 2: Create a session
echo "[2] Creating session..."
SESSION_RESPONSE=$(curl -s -X POST "$API_URL/sessions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $USER_ID" \
  -d '{
    "scenario_id": "scenario-1",
    "level": "A1",
    "selected_goal": "greeting"
  }')

SESSION_ID=$(echo $SESSION_RESPONSE | jq -r '.session_id // .data.session_id // empty')

if [ -z "$SESSION_ID" ]; then
  echo "❌ Failed to create session"
  echo "Response: $SESSION_RESPONSE"
  exit 1
fi

echo "✅ Session ID: $SESSION_ID"
echo ""

# Step 3: Submit a turn (conversation)
echo "[3] Submitting conversation turn..."
echo "   Message: 'Hello, how are you?'"
echo ""

TURN_RESPONSE=$(curl -s -X POST "$API_URL/sessions/$SESSION_ID/turns" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $USER_ID" \
  -d '{
    "user_message": "Hello, how are you?",
    "audio_url": null
  }')

echo "Response:"
echo $TURN_RESPONSE | jq '.' 2>/dev/null || echo $TURN_RESPONSE

echo ""
echo "=========================================="

# Check if response is from Bedrock or fallback
AI_RESPONSE=$(echo $TURN_RESPONSE | jq -r '.ai_response // .data.ai_response // empty')

if [ -z "$AI_RESPONSE" ]; then
  echo "❌ No AI response in result"
  exit 1
fi

if [[ "$AI_RESPONSE" == *"Thanks. Could you say a bit more about that?"* ]]; then
  echo "❌ Got FALLBACK response (Bedrock not called)"
  echo "Response: $AI_RESPONSE"
  exit 1
else
  echo "✅ Got REAL Bedrock response!"
  echo "Response: ${AI_RESPONSE:0:150}..."
  exit 0
fi
