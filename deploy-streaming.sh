#!/bin/bash

# Deployment script for streaming transcription feature
# This script deploys the CloudFormation stack with Cognito Identity Pool

set -e

echo "🚀 Deploying Streaming Transcription Feature"
echo "=============================================="

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo "❌ SAM CLI is not installed. Please install it first."
    exit 1
fi

# Get AWS region
REGION=${AWS_REGION:-ap-southeast-1}
echo "📍 Region: $REGION"

# Get S3 bucket for deployment artifacts
read -p "Enter S3 bucket name for deployment artifacts: " S3_BUCKET

if [ -z "$S3_BUCKET" ]; then
    echo "❌ S3 bucket name is required"
    exit 1
fi

echo ""
echo "📦 Building SAM application..."
sam build

echo ""
echo "📤 Packaging SAM application..."
sam package \
    --output-template-file packaged.yaml \
    --s3-bucket "$S3_BUCKET" \
    --region "$REGION"

echo ""
echo "🚀 Deploying CloudFormation stack..."
sam deploy \
    --template-file packaged.yaml \
    --stack-name lexi-be \
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
    --region "$REGION" \
    --no-fail-on-empty-changeset

echo ""
echo "✅ Deployment complete!"
echo ""

# Get stack outputs
echo "📋 Retrieving stack outputs..."
echo ""

# Get nested stack name for AuthModule
AUTH_STACK=$(aws cloudformation describe-stack-resources \
    --stack-name lexi-be \
    --region "$REGION" \
    --query "StackResources[?LogicalResourceId=='AuthModule'].PhysicalResourceId" \
    --output text)

if [ -z "$AUTH_STACK" ]; then
    echo "⚠️  Could not find AuthModule nested stack"
    echo "Please manually retrieve the Identity Pool ID from CloudFormation console"
    exit 0
fi

# Get Identity Pool ID
IDENTITY_POOL_ID=$(aws cloudformation describe-stacks \
    --stack-name "$AUTH_STACK" \
    --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='IdentityPoolId'].OutputValue" \
    --output text)

if [ -z "$IDENTITY_POOL_ID" ]; then
    echo "⚠️  Could not retrieve Identity Pool ID"
    echo "Please manually retrieve it from CloudFormation console"
    exit 0
fi

echo "🎉 Identity Pool ID: $IDENTITY_POOL_ID"
echo ""
echo "📝 Next steps:"
echo "1. Update lexi-fe/.env.local with:"
echo "   NEXT_PUBLIC_IDENTITY_POOL_ID=$IDENTITY_POOL_ID"
echo ""
echo "2. Install frontend dependencies:"
echo "   cd lexi-fe && npm install"
echo ""
echo "3. Test the streaming feature with NEXT_PUBLIC_USE_STREAMING=true"
echo ""
echo "For detailed implementation guide, see:"
echo "   lexi-fe/STREAMING_IMPLEMENTATION_GUIDE.md"
