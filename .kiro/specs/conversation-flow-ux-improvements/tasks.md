# Implementation Plan: Conversation Flow UX Improvements

## Overview

This implementation plan breaks down the conversation flow UX improvements into three phases:
1. **Phase 1: Greeting Generation** - AI greetings and first questions at session creation
2. **Phase 2: Structured Hints** - Enhanced bilingual hints with context and examples
3. **Phase 3: Testing & Deployment** - Integration tests and deployment verification

The implementation uses Python and integrates with existing AWS services (Bedrock, Polly, DynamoDB).

## Tasks

- [x] 1. Implement GreetingGenerator domain service
  - [x] 1.1 Create GreetingGenerator class with greeting templates
    - Create `src/domain/services/greeting_generator.py`
    - Define `GreetingResult` dataclass with greeting_text, first_question, combined_text
    - Implement `GreetingGenerator` class with Bedrock client dependency
    - Add greeting templates dictionary for levels A1-C2 (cached, no LLM call)
    - _Requirements: 1.1, 1.2, 1.5, 1.6, 1.7, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_
  
  - [x] 1.2 Implement first question generation with Bedrock
    - Add `generate()` method that takes level, scenario_title, learner_role, ai_role, selected_goals, ai_gender
    - Build prompt with scenario context, roles, goals, and level
    - Call Bedrock (Amazon Nova Micro: apac.amazon.nova-micro-v1:0) with max_tokens=100, temperature=0.7
    - Parse response and combine greeting template + first question
    - Return GreetingResult with combined text
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.7, 3.7, 10.1, 10.5_
  
  - [ ]* 1.3 Write unit tests for GreetingGenerator
    - Test greeting template selection for each level (A1-C2)
    - Test first question generation with mocked Bedrock responses
    - Test combined text format (greeting + first question)
    - Test error handling when Bedrock call fails
    - _Requirements: 1.1, 1.2, 1.5, 1.6, 2.1, 2.2, 2.3, 2.4, 3.1-3.6_

- [x] 2. Integrate greeting generation into CreateSpeakingSessionUseCase
  - [x] 2.1 Modify CreateSpeakingSessionUseCase to call GreetingGenerator
    - Add `greeting_generator` dependency to `__init__`
    - After session creation and save, call `greeting_generator.generate()` with session parameters
    - Generate TTS audio using `speech_synthesis_service.synthesize()` with path pattern `speaking/audio/{session_id}/0.mp3`
    - Create Turn entity with turn_index=0, speaker=AI, content=combined_text, audio_url
    - Save greeting turn using `turn_repo.save()`
    - Wrap in try-except to handle failures gracefully (log warning, continue without greeting)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.5, 2.6, 8.1, 8.2, 8.3, 8.4, 8.5, 8.7, 7.5_
  
  - [ ]* 2.2 Write unit tests for CreateSpeakingSessionUseCase greeting integration
    - Test session creation with successful greeting generation
    - Test greeting turn saved with correct turn_index=0 and speaker=AI
    - Test audio generation for greeting
    - Test backward compatibility when greeting generation fails (session still created)
    - Test error logging when GreetingGenerator or TTS fails
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 7.5, 7.7, 8.5_

- [x] 3. Checkpoint - Verify greeting generation works end-to-end
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement StructuredHintGenerator domain service
  - [x] 4.1 Create StructuredHintGenerator class with Bedrock integration
    - Create `src/domain/services/structured_hint_generator.py`
    - Define `StructuredHint` dataclass with bilingual fields (conversation_context, turn_goal, suggested_approach, example_phrases, grammar_tip)
    - Implement `StructuredHintGenerator` class with Bedrock client dependency
    - Add `generate()` method that takes session, last_ai_turn, turn_history
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 5.1, 5.2, 5.3, 5.4, 5.5_
  
  - [x] 4.2 Implement structured hint generation with Bedrock
    - Build prompt with last AI turn content, learner level, current goal, learner role
    - Call Bedrock (Amazon Nova Micro) requesting JSON response with bilingual fields
    - Parse JSON response and validate required fields (conversation_context, turn_goal, suggested_approach, example_phrases, grammar_tip)
    - Validate bilingual structure (each field has "vi" and "en" keys)
    - Validate example_phrases contains lists for both languages
    - Return StructuredHint dataclass
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 6.1, 6.2, 6.3, 6.6, 10.2, 10.6_
  
  - [x] 4.3 Add validation helper for structured hints
    - Create `validate_structured_hint()` function that checks required fields
    - Validate bilingual structure (dict with "vi" and "en" keys)
    - Validate example_phrases is list type for both languages
    - Return boolean indicating validity
    - _Requirements: 9.3, 9.4_
  
  - [ ]* 4.4 Write unit tests for StructuredHintGenerator
    - Test hint generation with mocked Bedrock responses
    - Test JSON parsing from LLM response
    - Test validation of required fields
    - Test validation of bilingual structure
    - Test error handling for malformed JSON
    - Test error handling for missing required fields
    - _Requirements: 4.1-4.6, 5.1-5.6, 6.1-6.6, 9.3, 9.4_

- [x] 5. Integrate structured hints into WebSocketSessionController
  - [x] 5.1 Modify WebSocketSessionController.use_hint to use StructuredHintGenerator
    - Add `structured_hint_generator` dependency to `__init__`
    - In `use_hint()` method, get session and turns
    - Find last AI turn from turn history
    - Call `structured_hint_generator.generate()` with session, last_ai_turn, turn_history
    - Send HINT_TEXT event with structured hint object (call `to_dict()` method)
    - Wrap in try-except to handle failures gracefully
    - _Requirements: 4.7, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 9.1, 9.2_
  
  - [x] 5.2 Add fallback to simple hint format on error
    - In except block, log warning with error details
    - Call existing `_generate_contextual_hint()` method as fallback
    - Send HINT_TEXT event with simple string hint
    - Maintain backward compatibility with old clients
    - _Requirements: 7.2, 7.3, 7.6, 7.7, 9.5_
  
  - [ ]* 5.3 Write unit tests for WebSocketSessionController hint integration
    - Test use_hint with successful structured hint generation
    - Test HINT_TEXT event format with structured hint object
    - Test fallback to simple hint when StructuredHintGenerator fails
    - Test HINT_TEXT event format with simple string (backward compatibility)
    - Test error logging when hint generation fails
    - _Requirements: 4.7, 7.2, 7.3, 7.6, 7.7, 9.1, 9.2, 9.5_

- [x] 6. Checkpoint - Verify structured hints work end-to-end
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Add error handling and logging
  - [x] 7.1 Add comprehensive error logging for greeting generation
    - Log session_id, level, scenario when greeting generation fails
    - Log Bedrock API errors with context
    - Log TTS synthesis failures with context
    - Log turn repository save failures
    - _Requirements: 7.5, 7.7, 10.7_
  
  - [x] 7.2 Add comprehensive error logging for hint generation
    - Log session_id, turn_index when hint generation fails
    - Log Bedrock API errors with context
    - Log JSON parsing failures with malformed response
    - Log validation failures with missing fields
    - _Requirements: 7.6, 7.7, 10.7_
  
  - [x] 7.3 Add performance logging for greeting and hint generation
    - Log latency_ms for greeting generation
    - Log latency_ms for hint generation
    - Log Bedrock token usage (input_tokens, output_tokens)
    - Log cost estimates per operation
    - _Requirements: 10.3, 10.4, 10.7_

- [ ]* 8. Write integration tests for end-to-end flows
  - [ ]* 8.1 Write integration test for greeting generation flow
    - Create session via CreateSpeakingSessionUseCase
    - Verify greeting turn exists with turn_index=0
    - Verify audio URL is valid S3 path
    - Verify greeting content is level-appropriate
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.5, 2.6, 8.1, 8.2, 8.3, 8.4_
  
  - [ ]* 8.2 Write integration test for structured hint flow
    - Create session and add user turn
    - Call use_hint via WebSocketSessionController
    - Verify HINT_TEXT event received
    - Verify structured hint has all required fields
    - Verify bilingual content (vi + en) in all fields
    - _Requirements: 4.1-4.6, 5.1-5.6, 6.1-6.6, 9.1, 9.2_

- [x] 9. Update handler factory to inject new dependencies
  - [x] 9.1 Wire GreetingGenerator into CreateSpeakingSessionUseCase
    - In handler factory (lambda_handler.py or similar), create GreetingGenerator instance with Bedrock client
    - Pass greeting_generator to CreateSpeakingSessionUseCase constructor
    - _Requirements: 1.1, 1.2_
  
  - [x] 9.2 Wire StructuredHintGenerator into WebSocketSessionController
    - In WebSocket handler factory, create StructuredHintGenerator instance with Bedrock client
    - Pass structured_hint_generator to WebSocketSessionController constructor
    - _Requirements: 4.1, 4.7_

- [x] 10. Final checkpoint - Verify all components integrated
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- No property-based tests (design has no Correctness Properties section)
- Unit tests validate specific examples and error handling
- Integration tests validate end-to-end flows with real AWS services
- Manual QA required for content quality (greeting appropriateness, hint relevance, translation quality)
