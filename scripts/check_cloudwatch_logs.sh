#!/bin/bash

# Check CloudWatch logs for Lambda functions
# Kiểm tra logs để phát hiện lỗi

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}CloudWatch Logs Checker - Lexi-BE${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    exit 1
fi

# Get stack name
STACK_NAME="${1:-lexi-be}"

echo -e "${YELLOW}Stack Name: $STACK_NAME${NC}"
echo ""

# Get Lambda function names from stack
echo -e "${YELLOW}Fetching Lambda functions from stack...${NC}"

FUNCTIONS=$(aws cloudformation describe-stack-resources \
    --stack-name "$STACK_NAME" \
    --query 'StackResources[?ResourceType==`AWS::Lambda::Function`].PhysicalResourceId' \
    --output text)

if [ -z "$FUNCTIONS" ]; then
    echo -e "${RED}No Lambda functions found in stack: $STACK_NAME${NC}"
    exit 1
fi

echo -e "${GREEN}Found Lambda functions:${NC}"
for func in $FUNCTIONS; do
    echo "  - $func"
done

echo ""
echo -e "${YELLOW}Fetching recent logs (last 100 lines)...${NC}"
echo ""

# Get logs for each function
for func in $FUNCTIONS; do
    LOG_GROUP="/aws/lambda/$func"
    
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Function: $func${NC}"
    echo -e "${BLUE}Log Group: $LOG_GROUP${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    # Check if log group exists
    if ! aws logs describe-log-groups --log-group-name-prefix "$LOG_GROUP" --query 'logGroups[0].logGroupName' --output text 2>/dev/null | grep -q "$LOG_GROUP"; then
        echo -e "${YELLOW}No logs found for this function yet${NC}"
        echo ""
        continue
    fi
    
    # Get latest log stream
    LATEST_STREAM=$(aws logs describe-log-streams \
        --log-group-name "$LOG_GROUP" \
        --order-by LastEventTime \
        --descending \
        --max-items 1 \
        --query 'logStreams[0].logStreamName' \
        --output text 2>/dev/null)
    
    if [ -z "$LATEST_STREAM" ] || [ "$LATEST_STREAM" = "None" ]; then
        echo -e "${YELLOW}No log streams found${NC}"
        echo ""
        continue
    fi
    
    echo -e "${YELLOW}Latest Log Stream: $LATEST_STREAM${NC}"
    echo ""
    
    # Get log events
    aws logs get-log-events \
        --log-group-name "$LOG_GROUP" \
        --log-stream-name "$LATEST_STREAM" \
        --limit 100 \
        --query 'events[*].[timestamp,message]' \
        --output text | while read -r timestamp message; do
        
        # Format timestamp
        date_str=$(date -d @$((timestamp/1000)) '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo "")
        
        # Color code based on message content
        if echo "$message" | grep -q "ERROR\|Exception\|Failed\|error"; then
            echo -e "${RED}[$date_str] $message${NC}"
        elif echo "$message" | grep -q "WARNING\|Warn\|warn"; then
            echo -e "${YELLOW}[$date_str] $message${NC}"
        elif echo "$message" | grep -q "SUCCESS\|success\|completed"; then
            echo -e "${GREEN}[$date_str] $message${NC}"
        else
            echo "[$date_str] $message"
        fi
    done
    
    echo ""
done

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Log Check Complete${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check for errors
echo -e "${YELLOW}Checking for errors in logs...${NC}"

ERROR_COUNT=0
for func in $FUNCTIONS; do
    LOG_GROUP="/aws/lambda/$func"
    
    # Count errors in last 1000 events
    errors=$(aws logs filter-log-events \
        --log-group-name "$LOG_GROUP" \
        --filter-pattern "ERROR" \
        --query 'events | length(@)' \
        --output text 2>/dev/null || echo "0")
    
    if [ "$errors" -gt 0 ]; then
        echo -e "${RED}  $func: $errors errors found${NC}"
        ((ERROR_COUNT += errors))
    else
        echo -e "${GREEN}  $func: No errors${NC}"
    fi
done

echo ""

if [ $ERROR_COUNT -eq 0 ]; then
    echo -e "${GREEN}✓ No errors found in logs${NC}"
else
    echo -e "${RED}✗ Found $ERROR_COUNT errors in logs${NC}"
    echo ""
    echo "To see more details:"
    echo "  aws logs tail /aws/lambda/<function-name> --follow"
fi

echo ""
