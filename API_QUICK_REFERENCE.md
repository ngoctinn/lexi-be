# Lexi API - Quick Reference

**Base URL**: `https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod`

---

## Authentication

```bash
# Get token
TOKEN=$(aws cognito-idp admin-initiate-auth \
  --user-pool-id ap-southeast-1_VhFl3NxNy \
  --client-id 4krhiauplon0iei1f5r4cgpq7i \
  --auth-flow ADMIN_NO_SRP_AUTH \
  --auth-parameters USERNAME=user@example.com,PASSWORD=password \
  --region ap-southeast-1 \
  --query 'AuthenticationResult.IdToken' \
  --output text)

# Use token
curl -H "Authorization: Bearer $TOKEN" https://...
```

---

## Onboarding

```bash
# Complete onboarding
curl -X POST https://.../onboarding/complete \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "John Doe",
    "current_level": "A1",
    "target_level": "B2"
  }'
```

---

## Profile

```bash
# Get profile
curl -X GET https://.../profile \
  -H "Authorization: Bearer $TOKEN"

# Update profile
curl -X PATCH https://.../profile \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"display_name": "Jane Doe"}'
```

---

## Vocabulary

```bash
# Translate word
curl -X POST https://.../vocabulary/translate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"word": "hello"}'

# Translate sentence
curl -X POST https://.../vocabulary/translate-sentence \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sentence": "How are you?"}'
```

---

## Flashcards

```bash
# Create flashcard
curl -X POST https://.../flashcards \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "word": "hello",
    "translation": "xin chào",
    "example_sentence": "Hello, how are you?"
  }'

# List flashcards
curl -X GET "https://.../flashcards?limit=10" \
  -H "Authorization: Bearer $TOKEN"

# Get flashcard
curl -X GET https://.../flashcards/{flashcard_id} \
  -H "Authorization: Bearer $TOKEN"

# List due flashcards
curl -X GET https://.../flashcards/due \
  -H "Authorization: Bearer $TOKEN"

# Review flashcard
curl -X POST https://.../flashcards/{flashcard_id}/review \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_correct": true}'
```

---

## Scenarios

```bash
# List scenarios (no auth required)
curl -X GET "https://.../scenarios?limit=10"

# Filter by level
curl -X GET "https://.../scenarios?level=B1"
```

---

## Speaking Sessions

```bash
# Create session
curl -X POST https://.../sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_id": "restaurant-ordering",
    "learner_role_id": "customer",
    "ai_role_id": "waiter",
    "ai_gender": "female",
    "level": "B1",
    "selected_goals": ["order food"]
  }'

# List sessions
curl -X GET "https://.../sessions?limit=10" \
  -H "Authorization: Bearer $TOKEN"

# Get session
curl -X GET https://.../sessions/{session_id} \
  -H "Authorization: Bearer $TOKEN"

# Submit turn
curl -X POST https://.../sessions/{session_id}/turns \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, I would like to order a coffee please.",
    "audio_url": "s3://bucket/audio.mp3",
    "is_hint_used": false
  }'

# Complete session
curl -X POST https://.../sessions/{session_id}/complete \
  -H "Authorization: Bearer $TOKEN"
```

---

## WebSocket

```bash
# Connect
wscat -c "wss://no8fa2u3qg.execute-api.ap-southeast-1.amazonaws.com/Prod?token=$TOKEN"

# Start session
{"action": "start_session", "session_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD"}

# Send message turn
{"action": "send_message_turn", "session_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD", "text": "Hello"}

# Use hint
{"action": "use_hint", "session_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD"}

# End session
{"action": "end_session", "session_id": "01KQ1R5T9B44RWK3WJZNDJ64ZD"}
```

---

## Admin

```bash
# List users
curl -X GET "https://.../admin/users?limit=10" \
  -H "Authorization: Bearer $TOKEN"

# Update user
curl -X PATCH https://.../admin/users/{user_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'

# List scenarios
curl -X GET https://.../admin/scenarios \
  -H "Authorization: Bearer $TOKEN"

# Create scenario
curl -X POST https://.../admin/scenarios \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_id": "hotel-booking",
    "title": "Hotel Booking",
    "level": "A2"
  }'

# Update scenario
curl -X PATCH https://.../admin/scenarios/{scenario_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Hotel Booking (Updated)"}'
```

---

## Response Format

### Success
```json
{
  "success": true,
  "message": "Success",
  "data": { /* response data */ }
}
```

### Error
```json
{
  "success": false,
  "message": "Error message",
  "error": "ERROR_CODE"
}
```

---

## Common Error Codes

| Code | Meaning |
|------|---------|
| `BAD_REQUEST` | Invalid JSON or missing fields |
| `VALIDATION_ERROR` | Data validation failed |
| `NOT_FOUND` | Resource not found |
| `UNAUTHORIZED` | Authentication failed |
| `SERVICE_ERROR` | External service error |

---

## Proficiency Levels

- **A1** - Beginner
- **A2** - Elementary
- **B1** - Intermediate
- **B2** - Upper Intermediate
- **C1** - Advanced
- **C2** - Mastery

---

## AI Model

- **Model**: Amazon Nova Micro (APAC inference profile)
- **Region**: ap-southeast-1
- **Max Tokens**: 40-250 (by level)
- **Temperature**: 0.6-0.85 (by level)

---

## Useful Links

- **API Base**: https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod
- **WebSocket**: wss://no8fa2u3qg.execute-api.ap-southeast-1.amazonaws.com/Prod
- **User Pool**: ap-southeast-1_VhFl3NxNy
- **Client ID**: 4krhiauplon0iei1f5r4cgpq7i
- **Region**: ap-southeast-1 (Singapore)

---

## Testing

```bash
# Test endpoint
curl -X GET https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod/scenarios

# Pretty print JSON
curl -s ... | jq '.'

# Save response to file
curl -s ... > response.json

# Check status code
curl -w "%{http_code}" -o /dev/null -s ...
```

---

**Last Updated**: April 25, 2026
