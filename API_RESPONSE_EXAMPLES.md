# API Response Examples - Complete Reference

**Mục đích**: Tất cả response examples cho frontend development

---

## 📌 Response Format Standard

Tất cả responses follow format này:

```json
{
  "success": true,
  "data": {...},
  "error": null
}
```

Hoặc khi error:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message"
  }
}
```

---

## 🎬 Scenario Endpoints

### GET /scenarios - List All Scenarios

**Request**:
```http
GET /scenarios
Authorization: Bearer {JWT_TOKEN}
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "scenarios": [
      {
        "scenario_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
        "scenario_title": "Restaurant Ordering",
        "context": "restaurant",
        "roles": ["customer", "waiter"],
        "goals": ["order_food", "ask_questions", "handle_special_requests"],
        "difficulty_level": "B1",
        "is_active": true,
        "usage_count": 1250,
        "created_at": "2026-01-15T10:00:00Z",
        "updated_at": "2026-04-20T15:30:00Z"
      },
      {
        "scenario_id": "01ARZ3NDEKTSV4RRFFQ69G5FAW",
        "scenario_title": "Hotel Check-in",
        "context": "hotel",
        "roles": ["guest", "receptionist"],
        "goals": ["check_in", "ask_for_services", "handle_problems"],
        "difficulty_level": "A2",
        "is_active": true,
        "usage_count": 890,
        "created_at": "2026-01-10T09:00:00Z",
        "updated_at": "2026-04-22T12:00:00Z"
      }
    ],
    "total": 2
  }
}
```

**Error** (401 Unauthorized):
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Missing or invalid JWT token"
  }
}
```

---

## 🎯 Session Endpoints

### POST /sessions - Create Session

**Request**:
```http
POST /sessions
Content-Type: application/json
Authorization: Bearer {JWT_TOKEN}

{
  "scenario_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
  "learner_role_id": "customer",
  "ai_role_id": "waiter",
  "ai_gender": "female",
  "level": "B1",
  "selected_goals": ["order_food", "ask_questions"]
}
```

**Response** (201 Created):
```json
{
  "success": true,
  "data": {
    "session_id": "01ARZ3NDEKTSV4RRFFQ69G5FAX",
    "session": {
      "session_id": "01ARZ3NDEKTSV4RRFFQ69G5FAX",
      "user_id": "user-123",
      "scenario_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
      "learner_role_id": "customer",
      "ai_role_id": "waiter",
      "ai_gender": "female",
      "level": "B1",
      "selected_goals": ["order_food", "ask_questions"],
      "status": "ACTIVE",
      "total_turns": 0,
      "user_turns": 0,
      "hint_used_count": 0,
      "turns": [],
      "created_at": "2026-04-25T11:00:00Z",
      "updated_at": "2026-04-25T11:00:00Z",
      "assigned_model": "amazon.nova-micro-v1:0",
      "avg_ttft_ms": "0.0",
      "avg_latency_ms": "0.0",
      "avg_output_tokens": 0,
      "total_cost_usd": "0.0"
    }
  }
}
```

**Error** (400 Bad Request):
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid scenario_id: scenario not found"
  }
}
```

---

### POST /sessions/{session_id}/turns - Submit Turn

**Request**:
```http
POST /sessions/01ARZ3NDEKTSV4RRFFQ69G5FAX/turns
Content-Type: application/json
Authorization: Bearer {JWT_TOKEN}

{
  "text": "I'd like to order a coffee, please.",
  "audio_url": "s3://bucket/audio/user-turn-1.webm",
  "is_hint_used": false
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "session": {
      "session_id": "01ARZ3NDEKTSV4RRFFQ69G5FAX",
      "user_id": "user-123",
      "scenario_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
      "learner_role_id": "customer",
      "ai_role_id": "waiter",
      "ai_gender": "female",
      "level": "B1",
      "selected_goals": ["order_food", "ask_questions"],
      "status": "ACTIVE",
      "total_turns": 2,
      "user_turns": 1,
      "hint_used_count": 0,
      "turns": [
        {
          "turn_index": 0,
          "speaker": "USER",
          "content": "I'd like to order a coffee, please.",
          "audio_url": "s3://bucket/audio/user-turn-1.webm",
          "translated_content": "Tôi muốn gọi một cà phê, vui lòng.",
          "is_hint_used": false,
          "ttft_ms": null,
          "latency_ms": null,
          "input_tokens": 0,
          "output_tokens": 0,
          "cost_usd": "0.0",
          "delivery_cue": ""
        },
        {
          "turn_index": 1,
          "speaker": "AI",
          "content": "Of course! Would you like it hot or iced?",
          "audio_url": "s3://bucket/audio/ai-turn-1.mp3",
          "translated_content": "Tất nhiên! Bạn muốn nó nóng hay lạnh?",
          "is_hint_used": false,
          "ttft_ms": "245.5",
          "latency_ms": "1250.3",
          "input_tokens": 156,
          "output_tokens": 42,
          "cost_usd": "0.00015",
          "delivery_cue": "[friendly]"
        }
      ],
      "created_at": "2026-04-25T11:00:00Z",
      "updated_at": "2026-04-25T11:01:15Z",
      "assigned_model": "amazon.nova-micro-v1:0",
      "avg_ttft_ms": "245.5",
      "avg_latency_ms": "1250.3",
      "avg_output_tokens": 42,
      "total_cost_usd": "0.00015"
    },
    "user_turn": {
      "turn_index": 0,
      "speaker": "USER",
      "content": "I'd like to order a coffee, please.",
      "audio_url": "s3://bucket/audio/user-turn-1.webm",
      "translated_content": "Tôi muốn gọi một cà phê, vui lòng.",
      "is_hint_used": false,
      "ttft_ms": null,
      "latency_ms": null,
      "input_tokens": 0,
      "output_tokens": 0,
      "cost_usd": "0.0",
      "delivery_cue": ""
    },
    "ai_turn": {
      "turn_index": 1,
      "speaker": "AI",
      "content": "Of course! Would you like it hot or iced?",
      "audio_url": "s3://bucket/audio/ai-turn-1.mp3",
      "translated_content": "Tất nhiên! Bạn muốn nó nóng hay lạnh?",
      "is_hint_used": false,
      "ttft_ms": "245.5",
      "latency_ms": "1250.3",
      "input_tokens": 156,
      "output_tokens": 42,
      "cost_usd": "0.00015",
      "delivery_cue": "[friendly]"
    },
    "analysis_keywords": ["coffee", "order", "please"]
  }
}
```

**Error** (500 Internal Server Error - Bedrock Failure):
```json
{
  "success": true,
  "data": {
    "session": {...},
    "user_turn": {...},
    "ai_turn": {
      "turn_index": 1,
      "speaker": "AI",
      "content": "Thanks. Could you say a bit more about that?",
      "audio_url": "s3://bucket/audio/ai-turn-1.mp3",
      "ttft_ms": null,
      "latency_ms": null,
      "output_tokens": 0,
      "cost_usd": "0.0"
    },
    "analysis_keywords": []
  }
}
```

**Note**: Khi Bedrock fail, backend vẫn trả về 200 OK với fallback response. Frontend không cần xử lý đặc biệt.

---

### GET /sessions/{session_id} - Get Session

**Request**:
```http
GET /sessions/01ARZ3NDEKTSV4RRFFQ69G5FAX
Authorization: Bearer {JWT_TOKEN}
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "session": {
      "session_id": "01ARZ3NDEKTSV4RRFFQ69G5FAX",
      "user_id": "user-123",
      "scenario_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
      "learner_role_id": "customer",
      "ai_role_id": "waiter",
      "ai_gender": "female",
      "level": "B1",
      "selected_goals": ["order_food", "ask_questions"],
      "status": "ACTIVE",
      "total_turns": 4,
      "user_turns": 2,
      "hint_used_count": 0,
      "turns": [
        {
          "turn_index": 0,
          "speaker": "USER",
          "content": "I'd like to order a coffee, please.",
          "audio_url": "s3://bucket/audio/user-turn-1.webm"
        },
        {
          "turn_index": 1,
          "speaker": "AI",
          "content": "Of course! Would you like it hot or iced?",
          "audio_url": "s3://bucket/audio/ai-turn-1.mp3",
          "ttft_ms": "245.5",
          "latency_ms": "1250.3",
          "output_tokens": 42,
          "cost_usd": "0.00015"
        },
        {
          "turn_index": 2,
          "speaker": "USER",
          "content": "Hot, please. And can I add sugar?"
        },
        {
          "turn_index": 3,
          "speaker": "AI",
          "content": "Absolutely! How much sugar would you like?",
          "audio_url": "s3://bucket/audio/ai-turn-2.mp3",
          "ttft_ms": "198.2",
          "latency_ms": "1100.5",
          "output_tokens": 38,
          "cost_usd": "0.00014"
        }
      ],
      "created_at": "2026-04-25T11:00:00Z",
      "updated_at": "2026-04-25T11:02:30Z",
      "assigned_model": "amazon.nova-micro-v1:0",
      "avg_ttft_ms": "221.85",
      "avg_latency_ms": "1175.4",
      "avg_output_tokens": 40,
      "total_cost_usd": "0.00029"
    }
  }
}
```

---

### GET /sessions - List Sessions

**Request**:
```http
GET /sessions?limit=10
Authorization: Bearer {JWT_TOKEN}
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "sessions": [
      {
        "session_id": "01ARZ3NDEKTSV4RRFFQ69G5FAX",
        "user_id": "user-123",
        "scenario_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
        "learner_role_id": "customer",
        "ai_role_id": "waiter",
        "ai_gender": "female",
        "level": "B1",
        "selected_goals": ["order_food"],
        "status": "COMPLETED",
        "total_turns": 4,
        "user_turns": 2,
        "hint_used_count": 0,
        "created_at": "2026-04-25T11:00:00Z",
        "updated_at": "2026-04-25T11:05:00Z",
        "assigned_model": "amazon.nova-micro-v1:0",
        "avg_ttft_ms": "221.85",
        "avg_latency_ms": "1175.4",
        "avg_output_tokens": 40,
        "total_cost_usd": "0.00029"
      },
      {
        "session_id": "01ARZ3NDEKTSV4RRFFQ69G5FAY",
        "user_id": "user-123",
        "scenario_id": "01ARZ3NDEKTSV4RRFFQ69G5FAW",
        "learner_role_id": "guest",
        "ai_role_id": "receptionist",
        "ai_gender": "male",
        "level": "A2",
        "selected_goals": ["check_in"],
        "status": "ACTIVE",
        "total_turns": 2,
        "user_turns": 1,
        "hint_used_count": 0,
        "created_at": "2026-04-25T12:00:00Z",
        "updated_at": "2026-04-25T12:01:30Z",
        "assigned_model": "amazon.nova-micro-v1:0",
        "avg_ttft_ms": "267.3",
        "avg_latency_ms": "1350.2",
        "avg_output_tokens": 45,
        "total_cost_usd": "0.00018"
      }
    ],
    "total": 2
  }
}
```

---

### POST /sessions/{session_id}/complete - Complete Session

**Request**:
```http
POST /sessions/01ARZ3NDEKTSV4RRFFQ69G5FAX/complete
Authorization: Bearer {JWT_TOKEN}
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "session": {
      "session_id": "01ARZ3NDEKTSV4RRFFQ69G5FAX",
      "status": "COMPLETED",
      "total_turns": 4,
      "user_turns": 2,
      "updated_at": "2026-04-25T11:05:00Z"
    },
    "scoring": {
      "fluency": 78,
      "pronunciation": 82,
      "grammar": 75,
      "vocabulary": 80,
      "overall": 79,
      "feedback": "Great job! Your pronunciation is excellent. Work on grammar and vocabulary."
    }
  }
}
```

---

## 📊 Data Type Reference

### Decimal Fields

Các field như `ttft_ms`, `latency_ms`, `cost_usd` được trả về dưới dạng string (Decimal):

```json
{
  "ttft_ms": "245.5",
  "latency_ms": "1250.3",
  "cost_usd": "0.00015"
}
```

**Frontend**: Convert to number khi cần:
```typescript
const ttft = parseFloat(response.ai_turn.ttft_ms);  // 245.5
```

---

### Timestamps

Tất cả timestamps ở format ISO 8601:

```
2026-04-25T11:00:00Z
```

**Frontend**: Parse with Date:
```typescript
const date = new Date('2026-04-25T11:00:00Z');
```

---

## ❌ Error Responses

### 400 Bad Request

```json
{
  "statusCode": 400,
  "body": {
    "error": "Invalid JSON format",
    "code": "BAD_REQUEST"
  }
}
```

### 401 Unauthorized

```json
{
  "statusCode": 401,
  "body": {
    "error": "Unauthorized"
  }
}
```

### 404 Not Found

```json
{
  "statusCode": 404,
  "body": {
    "error": "Session not found"
  }
}
```

### 500 Internal Server Error

```json
{
  "statusCode": 500,
  "body": {
    "success": false,
    "message": "Internal server error",
    "error": "Database connection failed"
  }
}
```

---

## 🔄 Typical Session Flow

```
1. GET /scenarios
   ↓
2. POST /sessions (create)
   ↓
3. POST /sessions/{id}/turns (submit turn 1)
   ↓
4. POST /sessions/{id}/turns (submit turn 2)
   ↓
5. POST /sessions/{id}/turns (submit turn 3)
   ↓
6. POST /sessions/{id}/complete
   ↓
7. Show scoring results
```

---

## 📝 Notes for Frontend

1. **Decimal Fields**: Always parse as string first, then convert to number if needed
2. **Timestamps**: Use ISO 8601 format, parse with Date constructor
3. **Audio URLs**: S3 presigned URLs, valid for 1 hour
4. **Fallback Response**: If Bedrock fails, AI response is "Thanks. Could you say a bit more about that?"
5. **Metrics**: Only available on AI turns, not user turns
6. **Session Status**: Can be "ACTIVE", "COMPLETED", or "PAUSED"

---

**Liên hệ**: Backend Team  
**Phiên bản**: 1.0  
**Ngày cập nhật**: 2026-04-25
