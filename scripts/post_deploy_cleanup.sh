#!/bin/bash

# Post-deployment cleanup script
# Automatically cleanup old CloudWatch log groups after SAM deploy
# Usage: ./scripts/post_deploy_cleanup.sh

set -e

echo "🚀 Post-Deployment Cleanup"
echo "=========================="
echo ""

# Step 1: Cleanup old log groups
echo "📋 Step 1: Cleaning up old CloudWatch log groups..."
./scripts/cleanup_cloudwatch_logs.sh --dry-run

echo ""
read -p "Proceed with cleanup? (yes/no): " confirm

if [ "$confirm" = "yes" ]; then
    ./scripts/cleanup_cloudwatch_logs.sh
else
    echo "⏭️  Skipping cleanup"
fi

echo ""

# Step 2: Set retention policy (optional)
echo "📋 Step 2: Set retention policy (optional)"
read -p "Set retention policy? (yes/no): " set_retention

if [ "$set_retention" = "yes" ]; then
    read -p "Retention days (7/30/90): " days
    ./scripts/set_log_retention.sh --days "$days"
else
    echo "⏭️  Skipping retention policy"
fi

echo ""
echo "✅ Post-deployment cleanup complete!"
echo ""
echo "💡 To monitor logs:"
echo "   ./scripts/monitor_lambda_logs.sh"
