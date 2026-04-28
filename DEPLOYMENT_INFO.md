# Lexi-BE Deployment Summary

## ✅ Deployment Status: SUCCESS

### Infrastructure Deployed

#### 1. DynamoDB
- **Table Name**: LexiApp
- **Status**: ACTIVE
- **ARN**: arn:aws:dynamodb:ap-southeast-1:826229823693:table/LexiApp
- **Billing Mode**: PAY_PER_REQUEST
- **Features**: 
  - Point-in-time recovery enabled
  - TTL enabled for automatic expiration
  - 4 Global Secondary Indexes (GSI)

#### 2. Cognito User Pool
- **User Pool ID**: ap-southeast-1_6GzL5k9Fr
- **User Pool Name**: LexiUserPool
- **Region**: ap-southeast-1
- **ARN**: arn:aws:cognito-idp:ap-southeast-1:826229823693:userpool/ap-southeast-1_6GzL5k9Fr

#### 3. Cognito User Pool Client
- **Client ID**: 6r7npt973q3pbb48s1ied5lmb5
- **Client Name**: LexiWebClient
- **Supported Auth Flows**: 
  - ALLOW_USER_PASSWORD_AUTH
  - ALLOW_REFRESH_TOKEN_AUTH
  - ALLOW_USER_SRP_AUTH
- **OAuth Providers**: COGNITO, Google
- **OAuth Scopes**: email, openid, profile

#### 4. Cognito Domain
- **Domain**: lexi-auth-826229823693
- **Full Domain**: lexi-auth-826229823693.auth.ap-southeast-1.amazoncognito.com

#### 5. Google Identity Provider
- **Provider Name**: Google
- **Credentials**: Stored in AWS Parameter Store
  - `/lexi/auth/google/client_id`
  - `/lexi/auth/google/client_secret`

#### 6. Lambda Functions (Auth Module)
- **PreSignUp Lambda**: 
  - ARN: arn:aws:lambda:ap-southeast-1:826229823693:function:lexi-be-AuthModule-14XXR3EEHSPTM-PreSignUpLambda-jpxnXr0PvMET
  - Purpose: Link federated users (Google) to existing email/password accounts
  - Trigger: Cognito PreSignUp event

- **PostConfirmation Lambda**:
  - ARN: arn:aws:lambda:ap-southeast-1:826229823693:function:lexi-be-AuthModule-14XXR3EE-PostConfirmationLambda-wxOTbJALGt7U
  - Purpose: Create user profile in DynamoDB after successful sign-up
  - Trigger: Cognito PostConfirmation event

#### 7. API Gateway
- **API Name**: LexiApi
- **Stage**: Prod
- **URL**: https://1eplxzdpsb.execute-api.ap-southeast-1.amazonaws.com/Prod/
- **Authorizer**: Cognito User Pool (MyCognitoAuthorizer)

#### 8. WebSocket API
- **API Name**: SpeakingWebSocketApi
- **Stage**: Prod
- **URL**: wss://tpibtuvnk6.execute-api.ap-southeast-1.amazonaws.com/Prod
- **Routes**: $connect, $disconnect, $default

#### 9. S3 Bucket
- **Bucket Name**: lexi-be-speakingaudiobucket-9lc7kw2fsuxx
- **Purpose**: Store audio files for speaking practice
- **Encryption**: AES256 (Server-side)
- **CORS**: Enabled for cross-origin requests

#### 10. Lambda Functions (Main Stack)
- 22 Lambda functions deployed for various features:
  - Onboarding, Admin, Profile, Vocabulary, Flashcard, Scenarios, Speaking Session, WebSocket

### Frontend Configuration

Update your frontend with these values from `frontend-cognito-config.json`:

```json
{
  "userPoolId": "ap-southeast-1_6GzL5k9Fr",
  "userPoolClientId": "6r7npt973q3pbb48s1ied5lmb5",
  "domain": "lexi-auth-826229823693",
  "region": "ap-southeast-1",
  "oauth": {
    "domain": "lexi-auth-826229823693.auth.ap-southeast-1.amazoncognito.com",
    "scope": ["email", "openid", "profile"],
    "redirectSignIn": "http://localhost:3000/oauth-callback,https://ngoctin.me/oauth-callback",
    "redirectSignOut": "http://localhost:3000,https://ngoctin.me",
    "responseType": "code"
  },
  "loginUrl": "https://lexi-auth-826229823693.auth.ap-southeast-1.amazoncognito.com/login?client_id=6r7npt973q3pbb48s1ied5lmb5&response_type=code&scope=email+openid+profile&redirect_uri=http://localhost:3000/oauth-callback"
}
```

### Testing the Flow

#### 1. Sign Up with Email/Password
```bash
aws cognito-idp sign-up \
  --client-id 6r7npt973q3pbb48s1ied5lmb5 \
  --username test@example.com \
  --password TempPassword123! \
  --user-attributes Name=email,Value=test@example.com \
  --region ap-southeast-1
```

#### 2. Confirm User
```bash
aws cognito-idp admin-confirm-sign-up \
  --user-pool-id ap-southeast-1_6GzL5k9Fr \
  --username test@example.com \
  --region ap-southeast-1
```

#### 3. Login with Google
- Visit: https://lexi-auth-826229823693.auth.ap-southeast-1.amazoncognito.com/login\?client_id\=6r7npt973q3pbb48s1ied5lmb5\&response_type\=code\&scope\=email+openid+profile\&redirect_uri\=http://localhost:3000/oauth-callback
- Click "Google" button
- Use same email as step 1
- PreSignUp Lambda will link the Google identity to existing user

#### 4. Verify User Profile
```bash
aws dynamodb get-item \
  --table-name LexiApp \
  --key '{"PK":{"S":"USER#test@example.com"},"SK":{"S":"PROFILE"}}' \
  --region ap-southeast-1
```

### Key Features Implemented

✅ **Cognito Pre Sign-up Lambda Trigger**
- Detects federated sign-ups (Google)
- Searches for existing users by email
- Links Google identity to existing user using AdminLinkProviderForUser
- Fail-open approach (returns event on errors to not block sign-ups)

✅ **Cognito Post Confirmation Lambda Trigger**
- Creates user profile in DynamoDB after successful sign-up
- Stores user metadata and preferences

✅ **Google OAuth Integration**
- Google Identity Provider configured
- OAuth credentials stored in Parameter Store
- Callback URLs configured for localhost and production

✅ **Infrastructure as Code**
- All resources defined in SAM templates
- Modular structure (DatabaseModule, AuthModule)
- Proper IAM permissions and security policies

### Troubleshooting

#### Lambda Trigger Not Working
Check CloudWatch Logs:
```bash
aws logs tail /aws/lambda/lexi-be-AuthModule-14XXR3EEHSPTM-PreSignUpLambda-jpxnXr0PvMET --follow --region ap-southeast-1
```

#### User Not Created in DynamoDB
Check PostConfirmation Lambda logs:
```bash
aws logs tail /aws/lambda/lexi-be-AuthModule-14XXR3EE-PostConfirmationLambda-wxOTbJALGt7U --follow --region ap-southeast-1
```

#### Google OAuth Not Working
Verify Parameter Store values:
```bash
aws ssm get-parameter --name /lexi/auth/google/client_id --region ap-southeast-1
aws ssm get-parameter --name /lexi/auth/google/client_secret --with-decryption --region ap-southeast-1
```

### Stack Information

- **Main Stack**: lexi-be
- **Nested Stacks**:
  - lexi-be-DatabaseModule-DS9TCPDK...
  - lexi-be-AuthModule-14XXR3EEHSPTM
- **Region**: ap-southeast-1
- **Account ID**: 826229823693

### Next Steps

1. ✅ Deploy infrastructure (DONE)
2. ✅ Add Lambda triggers (DONE)
3. ⏳ Test sign-up flow with email/password
4. ⏳ Test Google OAuth login
5. ⏳ Verify user profile creation in DynamoDB
6. ⏳ Test API endpoints with Cognito authorization
7. ⏳ Deploy frontend with Cognito integration

