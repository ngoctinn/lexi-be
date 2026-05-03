#!/bin/bash
# AWS Account Check Script for Lexi-BE Project
# This script checks various aspects of your AWS account configuration

set -e

echo "================================================"
echo "AWS Account Configuration Check"
echo "================================================"
echo "Date: $(date)"
echo "Account ID: $(aws sts get-caller-identity --query Account --output text)"
echo "User ARN: $(aws sts get-caller-identity --query Arn --output text)"
echo "Region: $(aws configure get region)"
echo "================================================"

echo ""
echo "1. Checking IAM User/Role..."
aws iam get-user --output table || aws sts get-caller-identity --output table

echo ""
echo "2. Checking S3 Buckets..."
aws s3api list-buckets --query "Buckets[].Name" --output table

echo ""
echo "3. Checking Lambda Functions..."
aws lambda list-functions --query "Functions[].FunctionName" --output table

echo ""
echo "4. Checking DynamoDB Tables..."
aws dynamodb list-tables --output table

echo ""
echo "5. Checking API Gateway APIs..."
aws apigateway get-rest-apis --query "items[].name" --output table

echo ""
echo "6. Checking CloudFormation Stacks..."
aws cloudformation list-stacks --query "StackSummaries[?StackStatus!='DELETE_COMPLETE'].StackName" --output table

echo ""
echo "7. Checking Cost Explorer Status..."
aws ce get-cost-and-usage --time-period Start=2026-04-01,End=2026-04-30 --granularity MONTHLY --metrics UnblendedCost --output table 2>/dev/null || echo "Cost Explorer not enabled or no permissions"

echo ""
echo "8. Checking Free Tier Usage..."
echo "Note: Free tier usage can be checked in AWS Billing Dashboard"
echo "Free tiers typically include:"
echo "  - 1M Lambda requests/month (12 months)"
echo "  - 25GB DynamoDB storage"
echo "  - 5GB S3 storage"
echo "  - 1M API Gateway REST requests/month"
echo "  - 750K WebSocket connection minutes"

echo ""
echo "================================================"
echo "RECOMMENDATIONS:"
echo "================================================"
echo "1. Enable AWS Cost Explorer for detailed cost analysis"
echo "2. Set up AWS Budgets with alerts"
echo "3. Implement cost allocation tags"
echo "4. Review IAM permissions regularly"
echo "5. Monitor usage with CloudWatch metrics"
echo "6. Consider Reserved Instances for predictable workloads"
echo "7. Use AWS Organizations for multi-account management"
echo "8. Implement least privilege access controls"

echo ""
echo "================================================"
echo "NEXT STEPS:"
echo "================================================"
echo "1. Run the cost estimator script:"
echo "   python3 scripts/aws_cost_estimator.py --usage MEDIUM"
echo ""
echo "2. Check the detailed report:"
echo "   cat aws-cost-estimate-report.md"
echo ""
echo "3. Set up monitoring:"
echo "   - CloudWatch alarms for cost thresholds"
echo "   - AWS Budgets for spending limits"
echo "   - Cost Explorer for trend analysis"
echo ""
echo "4. Review architecture:"
echo "   - Optimize Lambda memory settings"
echo "   - Implement caching strategies"
echo "   - Use appropriate instance types"

echo ""
echo "================================================"
echo "IMPORTANT LINKS:"
echo "================================================"
echo "• AWS Pricing Calculator: https://calculator.aws/"
echo "• AWS Free Tier: https://aws.amazon.com/free/"
echo "• AWS Cost Management: https://aws.amazon.com/aws-cost-management/"
echo "• AWS Well-Architected Framework: https://aws.amazon.com/architecture/well-architected/"
echo "• AWS Trusted Advisor: https://aws.amazon.com/premiumsupport/technology/trusted-advisor/"

echo ""
echo "Script completed successfully!"