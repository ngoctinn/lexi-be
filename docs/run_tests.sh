#!/bin/bash
BASE_URL="https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod"
CLIENT_ID="4krhiauplon0iei1f5r4cgpq7i"
REGION="ap-southeast-1"
USER_POOL_ID="ap-southeast-1_VhFl3NxNy"
EMAIL="testuser@lexi.dev"
PASSWORD="Test@12345"

PASS=0; FAIL=0
p() { echo "  ✅ PASS: $1"; PASS=$((PASS+1)); }
f() { echo "  ❌ FAIL: $1"; FAIL=$((FAIL+1)); }
chk() { [ "$1" = "$2" ] && p "$3" || f "$3 (HTTP $1, want $2)"; }

echo "Getting token..."
TOKEN=$(aws cognito-idp initiate-auth \
  --region $REGION --auth-flow USER_PASSWORD_AUTH \
  --client-id $CLIENT_ID \
  --auth-parameters USERNAME=$EMAIL,PASSWORD=$PASSWORD \
  --query 'AuthenticationResult.IdToken' --output text 2>/dev/null)
[ -n "$TOKEN" ] && p "T-00: Login OK" || { f "T-00: Login FAILED"; exit 1; }

# ── T-01 ──────────────────────────────────────────────────────────────
echo ""
echo "── T-01: GET /scenarios (no auth) ──"
S=$(curl -s -o /tmp/r.json -w "%{http_code}" "$BASE_URL/scenarios")
chk "$S" "200" "T-01 HTTP 200"
COUNT=$(python3 -c "import json; print(len(json.load(open('/tmp/r.json')).get('scenarios',[])))" 2>/dev/null || echo 0)
[ "$COUNT" -gt 0 ] && p "T-01 scenarios not empty ($COUNT items)" || f "T-01 scenarios empty (no seed data)"
SCENARIO_ID=$(python3 -c "import json; d=json.load(open('/tmp/r.json')); print(d['scenarios'][0]['scenario_id'])" 2>/dev/null || echo "")
echo "  scenario_id: ${SCENARIO_ID:-N/A}"

# ── T-20 ──────────────────────────────────────────────────────────────
echo ""
echo "── T-20: No token → 401 ──"
S=$(curl -s -o /tmp/r.json -w "%{http_code}" "$BASE_URL/profile")
chk "$S" "401" "T-20 HTTP 401"

# ── T-02 ──────────────────────────────────────────────────────────────
echo ""
echo "── T-02: GET /profile ──"
S=$(curl -s -o /tmp/r.json -w "%{http_code}" "$BASE_URL/profile" -H "Authorization: Bearer $TOKEN")
chk "$S" "200" "T-02 HTTP 200"
python3 -c "
import json
d=json.load(open('/tmp/r.json'))
print(f'  email={d.get(\"email\")} role={d.get(\"role\")} is_new_user={d.get(\"is_new_user\")}')
" 2>/dev/null

# ── T-03 ──────────────────────────────────────────────────────────────
echo ""
echo "── T-03: PATCH /profile ──"
S=$(curl -s -o /tmp/r.json -w "%{http_code}" -X PATCH "$BASE_URL/profile" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"display_name":"Test User","current_level":"B1","target_level":"C1","is_new_user":false}')
chk "$S" "200" "T-03 HTTP 200"
python3 -c "import json; d=json.load(open('/tmp/r.json')); print(f'  is_success={d.get(\"is_success\")}')" 2>/dev/null

# ── T-04 ──────────────────────────────────────────────────────────────
echo ""
echo "── T-04: PATCH /profile bad level ──"
S=$(curl -s -o /tmp/r.json -w "%{http_code}" -X PATCH "$BASE_URL/profile" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"current_level":"Z9"}')
{ [ "$S" = "400" ] || [ "$S" = "422" ]; } && p "T-04 HTTP 4xx ($S)" || f "T-04 HTTP $S (want 4xx)"
python3 -c "import json; d=json.load(open('/tmp/r.json')); print(f'  error={d.get(\"error\")}')" 2>/dev/null

# ── T-05 ──────────────────────────────────────────────────────────────
echo ""
echo "── T-05: POST /onboarding/complete ──"
S=$(curl -s -o /tmp/r.json -w "%{http_code}" -X POST "$BASE_URL/onboarding/complete" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"display_name":"Test User","current_level":"A2","target_level":"B2","avatar_url":"https://api.dicebear.com/9.x/lorelei/svg?seed=Aria"}')
chk "$S" "200" "T-05 HTTP 200"
python3 -c "import json; d=json.load(open('/tmp/r.json')); print(f'  {d}')" 2>/dev/null

# ── T-06 ──────────────────────────────────────────────────────────────
echo ""
echo "── T-06: POST /vocabulary/translate ──"
S=$(curl -s -o /tmp/r.json -w "%{http_code}" -X POST "$BASE_URL/vocabulary/translate" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"word":"burger","sentence":"I would like to order a burger please."}')
chk "$S" "200" "T-06 HTTP 200"
python3 -c "import json; d=json.load(open('/tmp/r.json')); print(f'  word={d.get(\"word\")} translation_vi={d.get(\"translation_vi\")}')" 2>/dev/null

# ── T-07 ──────────────────────────────────────────────────────────────
echo ""
echo "── T-07: POST /vocabulary/translate-sentence ──"
S=$(curl -s -o /tmp/r.json -w "%{http_code}" -X POST "$BASE_URL/vocabulary/translate-sentence" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"sentence":"Would you like fries with that?"}')
chk "$S" "200" "T-07 HTTP 200"
python3 -c "import json; d=json.load(open('/tmp/r.json')); print(f'  sentence_vi={d.get(\"sentence_vi\",d.get(\"translation_vi\"))}')" 2>/dev/null

# ── T-08 ──────────────────────────────────────────────────────────────
echo ""
echo "── T-08: POST /vocabulary/translate empty body ──"
S=$(curl -s -o /tmp/r.json -w "%{http_code}" -X POST "$BASE_URL/vocabulary/translate" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{}')
{ [ "$S" = "400" ] || [ "$S" = "404" ] || [ "$S" = "422" ]; } && p "T-08 HTTP 4xx ($S)" || f "T-08 HTTP $S (want 4xx)"

# ── T-09 ──────────────────────────────────────────────────────────────
echo ""
echo "── T-09: POST /sessions ──"
if [ -n "$SCENARIO_ID" ]; then
  BODY="{\"scenario_id\":\"$SCENARIO_ID\",\"ai_gender\":\"female\",\"level\":\"B1\",\"selected_goals\":[],\"prompt_snapshot\":\"\"}"
else
  BODY='{"scenario_id":"test-scenario","ai_gender":"female","level":"B1","selected_goals":[],"prompt_snapshot":""}'
fi
S=$(curl -s -o /tmp/r.json -w "%{http_code}" -X POST "$BASE_URL/sessions" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d "$BODY")
chk "$S" "201" "T-09 HTTP 201"
SESSION_ID=$(python3 -c "import json; print(json.load(open('/tmp/r.json')).get('session_id',''))" 2>/dev/null || echo "")
echo "  session_id: ${SESSION_ID:-N/A}"
python3 -c "import json; d=json.load(open('/tmp/r.json')); print(f'  status={d.get(\"session\",{}).get(\"status\")}')" 2>/dev/null

# ── T-10 ──────────────────────────────────────────────────────────────
echo ""
echo "── T-10: GET /sessions ──"
S=$(curl -s -o /tmp/r.json -w "%{http_code}" "$BASE_URL/sessions?limit=5" \
  -H "Authorization: Bearer $TOKEN")
chk "$S" "200" "T-10 HTTP 200"
python3 -c "import json; d=json.load(open('/tmp/r.json')); print(f'  sessions count={len(d.get(\"sessions\",[]))}')" 2>/dev/null

# ── T-11 ──────────────────────────────────────────────────────────────
echo ""
echo "── T-11: GET /sessions/{id} ──"
if [ -n "$SESSION_ID" ]; then
  S=$(curl -s -o /tmp/r.json -w "%{http_code}" "$BASE_URL/sessions/$SESSION_ID" \
    -H "Authorization: Bearer $TOKEN")
  chk "$S" "200" "T-11 HTTP 200"
  python3 -c "import json; d=json.load(open('/tmp/r.json')); s=d.get('session',{}); print(f'  status={s.get(\"status\")} turns={len(s.get(\"turns\",[]))}')" 2>/dev/null
else
  f "T-11 SKIP (no session_id)"
fi

# ── T-12 ──────────────────────────────────────────────────────────────
echo ""
echo "── T-12: POST /sessions/{id}/turns ──"
if [ -n "$SESSION_ID" ]; then
  S=$(curl -s -o /tmp/r.json -w "%{http_code}" -X POST "$BASE_URL/sessions/$SESSION_ID/turns" \
    -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
    -d '{"text":"Hello, I would like to order a burger please.","is_hint_used":false}')
  chk "$S" "200" "T-12 HTTP 200"
  python3 -c "
import json
d=json.load(open('/tmp/r.json'))
ut=d.get('user_turn',{})
at=d.get('ai_turn',{})
print(f'  user_turn speaker={ut.get(\"speaker\")} content={str(ut.get(\"content\",\"\"))[:40]}')
print(f'  ai_turn speaker={at.get(\"speaker\")} content={str(at.get(\"content\",\"\"))[:40]}')
print(f'  keywords={d.get(\"analysis_keywords\",[])[:3]}')
" 2>/dev/null
else
  f "T-12 SKIP (no session_id)"
fi

# ── T-13 ──────────────────────────────────────────────────────────────
echo ""
echo "── T-13: POST /sessions/{id}/complete ──"
if [ -n "$SESSION_ID" ]; then
  S=$(curl -s -o /tmp/r.json -w "%{http_code}" -X POST "$BASE_URL/sessions/$SESSION_ID/complete" \
    -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{}')
  chk "$S" "200" "T-13 HTTP 200"
  python3 -c "
import json
d=json.load(open('/tmp/r.json'))
sc=d.get('scoring',{})
print(f'  overall={sc.get(\"overall\")} fluency={sc.get(\"fluency\")} grammar={sc.get(\"grammar\")}')
" 2>/dev/null
else
  f "T-13 SKIP (no session_id)"
fi

# ── T-14 ──────────────────────────────────────────────────────────────
echo ""
echo "── T-14: POST /flashcards ──"
S=$(curl -s -o /tmp/r.json -w "%{http_code}" -X POST "$BASE_URL/flashcards" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"vocab":"burger","vocab_type":"noun","translation_vi":"banh mi kep thit","definition_vi":"A sandwich with beef patty","phonetic":"/bɜːɡər/","example_sentence":"I would like a burger."}')
chk "$S" "201" "T-14 HTTP 201"
FLASHCARD_ID=$(python3 -c "import json; print(json.load(open('/tmp/r.json')).get('flashcard_id',''))" 2>/dev/null || echo "")
echo "  flashcard_id: ${FLASHCARD_ID:-N/A}"

# ── T-15 ──────────────────────────────────────────────────────────────
echo ""
echo "── T-15: GET /flashcards ──"
S=$(curl -s -o /tmp/r.json -w "%{http_code}" "$BASE_URL/flashcards?limit=10" \
  -H "Authorization: Bearer $TOKEN")
chk "$S" "200" "T-15 HTTP 200"
python3 -c "import json; d=json.load(open('/tmp/r.json')); print(f'  cards count={len(d.get(\"cards\",[]))}')" 2>/dev/null

# ── T-16 ──────────────────────────────────────────────────────────────
echo ""
echo "── T-16: GET /flashcards/{id} ──"
if [ -n "$FLASHCARD_ID" ]; then
  S=$(curl -s -o /tmp/r.json -w "%{http_code}" "$BASE_URL/flashcards/$FLASHCARD_ID" \
    -H "Authorization: Bearer $TOKEN")
  chk "$S" "200" "T-16 HTTP 200"
  python3 -c "import json; d=json.load(open('/tmp/r.json')); print(f'  word={d.get(\"word\")} interval_days={d.get(\"interval_days\")} review_count={d.get(\"review_count\")}')" 2>/dev/null
else
  f "T-16 SKIP (no flashcard_id)"
fi

# ── T-17 ──────────────────────────────────────────────────────────────
echo ""
echo "── T-17: GET /flashcards/due ──"
S=$(curl -s -o /tmp/r.json -w "%{http_code}" "$BASE_URL/flashcards/due" \
  -H "Authorization: Bearer $TOKEN")
chk "$S" "200" "T-17 HTTP 200"
python3 -c "import json; d=json.load(open('/tmp/r.json')); print(f'  due cards={len(d.get(\"cards\",[]))}')" 2>/dev/null

# ── T-18 ──────────────────────────────────────────────────────────────
echo ""
echo "── T-18: POST /flashcards/{id}/review ──"
if [ -n "$FLASHCARD_ID" ]; then
  S=$(curl -s -o /tmp/r.json -w "%{http_code}" -X POST "$BASE_URL/flashcards/$FLASHCARD_ID/review" \
    -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
    -d '{"rating":"good"}')
  chk "$S" "200" "T-18 HTTP 200"
  python3 -c "import json; d=json.load(open('/tmp/r.json')); print(f'  interval_days={d.get(\"interval_days\")} review_count={d.get(\"review_count\")} next_review_at={d.get(\"next_review_at\",\"\")[:10]}')" 2>/dev/null
else
  f "T-18 SKIP (no flashcard_id)"
fi

# ── T-19 ──────────────────────────────────────────────────────────────
echo ""
echo "── T-19: POST /flashcards/{id}/review bad rating ──"
if [ -n "$FLASHCARD_ID" ]; then
  S=$(curl -s -o /tmp/r.json -w "%{http_code}" -X POST "$BASE_URL/flashcards/$FLASHCARD_ID/review" \
    -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
    -d '{"rating":"invalid_rating"}')
  chk "$S" "400" "T-19 HTTP 400"
  python3 -c "import json; d=json.load(open('/tmp/r.json')); print(f'  error={d.get(\"error\")}')" 2>/dev/null
else
  f "T-19 SKIP (no flashcard_id)"
fi

# ── T-21 ──────────────────────────────────────────────────────────────
echo ""
echo "── T-21: GET /admin/users (USER role → 403) ──"
S=$(curl -s -o /tmp/r.json -w "%{http_code}" "$BASE_URL/admin/users" \
  -H "Authorization: Bearer $TOKEN")
chk "$S" "403" "T-21 HTTP 403"
python3 -c "import json; d=json.load(open('/tmp/r.json')); print(f'  error={d.get(\"error\")}')" 2>/dev/null

# ── Summary ───────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════"
echo "  TOTAL: $((PASS+FAIL)) | ✅ $PASS PASS | ❌ $FAIL FAIL"
echo "════════════════════════════════════"
