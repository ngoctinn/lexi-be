#!/bin/bash

# Check DynamoDB table status and data
# Kiểm tra DynamoDB table có tồn tại và hoạt động bình thường

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}DynamoDB Table Checker - Lexi-BE${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    exit 1
fi

# Get stack name
STACK_NAME="${1:-lexi-be}"
TABLE_NAME="${2:-}"

echo -e "${YELLOW}Stack Name: $STACK_NAME${NC}"
echo ""

# Get table name from stack if not provided
if [ -z "$TABLE_NAME" ]; then
    echo -e "${YELLOW}Fetching DynamoDB table name from stack...${NC}"
    TABLE_NAME=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --query 'Stacks[0].Outputs[?OutputKey==`LexiAppTableName`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    if [ -z "$TABLE_NAME" ] || [ "$TABLE_NAME" = "None" ]; then
        # Try to get from nested stack
        TABLE_NAME=$(aws cloudformation describe-stack-resources \
            --stack-name "$STACK_NAME" \
            --query 'StackResources[?ResourceType==`AWS::DynamoDB::Table`].PhysicalResourceId' \
            --output text 2>/dev/null | head -1)
    fi
fi

if [ -z "$TABLE_NAME" ] || [ "$TABLE_NAME" = "None" ]; then
    echo -e "${RED}Error: Could not find DynamoDB table name${NC}"
    exit 1
fi

echo -e "${GREEN}Table Name: $TABLE_NAME${NC}"
echo ""

# Check table status
echo -e "${YELLOW}Checking table status...${NC}"

TABLE_INFO=$(aws dynamodb describe-table \
    --table-name "$TABLE_NAME" \
    --query 'Table.[TableStatus,ItemCount,TableSizeBytes,BillingModeSummary.BillingMode]' \
    --output text 2>/dev/null)

if [ -z "$TABLE_INFO" ]; then
    echo -e "${RED}Error: Could not describe table${NC}"
    exit 1
fi

read -r STATUS ITEM_COUNT SIZE BILLING_MODE <<< "$TABLE_INFO"

echo -e "${BLUE}Table Information:${NC}"
echo -e "  Status: ${GREEN}$STATUS${NC}"
echo -e "  Item Count: $ITEM_COUNT"
echo -e "  Size: $(numfmt --to=iec-i --suffix=B $SIZE 2>/dev/null || echo "$SIZE bytes")"
echo -e "  Billing Mode: $BILLING_MODE"

echo ""

# Check table schema
echo -e "${YELLOW}Table Schema:${NC}"

aws dynamodb describe-table \
    --table-name "$TABLE_NAME" \
    --query 'Table.[KeySchema,AttributeDefinitions]' \
    --output json | python3 -m json.tool

echo ""

# Check for global secondary indexes
echo -e "${YELLOW}Global Secondary Indexes:${NC}"

GSI_COUNT=$(aws dynamodb describe-table \
    --table-name "$TABLE_NAME" \
    --query 'Table.GlobalSecondaryIndexes | length(@)' \
    --output text 2>/dev/null || echo "0")

if [ "$GSI_COUNT" -gt 0 ]; then
    echo -e "${GREEN}Found $GSI_COUNT GSI(s)${NC}"
    aws dynamodb describe-table \
        --table-name "$TABLE_NAME" \
        --query 'Table.GlobalSecondaryIndexes[*].[IndexName,IndexStatus,ItemCount]' \
        --output table
else
    echo -e "${YELLOW}No GSIs found${NC}"
fi

echo ""

# Check for local secondary indexes
echo -e "${YELLOW}Local Secondary Indexes:${NC}"

LSI_COUNT=$(aws dynamodb describe-table \
    --table-name "$TABLE_NAME" \
    --query 'Table.LocalSecondaryIndexes | length(@)' \
    --output text 2>/dev/null || echo "0")

if [ "$LSI_COUNT" -gt 0 ]; then
    echo -e "${GREEN}Found $LSI_COUNT LSI(s)${NC}"
    aws dynamodb describe-table \
        --table-name "$TABLE_NAME" \
        --query 'Table.LocalSecondaryIndexes[*].[IndexName,ItemCount]' \
        --output table
else
    echo -e "${YELLOW}No LSIs found${NC}"
fi

echo ""

# Check table capacity
echo -e "${YELLOW}Capacity Information:${NC}"

if [ "$BILLING_MODE" = "PROVISIONED" ]; then
    CAPACITY=$(aws dynamodb describe-table \
        --table-name "$TABLE_NAME" \
        --query 'Table.BillingModeSummary' \
        --output json)
    echo "$CAPACITY" | python3 -m json.tool
else
    echo -e "${GREEN}On-Demand Billing Mode${NC}"
fi

echo ""

# Sample data
echo -e "${YELLOW}Sample Data (first 5 items):${NC}"

SAMPLE=$(aws dynamodb scan \
    --table-name "$TABLE_NAME" \
    --limit 5 \
    --output json 2>/dev/null)

ITEM_COUNT=$(echo "$SAMPLE" | python3 -c "import sys, json; print(len(json.load(sys.stdin)['Items']))")

if [ "$ITEM_COUNT" -gt 0 ]; then
    echo -e "${GREEN}Found $ITEM_COUNT items${NC}"
    echo "$SAMPLE" | python3 -m json.tool | head -50
else
    echo -e "${YELLOW}No items in table${NC}"
fi

echo ""

# Check CloudWatch metrics
echo -e "${YELLOW}CloudWatch Metrics (last hour):${NC}"

METRICS=$(aws cloudwatch get-metric-statistics \
    --namespace AWS/DynamoDB \
    --metric-name ConsumedWriteCapacityUnits \
    --dimensions Name=TableName,Value="$TABLE_NAME" \
    --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 300 \
    --statistics Sum \
    --output json 2>/dev/null)

DATAPOINTS=$(echo "$METRICS" | python3 -c "import sys, json; print(len(json.load(sys.stdin)['Datapoints']))")

if [ "$DATAPOINTS" -gt 0 ]; then
    echo -e "${GREEN}Write operations in last hour: $DATAPOINTS data points${NC}"
else
    echo -e "${YELLOW}No write operations in last hour${NC}"
fi

echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}DynamoDB Check Complete${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ "$STATUS" = "ACTIVE" ]; then
    echo -e "${GREEN}✓ Table is active and ready${NC}"
else
    echo -e "${RED}✗ Table status is: $STATUS${NC}"
fi

echo ""
