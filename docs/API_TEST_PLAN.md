# Lexi BE — API Test Plan (curl)

**Base URL:** `https://htv5bybfsc.execute-api.ap-southeast-1.amazonaws.com/Prod`

## Setup

```bash
# Đặt biến môi trường một lần, dùng cho tất cả lệnh bên dưới
BASE_URL="https://htv5bybfsc.execute-api.ap-southeast-1.amazonaws.com/Prod"

# Lấy token sau khi đăng nhập Cognito (xem bước T-01)
TOKEN="<id_token_từ_cognito>"
```

---

## T-00 — Đăng nhập lấy token

Dùng Cognito USER_PASSWORD_AUTH để lấy `IdToken`.

```bash
aws cognito-idp initiate-auth \
  --region ap-southeast-1 \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id 1b87am8h2lh4atll7cbqc22ago \
  --auth-parameters USERNAME=<email>,PASSWORD=<password> \
  --query 'AuthenticationResult.IdToken' \
  --output text
```

**Expected:** Trả về chuỗi JWT dài. Gán vào biến `TOKEN`.

```bash
TOKEN=$(aws cognito-idp initiate-auth \
  --region ap-southeast-1 \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id 1b87am8h2lh4atll7cbqc22ago \
  --auth-parameters USERNAME=<email>,PASSWORD=<password> \
  --query 'AuthenticationResult.IdToken' \
  --output text)

echo "Token: ${TOKEN:0:50}..."
```

---

## T-01 — Scenarios (Public, không cần auth)

```bash
curl -s "$BASE_URL/scenarios" | python3 -m json.tool
```

**Expected:** `200` với `success: true` và mảng `scenarios`.  
**Verify:** `scenarios` không rỗng, mỗi item có `scenario_id`, `scenario_title`, `roles`, `goals`.

```bash
# Lưu scenario_id đầu tiên để dùng cho test session
SCENARIO_ID=$(curl -s "$BASE_URL/scenarios" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['scenarios'][0]['scenario_id'])")
echo "Scenario ID: $SCENARIO_ID"
```

---

## T-02 — Profile: GET

```bash
curl -s "$BASE_URL/profile" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**Expected:** `200` với object profile có `user_id`, `email`, `display_name`, `role`, `is_new_user`.  
**Verify:** `email` khớp với tài khoản đăng nhập.

---

## T-03 — Profile: PATCH

```bash
curl -s -X PATCH "$BASE_URL/profile" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Test User",
    "current_level": "B1",
    "target_level": "C1",
    "is_new_user": false
  }' | python3 -m json.tool
```

**Expected:** `200` với `is_success: true`.  
**Verify:** Gọi lại T-02, kiểm tra `display_name` đã đổi thành `"Test User"`.

---

## T-04 — Profile: PATCH với dữ liệu sai

```bash
curl -s -X PATCH "$BASE_URL/profile" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"current_level": "Z9"}' | python3 -m json.tool
```

**Expected:** `400` hoặc `422` với `error` mô tả lỗi trình độ không hợp lệ.

---

## T-05 — Onboarding: Complete

```bash
curl -s -X POST "$BASE_URL/onboarding/complete" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Test User",
    "current_level": "A2",
    "target_level": "B2",
    "avatar_url": "https://api.dicebear.com/9.x/lorelei/svg?seed=Aria"
  }' | python3 -m json.tool
```

**Expected:** `200` với `success: true`.

---

## T-06 — Vocabulary: Translate word

```bash
curl -s -X POST "$BASE_URL/vocabulary/translate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "word": "burger",
    "sentence": "I would like to order a burger please."
  }' | python3 -m json.tool
```

**Expected:** `200` với `word`, `translation_vi`, `definition_vi`.  
**Verify:** `translation_vi` không rỗng.

---

## T-07 — Vocabulary: Translate sentence

```bash
curl -s -X POST "$BASE_URL/vocabulary/translate-sentence" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sentence": "Would you like fries with that?"}' | python3 -m json.tool
```

**Expected:** `200` với `sentence` và `translation_vi`.

---

## T-08 — Vocabulary: Thiếu field bắt buộc

```bash
curl -s -X POST "$BASE_URL/vocabulary/translate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}' | python3 -m json.tool
```

**Expected:** `400` với `error`.

---

## T-09 — Sessions: Tạo session mới

```bash
SESSION_RESPONSE=$(curl -s -X POST "$BASE_URL/sessions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"scenario_id\": \"$SCENARIO_ID\",
    \"ai_gender\": \"female\",
    \"level\": \"B1\",
    \"selected_goals\": [],
    \"prompt_snapshot\": \"\"
  }")

echo $SESSION_RESPONSE | python3 -m json.tool

SESSION_ID=$(echo $SESSION_RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin)['session_id'])")
echo "Session ID: $SESSION_ID"
```

**Expected:** `201` với `success: true`, `session_id`, `session.status = "ACTIVE"`.

---

## T-10 — Sessions: List sessions

```bash
curl -s "$BASE_URL/sessions?limit=5" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**Expected:** `200` với `success: true`, mảng `sessions` chứa session vừa tạo.

---

## T-11 — Sessions: Get session detail

```bash
curl -s "$BASE_URL/sessions/$SESSION_ID" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**Expected:** `200` với `session.session_id` khớp, `turns` là mảng (có thể rỗng hoặc có AI turn đầu tiên).

---

## T-12 — Sessions: Submit turn

```bash
curl -s -X POST "$BASE_URL/sessions/$SESSION_ID/turns" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, I would like to order a burger please.",
    "is_hint_used": false
  }' | python3 -m json.tool
```

**Expected:** `200` với `user_turn`, `ai_turn` (AI phản hồi), `analysis_keywords`.  
**Verify:** `ai_turn.content` không rỗng, `ai_turn.audio_url` có giá trị.

---

## T-13 — Sessions: Complete session

```bash
curl -s -X POST "$BASE_URL/sessions/$SESSION_ID/complete" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}' | python3 -m json.tool
```

**Expected:** `200` với `scoring` có `fluency`, `pronunciation`, `grammar`, `vocabulary`, `overall`, `feedback`.

---

## T-14 — Flashcards: Tạo flashcard

```bash
FLASHCARD_RESPONSE=$(curl -s -X POST "$BASE_URL/flashcards" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "vocab": "burger",
    "vocab_type": "noun",
    "translation_vi": "bánh mì kẹp thịt",
    "definition_vi": "Một loại bánh sandwich với thịt bò",
    "phonetic": "/ˈbɜːɡər/",
    "example_sentence": "I would like to order a burger."
  }')

echo $FLASHCARD_RESPONSE | python3 -m json.tool

FLASHCARD_ID=$(echo $FLASHCARD_RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin)['flashcard_id'])")
echo "Flashcard ID: $FLASHCARD_ID"
```

**Expected:** `201` với `flashcard_id`, `word`.

---

## T-15 — Flashcards: List all

```bash
curl -s "$BASE_URL/flashcards?limit=10" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**Expected:** `200` với `cards` chứa flashcard vừa tạo.

---

## T-16 — Flashcards: Get detail

```bash
curl -s "$BASE_URL/flashcards/$FLASHCARD_ID" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**Expected:** `200` với đầy đủ thông tin flashcard, `source_session_id` null.

---

## T-17 — Flashcards: Due cards

```bash
curl -s "$BASE_URL/flashcards/due" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**Expected:** `200` với `cards` (có thể rỗng nếu chưa đến hạn ôn tập).

---

## T-18 — Flashcards: Review

```bash
curl -s -X POST "$BASE_URL/flashcards/$FLASHCARD_ID/review" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"rating": "good"}' | python3 -m json.tool
```

**Expected:** `200` với `interval_days` tăng lên, `review_count` = 1, `next_review_at` trong tương lai.

---

## T-19 — Flashcards: Review với rating sai

```bash
curl -s -X POST "$BASE_URL/flashcards/$FLASHCARD_ID/review" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"rating": "invalid_rating"}' | python3 -m json.tool
```

**Expected:** `400` với `error: "Invalid rating. Must be one of: forgot, hard, good, easy"`.

---

## T-20 — Auth: Không có token

```bash
curl -s "$BASE_URL/profile" | python3 -m json.tool
```

**Expected:** `401` từ API Gateway (không vào Lambda).

---

## T-21 — Admin: Không có quyền (USER role)

```bash
curl -s "$BASE_URL/admin/users" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**Expected:** `403 Forbidden` (nếu account là USER thường).

---

## Checklist tổng hợp

| # | Endpoint | Method | Auth | Expected | Pass |
|---|----------|--------|------|----------|------|
| T-00 | Cognito login | - | - | JWT token | ☐ |
| T-01 | /scenarios | GET | None | 200 + list | ☐ |
| T-02 | /profile | GET | Yes | 200 + profile | ☐ |
| T-03 | /profile | PATCH | Yes | 200 updated | ☐ |
| T-04 | /profile | PATCH | Yes | 400/422 bad level | ☐ |
| T-05 | /onboarding/complete | POST | Yes | 200 success | ☐ |
| T-06 | /vocabulary/translate | POST | Yes | 200 + translation | ☐ |
| T-07 | /vocabulary/translate-sentence | POST | Yes | 200 + translation | ☐ |
| T-08 | /vocabulary/translate | POST | Yes | 400 missing field | ☐ |
| T-09 | /sessions | POST | Yes | 201 + session_id | ☐ |
| T-10 | /sessions | GET | Yes | 200 + list | ☐ |
| T-11 | /sessions/{id} | GET | Yes | 200 + detail | ☐ |
| T-12 | /sessions/{id}/turns | POST | Yes | 200 + ai_turn | ☐ |
| T-13 | /sessions/{id}/complete | POST | Yes | 200 + scoring | ☐ |
| T-14 | /flashcards | POST | Yes | 201 + flashcard_id | ☐ |
| T-15 | /flashcards | GET | Yes | 200 + list | ☐ |
| T-16 | /flashcards/{id} | GET | Yes | 200 + detail | ☐ |
| T-17 | /flashcards/due | GET | Yes | 200 + list | ☐ |
| T-18 | /flashcards/{id}/review | POST | Yes | 200 + updated | ☐ |
| T-19 | /flashcards/{id}/review | POST | Yes | 400 bad rating | ☐ |
| T-20 | /profile (no token) | GET | None | 401 | ☐ |
| T-21 | /admin/users (USER role) | GET | Yes | 403 | ☐ |
