#!/bin/bash

# Check entire infrastructure after deployment
# Kiểm tra toàn bộ infrastructure sau khi deploy

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Infrastructure Checker - Lexi-BE${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Get stack name
STACK_NAME="${1:-lexi-be}"

echo -e "${YELLOW}Stack Name: $STACK_NAME${NC}"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    exit 1
fi

# Check stack status
echo -e "${YELLOW}[1] Checking CloudFormation Stack Status...${NC}"

STACK_STATUS=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].StackStatus' \
    --output text 2>/dev/null)

if [ -z "$STACK_STATUS" ]; then
    echo -e "${RED}✗ Stack not found: $STACK_NAME${NC}"
    exit 1
fi

if [[ "$STACK_STATUS" == *"COMPLETE"* ]]; then
    echo -e "${GREEN}✓ Stack Status: $STACK_STATUS${NC}"
elif [[ "$STACK_STATUS" == *"IN_PROGRESS"* ]]; then
    echo -e "${YELLOW}⚠ Stack Status: $STACK_STATUS (still updating)${NC}"
else
    echo -e "${RED}✗ Stack Status: $STACK_STATUS${NC}"
fi

echo ""

# Get stack outputs
echo -e "${YELLOW}[2] Stack Outputs...${NC}"

OUTPUTS=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs' \
    --output json)

echo "$OUTPUTS" | python3 -m json.tool

echo ""

# Check Lambda functions
echo -e "${YELLOW}[3] Checking Lambda Functions...${NC}"

FUNCTIONS=$(aws cloudformation describe-stack-resources \
    --stack-name "$STACK_NAME" \
    --query 'StackResources[?ResourceType==`AWS::Lambda::Function`].PhysicalResourceId' \
    --output text)

FUNC_COUNT=$(echo "$FUNCTIONS" | wc -w)
echo -e "${GREEN}Found $FUNC_COUNT Lambda functions${NC}"

for func in $FUNCTIONS; do
    # Get function config
    CONFIG=$(aws lambda get-function-configuration \
        --function-name "$func" \
        --query '[Runtime,MemorySize,Timeout,State]' \
        --output text 2>/dev/null)
    
    read -r RUNTIME MEMORY TIMEOUT STATE <<< "$CONFIG"
    
    if [ "$STATE" = "Active" ]; then
        echo -e "  ${GREEN}✓${NC} $func (Runtime: $RUNTIME, Memory: ${MEMORY}MB, Timeout: ${TIMEOUT}s)"
    else
        echo -e "  ${RED}✗${NC} $func (State: $STATE)"
    fi
done

echo ""

# Check API Gateway
echo -e "${YELLOW}[4] Checking API Gateway...${NC}"

API_ID=$(aws cloudformation describe-stack-resources \
    --stack-name "$STACK_NAME" \
    --query 'StackResources[?ResourceType==`AWS::Serverless::Api`].PhysicalResourceId' \
    --output text | head -1)

if [ -n "$API_ID" ]; then
    API_STATUS=$(aws apigateway get-rest-api \
        --rest-api-id "$API_ID" \
        --query 'name' \
        --output text 2>/dev/null)
    
    if [ -n "$API_STATUS" ]; then
        echo -e "${GREEN}✓ API Gateway: $API_STATUS${NC}"
        
        # Get API stages
        STAGES=$(aws apigateway get-stages \
            --rest-api-id "$API_ID" \
            --query 'item[*].stageName' \
            --output text)
        
        echo -e "  Stages: $STAGES"
    else
        echo -e "${RED}✗ Could not get API Gateway info${NC}"
    fi
else
    echo -e "${YELLOW}⚠ No API Gateway found${NC}"
fi

echo ""

# Check DynamoDB
echo -e "${YELLOW}[5] Checking DynamoDB Tables...${NC}"

TABLES=$(aws cloudformation describe-stack-resources \
    --stack-name "$STACK_NAME" \
    --query 'StackResources[?ResourceType==`AWS::DynamoDB::Table`].PhysicalResourceId' \
    --output text)

TABLE_COUNT=$(echo "$TABLES" | wc -w)
echo -e "${GREEN}Found $TABLE_COUNT DynamoDB table(s)${NC}"

for table in $TABLES; do
    STATUS=$(aws dynamodb describe-table \
        --table-name "$table" \
        --query 'Table.TableStatus' \
        --output text 2>/dev/null)
    
    if [ "$STATUS" = "ACTIVE" ]; then
        echo -e "  ${GREEN}✓${NC} $table (Status: $STATUS)"
    else
        echo -e "  ${RED}✗${NC} $table (Status: $STATUS)"
    fi
done

echo ""

# Check S3 buckets
echo -e "${YELLOW}[6] Checking S3 Buckets...${NC}"

BUCKETS=$(aws cloudformation describe-stack-resources \
    --stack-name "$STACK_NAME" \
    --query 'StackResources[?ResourceType==`AWS::S3::Bucket`].PhysicalResourceId' \
    --output text)

BUCKET_COUNT=$(echo "$BUCKETS" | wc -w)

if [ $BUCKET_COUNT -gt 0 ]; then
    echo -e "${GREEN}Found $BUCKET_COUNT S3 bucket(s)${NC}"
    
    for bucket in $BUCKETS; do
        # Check if bucket exists
        if aws s3 ls "s3://$bucket" > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓${NC} $bucket"
        else
            echo -e "  ${RED}✗${NC} $bucket (not accessible)"
        fi
    done
else
    echo -e "${YELLOW}⚠ No S3 buckets found${NC}"
fi

echo ""

# Check IAM roles
echo -e "${YELLOW}[7] Checking IAM Roles...${NC}"

ROLES=$(aws cloudformation describe-stack-resources \
    --stack-name "$STACK_NAME" \
    --query 'StackResources[?ResourceType==`AWS::IAM::Role`].PhysicalResourceId' \
    --output text)

ROLE_COUNT=$(echo "$ROLES" | wc -w)
echo -e "${GREEN}Found $ROLE_COUNT IAM role(s)${NC}"

echo ""

# Check CloudWatch Alarms
echo -e "${YELLOW}[8] Checking CloudWatch Alarms...${NC}"

ALARMS=$(aws cloudwatch describe-alarms \
    --query "MetricAlarms[?contains(AlarmName, '$STACK_NAME')].AlarmName" \
    --output text)

ALARM_COUNT=$(echo "$ALARMS" | wc -w)

if [ $ALARM_COUNT -gt 0 ]; then
    echo -e "${GREEN}Found $ALARM_COUNT alarm(s)${NC}"
    for alarm in $ALARMS; do
        echo "  - $alarm"
    done
else
    echo -e "${YELLOW}⚠ No alarms found${NC}"
fi

echo ""

# Check recent stack events
echo -e "${YELLOW}[9] Recent Stack Events...${NC}"

EVENTS=$(aws cloudformation describe-stack-events \
    --stack-name "$STACK_NAME" \
    --query 'StackEvents[0:5].[Timestamp,ResourceStatus,ResourceType,LogicalResourceId]' \
    --output table)

echo "$EVENTS"

echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Infrastructure Check Complete${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ "$STACK_STATUS" = "CREATE_COMPLETE" ] || [ "$STACK_STATUS" = "UPDATE_COMPLETE" ]; then
    echo -e "${GREEN}✓ Infrastructure is healthy${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Check CloudWatch logs: ./scripts/check_cloudwatch_logs.sh $STACK_NAME"
    echo "  2. Check DynamoDB: ./scripts/check_dynamodb.sh $STACK_NAME"
    echo "  3. Test API: python3 scripts/test_api.py <API_URL> <AUTH_TOKEN>"
else
    echo -e "${RED}✗ Infrastructure may have issues${NC}"
    echo ""
    echo "Check stack events above for details"
fi

echo ""
