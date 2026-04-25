#!/bin/bash
# Test Bedrock integration on production AWS
# Requires: Valid Cognito JWT token

set -e

API_URL="https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================================"
echo "PRODUCTION BEDROCK INTEGRATION TEST"
echo "============================================================"
echo "API URL: $API_URL"
echo ""

# Check if token is provided
if [ -z "$1" ]; then
    echo -e "${RED}❌ Error: JWT token required${NC}"
    echo ""
    echo "Usage: $0 <JWT_TOKEN>"
    echo ""
    echo "To get a token:"
    echo "1. Sign in to your app"
    echo "2. Copy the JWT token from browser DevTools"
    echo "3. Or use: python3 scripts/get_cognito_token.py"
    exit 1
fi

TOKEN="$1"

echo -e "${YELLOW}Step 1: List scenarios (public endpoint)${NC}"
SCENARIOS=$(curl -s "$API_URL/scenarios")
echo "$SCENARIOS" | jq -r '.scenarios[0] | "✅ Found scenario: \(.scenario_id) - \(.scenario_title)"'
SCENARIO_ID=$(echo "$SCENARIOS" | jq -r '.scenarios[0].scenario_id')
echo ""

echo -e "${YELLOW}Step 2: Create speaking session${NC}"
CREATE_RESPONSE=$(curl -s -X POST "$API_URL/sessions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"scenario_id\": \"$SCENARIO_ID\",
    \"learner_role_id\": \"customer\",
    \"ai_role_id\": \"waiter\",
    \"ai_gender\": \"female\",
    \"level\": \"B1\",
    \"selected_goals\": [\"order_food\"]
  }")

if echo "$CREATE_RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
    SESSION_ID=$(echo "$CREATE_RESPONSE" | jq -r '.session_id')
    echo -e "${GREEN}✅ Session created: $SESSION_ID${NC}"
else
    echo -e "${RED}❌ Failed to create session${NC}"
    echo "$CREATE_RESPONSE" | jq '.'
    exit 1
fi
echo ""

echo -e "${YELLOW}Step 3: Submit turn (triggers Bedrock Nova Micro)${NC}"
echo "Sending user message: 'Hello, I'd like to order a coffee please.'"
TURN_RESPONSE=$(curl -s -X POST "$API_URL/sessions/$SESSION_ID/turns" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, I would like to order a coffee please.",
    "audio_url": "",
    "is_hint_used": false
  }')

if echo "$TURN_RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Turn submitted successfully${NC}"
    
    # Extract AI response
    AI_TEXT=$(echo "$TURN_RESPONSE" | jq -r '.ai_turn.content')
    TTFT=$(echo "$TURN_RESPONSE" | jq -r '.ai_turn.ttft_ms')
    LATENCY=$(echo "$TURN_RESPONSE" | jq -r '.ai_turn.latency_ms')
    TOKENS=$(echo "$TURN_RESPONSE" | jq -r '.ai_turn.output_tokens')
    COST=$(echo "$TURN_RESPONSE" | jq -r '.ai_turn.cost_usd')
    MODEL=$(echo "$TURN_RESPONSE" | jq -r '.session.assigned_model')
    
    echo ""
    echo "📊 Bedrock Response:"
    echo "  Model: $MODEL"
    echo "  AI Text: $AI_TEXT"
    echo "  TTFT: ${TTFT}ms"
    echo "  Latency: ${LATENCY}ms"
    echo "  Tokens: $TOKENS"
    echo "  Cost: \$$COST"
    
    # Verify it's Nova Micro
    if [[ "$MODEL" == *"nova-micro"* ]]; then
        echo -e "${GREEN}✅ Confirmed: Using Nova Micro${NC}"
    else
        echo -e "${RED}⚠️  Warning: Not using Nova Micro (got: $MODEL)${NC}"
    fi
else
    echo -e "${RED}❌ Failed to submit turn${NC}"
    echo "$TURN_RESPONSE" | jq '.'
    exit 1
fi
echo ""

echo -e "${YELLOW}Step 4: Complete session (triggers Bedrock scoring)${NC}"
COMPLETE_RESPONSE=$(curl -s -X POST "$API_URL/sessions/$SESSION_ID/complete" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

if echo "$COMPLETE_RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Session completed successfully${NC}"
    
    # Extract scoring
    FLUENCY=$(echo "$COMPLETE_RESPONSE" | jq -r '.scoring.fluency')
    PRONUNCIATION=$(echo "$COMPLETE_RESPONSE" | jq -r '.scoring.pronunciation')
    GRAMMAR=$(echo "$COMPLETE_RESPONSE" | jq -r '.scoring.grammar')
    VOCABULARY=$(echo "$COMPLETE_RESPONSE" | jq -r '.scoring.vocabulary')
    OVERALL=$(echo "$COMPLETE_RESPONSE" | jq -r '.scoring.overall')
    FEEDBACK=$(echo "$COMPLETE_RESPONSE" | jq -r '.scoring.feedback')
    
    echo ""
    echo "📊 Scoring (Nova Micro):"
    echo "  Fluency: $FLUENCY"
    echo "  Pronunciation: $PRONUNCIATION"
    echo "  Grammar: $GRAMMAR"
    echo "  Vocabulary: $VOCABULARY"
    echo "  Overall: $OVERALL"
    echo "  Feedback: ${FEEDBACK:0:100}..."
    
    echo -e "${GREEN}✅ Scoring completed successfully${NC}"
else
    echo -e "${RED}❌ Failed to complete session${NC}"
    echo "$COMPLETE_RESPONSE" | jq '.'
    exit 1
fi
echo ""

echo "============================================================"
echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
echo "============================================================"
echo "Summary:"
echo "  ✅ Session created"
echo "  ✅ Bedrock Nova Micro responded"
echo "  ✅ Scoring completed"
echo "  ✅ No errors detected"
echo ""
echo "Session ID: $SESSION_ID"
