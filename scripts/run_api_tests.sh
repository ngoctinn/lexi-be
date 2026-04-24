#!/bin/bash

# Script để chạy API tests
# Usage: ./scripts/run_api_tests.sh <api_url> <auth_token>

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check arguments
if [ $# -lt 2 ]; then
    echo -e "${RED}Usage: $0 <api_url> <auth_token>${NC}"
    echo ""
    echo "Example:"
    echo "  $0 https://xxx.execute-api.us-east-1.amazonaws.com/Prod 'eyJhbGc...'"
    echo ""
    echo "To get auth token:"
    echo "  1. Sign in to your app"
    echo "  2. Open browser DevTools (F12)"
    echo "  3. Go to Application > Local Storage"
    echo "  4. Find the token in localStorage"
    exit 1
fi

API_URL="$1"
AUTH_TOKEN="$2"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Lexi-BE API Test Suite${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}API URL:${NC} $API_URL"
echo -e "${YELLOW}Auth Token:${NC} ${AUTH_TOKEN:0:20}..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

# Check if requests library is installed
if ! python3 -c "import requests" 2>/dev/null; then
    echo -e "${YELLOW}Installing requests library...${NC}"
    pip3 install requests
fi

# Run the test script
echo -e "${BLUE}Starting tests...${NC}"
echo ""

python3 "$(dirname "$0")/test_api.py" "$API_URL" "$AUTH_TOKEN"

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
else
    echo -e "${RED}Some tests failed. Please check the output above.${NC}"
fi

exit $exit_code
