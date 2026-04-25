# Kiến Trúc Hệ Thống Hội Thoại - Lexi Backend

**Phiên bản**: 1.0  
**Ngày cập nhật**: 2026-04-25  
**Mục đích**: Tài liệu chi tiết cho Frontend team về luồng hội thoại, API endpoints, data models, và real-time streaming

---

## 📋 Mục Lục

1. [Tổng Quan Kiến Trúc](#tổng-quan-kiến-trúc)
2. [Luồng Hội Thoại Chi Tiết](#luồng-hội-thoại-chi-tiết)
3. [API Endpoints](#api-endpoints)
4. [Data Models](#data-models)
5. [Real-time Streaming](#real-time-streaming)
6. [Error Handling](#error-handling)
7. [Metrics & Performance](#metrics--performance)

---

## 🏗️ Tổng Quan Kiến Trúc

### Các Thành Phần Chính

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (Next.js)                      │
│  - UI Components (React)                                    │
│  - WebSocket Client                                         │
│  - HTTP Client (Fetch/Axios)                                │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
   ┌─────────────┐         ┌──────────────┐
   │ HTTP API    │         │ WebSocket    │
   │ (REST)      │         │ (Real-time)  │
   └──────┬──────┘         └──────┬───────┘
          │                       │
          └───────────┬───────────┘
                      ▼
        ┌─────────────────────────────┐
        │   AWS Lambda Handlers       │
        │  - session_handler.py       │
        │  - websocket_handler.py     │
        └──────────┬──────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
   ┌─────────────┐      ┌──────────────┐
   │ Controllers │      │ Use Cases    │
   │ (Clean Arch)│      │ (Business    │
   │             │      │  Logic)      │
   └──────┬──────┘      └──────┬───────┘
          │                    │
          └────────┬───────────┘
                   ▼
        ┌─────────────────────────────┐
        │   Domain Services           │
        │  - ConversationOrchestrator │
        │  - StreamingResponse        │
        │  - MetricsLogger            │
        └──────────┬──────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
   ┌─────────────┐      ┌──────────────┐
   │ AWS Bedrock │      │ DynamoDB     │
   │ (LLM)       │      │ (Persistence)│
   └─────────────┘      └──────────────┘
```

### Kiến Trúc Clean Architecture

```
┌─────────────────────────────────────────────────────────┐
│ INTERFACES LAYER (HTTP/WebSocket)                       │
│ - Controllers (session_controller.py)                   │
│ - Mappers (session_mapper.py)                           │
│ - ViewModels (session_vm.py)                            │
│ - Presenters (http_presenter.py)                        │
└─────────────────────────────────────────────────────────┘
                         ▲
                         │ depends on
                         ▼
┌─────────────────────────────────────────────────────────┐
│ APPLICATION LAYER (Use Cases)                           │
│ - SubmitSpeakingTurnUseCase                             │
│ - CreateSpeakingSessionUseCase                          │
│ - CompleteSpeakingSessionUseCase                        │
│ - DTOs (Data Transfer Objects)                          │
└─────────────────────────────────────────────────────────┘
                         ▲
                         │ depends on
                         ▼
┌─────────────────────────────────────────────────────────┐
│ DOMAIN LAYER (Business Logic)                           │
│ - Entities (Session, Turn, Scenario)                    │
│ - Services (ConversationOrchestrator)                   │
│ - Value Objects (ProficiencyLevel, Gender)             │
│ - Repositories (interfaces only)                        │
└─────────────────────────────────────────────────────────┘
                         ▲
                         │ depends on
                         ▼
┌─────────────────────────────────────────────────────────┐
│ INFRASTRUCTURE LAYER (Implementation)                   │
│ - Repositories (DynamoDB)                               │
│ - Services (Bedrock, Comprehend, Polly)                │
│ - Handlers (Lambda entry points)                        │
└─────────────────────────────────────────────────────────┘
```

---

## 🔄 Luồng Hội Thoại Chi Tiết

### Phase 1: Khởi Tạo Session

```
Frontend                          Backend
   │                                │
   ├─ POST /sessions ──────────────>│
   │  {                             │
   │    scenario_id: "s123",        │
   │    learner_role_id: "customer",│
   │    ai_role_id: "waiter",       │
   │    ai_gender: "female",        │
   │    level: "B1",                │
   │    selected_goals: [...]       │
   │  }                             │
   │                                │
   │                    ┌─ CreateSpeakingSessionUseCase
   │                    │  - Validate input
   │                    │  - Load scenario
   │                    │  - Build prompt
   │                    │  - Create session in DB
   │                    │  - Assign model (Bedrock)
   │                    │
   │<─────────────────── 201 Created
   │  {                             │
   │    success: true,              │
   │    session_id: "01ARZ3NDEKTSV4RRFFQ69G5FAV",
   │    session: {                  │
   │      session_id: "...",        │
   │      scenario_id: "s123",      │
   │      status: "ACTIVE",         │
   │      total_turns: 0,           │
   │      created_at: "2026-04-25T11:00:00Z"
   │    }                           │
   │  }                             │
   │                                │
```

**Response Status**: 201 Created  
**Error Cases**:
- 400: Invalid scenario_id
- 401: Unauthorized (missing JWT)
- 500: Database error

---

### Phase 2: User Submits Turn (Main Loop)

```
Frontend                          Backend
   │                                │
   ├─ POST /sessions/{id}/turns ──>│
   │  {                             │
   │    text: "Hello, I'd like...", │
   │    audio_url: "s3://...",      │
   │    is_hint_used: false         │
   │  }                             │
   │                                │
   │                    ┌─ SubmitSpeakingTurnUseCase
   │                    │
   │                    ├─ 1. Validate input
   │                    │    - Check session exists
   │                    │    - Check user owns session
   │                    │    - Validate text not empty
   │                    │
   │                    ├─ 2. Analyze user input
   │                    │    - ComprehendTranscriptAnalysisService
   │                    │    - Extract key phrases
   │                    │    - Detect language
   │                    │    - Count words/sentences
   │                    │
   │                    ├─ 3. Save user turn to DB
   │                    │    - Turn index: 0, 2, 4, ... (even)
   │                    │    - Speaker: USER
   │                    │    - Content: user text
   │                    │
   │                    ├─ 4. Generate AI response
   │                    │    - ConversationOrchestrator
   │                    │    │
   │                    │    ├─ Route to model
   │                    │    │  (based on proficiency level)
   │                    │    │
   │                    │    ├─ Build optimized prompt
   │                    │    │  - Static prefix (cached)
   │                    │    │  - Dynamic suffix (session-specific)
   │                    │    │
   │                    │    ├─ Call Bedrock streaming API
   │                    │    │  - invoke_model_with_response_stream()
   │                    │    │  - Collect tokens in real-time
   │                    │    │  - Track TTFT (Time To First Token)
   │                    │    │  - Track total latency
   │                    │    │
   │                    │    ├─ Validate response quality
   │                    │    │  - Check length
   │                    │    │  - Check profanity
   │                    │    │  - Check relevance
   │                    │    │
   │                    │    └─ Log metrics (EMF format)
   │                    │       - TTFT, latency, tokens, cost
   │                    │
   │                    ├─ 5. Synthesize AI audio
   │                    │    - PollySpeechSynthesisService
   │                    │    - Generate MP3 from AI text
   │                    │    - Upload to S3
   │                    │    - Get presigned URL
   │                    │
   │                    ├─ 6. Save AI turn to DB
   │                    │    - Turn index: 1, 3, 5, ... (odd)
   │                    │    - Speaker: AI
   │                    │    - Content: AI response
   │                    │    - Audio URL: S3 presigned URL
   │                    │    - Metrics: TTFT, latency, tokens, cost
   │                    │
   │                    ├─ 7. Update session stats
   │                    │    - total_turns += 2
   │                    │    - user_turns += 1
   │                    │    - avg_ttft_ms (running average)
   │                    │    - avg_latency_ms (running average)
   │                    │    - total_cost_usd (cumulative)
   │                    │
   │<─────────────────── 200 OK
   │  {                             │
   │    success: true,              │
   │    session: {                  │
   │      session_id: "...",        │
   │      total_turns: 2,           │
   │      user_turns: 1,            │
   │      turns: [                  │
   │        {                       │
   │          turn_index: 0,        │
   │          speaker: "USER",      │
   │          content: "Hello...",  │
   │          audio_url: "s3://..." │
   │        },                      │
   │        {                       │
   │          turn_index: 1,        │
   │          speaker: "AI",        │
   │          content: "Hi! How...",│
   │          audio_url: "s3://...",│
   │          ttft_ms: 245.5,       │
   │          latency_ms: 1250.3,   │
   │          output_tokens: 42,    │
   │          cost_usd: 0.00015     │
   │        }                       │
   │      ]                         │
   │    },                          │
   │    user_turn: {...},           │
   │    ai_turn: {...},             │
   │    analysis_keywords: [...]    │
   │  }                             │
   │                                │
```

**Response Status**: 200 OK  
**Latency**: ~1-2 seconds (Bedrock streaming)  
**Error Cases**:
- 400: Invalid input
- 401: Unauthorized
- 404: Session not found
- 500: Bedrock error (fallback response returned)

---

### Phase 3: Complete Session

```
Frontend                          Backend
   │                                │
   ├─ POST /sessions/{id}/complete>│
   │                                │
   │                    ┌─ CompleteSpeakingSessionUseCase
   │                    │
   │                    ├─ 1. Validate session
   │                    │
   │                    ├─ 2. Calculate final score
   │                    │    - BedrockScorerAdapter
   │                    │    - Fluency (0-100)
   │                    │    - Pronunciation (0-100)
   │                    │    - Grammar (0-100)
   │                    │    - Vocabulary (0-100)
   │                    │    - Overall (0-100)
   │                    │
   │                    ├─ 3. Mark session COMPLETED
   │                    │
   │                    ├─ 4. Save scoring to DB
   │                    │
   │<─────────────────── 200 OK
   │  {                             │
   │    success: true,              │
   │    session: {...},             │
   │    scoring: {                  │
   │      fluency: 78,              │
   │      pronunciation: 82,        │
   │      grammar: 75,              │
   │      vocabulary: 80,           │
   │      overall: 79,              │
   │      feedback: "Good job!..."  │
   │    }                           │
   │  }                             │
   │                                │
```

---

## 🔌 API Endpoints

### 1. Create Session

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
  "session_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
  "session": {
    "session_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
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
    "created_at": "2026-04-25T11:00:00Z",
    "updated_at": "2026-04-25T11:00:00Z",
    "assigned_model": "amazon.nova-micro-v1:0",
    "avg_ttft_ms": "0.0",
    "avg_latency_ms": "0.0",
    "avg_output_tokens": 0,
    "total_cost_usd": "0.0"
  }
}
```

---

### 2. Submit Turn (Main Loop)

```http
POST /sessions/{session_id}/turns
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
  "session": {
    "session_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
    "total_turns": 2,
    "user_turns": 1,
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
    ]
  },
  "user_turn": {
    "turn_index": 0,
    "speaker": "USER",
    "content": "I'd like to order a coffee, please.",
    "audio_url": "s3://bucket/audio/user-turn-1.webm"
  },
  "ai_turn": {
    "turn_index": 1,
    "speaker": "AI",
    "content": "Of course! Would you like it hot or iced?",
    "audio_url": "s3://bucket/audio/ai-turn-1.mp3",
    "ttft_ms": "245.5",
    "latency_ms": "1250.3",
    "output_tokens": 42,
    "cost_usd": "0.00015"
  },
  "analysis_keywords": ["coffee", "order", "please"]
}
```

---

### 3. Get Session

```http
GET /sessions/{session_id}
Authorization: Bearer {JWT_TOKEN}
```

**Response** (200 OK):
```json
{
  "success": true,
  "session": {
    "session_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
    "total_turns": 4,
    "user_turns": 2,
    "turns": [...]
  }
}
```

---

### 4. List Sessions

```http
GET /sessions?limit=10
Authorization: Bearer {JWT_TOKEN}
```

**Response** (200 OK):
```json
{
  "success": true,
  "sessions": [
    {
      "session_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
      "scenario_id": "s123",
      "status": "COMPLETED",
      "total_turns": 4,
      "created_at": "2026-04-25T11:00:00Z"
    }
  ],
  "total": 1
}
```

---

### 5. Complete Session

```http
POST /sessions/{session_id}/complete
Authorization: Bearer {JWT_TOKEN}
```

**Response** (200 OK):
```json
{
  "success": true,
  "session": {...},
  "scoring": {
    "fluency": 78,
    "pronunciation": 82,
    "grammar": 75,
    "vocabulary": 80,
    "overall": 79,
    "feedback": "Great job! Your pronunciation is excellent. Work on grammar."
  }
}
```

---

## 📊 Data Models

### Session

```typescript
interface Session {
  // Định danh
  session_id: string;           // ULID
  user_id: string;
  scenario_id: string;

  // Cấu hình
  learner_role_id: string;      // e.g., "customer", "passenger"
  ai_role_id: string;           // e.g., "waiter", "check-in agent"
  ai_gender: "male" | "female";
  level: "A1" | "A2" | "B1" | "B2" | "C1" | "C2";
  selected_goals: string[];     // e.g., ["order_food", "ask_questions"]

  // Trạng thái
  status: "ACTIVE" | "COMPLETED" | "PAUSED";
  total_turns: number;          // Tổng lượt (user + AI)
  user_turns: number;           // Số lượt user
  hint_used_count: number;

  // Metrics (Phase 5)
  assigned_model: string;       // e.g., "amazon.nova-micro-v1:0"
  avg_ttft_ms: Decimal;         // Average Time To First Token
  avg_latency_ms: Decimal;      // Average total latency
  avg_output_tokens: number;    // Average tokens per turn
  total_cost_usd: Decimal;      // Cumulative cost

  // Timestamps
  created_at: string;           // ISO 8601
  updated_at: string;
}
```

### Turn

```typescript
interface Turn {
  // Định danh
  session_id: string;
  turn_index: number;           // 0, 1, 2, 3, ... (sequential)

  // Nội dung
  speaker: "USER" | "AI";
  content: string;              // Văn bản
  audio_url: string;            // S3 URL
  translated_content: string;   // Bản dịch (thường sang Việt)
  is_hint_used: boolean;

  // Metrics (Phase 5) - chỉ có với AI turns
  ttft_ms?: Decimal;            // Time to first token
  latency_ms?: Decimal;         // Total latency
  input_tokens: number;
  output_tokens: number;
  cost_usd: Decimal;
  delivery_cue: string;         // e.g., "[warmly]", "[formally]"
}
```

### Scenario

```typescript
interface Scenario {
  // Định danh
  scenario_id: string;          // ULID

  // Nội dung
  scenario_title: string;       // e.g., "Restaurant Ordering"
  context: string;              // e.g., "restaurant" (for icon lookup)
  roles: string[];              // Exactly 2 roles
  goals: string[];              // Learning goals

  // Metadata
  difficulty_level: string;     // CEFR: A1, A2, B1, B2, C1, C2
  is_active: boolean;
  usage_count: number;

  // Timestamps
  created_at: string;
  updated_at: string;
}
```

---

## 🔌 Real-time Streaming

### WebSocket Connection (Optional)

Nếu frontend muốn real-time streaming của AI response:

```javascript
// Frontend
const ws = new WebSocket('wss://api.example.com/ws');

ws.onopen = () => {
  ws.send(JSON.stringify({
    action: 'submit_turn',
    session_id: '01ARZ3NDEKTSV4RRFFQ69G5FAV',
    text: 'Hello, I would like...'
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.type === 'AI_TEXT_CHUNK') {
    // Streaming token từ Bedrock
    console.log('Token:', message.chunk);
    // Update UI in real-time
  }
  
  if (message.type === 'AI_TURN_COMPLETE') {
    // Turn hoàn thành
    console.log('AI Response:', message.ai_turn);
  }
};
```

**WebSocket Message Types**:

```typescript
// Incoming (from backend)
interface AITextChunk {
  type: 'AI_TEXT_CHUNK';
  chunk: string;
  ttft_ms?: number;  // Only on first chunk
}

interface AITurnComplete {
  type: 'AI_TURN_COMPLETE';
  ai_turn: Turn;
  session: Session;
}

interface Error {
  type: 'ERROR';
  message: string;
  code: string;
}
```

---

## ⚠️ Error Handling

### HTTP Error Responses

```json
{
  "statusCode": 400,
  "body": {
    "error": "Invalid session_id",
    "code": "VALIDATION_ERROR"
  }
}
```

### Error Codes

| Code | HTTP | Meaning |
|------|------|---------|
| `VALIDATION_ERROR` | 400 | Invalid input |
| `UNAUTHORIZED` | 401 | Missing/invalid JWT |
| `NOT_FOUND` | 404 | Resource not found |
| `SESSION_NOT_FOUND` | 404 | Session doesn't exist |
| `SCENARIO_NOT_FOUND` | 404 | Scenario doesn't exist |
| `BEDROCK_ERROR` | 500 | LLM error (fallback response returned) |
| `INTERNAL_ERROR` | 500 | Server error |

### Fallback Behavior

Nếu Bedrock API fail:
- Backend trả về mock response: `"Thanks. Could you say a bit more about that?"`
- Metrics không được ghi nhận
- Session vẫn được lưu
- Frontend không cần xử lý đặc biệt

---

## 📈 Metrics & Performance

### Phase 5 Metrics (Collected per Turn)

```typescript
interface TurnMetrics {
  // Timing
  ttft_ms: Decimal;             // Time to first token (ms)
  latency_ms: Decimal;          // Total latency (ms)

  // Tokens
  input_tokens: number;         // Tokens in prompt
  output_tokens: number;        // Tokens in response

  // Cost
  cost_usd: Decimal;            // Cost for this turn

  // Quality
  validation_passed: boolean;   // Response quality check
  model_source: "primary" | "fallback";
}
```

### Session Aggregation

```typescript
interface SessionMetrics {
  // Averages
  avg_ttft_ms: Decimal;         // Average TTFT across all turns
  avg_latency_ms: Decimal;      // Average latency
  avg_output_tokens: number;    // Average tokens per turn

  // Totals
  total_cost_usd: Decimal;      // Total cost for session
  total_turns: number;
  user_turns: number;
}
```

### CloudWatch Metrics (EMF Format)

Backend logs metrics to CloudWatch in EMF format:

```json
{
  "_aws": {
    "CloudWatchMetrics": [
      {
        "Namespace": "Lexi/Speaking",
        "Dimensions": [
          ["Level", "B1"],
          ["ModelSource", "primary"],
          ["Model", "amazon.nova-micro-v1:0"]
        ],
        "Metrics": [
          {
            "Name": "TTFT",
            "Unit": "Milliseconds"
          },
          {
            "Name": "TotalLatency",
            "Unit": "Milliseconds"
          },
          {
            "Name": "OutputTokens",
            "Unit": "Count"
          },
          {
            "Name": "CostPerTurn",
            "Unit": "None"
          }
        ]
      }
    ]
  },
  "TTFT": 245.5,
  "TotalLatency": 1250.3,
  "OutputTokens": 42,
  "CostPerTurn": 0.00015,
  "Level": "B1",
  "ModelSource": "primary",
  "Model": "amazon.nova-micro-v1:0"
}
```

---

## 🔐 Authentication

Tất cả endpoints yêu cầu JWT token trong header:

```http
Authorization: Bearer {JWT_TOKEN}
```

JWT được cấp bởi AWS Cognito. Token chứa:
- `sub`: User ID
- `email`: User email
- `cognito:username`: Username

---

## 🚀 Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| TTFT | < 500ms | Time to first token from Bedrock |
| Total Latency | 1-2s | Full turn submission to response |
| API Response | < 100ms | HTTP response time (excluding Bedrock) |
| Session Creation | < 500ms | Create session + load scenario |
| Concurrent Users | 1000+ | Lambda auto-scaling |

---

## 📝 Frontend Implementation Checklist

- [ ] Implement session creation flow
- [ ] Implement turn submission loop
- [ ] Display user turns with audio playback
- [ ] Display AI turns with streaming (optional)
- [ ] Show metrics (TTFT, latency, cost)
- [ ] Handle errors gracefully
- [ ] Implement session completion
- [ ] Show scoring results
- [ ] Cache scenarios locally
- [ ] Implement offline mode (optional)

---

## 🔗 Related Documentation

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Clean Architecture Pattern](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [API Response Format](./API_RESPONSE_FORMAT.md)
- [Error Handling Guide](./ERROR_HANDLING.md)

---

**Liên hệ**: Backend Team  
**Phiên bản cuối**: 2026-04-25
