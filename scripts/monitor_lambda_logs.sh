#!/bin/bash

# Script to monitor CloudWatch logs for all Lambda functions
# Usage: ./scripts/monitor_lambda_logs.sh [--function FUNCTION_NAME] [--tail] [--errors-only]

set -e

REGION="ap-southeast-1"
FUNCTION_NAME=""
TAIL_MODE=false
ERRORS_ONLY=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --function)
            FUNCTION_NAME="$2"
            shift 2
            ;;
        --tail)
            TAIL_MODE=true
            shift
            ;;
        --errors-only)
            ERRORS_ONLY=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--function FUNCTION_NAME] [--tail] [--errors-only]"
            exit 1
            ;;
    esac
done

if [ -n "$FUNCTION_NAME" ]; then
    # Monitor specific function
    LOG_GROUP="/aws/lambda/$FUNCTION_NAME"
    
    echo "📋 Monitoring logs for: $FUNCTION_NAME"
    echo "Log Group: $LOG_GROUP"
    echo ""
    
    if [ "$TAIL_MODE" = true ]; then
        echo "🔄 Tailing logs (Ctrl+C to stop)..."
        aws logs tail "$LOG_GROUP" \
            --region "$REGION" \
            --follow \
            --format short
    else
        echo "📋 Recent logs (last 10 minutes)..."
        START_TIME=$(date -u -d '10 minutes ago' +%s)000
        
        # Get latest log stream
        STREAM=$(aws logs describe-log-streams \
            --region "$REGION" \
            --log-group-name "$LOG_GROUP" \
            --order-by LastEventTime \
            --descending \
            --max-items 1 \
            --query 'logStreams[0].logStreamName' \
            --output text)
        
        if [ "$STREAM" = "None" ] || [ -z "$STREAM" ]; then
            echo "⚠️  No log streams found"
            exit 0
        fi
        
        aws logs get-log-events \
            --region "$REGION" \
            --log-group-name "$LOG_GROUP" \
            --log-stream-name "$STREAM" \
            --start-time "$START_TIME" \
            --query 'events[].message' \
            --output text
    fi
else
    # List all functions with recent activity
    echo "📋 Lambda Functions with Recent Activity (last 1 hour)..."
    echo ""
    
    FUNCTIONS=$(aws lambda list-functions \
        --region "$REGION" \
        --query 'Functions[?starts_with(FunctionName, `lexi-be`)].FunctionName' \
        --output json | jq -r '.[]')
    
    START_TIME=$(date -u -d '1 hour ago' +%s)000
    
    for func in $FUNCTIONS; do
        LOG_GROUP="/aws/lambda/$func"
        
        # Check if log group has recent activity
        LATEST=$(aws logs describe-log-streams \
            --region "$REGION" \
            --log-group-name "$LOG_GROUP" \
            --order-by LastEventTime \
            --descending \
            --max-items 1 \
            --query 'logStreams[0].lastEventTimestamp' \
            --output text 2>/dev/null || echo "0")
        
        if [ "$LATEST" = "None" ] || [ -z "$LATEST" ]; then
            LATEST=0
        fi
        
        if [ "$LATEST" -gt "$START_TIME" ]; then
            LAST_EVENT=$(date -d "@$((LATEST/1000))" '+%Y-%m-%d %H:%M:%S')
            echo "✅ $func"
            echo "   Last activity: $LAST_EVENT"
            
            if [ "$ERRORS_ONLY" = true ]; then
                # Show only errors
                STREAM=$(aws logs describe-log-streams \
                    --region "$REGION" \
                    --log-group-name "$LOG_GROUP" \
                    --order-by LastEventTime \
                    --descending \
                    --max-items 1 \
                    --query 'logStreams[0].logStreamName' \
                    --output text)
                
                if [ "$STREAM" != "None" ] && [ -n "$STREAM" ]; then
                    ERRORS=$(aws logs get-log-events \
                        --region "$REGION" \
                        --log-group-name "$LOG_GROUP" \
                        --log-stream-name "$STREAM" \
                        --start-time "$START_TIME" \
                        --query 'events[?contains(message, `ERROR`) || contains(message, `Exception`)].message' \
                        --output text)
                    
                    if [ -n "$ERRORS" ]; then
                        echo "   ⚠️  Recent errors:"
                        echo "$ERRORS" | head -5 | sed 's/^/      /'
                    fi
                fi
            fi
            echo ""
        fi
    done
    
    echo ""
    echo "💡 To monitor a specific function:"
    echo "   ./scripts/monitor_lambda_logs.sh --function FUNCTION_NAME --tail"
fi
