#!/bin/bash

# Full Test Suite for Lexi-BE
# Chạy toàn bộ các test trước khi deploy

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Full Test Suite - Lexi-BE${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Parse arguments
API_URL=""
AUTH_TOKEN=""
SKIP_LOCAL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --api-url)
            API_URL="$2"
            shift 2
            ;;
        --auth-token)
            AUTH_TOKEN="$2"
            shift 2
            ;;
        --skip-local)
            SKIP_LOCAL=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Step 1: Pre-deployment checks
echo -e "${YELLOW}[Step 1/4] Running pre-deployment checks...${NC}"
if bash "$SCRIPT_DIR/pre_deploy_check.sh"; then
    echo -e "${GREEN}✓ Pre-deployment checks passed${NC}"
else
    echo -e "${RED}✗ Pre-deployment checks failed${NC}"
    exit 1
fi

echo ""

# Step 2: Local API tests (optional)
if [ "$SKIP_LOCAL" = false ]; then
    echo -e "${YELLOW}[Step 2/4] Running local API tests...${NC}"
    echo "Note: Make sure SAM local is running (sam local start-api)"
    echo ""
    
    if python3 "$SCRIPT_DIR/test_api_local.py" --url http://localhost:3000; then
        echo -e "${GREEN}✓ Local API tests passed${NC}"
    else
        echo -e "${YELLOW}⚠ Local API tests failed (this is OK if SAM local is not running)${NC}"
    fi
else
    echo -e "${YELLOW}[Step 2/4] Skipping local API tests${NC}"
fi

echo ""

# Step 3: Build SAM
echo -e "${YELLOW}[Step 3/4] Building SAM application...${NC}"
cd "$PROJECT_ROOT"

if command -v sam &> /dev/null; then
    if sam build; then
        echo -e "${GREEN}✓ SAM build successful${NC}"
    else
        echo -e "${RED}✗ SAM build failed${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠ SAM CLI not installed, skipping build${NC}"
fi

echo ""

# Step 4: AWS API tests (if credentials provided)
if [ -n "$API_URL" ] && [ -n "$AUTH_TOKEN" ]; then
    echo -e "${YELLOW}[Step 4/4] Running AWS API tests...${NC}"
    
    if python3 "$SCRIPT_DIR/test_api.py" "$API_URL" "$AUTH_TOKEN"; then
        echo -e "${GREEN}✓ AWS API tests passed${NC}"
    else
        echo -e "${RED}✗ AWS API tests failed${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}[Step 4/4] Skipping AWS API tests (no credentials provided)${NC}"
    echo "To run AWS tests, use:"
    echo "  $0 --api-url <URL> --auth-token <TOKEN>"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ All tests completed successfully!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Review the test results above"
echo "  2. If all tests passed, deploy with: sam deploy"
echo "  3. After deployment, run AWS API tests to verify"
echo ""
