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
  --period 300 \# lexi-be

Backend serverless application for Lexi - English learning platform with AI-powered speaking practice.

## Architecture

This project uses AWS Serverless Application Model (SAM) with:
- **Lambda Functions**: Python 3.12 runtime
- **API Gateway**: REST API with Cognito Authorizer
- **WebSocket API**: Real-time speaking sessions
- **DynamoDB**: NoSQL database for user data, sessions, scenarios
- **Cognito**: User authentication and authorization
- **Bedrock**: AI conversation generation
- **Polly**: Text-to-speech synthesis
- **Transcribe**: Speech-to-text conversion

## Documentation

- **[Authentication Flow](./AUTHENTICATION_FLOW.md)** - Complete auth architecture and best practices
- **[Auth Cleanup Summary](./AUTH_CLEANUP_SUMMARY.md)** - Recent auth improvements
- **[Conversation Architecture](./CONVERSATION_ARCHITECTURE.md)** - Speaking session design
- **[Documentation Index](./DOCUMENTATION_INDEX.md)** - All project documentation

## Quick Start

### Prerequisites

- SAM CLI - [Install the SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
- [Python 3.12 installed](https://www.python.org/downloads/)
- Docker - [Install Docker community edition](https://hub.docker.com/search/?type=edition&offering=community)
- AWS CLI configured with credentials

### Deploy

```bash
sam build
sam deploy --guided
```

### Test Authentication

```bash
# Get Cognito token
python scripts/get_cognito_token.py

# Test API with token
TOKEN="<your-token>"
curl -X GET https://<api-id>.execute-api.us-east-1.amazonaws.com/Prod/profile \
  -H "Authorization: Bearer $TOKEN"
```

## Project Structure

```
lexi-be/
├── src/
│   ├── application/          # Use cases and DTOs
│   ├── domain/              # Business logic and entities
│   ├── infrastructure/      # AWS services, repositories, handlers
│   └── interfaces/          # Controllers, view models, mappers
├── config/                  # SAM module configs (auth, database)
├── scripts/                 # Testing and utility scripts
├── template.yaml           # Main SAM template
└── README.md
```

## Authentication

All REST API endpoints (except `/scenarios`) are protected by **AWS Cognito User Pool Authorizer**.

**Flow:**
1. Frontend signs in to Cognito → gets JWT token
2. Frontend calls API with `Authorization: Bearer <token>`
3. API Gateway validates JWT (cached, fast, secure)
4. Lambda receives validated user claims

See [AUTHENTICATION_FLOW.md](./AUTHENTICATION_FLOW.md) for details.

## Development

### Local Testing

```bash
# Start local API
sam local start-api

# Invoke function locally
sam local invoke FunctionName -e events/event.json
```

### Run Tests

```bash
pytest tests/
```

## Deployment

### First Time

```bash
sam build
sam deploy --guided
```

### Subsequent Deploys

```bash
sam build && sam deploy
```

## Environment Variables

Key environment variables (set in template.yaml):
- `LEXI_TABLE_NAME`: DynamoDB table name
- `COGNITO_USER_POOL_ID`: Cognito User Pool ID
- `COGNITO_APP_CLIENT_ID`: Cognito App Client ID
- `SPEAKING_AUDIO_BUCKET_NAME`: S3 bucket for audio files

## API Endpoints

### Public
- `GET /scenarios` - List available speaking scenarios

### Authenticated (Cognito)
- `GET /profile` - Get user profile
- `PATCH /profile` - Update user profile
- `POST /onboarding/complete` - Complete onboarding
- `POST /sessions` - Create speaking session
- `GET /sessions` - List user sessions
- `GET /sessions/{id}` - Get session details
- `POST /vocabulary/translate` - Translate vocabulary

### Admin Only
- `GET /admin/users` - List all users
- `PATCH /admin/users/{id}` - Update user
- `GET /admin/scenarios` - List all scenarios
- `POST /admin/scenarios` - Create scenario

## WebSocket API

- `wss://<api-id>.execute-api.us-east-1.amazonaws.com/Prod`
- Routes: `$connect`, `$disconnect`, `$default`
- Auth: JWT token in query parameter `?token=<jwt>`

## Resources

- [AWS SAM Developer Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html)
- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html)
- [AWS API Gateway Developer Guide](https://docs.aws.amazon.com/apigateway/latest/developerguide/welcome.html)
- [AWS Cognito Developer Guide](https://docs.aws.amazon.com/cognito/latest/developerguide/what-is-amazon-cognito.html)

## License

This project is licensed under the MIT License.

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
