# Lexi BE — API Reference

**Base URL:** `https://htv5bybfsc.execute-api.ap-southeast-1.amazonaws.com/Prod`  
**Region:** `ap-southeast-1`  
**Auth:** Cognito JWT — header `Authorization: Bearer <id_token>`  
**Content-Type:** `application/json`

---

## Mục lục

1. [Auth (Cognito Trigger)](#1-auth)
2. [Onboarding](#2-onboarding)
3. [Profile](#3-profile)
4. [Scenarios (Public)](#4-scenarios)
5. [Sessions (Speaking)](#5-sessions)
6. [Vocabulary](#6-vocabulary)
7. [Flashcards](#7-flashcards)
8. [Admin](#8-admin)

---

## 1. Auth

Auth được xử lý hoàn toàn qua **AWS Cognito** — không có REST endpoint riêng.  
Sau khi user xác nhận email, Cognito trigger `PostConfirmation` tự động tạo profile trong DynamoDB.

| Flow | Cognito API |
|------|-------------|
| Đăng ký | `signUp` |
| Xác nhận email | `confirmSignUp` |
| Đăng nhập | `initiateAuth` (USER_PASSWORD_AUTH / USER_SRP_AUTH) |
| Refresh token | `initiateAuth` (REFRESH_TOKEN_AUTH) |

**User Pool ID:** `ap-southeast-1_SGJAgKdrq`  
**Client ID:** `1b87am8h2lh4atll7cbqc22ago`

---

## 2. Onboarding

### POST /onboarding/complete

Hoàn tất thông tin ban đầu cho user mới (sau lần đăng nhập đầu tiên).

**Auth:** Required

**Request Body:**
```json
{
  "display_name": "Ngọc Tín",
  "current_level": "A2",
  "target_level": "B2",
  "avatar_url": "https://api.dicebear.com/9.x/lorelei/svg?seed=Aria"
}
```

| Field | Type | Required | Mô tả |
|-------|------|----------|-------|
| `display_name` | string | Yes | Tên hiển thị |
| `current_level` | string | Yes | Trình độ hiện tại: `A1` `A2` `B1` `B2` `C1` `C2` |
| `target_level` | string | Yes | Trình độ mục tiêu: `A1` `A2` `B1` `B2` `C1` `C2` |
| `avatar_url` | string | No | URL ảnh đại diện |

**Response 200:**
```json
{
  "success": true,
  "message": "Onboarding hoàn tất",
  "profile": { ... }
}
```

**Errors:** `400` thiếu field / `404` profile không tồn tại / `401` unauthorized

---

## 3. Profile

### GET /profile

Lấy thông tin hồ sơ của user đang đăng nhập.

**Auth:** Required

**Response 200:**
```json
{
  "user_id": "uuid-cognito-sub",
  "email": "user@example.com",
  "display_name": "Ngọc Tín",
  "avatar_url": "https://...",
  "current_level": "A2",
  "target_level": "B2",
  "current_streak": 5,
  "total_words_learned": 42,
  "role": "USER",
  "is_active": true,
  "is_new_user": false
}
```

**Errors:** `404` profile không tồn tại / `401` unauthorized

---

### PATCH /profile

Cập nhật thông tin hồ sơ.

**Auth:** Required

**Request Body** (tất cả fields đều optional):
```json
{
  "display_name": "Tên mới",
  "avatar_url": "https://...",
  "current_level": "B1",
  "target_level": "C1",
  "is_new_user": false
}
```

| Field | Type | Mô tả |
|-------|------|-------|
| `display_name` | string | Tên hiển thị |
| `avatar_url` | string | URL ảnh đại diện |
| `current_level` | string | `A1` `A2` `B1` `B2` `C1` `C2` |
| `target_level` | string | `A1` `A2` `B1` `B2` `C1` `C2` |
| `is_new_user` | boolean | Đánh dấu đã hoàn thành onboarding |

**Response 200:**
```json
{
  "is_success": true,
  "message": "Cập nhật thành công"
}
```

**Errors:** `400` dữ liệu không hợp lệ / `422` lỗi nghiệp vụ / `401` unauthorized

---

## 4. Scenarios

### GET /scenarios

Lấy danh sách kịch bản luyện nói đang hoạt động. **Không cần auth.**

**Auth:** None

**Response 200:**
```json
{
  "success": true,
  "scenarios": [
    {
      "scenario_id": "01JXXX...",
      "scenario_title": "Đặt đồ ăn tại nhà hàng",
      "context": "Bạn đang ở một nhà hàng...",
      "roles": ["customer", "waiter"],
      "goals": ["Order food", "Ask for the bill"],
      "is_active": true,
      "usage_count": 12,
      "difficulty_level": "A2",
      "order": 1
    }
  ]
}
```

---

## 5. Sessions (Speaking)

### POST /sessions

Tạo phiên luyện nói mới.

**Auth:** Required

**Request Body:**
```json
{
  "scenario_id": "01JXXX...",
  "learner_role_id": "customer",
  "ai_role_id": "waiter",
  "ai_gender": "female",
  "level": "B1",
  "selected_goals": ["Order food", "Ask for the bill"],
  "prompt_snapshot": ""
}
```

| Field | Type | Required | Mô tả |
|-------|------|----------|-------|
| `scenario_id` | string | Yes | ID kịch bản |
| `learner_role_id` | string | No | Vai của người học |
| `ai_role_id` | string | No | Vai của AI |
| `ai_gender` | string | No | `female` (default) hoặc `male` |
| `level` | string | No | `A1`–`C2`, default `B1` |
| `selected_goals` | array | No | Danh sách mục tiêu chọn |
| `prompt_snapshot` | string | No | Snapshot prompt (để trống) |

**Response 201:**
```json
{
  "success": true,
  "session_id": "01JXXX...",
  "session": {
    "session_id": "...",
    "user_id": "...",
    "scenario_id": "...",
    "status": "ACTIVE",
    "turns": [],
    ...
  }
}
```

---

### GET /sessions

Lấy danh sách phiên luyện nói của user.

**Auth:** Required

**Query Params:**

| Param | Type | Default | Mô tả |
|-------|------|---------|-------|
| `limit` | integer | 10 | Số lượng sessions trả về |

**Response 200:**
```json
{
  "success": true,
  "sessions": [ { ... } ]
}
```

---

### GET /sessions/{session_id}

Lấy chi tiết một phiên luyện nói.

**Auth:** Required

**Response 200:**
```json
{
  "success": true,
  "session": {
    "session_id": "...",
    "status": "ACTIVE",
    "turns": [
      {
        "turn_index": 0,
        "speaker": "AI",
        "content": "Hello, welcome!",
        "translated_content": "Xin chào, chào mừng!",
        "audio_url": "https://...",
        "is_hint_used": false
      }
    ],
    "scoring": null
  }
}
```

**Errors:** `404` session không tồn tại

---

### POST /sessions/{session_id}/turns

Gửi lượt nói của người học.

**Auth:** Required

**Request Body:**
```json
{
  "text": "I'd like to order a burger please.",
  "is_hint_used": false,
  "audio_url": null
}
```

| Field | Type | Required | Mô tả |
|-------|------|----------|-------|
| `text` | string | Yes | Nội dung lượt nói (transcript) |
| `is_hint_used` | boolean | No | Có dùng gợi ý không |
| `audio_url` | string | No | URL audio nếu có |

**Response 200:**
```json
{
  "success": true,
  "session": { ... },
  "user_turn": {
    "turn_index": 1,
    "speaker": "USER",
    "content": "I'd like to order a burger please."
  },
  "ai_turn": {
    "turn_index": 2,
    "speaker": "AI",
    "content": "Great choice! Would you like fries with that?",
    "audio_url": "https://..."
  },
  "analysis_keywords": ["order", "burger"]
}
```

---

### POST /sessions/{session_id}/complete

Kết thúc phiên và tính điểm.

**Auth:** Required

**Request Body:** (empty)

**Response 200:**
```json
{
  "success": true,
  "session": { "status": "COMPLETED", ... },
  "scoring": {
    "fluency": 75,
    "pronunciation": 80,
    "grammar": 70,
    "vocabulary": 85,
    "overall": 77,
    "feedback": "Good job! Work on grammar..."
  }
}
```

---

## 6. Vocabulary

### POST /vocabulary/translate

Dịch một từ/cụm từ, có thể kèm ngữ cảnh câu.

**Auth:** Required

**Request Body:**
```json
{
  "word": "burger",
  "sentence": "I'd like to order a burger please."
}
```

| Field | Type | Required | Mô tả |
|-------|------|----------|-------|
| `word` | string | Yes | Từ cần dịch |
| `sentence` | string | No | Câu ngữ cảnh để dịch chính xác hơn |

**Response 200:**
```json
{
  "word": "burger",
  "translation_vi": "bánh mì kẹp thịt",
  "definition_vi": "Một loại bánh sandwich...",
  "phonetic": "/ˈbɜːɡər/",
  "audio_url": "https://...",
  "example_sentence": "I'd like to order a burger."
}
```

**Errors:** `404` từ không tìm thấy / `502` lỗi dịch vụ dịch thuật

---

### POST /vocabulary/translate-sentence

Dịch toàn bộ một câu.

**Auth:** Required

**Request Body:**
```json
{
  "sentence": "Would you like fries with that?"
}
```

**Response 200:**
```json
{
  "sentence": "Would you like fries with that?",
  "translation_vi": "Bạn có muốn khoai tây chiên không?"
}
```

---

## 7. Flashcards

### POST /flashcards

Tạo flashcard mới.

**Auth:** Required

**Request Body:**
```json
{
  "vocab": "burger",
  "vocab_type": "noun",
  "translation_vi": "bánh mì kẹp thịt",
  "definition_vi": "Một loại bánh sandwich với thịt bò",
  "phonetic": "/ˈbɜːɡər/",
  "audio_url": "",
  "example_sentence": "I'd like to order a burger.",
  "source_session_id": "01JXXX...",
  "source_turn_index": 1
}
```

| Field | Type | Required | Mô tả |
|-------|------|----------|-------|
| `vocab` | string | Yes | Từ/cụm từ |
| `vocab_type` | string | No | `noun` `verb` `adj` ... (default: `noun`) |
| `translation_vi` | string | No | Nghĩa tiếng Việt |
| `definition_vi` | string | No | Định nghĩa tiếng Việt |
| `phonetic` | string | No | Phiên âm IPA |
| `audio_url` | string | No | URL audio |
| `example_sentence` | string | No | Câu ví dụ |
| `source_session_id` | string | No | Session nguồn |
| `source_turn_index` | integer | No | Turn index nguồn |

**Response 201:**
```json
{
  "flashcard_id": "01JXXX...",
  "word": "burger",
  "message": "Flashcard đã được tạo thành công"
}
```

---

### GET /flashcards

Lấy danh sách tất cả flashcard của user (có phân trang).

**Auth:** Required

**Query Params:**

| Param | Type | Default | Mô tả |
|-------|------|---------|-------|
| `limit` | integer | 20 | Số lượng (max 100) |
| `last_key` | string | - | Base64-encoded JSON cursor để phân trang |

**Response 200:**
```json
{
  "cards": [
    {
      "flashcard_id": "01JXXX...",
      "word": "burger",
      "translation_vi": "bánh mì kẹp thịt",
      "definition_vi": "...",
      "phonetic": "/ˈbɜːɡər/",
      "audio_url": "",
      "example_sentence": "...",
      "review_count": 3,
      "interval_days": 4,
      "difficulty": 0.3,
      "next_review_at": "2026-04-25T10:00:00",
      "last_reviewed_at": "2026-04-23T10:00:00"
    }
  ],
  "next_key": "eyJQSyI6..."
}
```

---

### GET /flashcards/due

Lấy danh sách flashcard đến hạn ôn tập hôm nay (SRS).

**Auth:** Required

**Response 200:**
```json
{
  "cards": [ { ... } ]
}
```

---

### GET /flashcards/{flashcard_id}

Lấy chi tiết một flashcard.

**Auth:** Required

**Response 200:**
```json
{
  "flashcard_id": "01JXXX...",
  "word": "burger",
  "translation_vi": "bánh mì kẹp thịt",
  "definition_vi": "...",
  "phonetic": "/ˈbɜːɡər/",
  "audio_url": "",
  "example_sentence": "...",
  "review_count": 3,
  "interval_days": 4,
  "difficulty": 0.3,
  "last_reviewed_at": "2026-04-23T10:00:00",
  "next_review_at": "2026-04-25T10:00:00",
  "source_session_id": "01JXXX...",
  "source_turn_index": 1
}
```

**Errors:** `404` không tìm thấy / `403` không có quyền

---

### POST /flashcards/{flashcard_id}/review

Đánh giá mức độ nhớ và cập nhật lịch ôn tập (thuật toán SRS).

**Auth:** Required

**Request Body:**
```json
{
  "rating": "good"
}
```

| `rating` | Ý nghĩa |
|----------|---------|
| `forgot` | Quên hoàn toàn — reset interval |
| `hard` | Khó nhớ — tăng interval chậm |
| `good` | Nhớ được — tăng interval bình thường |
| `easy` | Dễ — tăng interval nhanh |

**Response 200:**
```json
{
  "flashcard_id": "01JXXX...",
  "word": "burger",
  "interval_days": 7,
  "review_count": 4,
  "last_reviewed_at": "2026-04-23T10:30:00",
  "next_review_at": "2026-04-30T10:30:00"
}
```

**Errors:** `400` rating không hợp lệ / `404` không tìm thấy / `403` không có quyền

---

## 8. Admin

> Tất cả admin endpoints yêu cầu user có `role = ADMIN` trong DynamoDB.  
> Trả về `403 Forbidden` nếu role không phải ADMIN.

### GET /admin/users

Lấy danh sách tất cả users.

**Auth:** Required + ADMIN role

**Query Params:**

| Param | Type | Default | Mô tả |
|-------|------|---------|-------|
| `limit` | integer | 20 | Số lượng (max 100) |
| `last_key` | string | - | JSON string cursor phân trang |

**Response 200:**
```json
{
  "users": [
    {
      "user_id": "...",
      "email": "user@example.com",
      "display_name": "...",
      "role": "USER",
      "is_active": true,
      "is_new_user": false,
      "current_level": "B1",
      "target_level": "C1"
    }
  ],
  "next_key": "{\"PK\": ...}"
}
```

---

### PATCH /admin/users/{user_id}

Cập nhật thông tin user (admin only).

**Auth:** Required + ADMIN role

**Request Body:**
```json
{
  "is_active": true,
  "current_level": "B2",
  "target_level": "C1"
}
```

**Response 200:**
```json
{
  "success": true,
  "user": { ... }
}
```

**Errors:** `404` user không tồn tại

---

### GET /admin/scenarios

Lấy tất cả kịch bản (kể cả inactive).

**Auth:** Required + ADMIN role

**Response 200:**
```json
{
  "scenarios": [ { ... } ]
}
```

---

### POST /admin/scenarios

Tạo kịch bản mới.

**Auth:** Required + ADMIN role

**Request Body:**
```json
{
  "scenario_title": "Đặt đồ ăn tại nhà hàng",
  "context": "Bạn đang ở một nhà hàng Việt Nam...",
  "roles": ["customer", "waiter"],
  "goals": ["Order food", "Ask for the bill"],
  "difficulty_level": "A2",
  "order": 1,
  "notes": "Ghi chú nội bộ",
  "is_active": true
}
```

**Response 201:**
```json
{
  "success": true,
  "scenario": { ... }
}
```

---

### PATCH /admin/scenarios/{scenario_id}

Cập nhật kịch bản (tất cả fields optional).

**Auth:** Required + ADMIN role

**Request Body:** (bất kỳ field nào từ POST /admin/scenarios)

**Response 200:**
```json
{
  "success": true,
  "scenario": { ... }
}
```

**Errors:** `404` scenario không tồn tại

---

## Error Format chung

```json
{
  "error": "Mô tả lỗi"
}
```

| HTTP Code | Ý nghĩa |
|-----------|---------|
| 400 | Bad Request — dữ liệu không hợp lệ |
| 401 | Unauthorized — thiếu hoặc sai token |
| 403 | Forbidden — không đủ quyền |
| 404 | Not Found |
| 422 | Unprocessable — lỗi nghiệp vụ |
| 500 | Internal Server Error |
| 502 | Bad Gateway — lỗi dịch vụ bên ngoài (AWS Translate, Bedrock) |
