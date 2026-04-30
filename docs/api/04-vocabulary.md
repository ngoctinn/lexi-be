# Vocabulary

## Overview

Module dịch từ vựng và câu, sử dụng AWS Translate và Dictionary API.

## Endpoints

### 1. Translate Vocabulary

Dịch từ vựng với định nghĩa chi tiết, phiên âm, ví dụ.

**Endpoint**: `POST /vocabulary/translate`

**Handler**: `translate_vocabulary_handler.py`

**Authentication**: Required

#### Request Body

```json
{
  "word": "apple"
}
```

**Fields**:
- `word` (string, required): Từ cần dịch

#### Response

**Success (200)**:
```json
{
  "statusCode": 200,
  "body": {
    "word": "apple",
    "translation_vi": "quả táo",
    "phonetic": "/ˈæp.əl/",
    "audio_url": "https://...",
    "definitions": [
      {
        "part_of_speech": "noun",
        "definition_en": "a round fruit with firm white flesh",
        "definition_vi": "quả táo",
        "example_en": "I eat an apple every day",
        "example_vi": "Tôi ăn một quả táo mỗi ngày"
      }
    ],
    "synonyms": [
      {
        "en": "fruit",
        "vi": "trái cây"
      }
    ],
    "response_time_ms": 150,
    "cached": false
  }
}
```

**Error (404)**:
```json
{
  "statusCode": 404,
  "body": {
    "success": false,
    "message": "WORD_NOT_FOUND",
    "error": "WORD_NOT_FOUND"
  }
}
```

**Error (503)**:
```json
{
  "statusCode": 503,
  "body": {
    "success": false,
    "message": "DICTIONARY_SERVICE_ERROR",
    "error": "DICTIONARY_SERVICE_ERROR"
  }
}
```

**Error (400)**:
```json
{
  "statusCode": 400,
  "body": {
    "success": false,
    "message": "Invalid request data: ...",
    "error": "..."
  }
}
```

#### Example

```bash
curl -X POST https://mnjxcw3o1e.execute-api.ap-southeast-1.amazonaws.com/Prod/vocabulary/translate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "word": "apple"
  }'
```

---

### 2. Translate Sentence

Dịch câu hoàn chỉnh.

**Endpoint**: `POST /vocabulary/translate-sentence`

**Handler**: `translate_sentence_handler.py`

**Authentication**: Required

#### Request Body

```json
{
  "sentence": "I love learning English"
}
```

**Fields**:
- `sentence` (string, required): Câu cần dịch

#### Response

**Success (200)**:
```json
{
  "statusCode": 200,
  "body": {
    "sentence_en": "I love learning English",
    "sentence_vi": "Tôi thích học tiếng Anh"
  }
}
```

**Error (400)**:
```json
{
  "statusCode": 400,
  "body": {
    "error": "Missing required field: sentence"
  }
}
```

#### Example

```bash
curl -X POST https://mnjxcw3o1e.execute-api.ap-southeast-1.amazonaws.com/Prod/vocabulary/translate-sentence \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "sentence": "I love learning English"
  }'
```

## Services Used

- **Dictionary API**: Lấy định nghĩa, phiên âm, ví dụ chi tiết cho từ vựng
- **AWS Translate**: Dịch câu

## Error Codes

- `WORD_NOT_FOUND` (404): Không tìm thấy từ trong dictionary
- `DICTIONARY_SERVICE_ERROR` (503): Lỗi khi gọi Dictionary API
- `Invalid request data` (400): Lỗi validation request

## Notes

- Translate vocabulary sử dụng Dictionary API nên chi tiết hơn (có phonetic, definitions, synonyms)
- Translate sentence chỉ dịch thuần túy, không có định nghĩa
- Cả 2 endpoint đều có thể cache kết quả để tối ưu performance
- `response_time_ms` và `cached` cho biết performance metrics
