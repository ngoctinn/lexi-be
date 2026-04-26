# Deployment Guide - Turn Analysis with AgentCore Memory

## Overview

This guide walks you through deploying the turn-by-turn analysis feature with AgentCore Memory integration.

## Prerequisites

- AWS CLI configured (`aws configure`)
- SAM CLI installed (`pip install aws-sam-cli`)
- Python 3.12+
- Permissions for:
  - Lambda
  - API Gateway
  - DynamoDB
  - S3
  - Cognito
  - Bedrock
  - **Bedrock AgentCore** (new)

## Step 1: Review Changes

### New Resources in template.yaml:

1. **LexiLearnerMemory** (AWS::BedrockAgentCore::Memory)
   - 365-day retention
   - Semantic strategy for mistake patterns
   - Summarization strategy for session summaries

2. **Environment Variables**
   - `AGENTCORE_MEMORY_ID` added to both Lambda functions

3. **IAM Permissions**
   - `bedrock-agentcore:CreateEvent`
   - `bedrock-agentcore:GetEvent`
   - `bedrock-agentcore:SearchLongTermMemories`
   - `bedrock-agentcore:ListSessions`

### New Code:

1. **ConversationAnalyzer** (`src/domain/services/conversation_analyzer.py`)
   - LLM-based turn analysis
   - Level-adaptive prompts

2. **LearnerMemoryClient** (`src/infrastructure/services/memory_client.py`)
   - Memory operations wrapper
   - Graceful degradation

3. **WebSocket Action** (`ANALYZE_TURN`)
   - Added to `websocket_handler.py`
   - Consistent with hint system

## Step 2: Build

```bash
sam build
```

Expected output:
```
Building codeuri: src/ runtime: python3.12 ...
Build Succeeded

Built Artifacts  : .aws-sam/build
Built Template   : .aws-sam/build/template.yaml
```

## Step 3: Deploy

### First-time deployment:

```bash
sam deploy --guided
```

You'll be prompted for:
- Stack Name: `lexi-be` (or your preferred name)
- AWS Region: `ap-southeast-1` (or your region)
- Confirm changes: `Y`
- Allow SAM CLI IAM role creation: `Y`
- Disable rollback: `N`
- Save arguments to config: `Y`

### Subsequent deployments:

```bash
sam deploy
```

## Step 4: Verify Memory Creation

After deployment, check the memory was created:

```bash
# Get Memory ID from stack outputs
aws cloudformation describe-stacks \
  --stack-name lexi-be \
  --query 'Stacks[0].Outputs[?OutputKey==`AgentCoreMemoryId`].OutputValue' \
  --output text

# Check memory status
MEMORY_ID=$(aws cloudformation describe-stacks \
  --stack-name lexi-be \
  --query 'Stacks[0].Outputs[?OutputKey==`AgentCoreMemoryId`].OutputValue' \
  --output text)

aws bedrock-agentcore-control get-memory \
  --memory-id $MEMORY_ID \
  --region ap-southeast-1
```

Expected status: `ACTIVE`

## Step 5: Test the Feature

### 5.1 Connect to WebSocket

```javascript
const ws = new WebSocket('wss://your-websocket-url');

ws.onopen = () => {
  console.log('Connected');
  
  // Authenticate
  ws.send(JSON.stringify({
    action: 'AUTHENTICATE',
    token: 'your-cognito-token'
  }));
};
```

### 5.2 Start Session and Submit Turn

```javascript
// Start session
ws.send(JSON.stringify({
  action: 'START_SESSION',
  session_id: 'your-session-id'
}));

// Submit a turn (user speaks)
ws.send(JSON.stringify({
  action: 'SUBMIT_TRANSCRIPT',
  session_id: 'your-session-id',
  transcript: 'I go to school yesterday'
}));
```

### 5.3 Request Analysis

```javascript
// Analyze turn 1
ws.send(JSON.stringify({
  action: 'ANALYZE_TURN',
  session_id: 'your-session-id',
  turn_index: 1
}));

// Listen for response
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.event === 'TURN_ANALYSIS') {
    console.log('Vietnamese:', data.analysis.markdown.vi);
    console.log('English:', data.analysis.markdown.en);
  }
};
```

### 5.4 Verify Memory Storage

```bash
# List sessions for a user
aws bedrock-agentcore list-sessions \
  --memory-id $MEMORY_ID \
  --actor-id "user-cognito-sub" \
  --region ap-southeast-1

# Search long-term memories
aws bedrock-agentcore search-long-term-memories \
  --memory-id $MEMORY_ID \
  --actor-id "user-cognito-sub" \
  --query "common mistakes" \
  --namespace-path "/" \
  --top-k 5 \
  --region ap-southeast-1
```

## Step 6: Monitor

### CloudWatch Logs

```bash
# WebSocket function logs
aws logs tail /aws/lambda/lexi-be-SpeakingWebSocketFunction-xxx --follow

# Session function logs
aws logs tail /aws/lambda/lexi-be-SpeakingSessionFunction-xxx --follow
```

### CloudWatch Metrics

Check these metrics in CloudWatch:
- Lambda invocations
- Lambda errors
- Lambda duration
- Memory operations (custom metrics if added)

## Troubleshooting

### Memory creation failed

**Error:** `CREATE_FAILED: LexiLearnerMemory`

**Solution:** Check IAM permissions for Bedrock AgentCore:
```bash
aws iam get-role-policy \
  --role-name lexi-be-SpeakingWebSocketFunctionRole-xxx \
  --policy-name SpeakingWebSocketFunctionRolePolicy
```

### Memory not found

**Error:** `Memory client not initialized`

**Solution:** Verify environment variable:
```bash
aws lambda get-function-configuration \
  --function-name lexi-be-SpeakingWebSocketFunction-xxx \
  --query 'Environment.Variables.AGENTCORE_MEMORY_ID'
```

### Analysis not working

**Error:** `Failed to analyze turn`

**Check:**
1. Bedrock permissions: `bedrock:InvokeModel`
2. Lambda timeout: Should be at least 15s
3. Memory size: Should be at least 512MB

### Memory storage failing

**Error:** `Failed to store turn analysis in memory`

**Check:**
1. Memory is ACTIVE: `aws bedrock-agentcore-control get-memory`
2. Permissions: `bedrock-agentcore:CreateEvent`
3. CloudWatch logs for detailed error

## Rollback

If deployment fails or you want to rollback:

```bash
# Delete the stack
aws cloudformation delete-stack --stack-name lexi-be

# Wait for deletion
aws cloudformation wait stack-delete-complete --stack-name lexi-be
```

## Cost Estimate

### AgentCore Memory:
- Storage: $0.10/GB-month
- Event writes: $0.001 per 1K events
- Memory retrieval: $0.002 per 1K retrievals

### Estimated monthly cost (1000 users):
- Memory storage: ~$0.10
- Event writes: ~$0.10
- Retrievals: ~$0.20
- **Total: ~$0.40/month**

### Lambda:
- WebSocket function: ~$5/month (existing)
- Session function: ~$3/month (existing)
- **No additional Lambda costs**

## Next Steps

1. ✅ Deploy to staging
2. ✅ Test analysis feature
3. ✅ Verify memory storage
4. ✅ Monitor for 24 hours
5. 📝 Deploy to production
6. 📝 Update frontend to use `ANALYZE_TURN` action
7. 📝 Add monitoring dashboards
8. 📝 Set up CloudWatch alarms

## Support

For issues:
1. Check CloudWatch logs
2. Review `docs/TURN_ANALYSIS_FEATURE.md`
3. Review `docs/AGENTCORE_MEMORY_SETUP.md`
4. Check AWS Bedrock AgentCore documentation

## References

- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [Bedrock AgentCore Memory](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory.html)
- [WebSocket API](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-websocket-api.html)
