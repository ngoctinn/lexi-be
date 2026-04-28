#!/bin/bash

# Test all API endpoints
set -e

API_URL="https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod"
ID_TOKEN=$(cat id_token.txt)

echo "🔐 Using ID Token for user: ngoctin.work@gmail.com"
echo ""

# Helper function to test endpoint
test_endpoint() {
    local method=$1
    local path=$2
    local data=$3
    local description=$4
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📍 $description"
    echo "   $method $path"
    echo ""
    
    if [ -z "$data" ]; then
        curl -s -X $method "$API_URL$path" \
            -H "Authorization: $ID_TOKEN" \
            -H "Content-Type: application/json" | jq . 2>/dev/null || echo "❌ Failed to parse response"
    else
        curl -s -X $method "$API_URL$path" \
            -H "Authorization: $ID_TOKEN" \
            -H "Content-Type: application/json" \
            -d "$data" | jq . 2>/dev/null || echo "❌ Failed to parse response"
    fi
    echo ""
}

# Test Profile endpoints
echo "═══════════════════════════════════════════════════════════════"
echo "🔹 PROFILE ENDPOINTS"
echo "═══════════════════════════════════════════════════════════════"
echo ""

test_endpoint "GET" "/profile" "" "Get User Profile"

test_endpoint "PATCH" "/profile" '{"display_name":"Ngoc Tin Updated"}' "Update User Profile"

# Test Flashcard endpoints
echo "═══════════════════════════════════════════════════════════════"
echo "🔹 FLASHCARD ENDPOINTS"
echo "═══════════════════════════════════════════════════════════════"
echo ""

test_endpoint "GET" "/flashcards" "" "List All Flashcards"

test_endpoint "GET" "/flashcards/due" "" "List Due Flashcards"

test_endpoint "POST" "/flashcards" '{"word":"test-word","vocab_type":"noun","translation_vi":"từ kiểm tra"}' "Create Flashcard"

test_endpoint "GET" "/flashcards/statistics" "" "Get Flashcard Statistics"

# Test Vocabulary endpoints
echo "═══════════════════════════════════════════════════════════════"
echo "🔹 VOCABULARY ENDPOINTS"
echo "═══════════════════════════════════════════════════════════════"
echo ""

test_endpoint "POST" "/vocabulary/translate" '{"word":"hello"}' "Translate Vocabulary"

test_endpoint "POST" "/vocabulary/translate-sentence" '{"sentence":"Hello world"}' "Translate Sentence"

# Test Scenarios endpoint (public, no auth required)
echo "═══════════════════════════════════════════════════════════════"
echo "🔹 SCENARIOS ENDPOINT (Public)"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "📍 List All Scenarios (Public - No Auth)"
echo "   GET /scenarios"
echo ""
curl -s -X GET "$API_URL/scenarios" \
    -H "Content-Type: application/json" | jq . 2>/dev/null || echo "❌ Failed to parse response"
echo ""

# Test Sessions endpoints
echo "═══════════════════════════════════════════════════════════════"
echo "🔹 SPEAKING SESSION ENDPOINTS"
echo "═══════════════════════════════════════════════════════════════"
echo ""

test_endpoint "GET" "/sessions" "" "List Speaking Sessions"

test_endpoint "POST" "/sessions" '{"scenario_id":"restaurant-ordering"}' "Create Speaking Session"

echo "✅ API Testing Complete!"
