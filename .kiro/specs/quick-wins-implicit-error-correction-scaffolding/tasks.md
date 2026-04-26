# Implementation Plan: Quick Wins - Implicit Error Correction & Context-Aware Scaffolding

## Overview

This implementation plan breaks down the feature into discrete coding tasks that build incrementally. The approach follows three phases:

1. **Phase 1: PromptBuilder Enhancement** - Add implicit error correction instructions and level-specific examples
2. **Phase 2: ScaffoldingSystem Enhancement** - Add context-aware hint generation with scenario vocabulary and grammar pattern detection
3. **Phase 3: Use Case Integration** - Wire context extraction and passing to ScaffoldingSystem

Each task references specific requirements and builds on previous work. Testing tasks are marked optional with `*` for faster MVP delivery.

**Estimated Total Effort:** 9-13 days (1.5-2 weeks)

---

## Tasks

### Phase 1: PromptBuilder Enhancement (2-3 days)

- [x] 1. Add implicit error correction instructions to PromptBuilder
  - Add `_IMPLICIT_CORRECTION_INSTRUCTIONS` constant with instructions for all CEFR levels (A1-C2)
  - Instructions should tell AI to model correct usage naturally without explicit correction
  - Instructions should specify correction applies to grammar, vocabulary, and pronunciation errors
  - Instructions should maintain existing explicit correction rules (Vietnamese, inappropriate, off-topic)
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  - _Estimated effort: 0.5 days_

- [ ] 2. Add level-specific few-shot examples for implicit correction
  - [x] 2.1 Add `_IMPLICIT_CORRECTION_EXAMPLES` constant with examples for A1 level
    - Include 3 examples: grammar error, vocabulary error, pronunciation-related error
    - Show "Good" response (implicit correction) vs "Bad" response (explicit correction)
    - Demonstrate natural conversation flow with modeled correct usage
    - _Requirements: 2.1, 2.7, 2.8, 9.1_
  
  - [x] 2.2 Add examples for A2 level
    - Include 3 examples: tense error, vocabulary error, sentence structure error
    - _Requirements: 2.2, 2.7, 2.8, 9.2_
  
  - [x] 2.3 Add examples for B1 level
    - Include 3 examples: present perfect error, preposition error, intermediate vocabulary error
    - _Requirements: 2.3, 2.7, 2.8, 9.3_
  
  - [x] 2.4 Add examples for B2 level
    - Include 3 examples: conditional error, passive voice error, advanced vocabulary error
    - _Requirements: 2.4, 2.7, 2.8, 9.4_
  
  - [x] 2.5 Add examples for C1 level
    - Include 3 examples: subjunctive error, idiomatic usage error, sophisticated vocabulary error
    - _Requirements: 2.5, 2.7, 2.8, 9.5_
  
  - [x] 2.6 Add examples for C2 level
    - Include 3 examples: advanced structure error, collocation error, native-level nuance error
    - _Requirements: 2.6, 2.7, 2.8, 9.6_
  
  - _Estimated effort: 1 day_

- [x] 3. Integrate implicit correction into build_session_prompt()
  - Modify `build_session_prompt()` to append implicit correction instructions
  - Append level-specific few-shot examples after instructions
  - Maintain existing prompt structure (append, don't replace)
  - Ensure backward compatibility (existing prompt format preserved)
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 7.1, 7.2_
  - _Estimated effort: 0.5 days_

- [ ]* 4. Write unit tests for PromptBuilder implicit correction
  - Test that implicit correction instructions are included for all levels (A1-C2)
  - Test that few-shot examples are included for all levels
  - Test that existing prompt structure is maintained
  - Test backward compatibility (existing tests pass)
  - _Requirements: 12.1, 12.2, 12.8_
  - _Estimated effort: 0.5 days_

- [x] 5. Checkpoint - Validate PromptBuilder changes
  - Ensure all tests pass
  - Manually inspect generated prompts for all levels
  - Verify implicit correction instructions are clear and actionable
  - Ask user if questions arise

---

### Phase 2: ScaffoldingSystem Enhancement (3-4 days)

- [x] 6. Add scenario vocabulary mappings to ScaffoldingSystem
  - Add `_SCENARIO_VOCABULARY` constant with mappings for restaurant, airport, hotel, shopping scenarios
  - Each scenario should have "questions" and "statements" lists with A1-A2 level phrases
  - Add fallback vocabulary for general conversation scenarios
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8_
  - _Estimated effort: 0.5 days_

- [x] 7. Add grammar pattern detection heuristics
  - Add `_GRAMMAR_PATTERNS` constant with keyword lists for past tense, present tense, questions
  - Add `_detect_grammar_pattern()` method using simple keyword matching
  - Detect past tense patterns (keywords: "yesterday", "last", "ago", "was", "were")
  - Detect present tense patterns (keywords: "now", "today", "always", "usually")
  - Detect question patterns (keywords: "what", "where", "when", "why", "how", "?")
  - Detect short responses (< 5 words) as vocabulary gaps
  - Return None when no pattern detected (fallback to generic hints)
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.6, 11.1, 11.2, 11.3, 11.4, 11.6, 11.7_
  - _Estimated effort: 1 day_

- [x] 8. Add context parameter to generate_hint()
  - Modify `generate_hint()` signature to accept optional `context` parameter (default None)
  - Add `ScaffoldingContext` dataclass with fields: scenario_title, scenario_vocabulary, last_utterance, conversation_goals
  - When context is None, generate generic hints (backward compatibility)
  - When context is provided, call new `_generate_context_aware_hint()` method
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 7.3, 7.4_
  - _Estimated effort: 0.5 days_

- [ ] 9. Implement context-aware hint generation
  - [x] 9.1 Add `_generate_context_aware_hint()` method
    - Extract scenario vocabulary using `_get_scenario_vocabulary()`
    - Detect grammar pattern using `_detect_grammar_pattern()`
    - Route to appropriate hint generator based on hint level
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 5.4_
  
  - [x] 9.2 Add `_get_scenario_vocabulary()` method
    - Look up scenario in `_SCENARIO_VOCABULARY` mapping
    - Return scenario-specific vocabulary if found
    - Return generic vocabulary if scenario not found (fallback)
    - _Requirements: 4.5, 10.8_
  
  - [x] 9.3 Add `_generate_vocabulary_hint_with_context()` method
    - Use scenario vocabulary to suggest relevant phrases
    - Use detected grammar pattern to suggest appropriate tense/form
    - Maintain bilingual format (Vietnamese + English)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.6, 5.1, 5.2, 5.3, 5.4_
  
  - [x] 9.4 Add `_generate_sentence_starter_with_context()` method
    - Use scenario vocabulary to provide sentence starters
    - Use detected grammar pattern to provide appropriate examples
    - Maintain bilingual format (Vietnamese + English)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.6, 5.1, 5.2, 5.3, 5.4_
  
  - _Estimated effort: 1.5 days_

- [ ]* 10. Write unit tests for ScaffoldingSystem context-aware hints
  - Test scenario-specific vocabulary hints for restaurant, airport, hotel, shopping scenarios
  - Test grammar pattern detection (past tense, present tense, questions, short responses)
  - Test fallback to generic hints when context unavailable
  - Test backward compatibility (context=None generates generic hints)
  - Test bilingual format maintained for all context-aware hints
  - _Requirements: 12.3, 12.4, 12.5_
  - _Estimated effort: 1 day_

- [x] 11. Checkpoint - Validate ScaffoldingSystem changes
  - Ensure all tests pass
  - Manually test context-aware hint generation with sample scenarios
  - Verify fallback behavior when context unavailable
  - Ask user if questions arise

---

### Phase 3: Use Case Integration (2-3 days)

- [ ] 12. Add context extraction to SubmitSpeakingTurnUseCase
  - [x] 12.1 Add `_extract_scaffolding_context()` helper function
    - Extract scenario title from session
    - Extract last user utterance from turn history
    - Extract conversation goals from session
    - Extract scenario vocabulary using `_get_scenario_keywords()`
    - Return context dict with all extracted data
    - _Requirements: 6.1, 6.2, 6.3_
  
  - [x] 12.2 Add `_get_scenario_keywords()` helper function
    - Reuse `OffTopicDetector._get_scenario_keywords()` method
    - Return list of keywords for scenario
    - Handle scenarios without keyword mappings (return empty list)
    - _Requirements: 6.1_
  
  - _Estimated effort: 1 day_

- [x] 13. Integrate context passing to ScaffoldingSystem
  - Modify `SubmitSpeakingTurnUseCase.execute()` to extract context before hint generation
  - Pass context to `ScaffoldingSystem.generate_hint()` for A1-A2 sessions
  - Do NOT call ScaffoldingSystem for B1+ sessions (existing behavior)
  - Maintain existing hint triggering logic (silence detection, hint count)
  - Handle missing scenario data gracefully (fallback to generic hints)
  - Handle empty turn history gracefully (fallback to generic hints)
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 7.5, 7.6_
  - _Estimated effort: 0.5 days_

- [ ]* 14. Write integration tests for end-to-end hint generation
  - Test context extraction from session/scenario/turn history
  - Test context passed to ScaffoldingSystem for A1-A2 sessions
  - Test ScaffoldingSystem NOT called for B1+ sessions
  - Test graceful handling of missing scenario data
  - Test graceful handling of empty turn history
  - _Requirements: 12.6, 12.7_
  - _Estimated effort: 1 day_

- [ ] 15. Checkpoint - Validate end-to-end integration
  - Ensure all tests pass
  - Manually test full conversation flow with context-aware hints
  - Verify hints reference scenario vocabulary and learner mistakes
  - Ask user if questions arise

---

### Phase 4: Testing & Validation (2-3 days)

- [ ]* 16. Manual validation with real scenarios
  - [ ]* 16.1 Test implicit correction with A1 learner making grammar errors
    - Create session with A1 level
    - Submit turns with grammar errors (e.g., "I go yesterday")
    - Verify AI response models correct usage naturally
    - Verify no explicit correction phrases
    - _Requirements: 9.1, 9.7, 9.8_
  
  - [ ]* 16.2 Test implicit correction with B1 learner making intermediate errors
    - Create session with B1 level
    - Submit turns with present perfect errors
    - Verify AI response models correct usage naturally
    - _Requirements: 9.3, 9.7, 9.8_
  
  - [ ]* 16.3 Test context-aware hints in restaurant scenario
    - Create A1 session with restaurant scenario
    - Trigger hint generation (silence)
    - Verify hint includes restaurant vocabulary
    - _Requirements: 4.1, 4.6, 12.3_
  
  - [ ]* 16.4 Test context-aware hints with past tense errors
    - Create A1 session with any scenario
    - Submit turn with past tense error (e.g., "I go yesterday")
    - Trigger hint generation
    - Verify hint includes past tense examples
    - _Requirements: 5.1, 12.4_
  
  - _Estimated effort: 1.5 days_

- [x]* 17. Verify backward compatibility
  - Run existing unit tests for PromptBuilder (should pass without modification)
  - Run existing unit tests for ScaffoldingSystem (should pass without modification)
  - Run existing integration tests for SubmitSpeakingTurnUseCase (should pass without modification)
  - Verify API contracts unchanged (Session, Turn, Hint endpoints)
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.7, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 12.8_
  - _Estimated effort: 0.5 days_

- [ ] 18. Final checkpoint - Complete validation
  - Ensure all tests pass (unit, integration, manual)
  - Verify implicit correction works for all CEFR levels
  - Verify context-aware hints work for all scenarios
  - Verify backward compatibility maintained
  - Document any known limitations or edge cases
  - Ask user if questions arise

---

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP delivery
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at phase boundaries
- Testing tasks are sub-tasks to keep implementation and validation together
- Context extraction reuses existing `OffTopicDetector` for scenario keywords
- Grammar pattern detection uses simple heuristics (no ML models required)
- All changes maintain backward compatibility (no breaking API changes)

## Success Criteria

**Phase 1 Complete When:**
- PromptBuilder generates prompts with implicit correction instructions for all levels
- Few-shot examples demonstrate natural error correction without explicit phrases
- Existing prompt structure maintained (backward compatible)

**Phase 2 Complete When:**
- ScaffoldingSystem accepts context parameter and generates context-aware hints
- Scenario vocabulary mappings cover restaurant, airport, hotel, shopping scenarios
- Grammar pattern detection identifies past/present tense, questions, short responses
- Generic hints generated when context unavailable (backward compatible)

**Phase 3 Complete When:**
- SubmitSpeakingTurnUseCase extracts context from session/scenario/turn history
- Context passed to ScaffoldingSystem for A1-A2 sessions only
- Graceful handling of missing data (fallback to generic hints)
- Existing hint triggering logic maintained

**Feature Complete When:**
- All implementation tasks completed
- All unit tests pass (existing + new)
- Manual validation confirms implicit correction and context-aware hints work
- Backward compatibility verified (existing sessions work unchanged)
- API contracts unchanged (no frontend updates required)
