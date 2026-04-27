#!/bin/bash

# Script test GET /profile endpoint
# Sử dụng ID token từ get_id_token.py

set -e

echo "🔐 Step 1: Getting ID Token..."
python3 get_id_token.py

if [ ! -f "id_token.txt" ]; then
    echo "❌ Failed to get ID token"
    exit 1
fi

ID_TOKEN=$(cat id_token.txt)
echo "✅ ID Token obtained"

# API Gateway endpoint - thay đổi theo môi trường của bạn
API_ENDPOINT="https://your-api-gateway-url/dev"  # Thay đổi URL này

echo ""
echo "🌐 Step 2: Testing GET /profile endpoint..."
echo "URL: $API_ENDPOINT/profile"
echo ""

curl -X GET "$API_ENDPOINT/profile" \
  -H "Authorization: $ID_TOKEN" \
  -H "Content-Type: application/json" \
  -v

echo ""
echo "✅ Test completed"
