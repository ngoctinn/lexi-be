# Lexi API Documentation Index

**Last Updated**: April 25, 2026  
**API Version**: 2.0  
**Status**: Production

---

## 📚 Documentation Files

### 1. **API_DOCUMENTATION.md** (Main Reference)
Complete API reference with all endpoints, request/response formats, and error handling.

**Contents**:
- Authentication & token management
- Response format standards
- Error codes & HTTP status codes
- 11 endpoint categories:
  - Onboarding
  - Profile Management
  - Vocabulary Translation
  - Flashcard Learning
  - Scenario Browsing
  - Speaking Sessions
  - WebSocket Real-time
  - Admin Operations
- AI Model Information (Amazon Nova Micro)
- Rate Limiting
- Troubleshooting Guide

**Best for**: Developers implementing API integration, API reference lookup

---

### 2. **API_QUICK_REFERENCE.md** (Cheat Sheet)
Quick curl examples and common patterns for rapid development.

**Contents**:
- Quick curl commands for all endpoints
- Authentication setup
- Common error codes
- Proficiency levels
- Useful links & endpoints
- Testing tips

**Best for**: Quick lookups, copy-paste examples, testing

---

### 3. **API_EXAMPLES.md** (Detailed Workflows)
Real-world examples and complete workflows with step-by-step instructions.

**Contents**:
- Complete user journey (registration → onboarding → profile)
- Speaking practice workflow (7 steps with full responses)
- Vocabulary learning workflow
- Admin operations (user & scenario management)
- Error handling examples
- WebSocket real-time examples
- Performance metrics

**Best for**: Understanding workflows, learning best practices, integration examples

---

## 🚀 Quick Start

### Get Started in 5 Minutes

1. **Get Authentication Token**
   ```bash
   TOKEN=$(aws cognito-idp admin-initiate-auth \
     --user-pool-id ap-southeast-1_VhFl3NxNy \
     --client-id 4krhiauplon0iei1f5r4cgpq7i \
     --auth-flow ADMIN_NO_SRP_AUTH \
     --auth-parameters USERNAME=user@example.com,PASSWORD=password \
     --region ap-southeast-1 \
     --query 'AuthenticationResult.IdToken' \
     --output text)
   ```

2. **Test an Endpoint**
   ```bash
   curl -X GET https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod/profile \
     -H "Authorization: Bearer $TOKEN"
   ```

3. **Read the Docs**
   - Start with **API_QUICK_REFERENCE.md** for quick examples
   - Use **API_DOCUMENTATION.md** for detailed reference
   - Check **API_EXAMPLES.md** for complete workflows

---

## 📋 Endpoint Categories

### Public Endpoints (No Auth Required)
- `GET /scenarios` - List available speaking scenarios

### User Endpoints (Auth Required)
- **Onboarding**: `POST /onboarding/complete`
- **Profile**: `GET /profile`, `PATCH /profile`
- **Vocabulary**: `POST /vocabulary/translate`, `POST /vocabulary/translate-sentence`
- **Flashcards**: `POST /flashcards`, `GET /flashcards`, `GET /flashcards/{id}`, `GET /flashcards/due`, `POST /flashcards/{id}/review`
- **Speaking**: `POST /sessions`, `GET /sessions`, `GET /sessions/{id}`, `POST /sessions/{id}/turns`, `POST /sessions/{id}/complete`
- **WebSocket**: `wss://...` (real-time)

### Admin Endpoints (Admin Auth Required)
- **Users**: `GET /admin/users`, `PATCH /admin/users/{id}`
- **Scenarios**: `GET /admin/scenarios`, `POST /admin/scenarios`, `PATCH /admin/scenarios/{id}`

---

## 🔐 Authentication

### Cognito Configuration
- **User Pool ID**: `ap-southeast-1_VhFl3NxNy`
- **Client ID**: `4krhiauplon0iei1f5r4cgpq7i`
- **Region**: `ap-southeast-1` (Singapore)

### Token Usage
Include JWT token in `Authorization` header:
```bash
Authorization: Bearer <JWT_TOKEN>
```

---

## 🤖 AI Model

### Amazon Nova Micro
- **Model ID**: `apac.amazon.nova-micro-v1:0` (APAC inference profile)
- **Region**: ap-southeast-1 (Singapore)
- **Use Cases**:
  - Conversation generation for speaking practice
  - Performance scoring and feedback
  - Contextual hint generation

### Proficiency Levels
| Level | Model | Max Tokens | Temperature | Fallback |
|-------|-------|-----------|-------------|----------|
| A1 | Micro | 40 | 0.6 | None |
| A2 | Micro | 60 | 0.65 | None |
| B1 | Micro | 100 | 0.7 | Lite (5%) |
| B2 | Micro | 150 | 0.75 | Lite (10%) |
| C1 | Micro | 200 | 0.8 | Pro (30%) |
| C2 | Micro | 250 | 0.85 | Pro (40%) |

---

## 🌐 Base URLs

### REST API
```
https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod
```

### WebSocket
```
wss://no8fa2u3qg.execute-api.ap-southeast-1.amazonaws.com/Prod
```

---

## 📊 Response Format

### Success Response
```json
{
  "success": true,
  "message": "Success",
  "data": {
    // Response data
  }
}
```

### Error Response
```json
{
  "success": false,
  "message": "Error message",
  "error": "ERROR_CODE"
}
```

### HTTP Status Codes
- `200 OK` - Request successful
- `201 Created` - Resource created
- `400 Bad Request` - Invalid request
- `401 Unauthorized` - Authentication failed
- `403 Forbidden` - Permission denied
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

---

## 🔍 Common Error Codes

| Code | Meaning |
|------|---------|
| `BAD_REQUEST` | Invalid JSON or missing fields |
| `VALIDATION_ERROR` | Data validation failed |
| `NOT_FOUND` | Resource not found |
| `UNAUTHORIZED` | Authentication failed |
| `FORBIDDEN` | Permission denied |
| `SERVICE_ERROR` | External service error |
| `SUBMISSION_FAILED` | Turn submission failed |
| `COMPLETION_FAILED` | Session completion failed |

---

## 📖 Documentation Map

```
API_INDEX.md (You are here)
├── API_DOCUMENTATION.md
│   ├── Authentication
│   ├── Response Format
│   ├── Error Handling
│   ├── Onboarding Endpoints
│   ├── Profile Endpoints
│   ├── Vocabulary Endpoints
│   ├── Flashcard Endpoints
│   ├── Scenario Endpoints
│   ├── Speaking Session Endpoints
│   ├── WebSocket Endpoints
│   ├── Admin Endpoints
│   ├── AI Model Information
│   ├── Rate Limiting
│   └── Troubleshooting
├── API_QUICK_REFERENCE.md
│   ├── Authentication
│   ├── Onboarding
│   ├── Profile
│   ├── Vocabulary
│   ├── Flashcards
│   ├── Scenarios
│   ├── Speaking Sessions
│   ├── WebSocket
│   ├── Admin
│   ├── Response Format
│   ├── Error Codes
│   ├── Proficiency Levels
│   └── Testing
└── API_EXAMPLES.md
    ├── Complete User Journey
    ├── Speaking Practice Workflow
    ├── Vocabulary Learning Workflow
    ├── Admin Operations
    ├── Error Handling Examples
    ├── WebSocket Real-time Examples
    └── Performance Metrics
```

---

## 🎯 Use Cases

### For Frontend Developers
1. Read **API_QUICK_REFERENCE.md** for quick examples
2. Use **API_EXAMPLES.md** for complete workflows
3. Reference **API_DOCUMENTATION.md** for detailed specs

### For Backend Developers
1. Start with **API_DOCUMENTATION.md** for complete reference
2. Check **API_EXAMPLES.md** for integration patterns
3. Use **API_QUICK_REFERENCE.md** for testing

### For DevOps/Infrastructure
1. Check base URLs and endpoints
2. Review authentication configuration
3. Monitor CloudWatch logs: `/aws/lambda/lexi-be-*`

### For QA/Testing
1. Use **API_QUICK_REFERENCE.md** for curl commands
2. Reference **API_EXAMPLES.md** for test scenarios
3. Check error codes in **API_DOCUMENTATION.md**

---

## 🔗 Related Documentation

- **AUTHENTICATION_FLOW.md** - Detailed authentication flow
- **CONVERSATION_ARCHITECTURE.md** - System architecture
- **NOVA_MIGRATION_COMPLETE.md** - Amazon Nova migration details
- **README.md** - Project overview

---

## 📞 Support

### Debugging
1. Check CloudWatch logs: `/aws/lambda/lexi-be-*`
2. Review error codes in **API_DOCUMENTATION.md**
3. Check **API_EXAMPLES.md** for error handling examples

### Common Issues
- **401 Unauthorized**: Token expired or invalid
- **422 Unprocessable Entity**: Missing required fields
- **500 Internal Server Error**: Check CloudWatch logs

### Performance
- **TTFT (Time To First Token)**: 250-280ms (Bedrock)
- **Latency**: 1150-1300ms (Bedrock)
- **Cost**: ~$0.0005 per turn

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | 2026-04-25 | Complete API documentation with Amazon Nova Micro |
| 1.0 | 2026-01-01 | Initial API documentation |

---

## 🚀 Next Steps

1. **Get Started**: Follow the Quick Start section above
2. **Explore**: Read through the documentation files
3. **Test**: Use curl examples from API_QUICK_REFERENCE.md
4. **Integrate**: Follow workflows in API_EXAMPLES.md
5. **Deploy**: Reference API_DOCUMENTATION.md for production

---

**Last Updated**: April 25, 2026  
**API Version**: 2.0  
**Status**: Production ✅
