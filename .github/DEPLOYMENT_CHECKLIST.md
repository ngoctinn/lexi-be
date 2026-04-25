# Deployment Checklist

## Pre-Deployment

- [ ] All tests pass: `pytest tests/`
- [ ] Code reviewed and approved
- [ ] Environment variables configured in template.yaml
- [ ] AWS credentials configured: `aws configure`

## Build & Deploy

```bash
# Build application
sam build

# Validate template
sam validate

# Deploy to AWS
sam deploy --guided  # First time
# OR
sam deploy          # Subsequent deploys
```

## Post-Deployment Verification

### 1. Check Stack Status

```bash
aws cloudformation describe-stacks \
  --stack-name lexi-be \
  --query 'Stacks[0].StackStatus'
```

Expected: `CREATE_COMPLETE` or `UPDATE_COMPLETE`

### 2. Get API Endpoints

```bash
aws cloudformation describe-stacks \
  --stack-name lexi-be \
  --query 'Stacks[0].Outputs'
```

Note down:
- `ApiUrl`: REST API endpoint
- `WebSocketUrl`: WebSocket endpoint
- `UserPoolId`: Cognito User Pool ID
- `UserPoolClientId`: Cognito App Client ID

### 3. Test Authentication

```bash
# Get Cognito token
python scripts/get_cognito_token.py

# Save token
export TOKEN="<your-token>"
```

### 4. Test Public Endpoint (No Auth)

```bash
curl -X GET ${API_URL}/scenarios
```

Expected: 200 OK with scenarios list

### 5. Test Protected Endpoint (With Auth)

```bash
curl -X GET ${API_URL}/profile \
  -H "Authorization: Bearer ${TOKEN}"
```

Expected: 200 OK with user profile

### 6. Test Vocabulary Endpoint (Fixed in this deployment)

```bash
curl -X POST ${API_URL}/vocabulary/translate \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"word": "hello", "context": "Hello world"}'
```

Expected: 200 OK with translation

### 7. Test Admin Endpoint (Requires ADMIN role)

```bash
curl -X GET ${API_URL}/admin/users \
  -H "Authorization: Bearer ${TOKEN}"
```

Expected:
- 200 OK if user is ADMIN
- 403 Forbidden if user is not ADMIN

### 8. Test WebSocket Connection

```bash
# Install wscat if needed
npm install -g wscat

# Connect to WebSocket
wscat -c "${WS_URL}?token=${TOKEN}"
```

Expected: Connection established

### 9. Check CloudWatch Logs

```bash
# List log groups
aws logs describe-log-groups \
  --log-group-name-prefix /aws/lambda/lexi-be

# Tail logs for a function
sam logs -n GetProfileFunction --tail
```

Expected: No errors, Cognito Authorizer execution logs visible

### 10. Verify API Gateway Authorizer

```bash
# Check API Gateway configuration
aws apigateway get-authorizers \
  --rest-api-id <api-id>
```

Expected: `MyCognitoAuthorizer` present with correct UserPoolArn

## Rollback (If Issues)

```bash
# Rollback to previous version
aws cloudformation rollback-stack --stack-name lexi-be

# OR delete and redeploy
sam delete
sam build && sam deploy --guided
```

## Monitoring

### CloudWatch Alarms

- [ ] Lambda errors < 1%
- [ ] API Gateway 4xx errors < 5%
- [ ] API Gateway 5xx errors < 1%
- [ ] Lambda duration < 3000ms (p99)

### Metrics to Watch

```bash
# API Gateway requests
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Count \
  --dimensions Name=ApiName,Value=lexi-be \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Lambda invocations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=lexi-be-GetProfileFunction \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

## Security Checklist

- [ ] All REST API endpoints (except `/scenarios`) require authentication
- [ ] Cognito Authorizer configured on API Gateway
- [ ] Admin endpoints check user role
- [ ] No sensitive data in logs
- [ ] CORS configured correctly
- [ ] API keys not exposed in code

## Documentation Updates

- [ ] README.md updated with new endpoints
- [ ] AUTHENTICATION_FLOW.md reflects current architecture
- [ ] API documentation updated (if applicable)
- [ ] Frontend team notified of changes

## Known Issues

- WebSocket API still uses manual JWT validation (TODO: migrate to Lambda Authorizer)
- No rate limiting configured (consider adding API Gateway usage plans)

## Support

If issues occur:
1. Check CloudWatch Logs
2. Verify API Gateway configuration
3. Test with Postman/curl
4. Review [AUTHENTICATION_FLOW.md](../AUTHENTICATION_FLOW.md)
5. Contact: [Your contact info]
