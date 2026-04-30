# Lexi API Documentation

## Base URL

- **Production**: `https://mnjxcw3o1e.execute-api.ap-southeast-1.amazonaws.com/Prod`
- **WebSocket**: `wss://zxb7hmt5c4.execute-api.ap-southeast-1.amazonaws.com/Prod`

## Authentication

Tất cả các endpoint (trừ `/scenarios`) yêu cầu **Cognito JWT Token** trong header:

```
Authorization: Bearer <id_token>
```

API Gateway sử dụng Cognito Authorizer để xác thực tự động.

## API Modules

API được chia thành các module chức năng:

### 1. [Authentication & Onboarding](./01-auth-onboarding.md)
- Hoàn tất thông tin người dùng mới
- POST `/onboarding/complete`

### 2. [User Profile](./02-profile.md)
- Quản lý thông tin cá nhân
- GET `/profile`
- PATCH `/profile`

### 3. [Flashcards](./03-flashcards.md)
- Hệ thống flashcard với spaced repetition
- CRUD operations, review, statistics, import/export
- 10 endpoints

### 4. [Vocabulary](./04-vocabulary.md)
- Dịch từ vựng và câu
- POST `/vocabulary/translate`
- POST `/vocabulary/translate-sentence`

### 5. [Speaking Practice](./05-speaking.md)
- Luyện nói với AI qua WebSocket
- Session management
- 5 endpoints (REST + WebSocket)

### 6. [Scenarios](./06-scenarios.md)
- Danh sách kịch bản luyện tập (public)
- GET `/scenarios`

### 7. [Admin](./07-admin.md)
- Quản lý users và scenarios (admin only)
- 5 endpoints

## Response Format

### Success Response
```json
{
  "statusCode": 200,
  "body": {
    "data": { ... }
  }
}
```

### Error Response
```json
{
  "statusCode": 4xx/5xx,
  "body": {
    "error": "Error message",
    "code": "ERROR_CODE"
  }
}
```

## Common HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request (validation error)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (không có quyền admin)
- `404` - Not Found
- `500` - Internal Server Error

## Rate Limiting

Hiện tại chưa có rate limiting. Sẽ được thêm trong tương lai.

## CORS

API hỗ trợ CORS cho:
- `http://localhost:3000` (development)
- `https://ngoctin.me` (production)
