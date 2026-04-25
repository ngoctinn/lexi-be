# Lexi API - Detailed Examples & Use Cases

---

## Table of Contents

1. [Complete User Journey](#complete-user-journey)
2. [Speaking Practice Workflow](#speaking-practice-workflow)
3. [Vocabulary Learning Workflow](#vocabulary-learning-workflow)
4. [Admin Operations](#admin-operations)
5. [Error Handling Examples](#error-handling-examples)
6. [WebSocket Real-time Examples](#websocket-real-time-examples)

---

## Complete User Journey

### Step 1: User Registration & Onboarding

**Scenario**: New user signs up and completes onboarding.

```bash
# 1. User signs up via Cognito (handled by frontend)
# 2. Cognito triggers PostConfirmation Lambda
# 3. User gets JWT token

# 4. Complete onboarding
curl -X POST https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod/onboarding/complete \
  -H "Authorization: Bearer eyJraWQiOiJBeUZDOGxXdkpiTnprUUJaQjNXc2FWeDRDUGhXdng2RXE1OHBxaW9uZ200PSIsImFsZyI6IlJTMjU2In0..." \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Nguyễn Văn A",
    "current_level": "A1",
    "target_level": "B2",
    "preferred_topics": ["business", "travel", "daily-life"]
  }'

# Response (201 Created)
{
  "success": true,
  "message": "Created",
  "data": {
    "is_success": true,
    "message": "Onboarding completed successfully",
    "profile": {
      "user_id": "794ab5cc-f0e1-708a-7902-6a087c2bb60c",
      "email": "user@example.com",
      "display_name": "Nguyễn Văn A",
      "avatar_url": null,
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

### Step 2: View & Update Profile

```bash
# Get profile
curl -X GET https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod/profile \
  -H "Authorization: Bearer $TOKEN"

# Response (200 OK)
{
  "success": true,
  "message": "Success",
  "data": {
    "user_id": "794ab5cc-f0e1-708a-7902-6a087c2bb60c",
    "email": "user@example.com",
    "display_name": "Nguyễn Văn A",
    "avatar_url": null,
    "current_level": "A1",
    "target_level": "B2",
    "current_streak": 0,
    "total_words_learned": 0,
    "role": "user",
    "is_active": true,
    "is_new_user": false
  }
}

# Update profile with avatar
curl -X PATCH https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod/profile \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Nguyễn Văn A",
    "avatar_url": "https://example.com/avatar.jpg",
    "target_level": "C1"
  }'

# Response (200 OK)
{
  "success": true,
  "message": "Success",
  "data": {
    "user_id": "794ab5cc-f0e1-708a-7902-6a087c2bb60c",
    "email": "user@example.com",
    "display_name": "Nguyễn Văn A",
    "avatar_url": "https://example.com/avatar.jpg",
    "current_level": "A1",
    "target_level": "C1",
    "current_streak": 0,
    "total_words_learned": 0,
    "role": "user",
    "is_active": true,
    "is_new_user": false
  }
}
```

---

## Speaking Practice Workflow

### Complete Speaking Session Flow

**Scenario**: User practices restaurant ordering at B1 level.

#### Step 1: Browse Available Scenarios

```bash
# List all scenarios (no auth required)
curl -X GET "https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod/scenarios?level=B1"

# Response (200 OK)
{
  "success": true,
  "message": "Success",
  "data": {
    "scenarios": [
      {
        "scenario_id": "restaurant-ordering",
        "title": "Restaurant Ordering",
        "description": "Order food at a restaurant and handle payment",
        "level": "B1",
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
        "goals": [
          "order food",
          "ask for recommendations",
          "handle payment"
        ],
        "created_at": "2026-01-01T00:00:00+00:00"
      },
      {
        "scenario_id": "hotel-booking",
        "title": "Hotel Booking",
        "description": "Book a hotel room",
        "level": "B1",
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
        "goals": [
          "book a room",
          "ask about amenities",
          "negotiate price"
        ],
        "created_at": "2026-01-01T00:00:00+00:00"
      }
    ],
    "total": 2
  }
}
```

#### Step 2: Create Speaking Session

```bash
# Create session for restaurant ordering
curl -X POST https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_id": "restaurant-ordering",
    "learner_role_id": "customer",
    "ai_role_id": "waiter",
    "ai_gender": "female",
    "level": "B1",
    "selected_goals": ["order food", "ask for recommendations"]
  }'

# Response (201 Created)
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

#### Step 3: Submit First Turn

```bash
# User speaks: "Hello, I would like to order a coffee please."
# Audio uploaded to S3 at: s3://bucket/speaking/audio/abc123.mp3

curl -X POST https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod/sessions/01KQ1R5T9B44RWK3WJZNDJ64ZD/turns \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, I would like to order a coffee please.",
    "audio_url": "s3://bucket/speaking/audio/abc123.mp3",
    "is_hint_used": false
  }'

# Response (200 OK)
# Note: Response shows minimal data - full turn data is in session details
{
  "success": true,
  "message": "Success",
  "data": {
    "session_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD",
    "user_id": "794ab5cc-f0e1-708a-7902-6a087c2bb60c",
    "scenario_id": "restaurant-ordering",
    "status": "ACTIVE",
    "created_at": "2026-04-25T07:25:13.798100+00:00",
    "turn_count": 1,
    "updated_at": "2026-04-25T07:25:30.000000+00:00",
    "completed_at": null
  }
}

# Behind the scenes:
# 1. Comprehend analyzes user's speech
# 2. Bedrock Nova Micro generates AI response
# 3. Polly synthesizes AI response to audio
# 4. Metrics recorded (TTFT, latency, cost)
```

#### Step 4: Get Session Details with Turns

```bash
# Get full session with all turns
curl -X GET https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod/sessions/01KQ1R5T9B44RWK3WJZNDJ64ZD \
  -H "Authorization: Bearer $TOKEN"

# Response (200 OK)
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
    "turn_count": 2,
    "updated_at": "2026-04-25T07:25:45.000000+00:00",
    "completed_at": null,
    "turns": [
      {
        "turn_index": 1,
        "speaker": "user",
        "content": "Hello, I would like to order a coffee please.",
        "audio_url": "s3://bucket/speaking/audio/abc123.mp3",
        "created_at": "2026-04-25T07:25:20.000000+00:00"
      },
      {
        "turn_index": 2,
        "speaker": "ai",
        "content": "Of course! What size would you like? We have small, medium, and large.",
        "audio_url": "s3://bucket/speaking/audio/ai-response-1.mp3",
        "created_at": "2026-04-25T07:25:25.000000+00:00"
      }
    ]
  }
}
```

#### Step 5: Use Hint (Optional)

```bash
# User gets stuck, requests a hint
curl -X POST https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod/sessions/01KQ1R5T9B44RWK3WJZNDJ64ZD/turns \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "use_hint"
  }'

# Response includes hint
# Hint is generated by Bedrock Nova Micro based on context
# Example hint: "You could say: I would like a medium coffee, please."
```

#### Step 6: Continue Conversation

```bash
# User responds: "I would like a medium coffee, please."
curl -X POST https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod/sessions/01KQ1R5T9B44RWK3WJZNDJ64ZD/turns \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "I would like a medium coffee, please.",
    "audio_url": "s3://bucket/speaking/audio/abc124.mp3",
    "is_hint_used": true
  }'

# Response (200 OK)
{
  "success": true,
  "message": "Success",
  "data": {
    "session_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD",
    "user_id": "794ab5cc-f0e1-708a-7902-6a087c2bb60c",
    "scenario_id": "restaurant-ordering",
    "status": "ACTIVE",
    "created_at": "2026-04-25T07:25:13.798100+00:00",
    "turn_count": 3,
    "updated_at": "2026-04-25T07:26:00.000000+00:00",
    "completed_at": null
  }
}
```

#### Step 7: Complete Session & Get Scoring

```bash
# User completes the session
curl -X POST https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod/sessions/01KQ1R5T9B44RWK3WJZNDJ64ZD/complete \
  -H "Authorization: Bearer $TOKEN"

# Response (200 OK) - Includes scoring from Bedrock Nova Micro
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
      "fluency_score": 78,
      "pronunciation_score": 82,
      "grammar_score": 75,
      "vocabulary_score": 80,
      "overall_score": 79,
      "feedback": "Tốt lắm! Phát âm của bạn rõ ràng. Hãy cải thiện tính linh hoạt và sử dụng thêm từ vựng phong phú."
    }
  }
}

# Behind the scenes:
# 1. Bedrock Nova Micro analyzes all turns
# 2. Scores on 4 dimensions (fluency, pronunciation, grammar, vocabulary)
# 3. Generates personalized feedback in Vietnamese
# 4. Updates user profile (streak, words learned, etc.)
```

---

## Vocabulary Learning Workflow

### Learning New Words

```bash
# Step 1: Translate a word
curl -X POST https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod/vocabulary/translate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"word": "restaurant"}'

# Response (200 OK)
{
  "success": true,
  "message": "Success",
  "data": {
    "word": "restaurant",
    "translation_vi": "nhà hàng"
  }
}

# Step 2: Create flashcard
curl -X POST https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod/flashcards \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "word": "restaurant",
    "translation": "nhà hàng",
    "example_sentence": "Let me recommend a good restaurant.",
    "difficulty": "easy"
  }'

# Response (201 Created)
{
  "success": true,
  "message": "Created",
  "data": {
    "flashcard_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD",
    "word": "restaurant",
    "translation": "nhà hàng",
    "example_sentence": "Let me recommend a good restaurant.",
    "difficulty": "easy",
    "created_at": "2026-04-25T07:25:13.798100+00:00",
    "next_review": "2026-04-26T07:25:13.798100+00:00"
  }
}

# Step 3: Review flashcard (next day)
curl -X POST https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod/flashcards/01KQ1R5T9B44RWK3WJZNDJ64ZD/review \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_correct": true,
    "time_spent_ms": 3000
  }'

# Response (200 OK)
{
  "success": true,
  "message": "Success",
  "data": {
    "flashcard_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD",
    "word": "restaurant",
    "next_review": "2026-04-27T07:25:13.798100+00:00",
    "difficulty": "easy"
  }
}

# Step 4: Get due flashcards
curl -X GET https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod/flashcards/due \
  -H "Authorization: Bearer $TOKEN"

# Response (200 OK)
{
  "success": true,
  "message": "Success",
  "data": {
    "flashcards": [
      {
        "flashcard_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD",
        "word": "restaurant",
        "translation": "nhà hàng",
        "difficulty": "easy",
        "next_review": "2026-04-25T07:25:13.798100+00:00"
      }
    ],
    "total": 1
  }
}
```

---

## Admin Operations

### Managing Users

```bash
# List all users
curl -X GET "https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod/admin/users?limit=20" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Response (200 OK)
{
  "success": true,
  "message": "Success",
  "data": {
    "users": [
      {
        "user_id": "794ab5cc-f0e1-708a-7902-6a087c2bb60c",
        "email": "user1@example.com",
        "display_name": "Nguyễn Văn A",
        "current_level": "A1",
        "role": "user",
        "is_active": true,
        "created_at": "2026-01-01T00:00:00+00:00"
      },
      {
        "user_id": "299a95fc-3021-7050-5812-42fffa4971ec",
        "email": "user2@example.com",
        "display_name": "Trần Thị B",
        "current_level": "B1",
        "role": "user",
        "is_active": true,
        "created_at": "2026-01-02T00:00:00+00:00"
      }
    ],
    "total": 2
  }
}

# Deactivate a user
curl -X PATCH https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod/admin/users/794ab5cc-f0e1-708a-7902-6a087c2bb60c \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'

# Response (200 OK)
{
  "success": true,
  "message": "Success",
  "data": {
    "user_id": "794ab5cc-f0e1-708a-7902-6a087c2bb60c",
    "email": "user1@example.com",
    "display_name": "Nguyễn Văn A",
    "current_level": "A1",
    "role": "user",
    "is_active": false,
    "created_at": "2026-01-01T00:00:00+00:00"
  }
}

# Promote user to admin
curl -X PATCH https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod/admin/users/299a95fc-3021-7050-5812-42fffa4971ec \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role": "admin"}'

# Response (200 OK)
{
  "success": true,
  "message": "Success",
  "data": {
    "user_id": "299a95fc-3021-7050-5812-42fffa4971ec",
    "email": "user2@example.com",
    "display_name": "Trần Thị B",
    "current_level": "B1",
    "role": "admin",
    "is_active": true,
    "created_at": "2026-01-02T00:00:00+00:00"
  }
}
```

### Managing Scenarios

```bash
# List scenarios
curl -X GET https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod/admin/scenarios \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Create new scenario
curl -X POST https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod/admin/scenarios \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_id": "airport-check-in",
    "title": "Airport Check-in",
    "description": "Check in at an airport counter",
    "level": "A2",
    "roles": [
      {
        "role_id": "passenger",
        "name": "Passenger",
        "description": "You are a passenger checking in"
      },
      {
        "role_id": "agent",
        "name": "Check-in Agent",
        "description": "You are an airport check-in agent"
      }
    ],
    "goals": ["check in luggage", "ask about seat selection", "confirm flight details"]
  }'

# Response (201 Created)
{
  "success": true,
  "message": "Created",
  "data": {
    "scenario_id": "airport-check-in",
    "title": "Airport Check-in",
    "description": "Check in at an airport counter",
    "level": "A2",
    "created_at": "2026-04-25T07:25:13.798100+00:00"
  }
}

# Update scenario
curl -X PATCH https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod/admin/scenarios/airport-check-in \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Airport Check-in (Updated)",
    "description": "Check in at an airport counter with baggage handling"
  }'

# Response (200 OK)
{
  "success": true,
  "message": "Success",
  "data": {
    "scenario_id": "airport-check-in",
    "title": "Airport Check-in (Updated)",
    "description": "Check in at an airport counter with baggage handling",
    "level": "A2",
    "created_at": "2026-04-25T07:25:13.798100+00:00"
  }
}
```

---

## Error Handling Examples

### Invalid Request

```bash
# Missing required field
curl -X POST https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_id": "restaurant-ordering"
    # Missing: learner_role_id, ai_role_id, level, etc.
  }'

# Response (422 Unprocessable Entity)
{
  "success": false,
  "message": "Invalid request data: 1 validation error for SubmitSpeakingTurnCommand\nlearner_role_id\n  Field required (type=missing)",
  "error": "VALIDATION_ERROR"
}
```

### Unauthorized Access

```bash
# Missing token
curl -X GET https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod/profile

# Response (401 Unauthorized)
{
  "success": false,
  "message": "Unauthorized",
  "error": "UNAUTHORIZED"
}

# Expired token
curl -X GET https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod/profile \
  -H "Authorization: Bearer eyJraWQiOiJleHBpcmVkLXRva2VuIn0..."

# Response (401 Unauthorized)
{
  "success": false,
  "message": "Token expired",
  "error": "UNAUTHORIZED"
}
```

### Resource Not Found

```bash
# Non-existent session
curl -X GET https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod/sessions/invalid-session-id \
  -H "Authorization: Bearer $TOKEN"

# Response (404 Not Found)
{
  "success": false,
  "message": "Session not found",
  "error": "NOT_FOUND"
}
```

### Service Error

```bash
# Bedrock service unavailable
curl -X POST https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod/sessions/session-id/turns \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello",
    "audio_url": "s3://bucket/audio.mp3",
    "is_hint_used": false
  }'

# Response (500 Internal Server Error) - if Bedrock is down
{
  "success": false,
  "message": "Internal server error",
  "error": "SERVICE_ERROR"
}

# Check CloudWatch logs for details
# /aws/lambda/lexi-be-SpeakingSessionFunction-*
```

---

## WebSocket Real-time Examples

### Real-time Speaking Session

```bash
# 1. Connect to WebSocket
wscat -c "wss://no8fa2u3qg.execute-api.ap-southeast-1.amazonaws.com/Prod?token=$TOKEN"

# 2. Start session
> {"action": "start_session", "session_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD"}

# Response
< {"event": "SESSION_READY", "upload_url": "https://s3.amazonaws.com/...", "s3_key": "speaking/audio/..."}

# 3. Send message turn
> {"action": "send_message_turn", "session_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD", "text": "Hello, I would like to order a coffee", "is_hint_used": false}

# Responses (multiple events)
< {"event": "TURN_SAVED", "turn_index": 1}
< {"event": "AI_TEXT_CHUNK", "chunk": "Of course! What size would you like?", "done": true}
< {"event": "AI_AUDIO_URL", "url": "s3://bucket/ai-audio.mp3", "text": "Of course! What size would you like?"}

# 4. Use hint
> {"action": "use_hint", "session_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD"}

# Response
< {"event": "HINT_TEXT", "hint": "You could say: I would like a medium coffee, please."}

# 5. End session
> {"action": "end_session", "session_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD"}

# Response
< {"event": "SCORING_COMPLETE", "session_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD"}

# 6. Disconnect
> (close connection)
```

---

## Performance Metrics

### Speaking Session Metrics

When a session completes, the following metrics are recorded:

```json
{
  "session_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD",
  "metrics": {
    "total_turns": 3,
    "total_duration_ms": 45000,
    "bedrock_calls": 3,
    "bedrock_ttft_ms": [250, 280, 260],
    "bedrock_latency_ms": [1200, 1150, 1300],
    "bedrock_input_tokens": [150, 200, 180],
    "bedrock_output_tokens": [50, 60, 55],
    "bedrock_cost_usd": 0.0015,
    "transcription_confidence": [0.95, 0.92, 0.98],
    "synthesis_duration_ms": [800, 900, 850]
  }
}
```

---

**Last Updated**: April 25, 2026
