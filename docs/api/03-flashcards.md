# Flashcards ✅ VERIFIED

## Overview

Hệ thống flashcard với thuật toán spaced repetition để học từ vựng hiệu quả.

## ⚠️ Response Format Đặc Biệt

**Khác với các module khác**, Flashcard API sử dụng format:

```json
{
  "success": true,
  "data": { ... }
}
```

---

## 1. Create Flashcard ✅

**POST** `/flashcards`

### Request
```json
{
  "word": "apple"
}
```

### Response (201)
```json
{
  "flashcard_id": "fc_123",
  "word": "apple",
  "meaning": "quả táo",
  "example": "I eat an apple",
  "created_at": "2026-04-30T10:00:00Z",
  "next_review_at": "2026-04-30T10:00:00Z"
}
```

---

## 2. List Flashcards ✅

**GET** `/flashcards?limit=20&last_key=xxx`

### Query Parameters
- `limit` (number, optional): 1-100, default 20
- `last_key` (string, optional): Base64 encoded pagination key

### Response (200)
```json
{
  "success": true,
  "data": {
    "cards": [
      {
        "flashcard_id": "fc_123",
        "word": "apple",
        "translation_vi": "quả táo",
        "phonetic": "/ˈæp.əl/",
        "audio_url": "https://...",
        "example_sentence": "I eat an apple",
        "review_count": 5,
        "interval_days": 7,
        "next_review_at": "2026-05-07T10:00:00Z",
        "last_reviewed_at": "2026-04-30T10:00:00Z"
      }
    ],
    "next_key": "base64_encoded_key"
  }
}
```

---

## 3. Search Flashcards ✅

**GET** `/flashcards?word_prefix=app&min_interval=0&max_interval=365&maturity_level=learning`

### Query Parameters
- `word_prefix` (string): Tìm từ bắt đầu với prefix
- `min_interval` (number): Interval tối thiểu (days)
- `max_interval` (number): Interval tối đa (days)
- `maturity_level` (string): `new`, `learning`, `mature`
- `cursor` (string): Pagination cursor
- `limit` (number): 1-100, default 50

### Response (200)
```json
{
  "success": true,
  "data": {
    "flashcards": [...],
    "next_cursor": "cursor_string",
    "total_count": 150,
    "count": 50
  }
}
```

---

## 4. List Due Cards ✅

**GET** `/flashcards/due`

### Response (200)
```json
{
  "success": true,
  "data": {
    "cards": [
      {
        "flashcard_id": "fc_123",
        "word": "apple",
        "translation_vi": "quả táo",
        "phonetic": "/ˈæp.əl/",
        "audio_url": "https://...",
        "example_sentence": "I eat an apple",
        "review_count": 5,
        "interval_days": 7,
        "next_review_at": "2026-04-30T10:00:00Z",
        "last_reviewed_at": "2026-04-29T10:00:00Z"
      }
    ]
  }
}
```

---

## 5. Get Flashcard ✅

**GET** `/flashcards/{flashcard_id}`

### Response (200)
```json
{
  "success": true,
  "data": {
    "flashcard_id": "fc_123",
    "word": "apple",
    "translation_vi": "quả táo",
    "phonetic": "/ˈæp.əl/",
    "audio_url": "https://...",
    "example_sentence": "I eat an apple",
    "review_count": 5,
    "interval_days": 7,
    "last_reviewed_at": "2026-04-30T10:00:00Z",
    "next_review_at": "2026-05-07T10:00:00Z",
    "source_session_id": "sess_abc",
    "source_turn_index": 3
  }
}
```

---

## 6. Update Flashcard ✅

**PATCH** `/flashcards/{flashcard_id}`

### Request
```json
{
  "translation_vi": "quả táo (updated)",
  "phonetic": "/ˈæp.əl/",
  "audio_url": "https://...",
  "example_sentence": "I eat an apple every day"
}
```

**Fields** (tất cả optional, ít nhất 1 field):
- `translation_vi` (string)
- `phonetic` (string)
- `audio_url` (string)
- `example_sentence` (string)

### Response (200)
```json
{
  "success": true,
  "data": {
    "flashcard_id": "fc_123",
    "word": "apple",
    "translation_vi": "quả táo (updated)",
    "phonetic": "/ˈæp.əl/",
    "audio_url": "https://...",
    "example_sentence": "I eat an apple every day",
    "ease_factor": 2.5,
    "repetition_count": 5,
    "interval_days": 7,
    "next_review_at": "2026-05-07T10:00:00Z"
  }
}
```

---

## 7. Delete Flashcard ✅

**DELETE** `/flashcards/{flashcard_id}`

### Response (204)
```
No Content
```

**Errors**:
- 403: Forbidden (không phải owner)
- 404: Flashcard not found

---

## 8. Review Flashcard ✅

**POST** `/flashcards/{flashcard_id}/review`

### Request
```json
{
  "rating": "good"
}
```

**Rating values**:
- `"forgot"` - Quên hoàn toàn
- `"hard"` - Khó nhớ
- `"good"` - Nhớ tốt
- `"easy"` - Dễ dàng

### Response (200)
```json
{
  "success": true,
  "data": {
    "flashcard_id": "fc_123",
    "word": "apple",
    "interval_days": 14,
    "review_count": 6,
    "last_reviewed_at": "2026-04-30T10:00:00Z",
    "next_review_at": "2026-05-14T10:00:00Z"
  }
}
```

---

## 9. Get Statistics ✅

**GET** `/flashcards/statistics`

### Response (200)
```json
{
  "success": true,
  "data": {
    "total_count": 150,
    "due_today_count": 12,
    "new_count": 20,
    "learning_count": 80,
    "mature_count": 50
  }
}
```

---

## 10. Export Flashcards ⚠️

**GET** `/flashcards/export?format=csv`

**Status**: Handler exists but not verified

---

## 11. Import Flashcards ⚠️

**POST** `/flashcards/import`

**Status**: Handler exists but not verified

---

## Key Differences from Other Modules

1. **Response format**: `{success: true, data: {...}}` thay vì direct body
2. **Rating system**: String values (`forgot`, `hard`, `good`, `easy`) thay vì numbers
3. **Field names**: `translation_vi` thay vì `back`, `meaning`
4. **Search support**: Có search parameters không documented trước đây
5. **Pagination**: Dùng base64 encoded `last_key` thay vì simple cursor

## Spaced Repetition Algorithm

- Dựa trên rating để tính `interval_days`
- `forgot` → reset về đầu
- `hard`, `good`, `easy` → tăng interval
- `next_review_at` được tính tự động
