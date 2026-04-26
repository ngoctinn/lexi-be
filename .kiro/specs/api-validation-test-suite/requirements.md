# API Validation Test Suite - Requirements

**Feature Name**: api-validation-test-suite  
**Version**: 1.0  
**Status**: In Progress  
**Last Updated**: April 26, 2026

---

## 1. Overview

Create a comprehensive test suite to validate all Lexi API endpoints before production deployment. Each API must be tested for:
- Happy path (success scenarios)
- Error handling (400, 401, 404, 422, 500, 503)
- Request/response schema validation
- Authentication (JWT token requirements)
- Pagination (where applicable)
- Data integrity

---

## 2. Business Requirements

### 2.1 Scope
Validate **27 API endpoints** across **8 modules**:

| Module | Count | Endpoints |
|--------|-------|-----------|
| Onboarding | 1 | POST /onboarding/complete |
| Profile | 2 | GET /profile, PATCH /profile |
| Vocabulary | 2 | POST /vocabulary/translate, POST /vocabulary/translate-sentence |
| Flashcard | 5 | POST /flashcards, GET /flashcards, GET /flashcards/{id}, GET /flashcards/due, POST /flashcards/{id}/review |
| Scenario | 1 | GET /scenarios (public, no auth) |
| Speaking Session | 5 | POST /sessions, GET /sessions, GET /sessions/{id}, POST /sessions/{id}/turns, POST /sessions/{id}/complete |
| WebSocket | 6 | start_session, audio_uploaded, use_hint, send_message_turn, end_session, ANALYZE_TURN |
| Admin | 5 | GET /admin/users, PATCH /admin/users/{id}, GET /admin/scenarios, POST /admin/scenarios, PATCH /admin/scenarios/{id} |

### 2.2 Success Criteria
- ✅ All 27 APIs respond with correct HTTP status codes
- ✅ Response schemas match API_DOCUMENTATION.md exactly
- ✅ Authentication works (JWT required except /scenarios)
- ✅ Error codes match documentation (BAD_REQUEST, VALIDATION_ERROR, etc.)
- ✅ Pagination works (limit, last_key/next_key)
- ✅ WebSocket events fire correctly
- ✅ No data corruption or unexpected side effects

---

## 3. Technical Requirements

### 3.1 Test Framework
- **Language**: Python (pytest)
- **HTTP Client**: requests or httpx
- **WebSocket**: websockets library
- **Assertions**: pytest assertions + custom validators

### 3.2 Test Structure
Each API test must:
1. Read ALL related source files (handler, controller, use case, entity, repository)
2. Test happy path with valid data
3. Test error cases (missing fields, invalid types, auth failures)
4. Validate response schema against documentation
5. Check HTTP status codes
6. Verify error codes match documentation

### 3.3 Test Data
- Use test user credentials from Cognito
- Create test scenarios/sessions as needed
- Clean up test data after each test
- Use fixtures for reusable test data

### 3.4 Coverage
- **Happy Path**: 100% of endpoints
- **Error Cases**: 
  - 400 Bad Request (invalid JSON, missing fields)
  - 401 Unauthorized (missing/invalid token)
  - 404 Not Found (resource doesn't exist)
  - 422 Validation Error (invalid data types)
  - 500 Internal Server Error (service failures)
  - 503 Service Unavailable (external service down)

---

## 4. API Validation Tasks

### Task 1: Onboarding API
- **Endpoint**: POST /onboarding/complete
- **Auth**: Required (JWT)
- **Test Cases**:
  - Happy path: valid onboarding data
  - Missing required fields (display_name, current_level, target_level)
  - Invalid level values (not A1-C2)
  - Invalid JSON
  - Unauthorized (no token)

### Task 2: Profile APIs
- **Endpoints**: GET /profile, PATCH /profile
- **Auth**: Required (JWT)
- **Test Cases**:
  - GET: retrieve user profile
  - PATCH: update display_name, avatar_url, target_level
  - PATCH: partial updates (only some fields)
  - Invalid avatar_url format
  - Unauthorized access

### Task 3: Vocabulary - Translate Word
- **Endpoint**: POST /vocabulary/translate
- **Auth**: Required (JWT)
- **Test Cases**:
  - Happy path: valid word with context
  - Word not found (404 WORD_NOT_FOUND)
  - Missing required field (word)
  - Invalid word length (>100 chars)
  - Dictionary service unavailable (503)

### Task 4: Vocabulary - Translate Sentence
- **Endpoint**: POST /vocabulary/translate-sentence
- **Auth**: Required (JWT)
- **Test Cases**:
  - Happy path: valid sentence
  - Missing sentence field
  - Empty sentence
  - Very long sentence

### Task 5: Flashcard - Create
- **Endpoint**: POST /flashcards
- **Auth**: Required (JWT)
- **Test Cases**:
  - Happy path: all fields provided
  - Missing required fields (vocab, translation_vi)
  - Invalid vocab_type
  - Duplicate word handling

### Task 6: Flashcard - List
- **Endpoint**: GET /flashcards
- **Auth**: Required (JWT)
- **Test Cases**:
  - Happy path: list with default limit
  - Pagination: limit parameter (1-100)
  - Pagination: last_key token
  - Invalid limit (>100)

### Task 7: Flashcard - Get Single
- **Endpoint**: GET /flashcards/{flashcard_id}
- **Auth**: Required (JWT)
- **Test Cases**:
  - Happy path: valid flashcard_id
  - Not found (404)
  - Invalid flashcard_id format

### Task 8: Flashcard - List Due
- **Endpoint**: GET /flashcards/due
- **Auth**: Required (JWT)
- **Test Cases**:
  - Happy path: list due cards
  - Empty list (no due cards)

### Task 9: Flashcard - Review
- **Endpoint**: POST /flashcards/{flashcard_id}/review
- **Auth**: Required (JWT)
- **Test Cases**:
  - Happy path: all rating types (forgot, hard, good, easy)
  - Invalid rating value
  - Flashcard not found (404)

### Task 10: Scenario - List (Public)
- **Endpoint**: GET /scenarios
- **Auth**: NOT required (public)
- **Test Cases**:
  - Happy path: list all scenarios
  - Filter by level (A1-C2)
  - Pagination: limit parameter
  - No auth header required

### Task 11: Session - Create
- **Endpoint**: POST /sessions
- **Auth**: Required (JWT)
- **Test Cases**:
  - Happy path: valid scenario_id, roles, level
  - Invalid scenario_id (404)
  - Missing required fields
  - Invalid level value

### Task 12: Session - List
- **Endpoint**: GET /sessions
- **Auth**: Required (JWT)
- **Test Cases**:
  - Happy path: list user's sessions
  - Pagination: limit parameter
  - Empty list (no sessions)

### Task 13: Session - Get Single
- **Endpoint**: GET /sessions/{session_id}
- **Auth**: Required (JWT)
- **Test Cases**:
  - Happy path: valid session_id
  - Not found (404)
  - Unauthorized (accessing other user's session)

### Task 14: Session - Submit Turn
- **Endpoint**: POST /sessions/{session_id}/turns
- **Auth**: Required (JWT)
- **Test Cases**:
  - Happy path: valid text, audio_url, is_hint_used
  - Missing required fields
  - Session not found (404)
  - Session already completed

### Task 15: Session - Complete
- **Endpoint**: POST /sessions/{session_id}/complete
- **Auth**: Required (JWT)
- **Test Cases**:
  - Happy path: complete active session
  - Session not found (404)
  - Already completed session

### Task 16: WebSocket - Start Session
- **Action**: start_session
- **Auth**: Required (JWT token in query)
- **Test Cases**:
  - Happy path: valid session_id
  - Invalid session_id
  - Unauthorized (invalid token)

### Task 17: WebSocket - Audio Uploaded
- **Action**: audio_uploaded
- **Auth**: Required (JWT)
- **Test Cases**:
  - Happy path: valid s3_key
  - Missing s3_key
  - Invalid session_id

### Task 18: WebSocket - Use Hint
- **Action**: use_hint
- **Auth**: Required (JWT)
- **Test Cases**:
  - Happy path: valid session_id
  - Session not found
  - Hint generation failure

### Task 19: WebSocket - Send Message Turn
- **Action**: send_message_turn
- **Auth**: Required (JWT)
- **Test Cases**:
  - Happy path: valid text, is_hint_used
  - Missing text field
  - Session not found

### Task 20: WebSocket - End Session
- **Action**: end_session
- **Auth**: Required (JWT)
- **Test Cases**:
  - Happy path: valid session_id
  - Session not found
  - Already ended session

### Task 21: WebSocket - Analyze Turn
- **Action**: ANALYZE_TURN
- **Auth**: Required (JWT)
- **Test Cases**:
  - Happy path: valid session_id, turn_index
  - Invalid turn_index
  - Session not found

### Task 22: Admin - List Users
- **Endpoint**: GET /admin/users
- **Auth**: Required (admin role)
- **Test Cases**:
  - Happy path: list all users
  - Pagination: limit parameter
  - Unauthorized (non-admin user)

### Task 23: Admin - Update User
- **Endpoint**: PATCH /admin/users/{user_id}
- **Auth**: Required (admin role)
- **Test Cases**:
  - Happy path: update is_active, current_level, target_level
  - User not found (404)
  - Unauthorized (non-admin)

### Task 24: Admin - List Scenarios
- **Endpoint**: GET /admin/scenarios
- **Auth**: Required (admin role)
- **Test Cases**:
  - Happy path: list all scenarios
  - Unauthorized (non-admin)

### Task 25: Admin - Create Scenario
- **Endpoint**: POST /admin/scenarios
- **Auth**: Required (admin role)
- **Test Cases**:
  - Happy path: valid scenario data
  - Missing required fields
  - Invalid roles (not exactly 2 elements)
  - Unauthorized (non-admin)

### Task 26: Admin - Update Scenario
- **Endpoint**: PATCH /admin/scenarios/{scenario_id}
- **Auth**: Required (admin role)
- **Test Cases**:
  - Happy path: update scenario_title, is_active, order
  - Scenario not found (404)
  - Unauthorized (non-admin)

### Task 27: Integration - Vocabulary → Flashcard Workflow
- **Workflow**: Translate word → Create flashcard → Review flashcard
- **Test Cases**:
  - Complete workflow with valid data
  - Error handling at each step
  - Data consistency across APIs

---

## 5. Non-Functional Requirements

### 5.1 Performance
- Each API should respond within 2 seconds
- WebSocket events should arrive within 1 second

### 5.2 Reliability
- All tests must be idempotent (can run multiple times)
- No test should affect other tests
- Proper cleanup of test data

### 5.3 Documentation
- Each test should have clear docstring
- Error messages should be descriptive
- Test results should be easy to interpret

---

## 6. Acceptance Criteria

- [ ] All 27 API tests pass
- [ ] All error cases handled correctly
- [ ] Response schemas validated
- [ ] Authentication working
- [ ] Pagination tested
- [ ] WebSocket events verified
- [ ] Test coverage > 90%
- [ ] No flaky tests
- [ ] Clear test documentation

---

## 7. Dependencies

- pytest >= 7.0
- requests >= 2.28
- websockets >= 10.0
- python-dotenv (for test credentials)
- AWS Cognito test user account

---

## 8. Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Test data pollution | Use unique IDs, cleanup after each test |
| Flaky WebSocket tests | Add retry logic, proper timeouts |
| Rate limiting | Stagger requests, use test account |
| External service failures | Mock external services in tests |
| Token expiration | Refresh token before each test |

---

## 9. Timeline

- **Phase 1**: Setup test framework & fixtures (2 days)
- **Phase 2**: Implement tests for REST APIs (5 days)
- **Phase 3**: Implement WebSocket tests (3 days)
- **Phase 4**: Integration tests & cleanup (2 days)
- **Total**: ~12 days

