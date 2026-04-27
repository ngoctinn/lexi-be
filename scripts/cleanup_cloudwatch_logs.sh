#!/bin/bash

# Script to cleanup old CloudWatch Log Groups and keep only active Lambda functions
# Usage: ./scripts/cleanup_cloudwatch_logs.sh [--dry-run]

set -e

REGION="ap-southeast-1"
DRY_RUN=false

# Parse arguments
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "🔍 DRY RUN MODE - No changes will be made"
fi

echo "📋 Step 1: Getting active Lambda functions..."
ACTIVE_FUNCTIONS=$(aws lambda list-functions \
    --region "$REGION" \
    --query 'Functions[?starts_with(FunctionName, `lexi-be`)].FunctionName' \
    --output json | jq -r '.[]')

echo "✅ Found $(echo "$ACTIVE_FUNCTIONS" | wc -l) active Lambda functions"
echo ""

echo "📋 Step 2: Getting all CloudWatch Log Groups..."
ALL_LOG_GROUPS=$(aws logs describe-log-groups \
    --region "$REGION" \
    --log-group-name-prefix "/aws/lambda/lexi-be" \
    --query 'logGroups[].logGroupName' \
    --output json | jq -r '.[]')

echo "✅ Found $(echo "$ALL_LOG_GROUPS" | wc -l) log groups"
echo ""

echo "📋 Step 3: Identifying log groups to delete..."
TO_DELETE=()
TO_KEEP=()

for log_group in $ALL_LOG_GROUPS; do
    # Extract function name from log group name
    # Format: /aws/lambda/lexi-be-FunctionName-RandomSuffix
    function_name=$(echo "$log_group" | sed 's|/aws/lambda/||')
    
    # Check if this function is active
    if echo "$ACTIVE_FUNCTIONS" | grep -q "^${function_name}$"; then
        TO_KEEP+=("$log_group")
    else
        TO_DELETE+=("$log_group")
    fi
done

echo "✅ Log groups to keep: ${#TO_KEEP[@]}"
echo "⚠️  Log groups to delete: ${#TO_DELETE[@]}"
echo ""

if [ ${#TO_DELETE[@]} -eq 0 ]; then
    echo "✅ No log groups to delete. All clean!"
    exit 0
fi

echo "📋 Log groups to delete:"
for log_group in "${TO_DELETE[@]}"; do
    echo "  - $log_group"
done
echo ""

if [ "$DRY_RUN" = true ]; then
    echo "🔍 DRY RUN - Would delete ${#TO_DELETE[@]} log groups"
    exit 0
fi

echo "⚠️  WARNING: This will permanently delete ${#TO_DELETE[@]} log groups!"
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Aborted"
    exit 1
fi

echo ""
echo "🗑️  Step 4: Deleting old log groups..."
DELETED=0
FAILED=0

for log_group in "${TO_DELETE[@]}"; do
    echo -n "Deleting $log_group... "
    if aws logs delete-log-group \
        --region "$REGION" \
        --log-group-name "$log_group" 2>/dev/null; then
        echo "✅"
        ((DELETED++))
    else
        echo "❌"
        ((FAILED++))
    fi
done

echo ""
echo "✅ Cleanup complete!"
echo "   - Deleted: $DELETED"
echo "   - Failed: $FAILED"
echo "   - Kept: ${#TO_KEEP[@]}"
