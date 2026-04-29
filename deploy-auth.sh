#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Lexi Auth Stack Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Configuration
STACK_NAME="lexi-auth"
REGION="ap-southeast-1"
ENVIRONMENT="prod"
DATABASE_TABLE="LexiApp"
DEPLOY_GOOGLE="false"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --environment)
      ENVIRONMENT="$2"
      shift 2
      ;;
    --table)
      DATABASE_TABLE="$2"
      shift 2
      ;;
    --with-google)
      DEPLOY_GOOGLE="true"
      shift
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      exit 1
      ;;
  esac
done

echo -e "${YELLOW}Configuration:${NC}"
echo "  Stack Name: $STACK_NAME"
echo "  Region: $REGION"
echo "  Environment: $ENVIRONMENT"
echo "  Database Table: $DATABASE_TABLE"
echo "  Deploy Google Provider: $DEPLOY_GOOGLE"
echo ""

# Check if database table exists
echo -e "${YELLOW}Checking if DynamoDB table exists...${NC}"
if aws dynamodb describe-table --table-name "$DATABASE_TABLE" --region "$REGION" &>/dev/null; then
  echo -e "${GREEN}✓ Table $DATABASE_TABLE exists${NC}"
else
  echo -e "${RED}✗ Table $DATABASE_TABLE does not exist!${NC}"
  echo -e "${YELLOW}Please deploy the database stack first or create the table manually.${NC}"
  exit 1
fi

# Build
echo -e "${YELLOW}Building SAM application...${NC}"
sam build --template-file config/auth.yaml --region "$REGION"

if [ $? -ne 0 ]; then
  echo -e "${RED}✗ Build failed!${NC}"
  exit 1
fi
echo -e "${GREEN}✓ Build successful${NC}"
echo ""

# Deploy
echo -e "${YELLOW}Deploying auth stack...${NC}"
sam deploy \
  --template-file .aws-sam/build/template.yaml \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
  --parameter-overrides \
    Environment="$ENVIRONMENT" \
    DatabaseTableName="$DATABASE_TABLE" \
    DeployGoogleProvider="$DEPLOY_GOOGLE" \
  --no-confirm-changeset \
  --no-fail-on-empty-changeset

if [ $? -ne 0 ]; then
  echo -e "${RED}✗ Deployment failed!${NC}"
  exit 1
fi

echo -e "${GREEN}✓ Deployment successful${NC}"
echo ""

# Get outputs
echo -e "${YELLOW}Fetching stack outputs...${NC}"
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text)

CLIENT_ID=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' \
  --output text)

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Auth Configuration:${NC}"
echo "  User Pool ID: $USER_POOL_ID"
echo "  Client ID: $CLIENT_ID"
echo "  Region: $REGION"
echo ""

# Get post-deployment steps
echo -e "${YELLOW}Post-Deployment Steps:${NC}"
aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query 'Stacks[0].Outputs[?OutputKey==`PostDeploymentSteps`].OutputValue' \
  --output text

echo ""
echo -e "${GREEN}Done!${NC}"
