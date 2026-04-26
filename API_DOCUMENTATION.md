# Lexi API Documentation

**Version**: 2.2  
**Last Updated**: April 26, 2026  
**Base URL**: `https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod`  
**WebSocket URL**: `wss://no8fa2u3qg.execute-api.ap-southeast-1.amazonaws.com/Prod`  
**Region**: `ap-southeast-1` (Singapore)

---

## Table of Contents

1. [Authentication](#authentication)
2. [Response Format](#response-format)
3. [Error Handling](#error-handling)
4. [Delivery Cues & Tone](#delivery-cues--tone)
5. [Hint Formatting](#hint-formatting)
6. [Onboarding Endpoints](#onboarding-endpoints)
7. [Profile Endpoints](#profile-endpoints)
8. [Vocabulary Endpoints](#vocabulary-endpoints)
9. [Flashcard Endpoints](#flashcard-endpoints)
10. [Scenario Endpoints](#scenario-endpoints)
11. [Speaking Session Endpoints](#speaking-session-endpoints)
12. [WebSocket Endpoints](#websocket-endpoints)
13. [Admin Endpoints](#admin-endpoints)

---

## Authentication

All endpoints (except `/scenarios` which is public) require **Cognito JWT authentication**.

### Getting a Token

```bash
aws cognito-idp admin-initiate-auth \
  --user-pool-id ap-southeast-1_VhFl3NxNy \
  --client-id 4krhiauplon0iei1f5r4cgpq7i \
  --auth-flow ADMIN_NO_SRP_AUTH \
  --auth-parameters USERNAME=user@example.com,PASSWORD=password \
  --region ap-southeast-1
```

### Using the Token

```bash
curl -H "Authorization: Bearer <JWT_TOKEN>" \
  https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod/profile
```

---

## Response Format

### Success Response

```json
{
  "success": true,
  "message": "Success",
  "data": {}
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

| Code | Meaning |
|------|---------|
| `200` | OK |
| `201` | Created |
| `400` | Bad Request |
| `401` | Unauthorized |
| `403` | Forbidden |
| `404` | Not Found |
| `422` | Validation Error |
| `503` | Service Unavailable (external service down) |
| `500` | Internal Server Error |

---

## Error Handling

| Code | Meaning |
|------|---------|
| `BAD_REQUEST` | Invalid JSON or missing required fields |
| `VALIDATION_ERROR` | Request data validation failed |
| `NOT_FOUND` | Resource not found |
| `WORD_NOT_FOUND` | Word not found in dictionary |
| `DICTIONARY_SERVICE_ERROR` | Dictionary API temporarily unavailable |
| `UNAUTHORIZED` | Authentication failed |
| `FORBIDDEN` | Permission denied |
| `SERVICE_ERROR` | External service error (Bedrock, Translate, etc.) |
| `SUBMISSION_FAILED` | Turn submission failed |
| `COMPLETION_FAILED` | Session completion failed |

---

## Delivery Cues & Tone

AI responses include delivery cues at the **start** of the response indicating emotional tone.

### Available Delivery Cues

| Cue | Meaning |
|-----|---------|
| `[warmly]` | Friendly and encouraging |
| `[encouragingly]` | Motivating and supportive |
| `[gently]` | Tactful — error correction, redirection |
| `[thoughtfully]` | Deep discussion (B2+) |
| `[naturally]` | Normal conversation flow |

### Frontend Implementation

```typescript
// Extract delivery cue (only at START of response)
const match = turn.content.match(/^\[([a-zA-Z\s]+)\]/);
const tone = match ? match[1] : "naturally";

// Clean text for display
const cleanText = turn.content.replace(/^\[[^\]]+\]\s*/, "");

const TONE_COLORS = {
  warmly: "#10b981",
  encouragingly: "#3b82f6",
  gently: "#f59e0b",
  thoughtfully: "#8b5cf6",
  naturally: "#6b7280",
};
```

---

## Hint Formatting

Hints are bilingual (Vietnamese + English) rendered as **markdown**, level-adaptive for all CEFR levels (A1–C2).

### Hint Response Format (WebSocket `HINT_TEXT` event)

```json
{
  "event": "HINT_TEXT",
  "hint": {
    "markdown": {
      "vi": "AI đang hỏi bạn muốn gọi món gì. Hãy nói rõ bạn muốn gì và nhớ dùng từ lịch sự.\n- **'I'd like a coffee, please.'**\n- **'Can I have a black coffee?'**\n- **'I'll have a latte, thank you.'**",
      "en": "The AI is asking what you'd like to order. Tell them clearly what you want and use polite words.\n- **'I'd like a coffee, please.'**\n- **'Can I have a black coffee?'**\n- **'I'll have a latte, thank you.'**"
    }
  }
}
```

### Hint Types & Sections by Level

Hints use a **natural conversational flow** (chain-of-hints approach) with:
1. Natural language guidance (2-3 sentences)
2. Bullet-point examples with bold formatting

| Level | Type | Format |
|-------|------|--------|
| A1, A2 | `vocabulary_suggestion` | Natural guidance + 2-3 bold examples |
| B1, B2 | `strategic_guidance` | Natural guidance + 2-3 bold examples |
| C1, C2 | `metacognitive_prompt` | Natural guidance + 2-3 bold examples |

**Example output:**
```
AI muốn biết thói quen sáng của bạn. Hãy kể về những hoạt động bạn làm từ lúc thức dậy đến khi đi làm/học.
- **'I wake up at 6 AM, have breakfast, take a shower, and then go to work'**
- **'I usually wake up late, drink coffee, and rush to school'**
- **'I wake up, exercise, shower, and have breakfast before work'**
```

### Frontend Rendering

```typescript
// hint.markdown.vi or hint.markdown.en based on user language preference
<ReactMarkdown>{hint.markdown.vi}</ReactMarkdown>
```

---

## Onboarding Endpoints

### Complete Onboarding

**POST** `/onboarding/complete`

**Request Body**:
```json
{
  "display_name": "John Doe",
  "current_level": "A1",
  "target_level": "B2",
  "preferred_topics": ["business", "travel"]
}
```

**Response** (201 Created):
```json
{
  "success": true,
  "message": "Created",
  "data": {
    "is_success": true,
    "message": "Onboarding completed successfully",
    "profile": {
      "user_id": "794ab5cc-f0e1-708a-7902-6a087c2bb60c",
      "email": "user@example.com",
      "display_name": "John Doe",
      "current_level": "A1",
      "target_level": "B2",
      "current_streak": 0,
      "total_words_learned": 0,
      "role": "user",
      "is_active": true,
      "is_new_user": false
    }
  }
}
```

---

## Profile Endpoints

### Get Profile

**GET** `/profile`

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "user_id": "794ab5cc-f0e1-708a-7902-6a087c2bb60c",
    "email": "user@example.com",
    "display_name": "John Doe",
    "avatar_url": "https://example.com/avatar.jpg",
    "current_level": "A1",
    "target_level": "B2",
    "current_streak": 5,
    "total_words_learned": 150,
    "role": "user",
    "is_active": true,
    "is_new_user": false
  }
}
```

### Update Profile

**PATCH** `/profile`

**Request Body**:
```json
{
  "display_name": "Jane Doe",
  "avatar_url": "https://example.com/new-avatar.jpg",
  "target_level": "C1"
}
```

**Response** (200 OK): Same structure as Get Profile.

---

## Vocabulary Endpoints

### Translate Word

**POST** `/vocabulary/translate`

Translate an English word to Vietnamese with dictionary enrichment (phonetic, meanings, examples).

**Request Body**:
```json
{
  "word": "run",
  "sentence": "I run every morning.",
  "context": "I run every morning for exercise."
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `word` | ✅ | English word (1–100 chars) |
| `sentence` | ❌ | Sentence for AWS Translate context |
| `context` | ❌ | Context for phrasal verb detection |

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "word": "run",
    "translation_vi": "chạy",
    "phonetic": "/rʌn/",
    "definitions": [
      {
        "part_of_speech": "verb",
        "definition_en": "Move at a speed faster than a walk",
        "definition_vi": "Di chuyển với tốc độ nhanh hơn đi bộ",
        "example_en": "She runs five miles every day.",
        "example_vi": "Cô ấy chạy năm dặm mỗi ngày."
      }
    ],
    "synonyms": [],
    "response_time_ms": 320,
    "cached": false
  }
}
```

**Error Responses**:

| Status | Code | Meaning |
|--------|------|---------|
| `404` | `WORD_NOT_FOUND` | Word not in dictionary |
| `503` | `DICTIONARY_SERVICE_ERROR` | Dictionary API unavailable |
| `400` | `VALIDATION_ERROR` | Invalid request |

> **Note for frontend**: Use `definitions[0].definition_vi` as the flashcard meaning. Use `phonetic` and `definitions[0].example_en` for flashcard fields.

### Translate Sentence

**POST** `/vocabulary/translate-sentence`

**Request Body**:
```json
{
  "sentence": "How are you today?"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "sentence_en": "How are you today?",
    "sentence_vi": "Bạn khỏe không hôm nay?"
  }
}
```

---

## Flashcard Endpoints

### Create Flashcard

**POST** `/flashcards`

**Request Body**:
```json
{
  "vocab": "run",
  "vocab_type": "verb",
  "translation_vi": "chạy",
  "example_sentence": "She runs five miles every day.",
  "phonetic": "/rʌn/",
  "audio_url": "https://example.com/audio.mp3"
}
```

> `definition_vi` field đã bị xóa. Dùng `translation_vi` cho nghĩa của thẻ.

**Response** (201 Created):
```json
{
  "success": true,
  "message": "Created",
  "data": {
    "flashcard_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD",
    "word": "run",
    "translation_vi": "chạy",
    "phonetic": "/rʌn/",
    "audio_url": "https://example.com/audio.mp3",
    "example_sentence": "She runs five miles every day.",
    "created_at": "2026-04-26T07:25:13.798100+00:00"
  }
}
```

### List Flashcards

**GET** `/flashcards`

**Query Parameters**: `limit` (default: 20, max: 100), `last_key` (base64 pagination token)

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "cards": [
      {
        "flashcard_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD",
        "word": "run",
        "translation_vi": "chạy",
        "phonetic": "/rʌn/",
        "audio_url": "https://example.com/audio.mp3",
        "example_sentence": "She runs five miles every day.",
        "review_count": 3,
        "interval_days": 4,
        "difficulty": "good",
        "next_review_at": "2026-04-30T07:25:13.798100+00:00",
        "last_reviewed_at": "2026-04-26T07:25:13.798100+00:00"
      }
    ],
    "next_key": "<base64_token_or_null>"
  }
}
```

### Get Flashcard

**GET** `/flashcards/{flashcard_id}`

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "flashcard_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD",
    "word": "run",
    "translation_vi": "chạy",
    "phonetic": "/rʌn/",
    "audio_url": "https://example.com/audio.mp3",
    "example_sentence": "She runs five miles every day.",
    "review_count": 3,
    "interval_days": 4,
    "difficulty": "good",
    "last_reviewed_at": "2026-04-26T07:25:13.798100+00:00",
    "next_review_at": "2026-04-30T07:25:13.798100+00:00",
    "source_session_id": null,
    "source_turn_index": null
  }
}
```

### List Due Flashcards

**GET** `/flashcards/due`

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "cards": [
      {
        "flashcard_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD",
        "word": "run",
        "translation_vi": "chạy",
        "phonetic": "/rʌn/",
        "audio_url": "https://example.com/audio.mp3",
        "example_sentence": "She runs five miles every day.",
        "review_count": 3,
        "interval_days": 4,
        "next_review_at": "2026-04-26T07:25:13.798100+00:00",
        "last_reviewed_at": null
      }
    ]
  }
}
```

### Review Flashcard

**POST** `/flashcards/{flashcard_id}/review`

**Request Body**:
```json
{
  "rating": "good"
}
```

| Rating | Meaning |
|--------|---------|
| `forgot` | Không nhớ — reset interval |
| `hard` | Khó — interval tăng ít |
| `good` | Ổn — interval tăng bình thường |
| `easy` | Dễ — interval tăng nhiều |

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "flashcard_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD",
    "word": "run",
    "interval_days": 4,
    "review_count": 3,
    "last_reviewed_at": "2026-04-26T07:25:13.798100+00:00",
    "next_review_at": "2026-04-30T07:25:13.798100+00:00"
  }
}
```

---

## Scenario Endpoints

### List Scenarios

**GET** `/scenarios`

**No authentication required** (public endpoint).

**Query Parameters**: `limit` (default: 10), `level` (A1/A2/B1/B2/C1/C2)

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "scenarios": [
      {
        "scenario_id": "restaurant-ordering",
        "scenario_title": "Restaurant Ordering",
        "context": "restaurant",
        "roles": ["customer", "waiter"],
        "goals": ["order food", "ask for recommendations", "handle payment"],
        "is_active": true,
        "usage_count": 42,
        "difficulty_level": "A1",
        "order": 1,
        "created_at": "2026-01-01T00:00:00+00:00"
      }
    ],
    "total": 1
  }
}
```

---

## Speaking Session Endpoints

### Create Speaking Session

**POST** `/sessions`

**Request Body**:
```json
{
  "scenario_id": "restaurant-ordering",
  "learner_role_id": "customer",
  "ai_role_id": "waiter",
  "ai_gender": "female",
  "level": "B1",
  "selected_goal": "order food"
}
```

**Response** (201 Created):
```json
{
  "success": true,
  "message": "Created",
  "data": {
    "session_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD",
    "user_id": "794ab5cc-f0e1-708a-7902-6a087c2bb60c",
    "scenario_id": "restaurant-ordering",
    "status": "ACTIVE",
    "created_at": "2026-04-26T07:25:13.798100+00:00",
    "turn_count": 0,
    "updated_at": null,
    "completed_at": null
  }
}
```

### List Speaking Sessions

**GET** `/sessions`

**Query Parameters**: `limit` (default: 10)

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "sessions": [
      {
        "session_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD",
        "scenario_id": "restaurant-ordering",
        "status": "ACTIVE",
        "created_at": "2026-04-26T07:25:13.798100+00:00",
        "turn_count": 3,
        "updated_at": "2026-04-26T07:26:00.000000+00:00",
        "completed_at": null
      }
    ],
    "total": 1
  }
}
```

### Get Speaking Session

**GET** `/sessions/{session_id}`

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "session_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD",
    "scenario_id": "restaurant-ordering",
    "learner_role_id": "customer",
    "ai_role_id": "waiter",
    "ai_gender": "female",
    "level": "B1",
    "selected_goal": "order food",
    "status": "ACTIVE",
    "created_at": "2026-04-26T07:25:13.798100+00:00",
    "turn_count": 2,
    "turns": [
      {
        "turn_index": 1,
        "speaker": "user",
        "content": "Hello, I would like to order a coffee please.",
        "audio_url": "s3://bucket/audio.mp3",
        "created_at": "2026-04-26T07:25:20.000000+00:00"
      },
      {
        "turn_index": 2,
        "speaker": "ai",
        "content": "[warmly] Of course! What size would you like?",
        "delivery_cue": "[warmly]",
        "audio_url": "s3://bucket/ai-audio.mp3",
        "created_at": "2026-04-26T07:25:25.000000+00:00"
      }
    ]
  }
}
```

### Submit Speaking Turn

**POST** `/sessions/{session_id}/turns`

**Request Body**:
```json
{
  "text": "Hello, I would like to order a coffee please.",
  "audio_url": "s3://bucket/audio.mp3",
  "is_hint_used": false
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "session_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD",
    "status": "ACTIVE",
    "turn_count": 2,
    "user_turn": {
      "turn_index": 1,
      "speaker": "user",
      "content": "Hello, I would like to order a coffee please.",
      "audio_url": "s3://bucket/audio.mp3",
      "is_hint_used": false,
      "created_at": "2026-04-26T07:25:20.000000+00:00"
    },
    "ai_turn": {
      "turn_index": 2,
      "speaker": "ai",
      "content": "[warmly] Of course! What size would you like?",
      "delivery_cue": "[warmly]",
      "audio_url": "s3://bucket/ai-audio.mp3",
      "created_at": "2026-04-26T07:25:25.000000+00:00"
    },
    "analysis_keywords": ["coffee", "order"]
  }
}
```

### Complete Speaking Session

**POST** `/sessions/{session_id}/complete`

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "session_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD",
    "status": "COMPLETED",
    "completed_at": "2026-04-26T07:26:30.000000+00:00",
    "scoring": {
      "fluency_score": 75,
      "pronunciation_score": 80,
      "grammar_score": 70,
      "vocabulary_score": 85,
      "overall_score": 77,
      "feedback": "Good job! Your pronunciation is clear. Work on grammar and fluency."
    }
  }
}
```

---

## WebSocket Endpoints

**URL**: `wss://no8fa2u3qg.execute-api.ap-southeast-1.amazonaws.com/Prod`

### Connection

```
wss://...?token=<JWT_TOKEN>
```

### Start Session

**Action**: `start_session`

```json
{ "action": "start_session", "session_id": "..." }
```

**Response**:
```json
{
  "event": "SESSION_READY",
  "upload_url": "https://s3.amazonaws.com/...",
  "s3_key": "speaking/audio/...",
  "session_id": "..."
}
```

### Audio Uploaded

**Action**: `audio_uploaded`

```json
{ "action": "audio_uploaded", "session_id": "...", "s3_key": "speaking/audio/..." }
```

**Response Events**:
- `STT_RESULT` — Transcription result
- `STT_LOW_CONFIDENCE` — Confidence too low
- `TURN_SAVED` — Turn saved
- `AI_TEXT_CHUNK` — AI response text (streaming)
- `AI_AUDIO_URL` — AI audio URL

### Use Hint

**Action**: `use_hint`

```json
{ "action": "use_hint", "session_id": "..." }
```

**Response** (all CEFR levels A1–C2):
```json
{
  "event": "HINT_TEXT",
  "hint": {
    "markdown": {
      "vi": "AI muốn biết thói quen sáng của bạn. Hãy kể về những hoạt động bạn làm từ lúc thức dậy đến khi đi làm/học.\n- **'I wake up at 6 AM, have breakfast, take a shower, and then go to work'**\n- **'I usually wake up late, drink coffee, and rush to school'**",
      "en": "AI wants to know your morning routine. Tell about what you do from waking up to going to work/school.\n- **'I wake up at 6 AM, have breakfast, take a shower, and then go to work'**\n- **'I usually wake up late, drink coffee, and rush to school'**"
    }
  }
}
```

> Render `hint.markdown.vi` hoặc `hint.markdown.en` bằng markdown renderer. Hints use natural conversational flow with bullet-point examples.

### Send Message Turn

**Action**: `send_message_turn`

```json
{
  "action": "send_message_turn",
  "session_id": "...",
  "text": "Hello, I would like to order a coffee please.",
  "is_hint_used": false
}
```

**Response Events**: `TURN_SAVED`, `AI_TEXT_CHUNK`, `AI_AUDIO_URL`

### End Session

**Action**: `end_session`

```json
{ "action": "end_session", "session_id": "..." }
```

**Response**:
```json
{ "event": "SCORING_COMPLETE", "session_id": "..." }
```

---

## Admin Endpoints

### List Admin Users

**GET** `/admin/users`

**Query Parameters**: `limit` (default: 20)

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "users": [
      {
        "user_id": "794ab5cc-f0e1-708a-7902-6a087c2bb60c",
        "email": "user@example.com",
        "display_name": "John Doe",
        "role": "learner",
        "is_active": true,
        "total_words_learned": 150,
        "joined_at": "2026-01-01T00:00:00+00:00"
      }
    ],
    "total_count": 1
  }
}
```

### Update Admin User

**PATCH** `/admin/users/{user_id}`

**Request Body**:
```json
{ "is_active": false, "current_level": "B1", "target_level": "C1" }
```

**Response** (200 OK): Updated user object.

### List Admin Scenarios

**GET** `/admin/scenarios`

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "scenarios": [
      {
        "scenario_id": "restaurant-ordering",
        "scenario_title": "Restaurant Ordering",
        "context": "restaurant",
        "roles": ["customer", "waiter"],
        "goals": ["order food", "ask for recommendations"],
        "is_active": true,
        "usage_count": 42,
        "difficulty_level": "A1",
        "order": 1,
        "notes": "",
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00"
      }
    ],
    "total_count": 1
  }
}
```

### Create Admin Scenario

**POST** `/admin/scenarios`

**Request Body**:
```json
{
  "scenario_title": "Hotel Booking",
  "context": "hotel",
  "difficulty_level": "A2",
  "roles": ["guest", "receptionist"],
  "goals": ["book a room", "ask about amenities"],
  "order": 2,
  "notes": "",
  "is_active": true
}
```

> `roles` phải có đúng **2 phần tử** (learner role và AI role).

**Response** (201 Created): Created scenario object.

### Update Admin Scenario

**PATCH** `/admin/scenarios/{scenario_id}`

**Request Body** (tất cả fields đều optional):
```json
{
  "scenario_title": "Hotel Booking (Updated)",
  "is_active": false,
  "order": 3
}
```

**Response** (200 OK): Updated scenario object.

---

## Turn Analysis (Formative Assessment)

### Analyze Turn (WebSocket Action)

**Action:** `ANALYZE_TURN`

Provides turn-by-turn formative assessment for learner's conversation.

**Use case:** User clicks "Analyze" button after speaking to get feedback on their performance.

**Request:**
```json
{
  "action": "ANALYZE_TURN",
  "session_id": "01HXXX...",
  "turn_index": 3
}
```

**Response Event:** `TURN_ANALYSIS`
```json
{
  "event": "TURN_ANALYSIS",
  "analysis": {
    "markdown": {
      "vi": "## ✅ Điểm mạnh\n- Bạn đã dùng từ vựng phù hợp...\n\n## ⚠️ Lỗi cần sửa\n- Thiếu động từ 'to be'...",
      "en": "## ✅ Strengths\n- You used appropriate vocabulary...\n\n## ⚠️ Mistakes to Fix\n- Missing 'to be' verb..."
    }
  }
}
```

**Analysis sections:**
- **✅ Strengths**: What the learner did well
- **⚠️ Mistakes**: Grammar, vocabulary, or usage errors
- **💡 Improvements**: Suggestions for better expression
- **🎯 Overall Assessment**: Summary and encouragement

**Features:**
- Level-adaptive feedback (A1-C2)
- Bilingual markdown (Vietnamese + English)
- AI provides immediate, actionable feedback
- Consistent with hint system (both use WebSocket)

---

## AI Model Information

### Amazon Nova Micro (Primary)

- **Model ID**: `apac.amazon.nova-micro-v1:0`
- **Region**: ap-southeast-1

### Proficiency Level Configuration

| Level | Max Tokens | Temperature | Fallback |
|-------|-----------|-------------|----------|
| A1 | 40 | 0.6 | None |
| A2 | 60 | 0.65 | None |
| B1 | 100 | 0.7 | Lite (5%) |
| B2 | 150 | 0.75 | Lite (10%) |
| C1 | 200 | 0.8 | Pro (30%) |
| C2 | 250 | 0.85 | Pro (40%) |

---

## Changelog

### v2.3 (April 26, 2026)

**Turn-by-Turn Analysis (Formative Assessment)**
- New WebSocket action: `ANALYZE_TURN` (consistent with hint system)
- Provides on-demand feedback with strengths, mistakes, improvements, and overall assessment
- Bilingual markdown output (Vietnamese + English)
- Level-adaptive analysis (A1-C2)
- AI provides personalized guidance based on learner performance
- Event: `TURN_ANALYSIS` with markdown payload

**Prompt Caching Refactor**
- Removed manual cache_control approach (Claude-specific)
- Amazon Nova automatic prompt caching (no configuration needed)
- Simplified code, removed unnecessary complexity

### v2.2 (April 26, 2026)

**Hint System — Rich Markdown Format**
- Hint response changed from `{ hint: {vi, en} }` → `{ markdown: {vi, en} }` — full markdown string
- Frontend renders with any markdown renderer, no custom parsing needed
- Level-adaptive sections:
  - A1/A2 `vocabulary_suggestion`: 💬 Tình huống · 📝 Từ khoá (với nghĩa) · ✅ Câu mẫu dùng ngay · 💡 Mẹo nhỏ
  - B1/B2 `strategic_guidance`: 💬 Tình huống · 🎯 Cách tiếp cận · ✅ Câu mẫu tham khảo · 💡 Ngữ pháp & từ nối
  - C1/C2 `metacognitive_prompt`: 💬 Tình huống · 🎯 Phân tích ngữ cảnh · ✅ Lựa chọn nâng cao · 💡 Phong cách & sắc thái
- Delivery cue stripped from AI message before building hint context

**Scenario & Admin API fixes**
- `roles` is `List[str]` (e.g. `["customer", "waiter"]`), not array of objects
- Admin create scenario: correct fields `scenario_title`, `context`, `difficulty_level`
- Admin list/update user: correct fields `joined_at`, `total_words_learned`, `total_count`
- Fixed `AdminController` type mismatch — use cases return dicts, not entity objects

### v2.1 (April 26, 2026)

**Vocabulary API**
- `POST /vocabulary/translate` response now includes `definitions[]`, `phonetic`, `response_time_ms`, `cached`
- Added `context` field to request for phrasal verb detection
- New error codes: `WORD_NOT_FOUND` (404), `DICTIONARY_SERVICE_ERROR` (503)
- Batch translation: word + definitions + examples in a single AWS Translate call

**Flashcard API**
- Removed `definition_vi` — use `translation_vi` instead

**Hint System**
- Hints available for all CEFR levels (previously A1/A2 only)
- Level-adaptive strategies: `vocabulary_suggestion` / `strategic_guidance` / `metacognitive_prompt`
- Delivery cue extraction fixed to match start of response only

**Conversation**
- Amazon Nova automatic prompt caching (no manual configuration needed)
- Greeting generator fallback per level
- `ScaffoldingSystem` removed — replaced by `StructuredHintGenerator`

---

## Troubleshooting

### 401 Unauthorized
- Token expired or missing `Authorization: Bearer <TOKEN>` header

### 404 WORD_NOT_FOUND
- Word doesn't exist in dictionary API — show user-friendly message

### 503 DICTIONARY_SERVICE_ERROR
- Dictionary API temporarily down — retry after a few seconds

### 422 Unprocessable Entity
- Missing required fields or invalid data types

### 500 Internal Server Error
- Check CloudWatch logs: `/aws/lambda/lexi-be-*`

---

## Example Workflows

### Vocabulary → Flashcard

```bash
# 1. Translate word (get enriched data)
POST /vocabulary/translate
{ "word": "run", "context": "I run every morning" }

# 2. Create flashcard using response data
POST /flashcards
{
  "vocab": "run",
  "vocab_type": "verb",
  "translation_vi": "<from translation_vi>",
  "example_sentence": "<from definitions[0].example_en>",
  "phonetic": "<from phonetic>",
  "audio_url": "<from audio_url>"
}

# 3. Review flashcard
POST /flashcards/{flashcard_id}/review
{ "is_correct": true }
```

### Speaking Practice Session

```bash
# 1. Create session
POST /sessions
{
  "scenario_id": "restaurant-ordering",
  "learner_role_id": "customer",
  "ai_role_id": "waiter",
  "ai_gender": "female",
  "level": "B1",
  "selected_goal": "order food"
}

# 2. Submit turn
POST /sessions/{session_id}/turns
{ "text": "I'd like a coffee please.", "is_hint_used": false }

# 3. Complete session
POST /sessions/{session_id}/complete
```

---

**Last Updated**: April 26, 2026  
**API Version**: 2.2  
**Status**: Production
