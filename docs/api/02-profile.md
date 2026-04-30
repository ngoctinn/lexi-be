# User Profile

## Overview

Module quản lý thông tin cá nhân của người dùng.

## Endpoints

### Get Profile

Lấy thông tin profile của user hiện tại.

**Endpoint**: `GET /profile`

**Authentication**: Required

**Handler**: `get_profile_handler.py`

#### Response

**Success (200)**:
```json
{
  "statusCode": 200,
  "body": {
    "user_id": "user123",
    "email": "user@example.com",
    "display_name": "Nguyen Van A",
    "avatar_url": "https://...",
    "current_level": "B1",
    "target_level": "C1",
    "current_streak": 7,
    "total_words_learned": 150,
    "role": "LEARNER",
    "is_active": true,
    "is_new_user": false
  }
}
```

**Error (404)**:
```json
{
  "statusCode": 404,
  "body": {
    "error": "User not found"
  }
}
```

#### Example

```bash
curl -X GET https://mnjxcw3o1e.execute-api.ap-southeast-1.amazonaws.com/Prod/profile \
  -H "Authorization: Bearer <token>"
```

---

### Update Profile

Cập nhật thông tin profile.

**Endpoint**: `PATCH /profile`

**Authentication**: Required

**Handler**: `update_profile_handler.py`

#### Request Body

```json
{
  "display_name": "Nguyen Van B",
  "avatar_url": "https://...",
  "current_level": "B2",
  "target_level": "C1"
}
```

**Fields** (tất cả optional):
- `display_name` (string): Tên hiển thị
- `avatar_url` (string): URL avatar
- `current_level` (string): Trình độ hiện tại (A1/A2/B1/B2/C1/C2)
- `target_level` (string): Trình độ mục tiêu (A1/A2/B1/B2/C1/C2)

#### Response

**Success (200)**:
```json
{
  "statusCode": 200,
  "body": {
    "user_id": "user123",
    "email": "user@example.com",
    "display_name": "Nguyen Van B",
    "avatar_url": "https://...",
    "current_level": "B2",
    "target_level": "C1",
    "current_streak": 7,
    "total_words_learned": 150,
    "role": "LEARNER",
    "is_active": true,
    "is_new_user": false
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

#### Example

```bash
curl -X PATCH https://mnjxcw3o1e.execute-api.ap-southeast-1.amazonaws.com/Prod/profile \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Nguyen Van B",
    "current_level": "B2",
    "target_level": "C1"
  }'
```

## Notes

- User chỉ có thể update profile của chính mình
- `user_id` được extract tự động từ JWT token
- Không thể thay đổi `email`, `role`, `is_active` qua endpoint này
- `current_streak` và `total_words_learned` được tính tự động bởi hệ thống
- Response luôn trả về full profile sau khi update
