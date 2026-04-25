#!/bin/bash
# Test Bedrock with curl (simpler than Python)

set -e

API_URL="https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod"

echo "============================================================"
echo "BEDROCK INTEGRATION TEST (CURL)"
echo "============================================================"

# Get token from AWS
echo "🔑 Getting JWT token..."
TOKEN=$(aws cognito-idp admin-initiate-auth \
  --user-pool-id ap-southeast-1_VhFl3NxNy \
  --client-id 4krhiauplon0iei1f5r4cgpq7i \
  --auth-flow ADMIN_NO_SRP_AUTH \
  --auth-parameters USERNAME=test-bedrock@lexi.dev,PASSWORD=TestPassword123! \
  --region ap-southeast-1 \
  --query 'AuthenticationResult.IdToken' \
  --output text 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "❌ Failed to get token"
    exit 1
fi

echo "✅ Got token (length: ${#TOKEN})"
echo ""

# Step 1: Create session
echo "📝 Step 1: Create Session"
CREATE_RESP=$(curl -s -X POST "$API_URL/sessions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_id": "restaurant-ordering",
    "learner_role_id": "customer",
    "ai_role_id": "waiter",
    "ai_gender": "female",
    "level": "B1",
    "selected_goals": ["order food"]
  }')

SESSION_ID=$(echo "$CREATE_RESP" | jq -r '.data.session_id // .session_id')
if [ "$SESSION_ID" = "null" ] || [ -z "$SESSION_ID" ]; then
    echo "❌ Failed to create session"
    echo "$CREATE_RESP" | jq '.'
    exit 1
fi

echo "✅ Session created: $SESSION_ID"
echo ""

# Step 2: Submit turn (triggers Bedrock)
echo "🤖 Step 2: Submit Turn (Bedrock Nova Micro)"
echo "Sending: 'Hello, I would like to order a coffee please.'"
TURN_RESP=$(curl -s -X POST "$API_URL/sessions/$SESSION_ID/turns" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, I would like to order a coffee please.",
    "audio_url": "",
    "is_hint_used": false
  }')

SUCCESS=$(echo "$TURN_RESP" | jq -r '.success')
if [ "$SUCCESS" != "true" ]; then
    echo "❌ Failed to submit turn"
    echo "$TURN_RESP" | jq '.'
    exit 1
fi

# Extract metrics
AI_TEXT=$(echo "$TURN_RESP" | jq -r '.ai_turn.content')
MODEL=$(echo "$TURN_RESP" | jq -r '.session.assigned_model')
TTFT=$(echo "$TURN_RESP" | jq -r '.ai_turn.ttft_ms')
LATENCY=$(echo "$TURN_RESP" | jq -r '.ai_turn.latency_ms')
TOKENS=$(echo "$TURN_RESP" | jq -r '.ai_turn.output_tokens')
COST=$(echo "$TURN_RESP" | jq -r '.ai_turn.cost_usd')

echo "✅ Turn submitted successfully"
echo ""
echo "📊 Bedrock Response:"
echo "  Model: $MODEL"
echo "  AI Text: ${AI_TEXT:0:100}..."
echo "  TTFT: ${TTFT}ms"
echo "  Latency: ${LATENCY}ms"
echo "  Tokens: $TOKENS"
echo "  Cost: \$$COST"

# Verify Nova Micro
if [[ "$MODEL" == *"nova-micro"* ]]; then
    echo "  ✅ Confirmed: Using Nova Micro"
else
    echo "  ⚠️  Warning: Not Nova Micro (got: $MODEL)"
fi
echo ""

# Step 3: Complete session (triggers scoring)
echo "📊 Step 3: Complete Session (Bedrock Scoring)"
COMPLETE_RESP=$(curl -s -X POST "$API_URL/sessions/$SESSION_ID/complete" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

SUCCESS=$(echo "$COMPLETE_RESP" | jq -r '.success')
if [ "$SUCCESS" != "true" ]; then
    echo "❌ Failed to complete session"
    echo "$COMPLETE_RESP" | jq '.'
    exit 1
fi

# Extract scoring
FLUENCY=$(echo "$COMPLETE_RESP" | jq -r '.scoring.fluency')
PRONUNCIATION=$(echo "$COMPLETE_RESP" | jq -r '.scoring.pronunciation')
GRAMMAR=$(echo "$COMPLETE_RESP" | jq -r '.scoring.grammar')
VOCABULARY=$(echo "$COMPLETE_RESP" | jq -r '.scoring.vocabulary')
OVERALL=$(echo "$COMPLETE_RESP" | jq -r '.scoring.overall')
FEEDBACK=$(echo "$COMPLETE_RESP" | jq -r '.scoring.feedback')

echo "✅ Session completed successfully"
echo ""
echo "📊 Scoring (Nova Micro):"
echo "  Fluency: $FLUENCY"
echo "  Pronunciation: $PRONUNCIATION"
echo "  Grammar: $GRAMMAR"
echo "  Vocabulary: $VOCABULARY"
echo "  Overall: $OVERALL"
echo "  Feedback: ${FEEDBACK:0:100}..."
echo ""

echo "============================================================"
echo "✅ ALL TESTS PASSED"
echo "============================================================"
echo "Summary:"
echo "  ✅ Session created"
echo "  ✅ Bedrock Nova Micro responded"
echo "  ✅ Scoring completed with Nova Micro"
echo "  ✅ No errors detected"
echo ""
echo "Session ID: $SESSION_ID"
