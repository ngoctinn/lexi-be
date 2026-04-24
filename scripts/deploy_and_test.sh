#!/bin/bash

# Complete deployment and testing workflow
# Quy trình deploy và test toàn bộ

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
echo -e "${BLUE}Complete Deploy & Test Workflow${NC}"
echo -e "${BLUE}Lexi-BE${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Parse arguments
STACK_NAME="lexi-be"
SKIP_TESTS=false
SKIP_LOCAL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --stack-name)
            STACK_NAME="$2"
            shift 2
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
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
echo -e "${YELLOW}[Step 1/6] Running pre-deployment checks...${NC}"
cd "$PROJECT_ROOT"

if bash "$SCRIPT_DIR/pre_deploy_check.sh"; then
    echo -e "${GREEN}✓ Pre-deployment checks passed${NC}"
else
    echo -e "${RED}✗ Pre-deployment checks failed${NC}"
    exit 1
fi

echo ""

# Step 2: Local tests (optional)
if [ "$SKIP_LOCAL" = false ] && [ "$SKIP_TESTS" = false ]; then
    echo -e "${YELLOW}[Step 2/6] Running local API tests...${NC}"
    echo "Note: Make sure SAM local is running (sam local start-api)"
    echo ""
    
    if python3 "$SCRIPT_DIR/test_api_local.py" --url http://localhost:3000 2>/dev/null; then
        echo -e "${GREEN}✓ Local API tests passed${NC}"
    else
        echo -e "${YELLOW}⚠ Local API tests skipped or failed${NC}"
    fi
else
    echo -e "${YELLOW}[Step 2/6] Skipping local API tests${NC}"
fi

echo ""

# Step 3: Build SAM
echo -e "${YELLOW}[Step 3/6] Building SAM application...${NC}"

if command -v sam &> /dev/null; then
    if sam build; then
        echo -e "${GREEN}✓ SAM build successful${NC}"
    else
        echo -e "${RED}✗ SAM build failed${NC}"
        exit 1
    fi
else
    echo -e "${RED}Error: SAM CLI not installed${NC}"
    echo "Install with: pip install aws-sam-cli"
    exit 1
fi

echo ""

# Step 4: Deploy
echo -e "${YELLOW}[Step 4/6] Deploying to AWS...${NC}"
echo "Stack Name: $STACK_NAME"
echo ""

if sam deploy --stack-name "$STACK_NAME"; then
    echo -e "${GREEN}✓ Deployment successful${NC}"
else
    echo -e "${RED}✗ Deployment failed${NC}"
    exit 1
fi

echo ""

# Step 5: Check infrastructure
echo -e "${YELLOW}[Step 5/6] Checking infrastructure...${NC}"

if bash "$SCRIPT_DIR/check_infrastructure.sh" "$STACK_NAME"; then
    echo -e "${GREEN}✓ Infrastructure check passed${NC}"
else
    echo -e "${YELLOW}⚠ Infrastructure check completed with warnings${NC}"
fi

echo ""

# Step 6: Check logs
echo -e "${YELLOW}[Step 6/6] Checking CloudWatch logs...${NC}"

if bash "$SCRIPT_DIR/check_cloudwatch_logs.sh" "$STACK_NAME"; then
    echo -e "${GREEN}✓ Log check completed${NC}"
else
    echo -e "${YELLOW}⚠ Log check completed with warnings${NC}"
fi

echo ""

# Get API URL
echo -e "${YELLOW}Retrieving API URL...${NC}"

API_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text 2>/dev/null)

if [ -n "$API_URL" ] && [ "$API_URL" != "None" ]; then
    echo -e "${GREEN}API URL: $API_URL${NC}"
else
    echo -e "${YELLOW}⚠ Could not retrieve API URL${NC}"
fi

echo ""

# Final summary
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ Deployment and checks completed!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo "Next steps:"
echo ""
echo "1. Get authentication token:"
echo "   - Sign in to your app"
echo "   - Open DevTools (F12)"
echo "   - Go to Application > Local Storage"
echo "   - Copy the auth token"
echo ""
echo "2. Test API endpoints:"
echo "   python3 scripts/test_api.py '$API_URL' '<AUTH_TOKEN>'"
echo ""
echo "3. Monitor logs:"
echo "   ./scripts/check_cloudwatch_logs.sh $STACK_NAME"
echo ""
echo "4. Check DynamoDB:"
echo "   ./scripts/check_dynamodb.sh $STACK_NAME"
echo ""
echo "5. View infrastructure:"
echo "   ./scripts/check_infrastructure.sh $STACK_NAME"
echo ""
