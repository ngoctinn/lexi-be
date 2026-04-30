# Lexi Backend Architecture

## Overview

Lexi Backend là hệ thống serverless trên AWS, sử dụng Clean Architecture pattern với Lambda functions, API Gateway, và DynamoDB.

## Tech Stack

- **Runtime**: Python 3.12
- **Framework**: AWS SAM (Serverless Application Model)
- **API Gateway**: REST API + WebSocket API
- **Authentication**: AWS Cognito
- **Database**: DynamoDB (Single Table Design)
- **Storage**: S3 (audio files)
- **AI Services**: 
  - AWS Bedrock (Claude) - AI conversation
  - AWS Transcribe - Speech-to-text
  - AWS Polly - Text-to-speech
  - AWS Translate - Translation
  - AWS Comprehend - Text analysis

## Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                    API Gateway                          │
│              (Cognito Authorizer)                       │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  Lambda Handlers                        │
│         (infrastructure/handlers/)                      │
│  - Extract user_id from JWT                            │
│  - Validate request                                     │
│  - Call controller                                      │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   Controllers                           │
│            (interfaces/controllers/)                    │
│  - Parse request body                                   │
│  - Call use case                                        │
│  - Format response                                      │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    Use Cases                            │
│           (application/use_cases/)                      │
│  - Business logic                                       │
│  - Orchestrate domain entities                          │
│  - Call repositories                                    │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  Domain Entities                        │
│              (domain/entities/)                         │
│  - Pure business objects                                │
│  - No dependencies                                      │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  Repositories                           │
│         (infrastructure/persistence/)                   │
│  - DynamoDB operations                                  │
│  - Data mapping                                         │
└─────────────────────────────────────────────────────────┘
```

## Project Structure

```
lexi-be/
├── config/                    # CloudFormation templates
│   ├── auth-base.yaml        # Cognito User Pool
│   └── database.yaml         # DynamoDB table
│
├── src/
│   ├── domain/               # Business entities
│   │   └── entities/
│   │       ├── user.py
│   │       ├── flashcard.py
│   │       └── scenario.py
│   │
│   ├── application/          # Use cases (business logic)
│   │   └── use_cases/
│   │       ├── flashcard_use_cases.py
│   │       ├── user_profile_use_cases.py
│   │       └── admin_*.py
│   │
│   ├── interfaces/           # Controllers & Presenters
│   │   ├── controllers/
│   │   └── presenters/
│   │
│   └── infrastructure/       # External services
│       ├── handlers/         # Lambda handlers
│       │   ├── base_handler.py
│       │   ├── admin_base_handler.py
│       │   ├── flashcard/
│       │   ├── profile/
│       │   ├── vocabulary/
│       │   └── admin/
│       │
│       ├── persistence/      # DynamoDB repositories
│       │   ├── dynamo_user_repo.py
│       │   ├── dynamo_flashcard_repo.py
│       │   └── dynamo_scenario_repo.py
│       │
│       └── services/         # AWS services
│           ├── translation_service.py
│           └── dictionary_service.py
│
├── template.yaml             # Main SAM template
└── docs/                     # Documentation
    └── api/                  # API docs
```

## Handler Pattern

Tất cả Lambda handlers sử dụng `BaseHandler` hoặc `AdminBaseHandler`:

```python
class MyHandler(BaseHandler[MyController]):
    def build_dependencies(self) -> MyController:
        # Lazy initialization (singleton)
        repo = RepositoryFactory.create_my_repository()
        uc = MyUseCase(repo)
        return MyController(uc)

    def handle(self, user_id: str, event: dict, context: Any) -> dict:
        controller = self.get_dependencies()
        result = controller.my_method(user_id, event)
        
        if result.is_success:
            return self.presenter.present_success(result.value)
        else:
            return self.presenter._format_response(400, {
                "error": result.error
            })
```

**Benefits**:
- ✅ Consistent authentication & authorization
- ✅ Consistent error handling & logging
- ✅ Lazy dependency initialization (singleton)
- ✅ Easy testing & mocking

## Database Design

### Single Table Design (DynamoDB)

**Table**: `LexiAppTable`

| PK | SK | Entity Type |
|----|----|----|
| `USER#{user_id}` | `PROFILE` | User Profile |
| `USER#{user_id}` | `FLASHCARD#{flashcard_id}` | Flashcard |
| `USER#{user_id}` | `SESSION#{session_id}` | Speaking Session |
| `SCENARIO#{scenario_id}` | `METADATA` | Scenario |

**GSI1** (Global Secondary Index):
- PK: `GSI1PK` (e.g., `FLASHCARD#DUE`)
- SK: `GSI1SK` (e.g., `2026-04-30#USER#{user_id}`)
- Use case: Query flashcards due today

## Authentication Flow

1. User đăng nhập qua Cognito (email/password hoặc Google OAuth)
2. Cognito trả về JWT tokens (id_token, access_token, refresh_token)
3. Frontend gửi `id_token` trong header: `Authorization: Bearer <token>`
4. API Gateway Cognito Authorizer validate token
5. Lambda handler extract `user_id` từ `event["requestContext"]["authorizer"]["claims"]`

## Deployment

### Prerequisites

```bash
# Install AWS SAM CLI
brew install aws-sam-cli

# Install Python dependencies
pip install -r requirements.txt
```

### Deploy Stacks

```bash
# 1. Deploy auth stack (Cognito)
sam deploy --template-file config/auth-base.yaml --stack-name lexi-auth-base

# 2. Deploy database stack (DynamoDB)
sam deploy --template-file config/database.yaml --stack-name lexi-database

# 3. Deploy main application
sam build
sam deploy --guided
```

### Environment Variables

Lambda functions sử dụng các environment variables:

- `LEXI_TABLE_NAME`: DynamoDB table name
- `COGNITO_USER_POOL_ID`: Cognito User Pool ID
- `COGNITO_APP_CLIENT_ID`: Cognito App Client ID
- `SPEAKING_AUDIO_BUCKET_NAME`: S3 bucket for audio files
- `LOG_LEVEL`: Logging level (INFO, DEBUG, ERROR)

## API Gateway Configuration

### REST API

- **Stage**: Prod
- **Base URL**: `https://mnjxcw3o1e.execute-api.ap-southeast-1.amazonaws.com/Prod`
- **Authorizer**: Cognito User Pool Authorizer (default)
- **CORS**: Enabled for `localhost:3000` and `ngoctin.me`

### WebSocket API

- **Stage**: Prod
- **URL**: `wss://zxb7hmt5c4.execute-api.ap-southeast-1.amazonaws.com/Prod`
- **Routes**: `$connect`, `$disconnect`, `$default`
- **Handler**: `websocket_handler.py`

## Monitoring & Logging

- **CloudWatch Logs**: Tất cả Lambda logs
- **CloudWatch Metrics**: Lambda invocations, errors, duration
- **X-Ray**: Distributed tracing (enabled)

### Log Format

```json
{
  "timestamp": "2026-04-30T10:00:00Z",
  "level": "INFO",
  "message": "Handler invoked",
  "context": {
    "user_id": "user123",
    "handler": "GetProfileHandler"
  }
}
```

## Security

- ✅ Cognito authentication for all endpoints (except `/scenarios`)
- ✅ Admin role check for `/admin/*` endpoints
- ✅ DynamoDB encryption at rest
- ✅ S3 bucket encryption (AES256)
- ✅ HTTPS only (TLS 1.2+)
- ✅ CORS restricted to known domains
- ✅ IAM least privilege principle

## Performance

- **Lambda Cold Start**: ~500ms (Python 3.12)
- **Lambda Warm**: ~50-100ms
- **DynamoDB**: Single-digit millisecond latency
- **API Gateway**: ~10ms overhead

### Optimization

- Singleton pattern for dependencies (reuse across invocations)
- DynamoDB batch operations where possible
- S3 presigned URLs for audio files
- Lambda MemorySize: 256MB (default), 512MB (WebSocket)

## Cost Estimation

**Monthly cost** (assuming 10,000 users, 100,000 requests/month):

- Lambda: ~$5
- API Gateway: ~$3.50
- DynamoDB: ~$2.50 (on-demand)
- Cognito: Free (< 50,000 MAU)
- S3: ~$1
- **Total**: ~$12/month

## Future Improvements

- [ ] Add rate limiting (API Gateway throttling)
- [ ] Add caching (API Gateway cache or ElastiCache)
- [ ] Add monitoring dashboard (CloudWatch Dashboard)
- [ ] Add CI/CD pipeline (GitHub Actions)
- [ ] Add integration tests
- [ ] Add API versioning
