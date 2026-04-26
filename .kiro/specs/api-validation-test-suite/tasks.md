# API Validation Test Suite - Tasks

**Feature Name**: api-validation-test-suite  
**Total Tasks**: 27  
**Status**: Ready for Implementation

---

## Phase 1: Test Framework Setup

- [x] 1.1 Create test directory structure
- [x] 1.2 Setup pytest configuration
- [x] 1.3 Create APIClient wrapper class
- [-] 1.4 Create WebSocketClient wrapper class
- [-] 1.5 Create pytest fixtures (conftest.py)
- [-] 1.6 Create test data generators
- [-] 1.7 Create response validators

---

## Phase 2: REST API Tests (Tasks 1-10)

- [x] 2.1 Task 1: Onboarding API - POST /onboarding/complete
  - Test happy path (valid data)
  - Test missing required fields
  - Test invalid level values
  - Test unauthorized (no token)
  - Verify response schema matches documentation

- [x] 2.2 Task 2: Profile APIs - GET /profile, PATCH /profile
  - Test GET /profile (retrieve user profile)
  - Test PATCH /profile (update fields)
  - Test partial updates
  - Test invalid avatar_url format
  - Test unauthorized access

- [x] 2.3 Task 3: Vocabulary - Translate Word - POST /vocabulary/translate
  - Test happy path (valid word with context)
  - Test word not found (404 WORD_NOT_FOUND)
  - Test missing required field (word)
  - Test invalid word length (>100 chars)
  - Test dictionary service unavailable (503)

- [ ] 2.4 Task 4: Vocabulary - Translate Sentence - POST /vocabulary/translate-sentence
  - Test happy path (valid sentence)
  - Test missing sentence field
  - Test empty sentence
  - Test very long sentence

- [ ] 2.5 Task 5: Flashcard - Create - POST /flashcards
  - Test happy path (all fields provided)
  - Test missing required fields (vocab, translation_vi)
  - Test invalid vocab_type
  - Test duplicate word handling
  - Verify response schema

- [ ] 2.6 Task 6: Flashcard - List - GET /flashcards
  - Test happy path (list with default limit)
  - Test pagination (limit parameter 1-100)
  - Test pagination (last_key token)
  - Test invalid limit (>100)
  - Verify no data overlap between pages

- [ ] 2.7 Task 7: Flashcard - Get Single - GET /flashcards/{flashcard_id}
  - Test happy path (valid flashcard_id)
  - Test not found (404)
  - Test invalid flashcard_id format

- [ ] 2.8 Task 8: Flashcard - List Due - GET /flashcards/due
  - Test happy path (list due cards)
  - Test empty list (no due cards)
  - Verify response schema

- [ ] 2.9 Task 9: Flashcard - Review - POST /flashcards/{flashcard_id}/review
  - Test all rating types (forgot, hard, good, easy)
  - Test invalid rating value
  - Test flashcard not found (404)
  - Verify interval_days updated correctly

- [ ] 2.10 Task 10: Scenario - List (Public) - GET /scenarios
  - Test happy path (list all scenarios)
  - Test filter by level (A1-C2)
  - Test pagination (limit parameter)
  - Verify NO auth header required

---

## Phase 3: Session APIs (Tasks 11-15)

- [ ] 3.1 Task 11: Session - Create - POST /sessions
  - Test happy path (valid scenario_id, roles, level)
  - Test invalid scenario_id (404)
  - Test missing required fields
  - Test invalid level value
  - Verify response schema

- [ ] 3.2 Task 12: Session - List - GET /sessions
  - Test happy path (list user's sessions)
  - Test pagination (limit parameter)
  - Test empty list (no sessions)
  - Verify only user's sessions returned

- [ ] 3.3 Task 13: Session - Get Single - GET /sessions/{session_id}
  - Test happy path (valid session_id)
  - Test not found (404)
  - Test unauthorized (accessing other user's session)
  - Verify turns array populated

- [ ] 3.4 Task 14: Session - Submit Turn - POST /sessions/{session_id}/turns
  - Test happy path (valid text, audio_url, is_hint_used)
  - Test missing required fields
  - Test session not found (404)
  - Test session already completed
  - Verify AI response generated

- [ ] 3.5 Task 15: Session - Complete - POST /sessions/{session_id}/complete
  - Test happy path (complete active session)
  - Test session not found (404)
  - Test already completed session
  - Verify scoring data returned

---

## Phase 4: WebSocket Tests (Tasks 16-21)

- [ ] 4.1 Task 16: WebSocket - Start Session - start_session action
  - Test happy path (valid session_id)
  - Test invalid session_id
  - Test unauthorized (invalid token)
  - Verify SESSION_READY event received
  - Verify upload_url and s3_key in response

- [ ] 4.2 Task 17: WebSocket - Audio Uploaded - audio_uploaded action
  - Test happy path (valid s3_key)
  - Test missing s3_key
  - Test invalid session_id
  - Verify STT_RESULT event received
  - Verify TURN_SAVED event received

- [ ] 4.3 Task 18: WebSocket - Use Hint - use_hint action
  - Test happy path (valid session_id)
  - Test session not found
  - Test hint generation failure
  - Verify HINT_TEXT event received
  - Verify markdown content in response

- [ ] 4.4 Task 19: WebSocket - Send Message Turn - send_message_turn action
  - Test happy path (valid text, is_hint_used)
  - Test missing text field
  - Test session not found
  - Verify TURN_SAVED event received
  - Verify AI_TEXT_CHUNK events received

- [ ] 4.5 Task 20: WebSocket - End Session - end_session action
  - Test happy path (valid session_id)
  - Test session not found
  - Test already ended session
  - Verify SCORING_COMPLETE event received

- [ ] 4.6 Task 21: WebSocket - Analyze Turn - ANALYZE_TURN action
  - Test happy path (valid session_id, turn_index)
  - Test invalid turn_index
  - Test session not found
  - Verify TURN_ANALYSIS event received
  - Verify markdown analysis in response

---

## Phase 5: Admin APIs (Tasks 22-26)

- [ ] 5.1 Task 22: Admin - List Users - GET /admin/users
  - Test happy path (list all users)
  - Test pagination (limit parameter)
  - Test unauthorized (non-admin user)
  - Verify admin role required

- [ ] 5.2 Task 23: Admin - Update User - PATCH /admin/users/{user_id}
  - Test happy path (update is_active, current_level, target_level)
  - Test user not found (404)
  - Test unauthorized (non-admin)
  - Verify only admin can update

- [ ] 5.3 Task 24: Admin - List Scenarios - GET /admin/scenarios
  - Test happy path (list all scenarios)
  - Test unauthorized (non-admin)
  - Verify admin role required
  - Verify includes all scenario fields

- [ ] 5.4 Task 25: Admin - Create Scenario - POST /admin/scenarios
  - Test happy path (valid scenario data)
  - Test missing required fields
  - Test invalid roles (not exactly 2 elements)
  - Test unauthorized (non-admin)
  - Verify scenario_id generated

- [ ] 5.5 Task 26: Admin - Update Scenario - PATCH /admin/scenarios/{scenario_id}
  - Test happy path (update scenario_title, is_active, order)
  - Test scenario not found (404)
  - Test unauthorized (non-admin)
  - Test partial updates

---

## Phase 6: Integration Tests (Task 27)

- [ ] 6.1 Task 27: Integration - Vocabulary → Flashcard Workflow
  - Test complete workflow (translate → create → review)
  - Test error handling at each step
  - Test data consistency across APIs
  - Test with multiple words
  - Verify flashcard data matches translation data

---

## Phase 7: Error Handling & Edge Cases

- [ ] 7.1 Test all error codes (400, 401, 404, 422, 500, 503)
- [ ] 7.2 Test invalid JSON payloads
- [ ] 7.3 Test missing required fields
- [ ] 7.4 Test invalid data types
- [ ] 7.5 Test boundary values (empty strings, max lengths)
- [ ] 7.6 Test concurrent requests
- [ ] 7.7 Test rate limiting
- [ ] 7.8 Test token expiration

---

## Phase 8: Test Report & Documentation

- [ ] 8.1 Generate test execution report
- [ ] 8.2 Document test coverage (endpoints, error cases)
- [ ] 8.3 Document test execution instructions
- [ ] 8.4 Create troubleshooting guide
- [ ] 8.5 Document test data cleanup strategy

---

## Success Criteria

- ✅ All 27 API tests pass
- ✅ All error cases handled correctly
- ✅ Response schemas validated against documentation
- ✅ Authentication working (JWT required except /scenarios)
- ✅ Pagination tested and working
- ✅ WebSocket events verified
- ✅ Test coverage > 90%
- ✅ No flaky tests
- ✅ Clear test documentation
- ✅ Test execution time < 5 minutes

---

## Notes

- Each task must read ALL related source files (handler, controller, use case, entity, repository)
- Use fixtures for reusable test data
- Implement proper cleanup to avoid test pollution
- Add retry logic for WebSocket tests (network latency)
- Mock external services (Bedrock, Translate) if needed
- Use descriptive test names and docstrings
- Generate detailed test report with pass/fail status

