# Authentication & Onboarding

## Overview

Module này xử lý việc hoàn tất thông tin người dùng sau khi đăng ký thành công qua Cognito.

## Endpoints

### Complete Onboarding

Hoàn tất thông tin ban đầu cho user mới (native_language, proficiency_level).

**Endpoint**: `POST /onboarding/complete`

**Authentication**: Required (Cognito JWT)

**Handler**: `complete_onboarding_handler.py`

#### Request Body

```json
{
  "display_name": "Nguyen Van A",
  "avatar_url": "https://...",
  "current_level": "A2",
  "target_level": "B2"
}
```

**Fields**:
- `display_name` (string, required): Tên hiển thị
- `avatar_url` (string, optional): URL avatar
- `current_level` (string, required): Trình độ hiện tại (CEFR)
  - Giá trị: `"A1"`, `"A2"`, `"B1"`, `"B2"`, `"C1"`, `"C2"`
- `target_level` (string, required): Trình độ mục tiêu (CEFR)
  - Giá trị: `"A1"`, `"A2"`, `"B1"`, `"B2"`, `"C1"`, `"C2"`

#### Response

**Success (200)**:
```json
{
  "statusCode": 200,
  "body": {
    "is_success": true,
    "message": "Onboarding hoàn tất",
    "profile": {
      "user_id": "user123",
      "display_name": "Nguyen Van A",
      "avatar_url": "https://...",
      "current_level": "A2",
      "target_level": "B2",
      "is_new_user": false,
      "role": "user",
      "is_active": true,
      "current_streak": 0,
      "total_words_learned": 0
    }
  }
}
```

**Error (400)**:
```json
{
  "statusCode": 400,
  "body": {
    "error": "Invalid request data: ..."
  }
}
```

**Validation Errors**:
- `"Tên hiển thị không được để trống"`
- `"Trình độ hiện tại không hợp lệ"`
- `"Trình độ mục tiêu không hợp lệ"`
- `"URL avatar không hợp lệ"`

#### Example

```bash
curl -X POST https://mnjxcw3o1e.execute-api.ap-southeast-1.amazonaws.com/Prod/onboarding/complete \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Nguyen Van A",
    "avatar_url": "https://example.com/avatar.jpg",
    "current_level": "A2",
    "target_level": "B2"
  }'
```

## Business Logic

1. Validate request body (display_name, current_level, target_level, avatar_url)
2. Get user profile from DynamoDB
3. Update profile với thông tin onboarding
4. Set `is_new_user = false`
5. Save to DynamoDB
6. Return success response với full profile

## Validation Rules

- `display_name`: Không được để trống
- `current_level`: Phải là CEFR level hợp lệ (A1-C2)
- `target_level`: Phải là CEFR level hợp lệ (A1-C2)
- `avatar_url`: Phải là URL hợp lệ (nếu có)

## Notes

- Endpoint này được gọi ngay sau khi user đăng ký thành công
- Frontend nên redirect user đến onboarding flow nếu `is_new_user = true`
- Sau khi complete, `is_new_user` sẽ được set thành `false`
- Response trả về full profile để frontend có thể update state
