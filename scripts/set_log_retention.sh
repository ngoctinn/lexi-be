#!/bin/bash

# Script to set retention policy for all CloudWatch Log Groups
# Usage: ./scripts/set_log_retention.sh [--days DAYS] [--dry-run]

set -e

REGION="ap-southeast-1"
RETENTION_DAYS=7  # Default: 7 days
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --days)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--days DAYS] [--dry-run]"
            exit 1
            ;;
    esac
done

# Validate retention days (AWS allowed values)
VALID_DAYS=(1 3 5 7 14 30 60 90 120 150 180 365 400 545 731 1096 1827 2192 2557 2922 3288 3653)
if [[ ! " ${VALID_DAYS[@]} " =~ " ${RETENTION_DAYS} " ]]; then
    echo "❌ Invalid retention days: $RETENTION_DAYS"
    echo "Valid values: ${VALID_DAYS[@]}"
    exit 1
fi

if [ "$DRY_RUN" = true ]; then
    echo "🔍 DRY RUN MODE - No changes will be made"
fi

echo "📋 Setting retention policy to $RETENTION_DAYS days for all lexi-be log groups..."
echo ""

echo "📋 Step 1: Getting all CloudWatch Log Groups..."
LOG_GROUPS=$(aws logs describe-log-groups \
    --region "$REGION" \
    --log-group-name-prefix "/aws/lambda/lexi-be" \
    --query 'logGroups[].logGroupName' \
    --output json | jq -r '.[]')

TOTAL=$(echo "$LOG_GROUPS" | wc -l)
echo "✅ Found $TOTAL log groups"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo "🔍 DRY RUN - Would set retention to $RETENTION_DAYS days for $TOTAL log groups"
    for log_group in $LOG_GROUPS; do
        echo "  - $log_group"
    done
    exit 0
fi

echo "🔧 Step 2: Setting retention policy..."
SUCCESS=0
FAILED=0

for log_group in $LOG_GROUPS; do
    echo -n "Setting retention for $log_group... "
    if aws logs put-retention-policy \
        --region "$REGION" \
        --log-group-name "$log_group" \
        --retention-in-days "$RETENTION_DAYS" 2>/dev/null; then
        echo "✅"
        ((SUCCESS++))
    else
        echo "❌"
        ((FAILED++))
    fi
done

echo ""
echo "✅ Retention policy update complete!"
echo "   - Success: $SUCCESS"
echo "   - Failed: $FAILED"
echo "   - Retention: $RETENTION_DAYS days"
