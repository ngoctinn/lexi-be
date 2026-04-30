# Speaking API - VERIFIED

**Status**: ✅ Verified với code thực tế  
**Verified date**: 2026-04-30  
**Verified files**:
- `src/infrastructure/handlers/session_handler.py`
- `src/infrastructure/handlers/websocket_handler.py`
- `src/interfaces/controllers/session_controller.py`
- `src/interfaces/view_models/session_vm.py`
- `src/application/dtos/speaking_session_dtos.py`

---

## REST API Endpoints

### 1. Create Speaking Session

**Endpoint**: `POST /sessions`

**Request Body**:
```json
{
  "scenario_id": "SCENARIO#01JGXXX",
  "learner_role_id": "role_1",
  "ai_role_id": "role_2",
  "ai_character": "Sarah",
  "level": "A1",
  "selected_goal": "Practice ordering food"
}
```

**Response** (201 Created):
```json
{
  "success": true,
  "session_id": "SESSION#01JGXXX",
  "session": {
    "session_id": "SESSION#01JGXXX",
    "user_id": "USER#xxx",
    "scenario_id": "SCENARIO#01JGXXX",
    "learner_role_id": "role_1",
    "ai_role_id": "role_2",
    "ai_character": "Sarah",
    "level": "A1",
    "prompt_snapshot": "...",
    "selected_goal": "Practice ordering food",
    "total_turns": 1,
    "user_turns": 0,
    "hint_used_count": 0,
    "turns": [
      {
        "turn_index": 0,
        "speaker": "AI",
        "content": "Hello! Welcome to...",
        "translated_content": "Xin chào! Chào mừng...",
        "audio_url": "https://s3.../greeting.mp3",
        "is_hint_used": false,
        "is_saved_to_flashcard": false,
        "is_pending": false,
        "ttft_ms": null,
        "latency_ms": null,
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_usd": 0.0,
        "delivery_cue": "",
        "quality_score": 0.0
      }
    ],
    "scoring": null,
    "connection_id": null,
    "created_at": "2026-04-30T10:00:00Z",
    "updated_at": "2026-04-30T10:00:00Z",
    "status": "ACTIVE",
    "assigned_model": "",
    "avg_ttft_ms": 0.0,
    "avg_latency_ms": 0.0,
    "avg_output_tokens": 0,
    "total_cost_usd": 0.0
  }
}
```

**Fields**:
- `success`: Always `true`
- `session_id`: Session ID
- `session`: Full session object with:
  - `turns`: Array of turns (AI greeting is turn 0)
  - `status`: `"ACTIVE"` | `"COMPLETED"`
  - Phase 5 metrics: `ttft_ms`, `latency_ms`, `input_tokens`, `output_tokens`, `cost_usd`, `quality_score`

---

### 2. List Speaking Sessions

**Endpoint**: `GET /sessions?limit=10`

**Query Parameters**:
- `limit` (optional): Max sessions to return (default: 10)

**Response** (200 OK):
```json
{
  "success": true,
  "sessions": [
    {
      "session_id": "SESSION#01JGXXX",
      "user_id": "USER#xxx",
      "scenario_id": "SCENARIO#01JGXXX",
      "learner_role_id": "role_1",
      "ai_role_id": "role_2",
      "ai_character": "Sarah",
      "level": "A1",
      "prompt_snapshot": "...",
      "selected_goal": "Practice ordering food",
      "total_turns": 5,
      "user_turns": 2,
      "hint_used_count": 1,
      "turns": [],
      "scoring": null,
      "connection_id": null,
      "created_at": "2026-04-30T10:00:00Z",
      "updated_at": "2026-04-30T10:05:00Z",
      "status": "ACTIVE",
      "assigned_model": "anthropic.claude-3-5-sonnet-20241022-v2:0",
      "avg_ttft_ms": 450.5,
      "avg_latency_ms": 1200.3,
      "avg_output_tokens": 85,
      "total_cost_usd": 0.0025
    }
  ],
  "total": 1
}
```

**Fields**:
- `success`: Always `true`
- `sessions`: Array of session objects (without `turns` array for performance)
- `total`: Total count

---

### 3. Get Speaking Session

**Endpoint**: `GET /sessions/{session_id}`

**Response** (200 OK):
```json
{
  "success": true,
  "session": {
    "session_id": "SESSION#01JGXXX",
    "user_id": "USER#xxx",
    "scenario_id": "SCENARIO#01JGXXX",
    "learner_role_id": "role_1",
    "ai_role_id": "role_2",
    "ai_character": "Sarah",
    "level": "A1",
    "prompt_snapshot": "...",
    "selected_goal": "Practice ordering food",
    "total_turns": 5,
    "user_turns": 2,
    "hint_used_count": 1,
    "turns": [
      {
        "turn_index": 0,
        "speaker": "AI",
        "content": "Hello! Welcome to...",
        "translated_content": "Xin chào!...",
        "audio_url": "https://s3.../greeting.mp3",
        "is_hint_used": false,
        "is_saved_to_flashcard": false,
        "is_pending": false,
        "ttft_ms": 420.5,
        "latency_ms": 1150.2,
        "input_tokens": 150,
        "output_tokens": 85,
        "cost_usd": 0.0012,
        "delivery_cue": "friendly",
        "quality_score": 0.95
      }
    ],
    "scoring": {
      "fluency": 7,
      "pronunciation": 6,
      "grammar": 8,
      "vocabulary": 7,
      "overall": 7,
      "feedback": "Good job! Your grammar is strong..."
    },
    "connection_id": "abc123",
    "created_at": "2026-04-30T10:00:00Z",
    "updated_at": "2026-04-30T10:05:00Z",
    "status": "COMPLETED",
    "assigned_model": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "avg_ttft_ms": 450.5,
    "avg_latency_ms": 1200.3,
    "avg_output_tokens": 85,
    "total_cost_usd": 0.0025
  }
}
```

**Fields**:
- `success`: Always `true`
- `session`: Full session object with all turns and scoring (if completed)

---

### 4. Submit Speaking Turn

**Endpoint**: `POST /sessions/{session_id}/turns`

**Request Body**:
```json
{
  "text": "I would like a coffee please",
  "is_hint_used": false,
  "audio_url": "https://s3.../audio.webm"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "session": {
    "session_id": "SESSION#01JGXXX",
    "total_turns": 3,
    "user_turns": 2,
    "hint_used_count": 0,
    "status": "ACTIVE",
    "avg_ttft_ms": 445.2,
    "avg_latency_ms": 1180.5,
    "avg_output_tokens": 82,
    "total_cost_usd": 0.0018
  },
  "user_turn": {
    "turn_index": 1,
    "speaker": "USER",
    "content": "I would like a coffee please",
    "translated_content": "Tôi muốn một ly cà phê",
    "audio_url": "https://s3.../audio.webm",
    "is_hint_used": false,
    "is_saved_to_flashcard": false,
    "is_pending": false,
    "ttft_ms": null,
    "latency_ms": null,
    "input_tokens": 0,
    "output_tokens": 0,
    "cost_usd": 0.0,
    "delivery_cue": "",
    "quality_score": 0.0
  },
  "ai_turn": {
    "turn_index": 2,
    "speaker": "AI",
    "content": "Of course! Would you like milk with that?",
    "translated_content": "Tất nhiên! Bạn có muốn thêm sữa không?",
    "audio_url": "https://s3.../ai-response.mp3",
    "is_hint_used": false,
    "is_saved_to_flashcard": false,
    "is_pending": false,
    "ttft_ms": 465.3,
    "latency_ms": 1220.8,
    "input_tokens": 180,
    "output_tokens": 75,
    "cost_usd": 0.0011,
    "delivery_cue": "helpful",
    "quality_score": 0.92
  },
  "analysis_keywords": ["coffee", "order", "polite"]
}
```

**Fields**:
- `success`: Always `true`
- `session`: Updated session summary
- `user_turn`: User's turn object
- `ai_turn`: AI's response turn object
- `analysis_keywords`: Keywords extracted from user input

---

### 5. Complete Speaking Session

**Endpoint**: `POST /sessions/{session_id}/complete`

**Response** (200 OK):
```json
{
  "success": true,
  "session": {
    "session_id": "SESSION#01JGXXX",
    "status": "COMPLETED",
    "total_turns": 5,
    "user_turns": 2,
    "hint_used_count": 1,
    "completed_at": "2026-04-30T10:05:00Z",
    "avg_ttft_ms": 450.5,
    "avg_latency_ms": 1200.3,
    "avg_output_tokens": 85,
    "total_cost_usd": 0.0025
  },
  "scoring": {
    "fluency": 7,
    "pronunciation": 6,
    "grammar": 8,
    "vocabulary": 7,
    "overall": 7,
    "feedback": "Good job! Your grammar is strong. Try to speak more fluently and work on pronunciation of 'th' sounds."
  }
}
```

**Fields**:
- `success`: Always `true`
- `session`: Updated session with `status: "COMPLETED"`
- `scoring`: Performance scores (1-10 scale) with feedback

---

## WebSocket API

**WebSocket URL**: `wss://{api-id}.execute-api.ap-southeast-1.amazonaws.com/prod`

### Connection

**Connect**: `$connect?session_id={session_id}&token={jwt_token}`

**Authentication**: JWT token in query parameter

**Disconnect**: `$disconnect` (automatic)

---

### WebSocket Actions

#### 1. START_SESSION

**Client → Server**:
```json
{
  "action": "START_SESSION",
  "session_id": "SESSION#01JGXXX"
}
```

**Server → Client**:
```json
{
  "event": "SESSION_STARTED",
  "session_id": "SESSION#01JGXXX",
  "greeting": "Hello! Welcome to the restaurant..."
}
```

---

#### 2. GET_TRANSCRIBE_URL

**Client → Server**:
```json
{
  "action": "GET_TRANSCRIBE_URL",
  "session_id": "SESSION#01JGXXX"
}
```

**Server → Client**:
```json
{
  "event": "TRANSCRIBE_URL",
  "url": "wss://transcribestreaming.ap-southeast-1.amazonaws.com/...",
  "expires_in": 300
}
```

---

#### 3. SUBMIT_TRANSCRIPT

**Client → Server** (Text input):
```json
{
  "action": "SUBMIT_TRANSCRIPT",
  "session_id": "SESSION#01JGXXX",
  "text": "I would like a coffee please"
}
```

**Client → Server** (Mic input with streaming transcription):
```json
{
  "action": "SUBMIT_TRANSCRIPT",
  "session_id": "SESSION#01JGXXX",
  "text": "I would like a coffee please",
  "confidence": 0.95
}
```

**Server → Client** (Multiple events):
```json
{"event": "TURN_SAVED", "turn_index": 1}
{"event": "AI_RESPONSE_CHUNK", "text": "Of course!"}
{"event": "AI_RESPONSE_CHUNK", "text": " Would you like"}
{"event": "AI_RESPONSE_CHUNK", "text": " milk with that?"}
{"event": "AI_AUDIO_URL", "url": "https://s3.../ai-response.mp3", "text": "Of course! Would you like milk with that?"}
```

---

#### 4. USE_HINT

**Client → Server**:
```json
{
  "action": "USE_HINT",
  "session_id": "SESSION#01JGXXX"
}
```

**Server → Client**:
```json
{
  "event": "HINT",
  "hint": "Try saying: 'I would like...'"
}
```

---

#### 5. ANALYZE_TURN

**Client → Server**:
```json
{
  "action": "ANALYZE_TURN",
  "session_id": "SESSION#01JGXXX",
  "turn_index": 1
}
```

**Server → Client**:
```json
{
  "event": "TURN_ANALYSIS",
  "turn_index": 1,
  "keywords": ["coffee", "order", "polite"],
  "grammar_score": 8,
  "vocabulary_level": "A1"
}
```

---

#### 6. END_SESSION

**Client → Server**:
```json
{
  "action": "END_SESSION",
  "session_id": "SESSION#01JGXXX"
}
```

**Server → Client**:
```json
{
  "event": "SESSION_ENDED",
  "session_id": "SESSION#01JGXXX",
  "scoring": {
    "fluency": 7,
    "pronunciation": 6,
    "grammar": 8,
    "vocabulary": 7,
    "overall": 7,
    "feedback": "Good job!..."
  }
}
```

---

### Error Events

**Server → Client**:
```json
{
  "event": "ERROR",
  "message": "Lỗi xử lý transcript."
}
```

---

## Phase 5 Metrics

All AI turns include performance metrics:

- `ttft_ms`: Time to first token (milliseconds)
- `latency_ms`: Total latency (milliseconds)
- `input_tokens`: Input token count
- `output_tokens`: Output token count
- `cost_usd`: Cost in USD (Decimal)
- `delivery_cue`: Delivery style hint (e.g., "friendly", "helpful")
- `quality_score`: Quality score (0.0-1.0)

Session-level aggregates:
- `assigned_model`: Model used (e.g., "anthropic.claude-3-5-sonnet-20241022-v2:0")
- `avg_ttft_ms`: Average TTFT
- `avg_latency_ms`: Average latency
- `avg_output_tokens`: Average output tokens
- `total_cost_usd`: Total cost

---

## Notes

1. **Response Format**: All REST endpoints return `{success: true, ...}` format
2. **WebSocket Streaming**: AI responses are streamed in chunks via `AI_RESPONSE_CHUNK` events
3. **Audio URLs**: S3 presigned URLs with 15-minute expiry
4. **Transcription**: Supports both text input and real-time streaming transcription
5. **Metrics**: Phase 5 metrics enabled via `ConversationOrchestrator`
6. **Authentication**: REST uses Cognito Authorizer, WebSocket uses JWT in query params
