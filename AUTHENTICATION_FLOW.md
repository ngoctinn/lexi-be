# Authentication Flow

## Overview

This project uses **AWS Cognito User Pool** with **API Gateway Cognito Authorizer** for authentication. This is the AWS-recommended approach for serverless REST APIs.

## Architecture

```
┌─────────────┐
│  Frontend   │
└──────┬──────┘
       │ 1. Sign in
       ▼
┌─────────────────┐
│ Cognito User    │
│ Pool            │
└──────┬──────────┘
       │ 2. Return JWT token (ID or Access token)
       ▼
┌─────────────┐
│  Frontend   │
└──────┬──────┘
       │ 3. API call with Authorization: Bearer <token>
       ▼
┌─────────────────────────────────────────────────┐
│ API Gateway                                     │
│ ┌─────────────────────────────────────────┐   │
│ │ Cognito Authorizer                      │   │
│ │ - Validates JWT signature               │   │
│ │ - Checks expiration (exp)               │   │
│ │ - Verifies issuer (iss)                 │   │
│ │ - Validates audience (aud)              │   │
│ │ - Caches validation result (5 min TTL)  │   │
│ └─────────────────────────────────────────┘   │
└──────┬──────────────────────────────────────────┘
       │ 4. If valid, forward to Lambda with claims
       ▼
┌─────────────────────────────────────────────────┐
│ Lambda Handler                                  │
│ - Read user_id from:                            │
│   event["requestContext"]["authorizer"]         │
│        ["claims"]["sub"]                        │
│ - No JWT validation needed                      │
└─────────────────────────────────────────────────┘
```

## Authentication by Endpoint Type

### 1. REST API Endpoints (Protected)

**All REST API endpoints** (except `/scenarios`) are protected by Cognito Authorizer:

- `/profile` (GET, PATCH)
- `/sessions/*` (POST, GET)
- `/onboarding/complete` (POST)
- `/admin/*` (GET, POST, PATCH) - Also requires ADMIN role check
- `/flashcards/*` (GET, POST)
- `/vocabulary/translate` (POST)
- `/vocabulary/translate-sentence` (POST)

**Configuration:**
```yaml
# template.yaml
LexiApi:
  Type: AWS::Serverless::Api
  Properties:
    Auth:
      DefaultAuthorizer: MyCognitoAuthorizer
      Authorizers:
        MyCognitoAuthorizer:
          UserPoolArn: !GetAtt AuthModule.Outputs.UserPoolArn
          Identity:
            Header: Authorization
```

**Lambda Handler Pattern:**
```python
def handler(event, context):
    # Get user_id from Cognito claims (validated by API Gateway)
    user_id = event["requestContext"]["authorizer"]["claims"]["sub"]
    
    # Process request...
```

### 2. Public Endpoints (No Auth)

**`/scenarios` (GET)** - Public endpoint for listing scenarios

**Configuration:**
```yaml
Events:
  ListScenarios:
    Type: Api
    Properties:
      Path: /scenarios
      Method: GET
      RestApiId: !Ref LexiApi
      Auth:
        Authorizer: NONE  # Public endpoint
```

### 3. WebSocket API (Custom Auth)

**WebSocket API** uses custom JWT validation in Lambda because:
- API Gateway WebSocket does NOT support Cognito Authorizer
- Token is passed as query parameter: `?token=<jwt>`

**Current Implementation:**
- Manual JWT validation in `websocket_handler.py`
- Validates signature, expiration, issuer, audience
- **TODO**: Migrate to Lambda Authorizer for better performance and caching

## Frontend Integration

### 1. Sign In

```javascript
import { CognitoIdentityProviderClient, InitiateAuthCommand } from "@aws-sdk/client-cognito-identity-provider";

const client = new CognitoIdentityProviderClient({ region: "us-east-1" });
const command = new InitiateAuthCommand({
  AuthFlow: "USER_PASSWORD_AUTH",
  ClientId: process.env.COGNITO_CLIENT_ID,
  AuthParameters: {
    USERNAME: email,
    PASSWORD: password,
  },
});

const response = await client.send(command);
const idToken = response.AuthenticationResult.IdToken;
const accessToken = response.AuthenticationResult.AccessToken;
```

### 2. Call API

```javascript
const response = await fetch(`${API_URL}/profile`, {
  method: "GET",
  headers: {
    "Authorization": `Bearer ${idToken}`,  // or accessToken
    "Content-Type": "application/json",
  },
});
```

### 3. WebSocket Connection

```javascript
const ws = new WebSocket(`${WS_URL}?token=${idToken}`);
```

## Token Types

### ID Token
- Contains user identity claims (sub, email, name, etc.)
- Use for: User profile, identity-based authorization
- Claim: `aud` (audience) = Client ID

### Access Token
- Contains OAuth 2.0 scopes
- Use for: Resource access, scope-based authorization
- Claim: `client_id` = Client ID

**Both tokens are valid** for API Gateway Cognito Authorizer.

## Security Best Practices

### ✅ What We Do

1. **Centralized Auth**: API Gateway validates JWT, not Lambda
2. **Token Caching**: API Gateway caches validation (5 min TTL)
3. **AWS Managed**: Cognito handles token signing, rotation, revocation
4. **Least Privilege**: Lambda only reads claims, no validation logic
5. **Role-Based Access**: Admin endpoints check role after authentication

### ⚠️ What to Avoid

1. ❌ **Manual JWT validation in Lambda** (slow, error-prone)
2. ❌ **Duplicate auth logic** across handlers
3. ❌ **Storing tokens in Lambda** (use claims from event)
4. ❌ **Custom token formats** (use Cognito standard tokens)

## Troubleshooting

### 401 Unauthorized

**Cause**: Token is invalid, expired, or missing

**Check:**
1. Token is in `Authorization: Bearer <token>` header
2. Token is not expired (check `exp` claim)
3. Token is from correct Cognito User Pool
4. Token `aud` or `client_id` matches app client ID

### 403 Forbidden

**Cause**: User is authenticated but not authorized (e.g., not ADMIN)

**Check:**
1. User role in DynamoDB
2. Admin check logic in handler

### Missing Claims

**Cause**: API Gateway Cognito Authorizer not configured

**Check:**
1. `RestApiId: !Ref LexiApi` in template.yaml
2. `DefaultAuthorizer: MyCognitoAuthorizer` in API config
3. Deploy stack: `sam build && sam deploy`

## References

- [AWS Docs: Control access to REST APIs using Cognito](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-integrate-with-cognito.html)
- [AWS Docs: Verifying JSON web tokens](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html)
- [AWS Docs: Security best practices in API Gateway](https://docs.aws.amazon.com/apigateway/latest/developerguide/security-best-practices.html)
