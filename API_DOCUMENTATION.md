# Lexi API Documentation

**Version**: 2.0  
**Last Updated**: April 25, 2026  
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

Include the token in the `Authorization` header:

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
  "data": {
    // Response data
  }
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

- `200 OK` - Request successful
- `201 Created` - Resource created
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Access denied
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

---

## Error Handling

Common error codes:

| Code | Meaning |
|------|---------|
| `BAD_REQUEST` | Invalid JSON or missing required fields |
| `VALIDATION_ERROR` | Request data validation failed |
| `NOT_FOUND` | Resource not found |
| `UNAUTHORIZED` | Authentication failed |
| `FORBIDDEN` | Permission denied |

---

## Delivery Cues & Tone

AI responses include delivery cues that indicate the emotional tone of the response. These are used for implicit error correction and natural conversation flow.

### Available Delivery Cues

| Cue | Meaning | Use Case |
|-----|---------|----------|
| `[warmly]` | Friendly and encouraging | Praise, encouragement, positive feedback |
| `[encouragingly]` | Motivating and supportive | When learner does well, needs motivation |
| `[gently]` | Tactful and considerate | Error correction, off-topic redirection, sensitive topics |
| `[thoughtfully]` | Engaging in deep discussion | Complex topics, advanced levels (B2+) |
| `[naturally]` | Conversational and neutral | Normal conversation flow |

### Frontend Implementation

**Step 1: Extract delivery cue from AI response**
```typescript
const tone = turn.delivery_cue?.replace(/[\[\]]/g, "") || "naturally";
// "[warmly]" → "warmly"
```

**Step 2: Clean text for display (remove delivery cue)**
```typescript
const cleanText = turn.content.replace(/\[[^\]]+\]\s*/, "");
// "[warmly] Hello" → "Hello"
```

**Step 3: Display with tone indicator (color-based)**
```typescript
const TONE_COLORS = {
  warmly: "#10b981",        // Green
  encouragingly: "#3b82f6", // Blue
  gently: "#f59e0b",        // Yellow
  thoughtfully: "#8b5cf6",  // Purple
  naturally: "#6b7280",     // Gray
};

// Use color for text or left border indicator
<div style={{ borderLeft: `3px solid ${TONE_COLORS[tone]}` }}>
  {cleanText}
</div>
```

---

## Hint Formatting

Hints for A1-A2 learners are bilingual (Vietnamese + English) and support multiple display formats.

### Hint Response Format

```json
{
  "hint": {
    "vietnamese": "Bạn có thể nói 'I went to the beach yesterday'",
    "english": "You can say 'I went to the beach yesterday'",
    "hint_level": "vocabulary_hint",
    "silence_duration": 20
  }
}
```

### Hint Levels

| Level | Description |
|-------|-------------|
| `gentle_prompt` | Encourage learner to continue (10s silence) |
| `vocabulary_hint` | Suggest relevant vocabulary (20s silence) |
| `sentence_starter` | Provide sentence starter example (30s silence) |

### Context-Aware Hints

Hints are generated based on:
- **Scenario**: Restaurant, Airport, Hotel, Shopping, General
- **Grammar Pattern**: Past tense, present tense, questions, short responses
- **Last Utterance**: Learner's previous response
- **Conversation Goals**: Session objectives

**Example: Restaurant scenario with past tense error**
```
Learner: "I go restaurant yesterday"
Hint: "You can say 'I went to the restaurant yesterday'"
```

**Example: Airport scenario with vocabulary gap**
```
Learner: "Where gate?"
Hint: "Try: 'Where is gate 5?' or 'Can you tell me where gate 5 is?'"
```
| `SERVICE_ERROR` | External service error (Bedrock, Translate, etc.) |
| `SUBMISSION_FAILED` | Turn submission failed |
| `COMPLETION_FAILED` | Session completion failed |

---

## Onboarding Endpoints

### Complete Onboarding

**POST** `/onboarding/complete`

Complete user onboarding and set initial profile.

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

Retrieve current user's profile information.

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

Update user profile information.

**Request Body**:
```json
{
  "display_name": "Jane Doe",
  "avatar_url": "https://example.com/new-avatar.jpg",
  "target_level": "C1"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "user_id": "794ab5cc-f0e1-708a-7902-6a087c2bb60c",
    "email": "user@example.com",
    "display_name": "Jane Doe",
    "avatar_url": "https://example.com/new-avatar.jpg",
    "current_level": "A1",
    "target_level": "C1",
    "current_streak": 5,
    "total_words_learned": 150,
    "role": "user",
    "is_active": true,
    "is_new_user": false
  }
}
```

---

## Vocabulary Endpoints

### Translate Word

**POST** `/vocabulary/translate`

Translate a single English word to Vietnamese.

**Request Body**:
```json
{
  "word": "hello"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "word": "hello",
    "translation_vi": "xin chào"
  }
}
```

### Translate Sentence

**POST** `/vocabulary/translate-sentence`

Translate an English sentence to Vietnamese.

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

Create a new flashcard for vocabulary learning.

**Request Body**:
```json
{
  "word": "hello",
  "translation": "xin chào",
  "example_sentence": "Hello, how are you?",
  "difficulty": "easy"
}
```

**Response** (201 Created):
```json
{
  "success": true,
  "message": "Created",
  "data": {
    "flashcard_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD",
    "word": "hello",
    "translation": "xin chào",
    "example_sentence": "Hello, how are you?",
    "difficulty": "easy",
    "created_at": "2026-04-25T07:25:13.798100+00:00",
    "next_review": "2026-04-26T07:25:13.798100+00:00"
  }
}
```

### List Flashcards

**GET** `/flashcards`

List all flashcards for the current user.

**Query Parameters**:
- `limit` (optional, default: 10) - Maximum number of flashcards to return
- `offset` (optional, default: 0) - Number of flashcards to skip

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "flashcards": [
      {
        "flashcard_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD",
        "word": "hello",
        "translation": "xin chào",
        "difficulty": "easy",
        "created_at": "2026-04-25T07:25:13.798100+00:00",
        "next_review": "2026-04-26T07:25:13.798100+00:00"
      }
    ],
    "total": 1
  }
}
```

### Get Flashcard

**GET** `/flashcards/{flashcard_id}`

Retrieve a specific flashcard.

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "flashcard_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD",
    "word": "hello",
    "translation": "xin chào",
    "example_sentence": "Hello, how are you?",
    "difficulty": "easy",
    "created_at": "2026-04-25T07:25:13.798100+00:00",
    "next_review": "2026-04-26T07:25:13.798100+00:00"
  }
}
```

### List Due Flashcards

**GET** `/flashcards/due`

List flashcards that are due for review.

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "flashcards": [
      {
        "flashcard_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD",
        "word": "hello",
        "translation": "xin chào",
        "difficulty": "easy",
        "next_review": "2026-04-25T07:25:13.798100+00:00"
      }
    ],
    "total": 1
  }
}
```

### Review Flashcard

**POST** `/flashcards/{flashcard_id}/review`

Submit a review for a flashcard (mark as correct/incorrect).

**Request Body**:
```json
{
  "is_correct": true,
  "time_spent_ms": 5000
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "flashcard_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD",
    "word": "hello",
    "next_review": "2026-04-27T07:25:13.798100+00:00",
    "difficulty": "medium"
  }
}
```

---

## Scenario Endpoints

### List Scenarios

**GET** `/scenarios`

List all available speaking scenarios. **No authentication required** (public endpoint).

**Query Parameters**:
- `limit` (optional, default: 10) - Maximum number of scenarios to return
- `level` (optional) - Filter by proficiency level (A1, A2, B1, B2, C1, C2)

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "scenarios": [
      {
        "scenario_id": "restaurant-ordering",
        "title": "Restaurant Ordering",
        "description": "Order food at a restaurant",
        "level": "A1",
        "roles": [
          {
            "role_id": "customer",
            "name": "Customer",
            "description": "You are a customer ordering food"
          },
          {
            "role_id": "waiter",
            "name": "Waiter",
            "description": "You are a waiter taking orders"
          }
        ],
        "goals": ["order food", "ask for recommendations", "handle payment"],
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

Create a new speaking practice session.

**Request Body**:
```json
{
  "scenario_id": "restaurant-ordering",
  "learner_role_id": "customer",
  "ai_role_id": "waiter",
  "ai_gender": "female",
  "level": "B1",
  "selected_goals": ["order food", "ask for recommendations"]
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
    "created_at": "2026-04-25T07:25:13.798100+00:00",
    "turn_count": 0,
    "updated_at": null,
    "completed_at": null
  }
}
```

### List Speaking Sessions

**GET** `/sessions`

List all speaking sessions for the current user.

**Query Parameters**:
- `limit` (optional, default: 10) - Maximum number of sessions to return

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "sessions": [
      {
        "session_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD",
        "user_id": "794ab5cc-f0e1-708a-7902-6a087c2bb60c",
        "scenario_id": "restaurant-ordering",
        "status": "ACTIVE",
        "created_at": "2026-04-25T07:25:13.798100+00:00",
        "turn_count": 3,
        "updated_at": "2026-04-25T07:26:00.000000+00:00",
        "completed_at": null
      }
    ],
    "total": 1
  }
}
```

### Get Speaking Session

**GET** `/sessions/{session_id}`

Retrieve details of a specific speaking session.

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "session_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD",
    "user_id": "794ab5cc-f0e1-708a-7902-6a087c2bb60c",
    "scenario_id": "restaurant-ordering",
    "learner_role_id": "customer",
    "ai_role_id": "waiter",
    "ai_gender": "female",
    "level": "B1",
    "selected_goals": ["order food", "ask for recommendations"],
    "status": "ACTIVE",
    "created_at": "2026-04-25T07:25:13.798100+00:00",
    "turn_count": 3,
    "updated_at": "2026-04-25T07:26:00.000000+00:00",
    "completed_at": null,
    "turns": [
      {
        "turn_index": 1,
        "speaker": "user",
        "content": "Hello, I would like to order a coffee please.",
        "audio_url": "s3://bucket/audio.mp3",
        "created_at": "2026-04-25T07:25:20.000000+00:00"
      },
      {
        "turn_index": 2,
        "speaker": "ai",
        "content": "[warmly] Of course! What size would you like?",
        "delivery_cue": "[warmly]",
        "audio_url": "s3://bucket/ai-audio.mp3",
        "created_at": "2026-04-25T07:25:25.000000+00:00"
      }
    ]
  }
}
```

### Submit Speaking Turn

**POST** `/sessions/{session_id}/turns`

Submit a user's spoken turn and get AI response with implicit error correction and context-aware scaffolding.

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
    "user_id": "794ab5cc-f0e1-708a-7902-6a087c2bb60c",
    "scenario_id": "restaurant-ordering",
    "status": "ACTIVE",
    "created_at": "2026-04-25T07:25:13.798100+00:00",
    "turn_count": 2,
    "updated_at": "2026-04-25T07:25:30.000000+00:00",
    "completed_at": null,
    "user_turn": {
      "turn_index": 1,
      "speaker": "user",
      "content": "Hello, I would like to order a coffee please.",
      "audio_url": "s3://bucket/audio.mp3",
      "is_hint_used": false,
      "created_at": "2026-04-25T07:25:20.000000+00:00"
    },
    "ai_turn": {
      "turn_index": 2,
      "speaker": "ai",
      "content": "[warmly] Of course! What size would you like?",
      "delivery_cue": "[warmly]",
      "audio_url": "s3://bucket/ai-audio.mp3",
      "created_at": "2026-04-25T07:25:25.000000+00:00"
    },
    "analysis_keywords": ["coffee", "order"]
  }
}
```

**Response Fields**:
- `user_turn` - User's submitted turn with analysis
- `ai_turn` - AI's response with delivery cue
- `delivery_cue` - Tone indicator (e.g., "[warmly]", "[thoughtfully]", "[gently]", "[encouragingly]", "[naturally]")
- `analysis_keywords` - Key phrases extracted from user's speech

### Complete Speaking Session

**POST** `/sessions/{session_id}/complete`

Complete a speaking session and get scoring results.

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "session_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD",
    "user_id": "794ab5cc-f0e1-708a-7902-6a087c2bb60c",
    "scenario_id": "restaurant-ordering",
    "status": "COMPLETED",
    "created_at": "2026-04-25T07:25:13.798100+00:00",
    "turn_count": 3,
    "updated_at": "2026-04-25T07:26:00.000000+00:00",
    "completed_at": "2026-04-25T07:26:30.000000+00:00",
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

WebSocket connections use the URL: `wss://no8fa2u3qg.execute-api.ap-southeast-1.amazonaws.com/Prod`

### Connection

**Action**: `$connect`

Connect to WebSocket with authentication token.

**Query Parameters**:
- `token` - Cognito JWT token

**Example**:
```
wss://no8fa2u3qg.execute-api.ap-southeast-1.amazonaws.com/Prod?token=<JWT_TOKEN>
```

### Disconnect

**Action**: `$disconnect`

Automatically triggered when client disconnects.

### Start Session

**Action**: `start_session`

Initialize a speaking session for WebSocket streaming.

**Request**:
```json
{
  "action": "start_session",
  "session_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD"
}
```

**Response**:
```json
{
  "event": "SESSION_READY",
  "upload_url": "https://s3.amazonaws.com/...",
  "s3_key": "speaking/audio/...",
  "session_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD"
}
```

### Audio Uploaded

**Action**: `audio_uploaded`

Notify that audio has been uploaded to S3.

**Request**:
```json
{
  "action": "audio_uploaded",
  "session_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD",
  "s3_key": "speaking/audio/..."
}
```

**Response Events**:
- `STT_RESULT` - Transcription successful
- `STT_LOW_CONFIDENCE` - Transcription confidence too low
- `TURN_SAVED` - Turn saved to database
- `AI_TEXT_CHUNK` - AI response text
- `AI_AUDIO_URL` - AI response audio URL

### Use Hint

**Action**: `use_hint`

Get a contextual hint for the current turn.

**Request**:
```json
{
  "action": "use_hint",
  "session_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD"
}
```

**Response**:
```json
{
  "event": "HINT_TEXT",
  "hint": "You could say: I would like to order a coffee, please."
}
```

### Send Message Turn

**Action**: `send_message_turn`

Submit a text-based turn (not audio).

**Request**:
```json
{
  "action": "send_message_turn",
  "session_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD",
  "text": "Hello, I would like to order a coffee please.",
  "is_hint_used": false
}
```

**Response Events**:
- `TURN_SAVED` - Turn saved
- `AI_TEXT_CHUNK` - AI response
- `AI_AUDIO_URL` - AI audio

### End Session

**Action**: `end_session`

Complete the speaking session.

**Request**:
```json
{
  "action": "end_session",
  "session_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD"
}
```

**Response**:
```json
{
  "event": "SCORING_COMPLETE",
  "session_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD"
}
```

---

## Admin Endpoints

### List Admin Users

**GET** `/admin/users`

List all users (admin only).

**Query Parameters**:
- `limit` (optional, default: 10)
- `offset` (optional, default: 0)

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
        "current_level": "A1",
        "role": "user",
        "is_active": true,
        "created_at": "2026-01-01T00:00:00+00:00"
      }
    ],
    "total": 1
  }
}
```

### Update Admin User

**PATCH** `/admin/users/{user_id}`

Update user information (admin only).

**Request Body**:
```json
{
  "is_active": false,
  "role": "admin"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "user_id": "794ab5cc-f0e1-708a-7902-6a087c2bb60c",
    "email": "user@example.com",
    "display_name": "John Doe",
    "current_level": "A1",
    "role": "admin",
    "is_active": false,
    "created_at": "2026-01-01T00:00:00+00:00"
  }
}
```

### List Admin Scenarios

**GET** `/admin/scenarios`

List all scenarios (admin only).

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "scenarios": [
      {
        "scenario_id": "restaurant-ordering",
        "title": "Restaurant Ordering",
        "description": "Order food at a restaurant",
        "level": "A1",
        "created_at": "2026-01-01T00:00:00+00:00"
      }
    ],
    "total": 1
  }
}
```

### Create Admin Scenario

**POST** `/admin/scenarios`

Create a new scenario (admin only).

**Request Body**:
```json
{
  "scenario_id": "hotel-booking",
  "title": "Hotel Booking",
  "description": "Book a hotel room",
  "level": "A2",
  "roles": [
    {
      "role_id": "guest",
      "name": "Guest",
      "description": "You are a guest booking a hotel"
    },
    {
      "role_id": "receptionist",
      "name": "Receptionist",
      "description": "You are a hotel receptionist"
    }
  ],
  "goals": ["book a room", "ask about amenities", "negotiate price"]
}
```

**Response** (201 Created):
```json
{
  "success": true,
  "message": "Created",
  "data": {
    "scenario_id": "hotel-booking",
    "title": "Hotel Booking",
    "description": "Book a hotel room",
    "level": "A2",
    "created_at": "2026-04-25T07:25:13.798100+00:00"
  }
}
```

### Update Admin Scenario

**PATCH** `/admin/scenarios/{scenario_id}`

Update scenario information (admin only).

**Request Body**:
```json
{
  "title": "Hotel Booking (Updated)",
  "description": "Book a hotel room with special requests"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "scenario_id": "hotel-booking",
    "title": "Hotel Booking (Updated)",
    "description": "Book a hotel room with special requests",
    "level": "A2",
    "created_at": "2026-04-25T07:25:13.798100+00:00"
  }
}
```

---

## AI Model Information

### Amazon Nova Micro (Primary Model)

- **Model ID**: `apac.amazon.nova-micro-v1:0` (APAC inference profile)
- **Region**: ap-southeast-1 (Singapore)
- **Use Cases**: 
  - Conversation generation for speaking practice
  - Performance scoring and feedback
  - Contextual hint generation
- **Max Tokens**: 40-250 (depends on proficiency level)
- **Temperature**: 0.6-0.85 (depends on proficiency level)

### Proficiency Level Configuration

| Level | Model | Max Tokens | Temperature | Fallback |
|-------|-------|-----------|-------------|----------|
| A1 | Micro | 40 | 0.6 | None |
| A2 | Micro | 60 | 0.65 | None |
| B1 | Micro | 100 | 0.7 | Lite (5%) |
| B2 | Micro | 150 | 0.75 | Lite (10%) |
| C1 | Micro | 200 | 0.8 | Pro (30%) |
| C2 | Micro | 250 | 0.85 | Pro (40%) |

---

## Rate Limiting

- **Default**: 100 requests per minute per user
- **Speaking Sessions**: 10 concurrent sessions per user
- **WebSocket**: 1 connection per user

---

## Troubleshooting

### 401 Unauthorized

- Token expired: Get a new token
- Invalid token: Check token format
- Missing Authorization header: Include `Authorization: Bearer <TOKEN>`

### 422 Unprocessable Entity

- Missing required fields: Check request body
- Invalid field values: Verify data types and formats
- Validation failed: Check error message for details

### 500 Internal Server Error

- Bedrock service unavailable: Retry after a few seconds
- Database error: Check CloudWatch logs
- External service error: Check service status

### WebSocket Connection Failed

- Invalid token: Verify JWT token is valid
- Token expired: Get a new token
- Network issue: Check internet connection

---

## Example Workflows

### Complete Speaking Practice Session

1. **Create Session**
   ```bash
   POST /sessions
   {
     "scenario_id": "restaurant-ordering",
     "learner_role_id": "customer",
     "ai_role_id": "waiter",
     "ai_gender": "female",
     "level": "B1",
     "selected_goals": ["order food"]
   }
   ```

2. **Submit Turn**
   ```bash
   POST /sessions/{session_id}/turns
   {
     "text": "Hello, I would like to order a coffee please.",
     "audio_url": "s3://bucket/audio.mp3",
     "is_hint_used": false
   }
   ```

3. **Complete Session**
   ```bash
   POST /sessions/{session_id}/complete
   ```

4. **Get Scoring**
   - Response includes fluency, pronunciation, grammar, vocabulary scores
   - Personalized feedback in Vietnamese

### Vocabulary Learning

1. **Translate Word**
   ```bash
   POST /vocabulary/translate
   { "word": "hello" }
   ```

2. **Create Flashcard**
   ```bash
   POST /flashcards
   {
     "word": "hello",
     "translation": "xin chào",
     "example_sentence": "Hello, how are you?"
   }
   ```

3. **Review Flashcard**
   ```bash
   POST /flashcards/{flashcard_id}/review
   { "is_correct": true }
   ```

---

## Support

For issues or questions:
- Check CloudWatch logs: `/aws/lambda/lexi-be-*`
- Review error codes and messages
- Contact development team

---

**Last Updated**: April 25, 2026  
**API Version**: 2.0  
**Status**: Production
