# Requirements Document: Quick Wins - Implicit Error Correction & Context-Aware Scaffolding

## Introduction

This document defines requirements for implementing two high-impact, low-effort improvements to the Lexi EdTech conversation system: implicit error correction and context-aware scaffolding. These "quick wins" address critical UX gaps identified in the conversation system analysis, targeting 1-2 weeks of implementation effort with immediate learner experience improvements.

The Lexi conversation system currently lacks implicit error correction (AI doesn't model correct usage when learners make mistakes) and has overly generic scaffolding hints that don't leverage scenario context or learner mistakes. These improvements will enhance pedagogical effectiveness while maintaining backward compatibility with existing sessions.

## Glossary

- **Conversation_System**: The Lexi EdTech AI-powered speaking practice system
- **PromptBuilder**: Service that generates optimized prompts for AI conversation partners (`src/domain/services/prompt_builder.py`)
- **ScaffoldingSystem**: Service that provides bilingual hints for A1-A2 learners (`src/domain/services/scaffolding_system.py`)
- **Implicit_Error_Correction**: Pedagogical technique where AI models correct usage naturally in response without explicit correction (e.g., learner says "I go yesterday" → AI responds "When you went there, did you...")
- **Context_Aware_Scaffolding**: Hints that reference scenario vocabulary, learner's last utterance, and conversation goals (vs. generic hints)
- **Few_Shot_Examples**: Example conversations in prompts that demonstrate desired AI behavior
- **CEFR**: Common European Framework of Reference for Languages (A1-C2 proficiency levels)
- **Scenario**: Learning context (e.g., restaurant, airport) with specific vocabulary and roles
- **Turn**: Single exchange in conversation (user utterance + AI response)
- **Use_Case**: Application layer service that orchestrates business logic (`src/application/use_cases/speaking_session_use_cases.py`)

## Requirements

### Requirement 1: Implicit Error Correction in Prompt Instructions

**User Story:** As a language learner, I want the AI to model correct grammar and vocabulary naturally in its responses, so that I can learn from correct examples without feeling explicitly corrected.

#### Acceptance Criteria

1. THE PromptBuilder SHALL include pedagogical instructions for implicit error correction in the system prompt
2. THE PromptBuilder SHALL instruct the AI to model correct usage naturally in responses WITHOUT explicit correction statements
3. THE PromptBuilder SHALL specify that implicit correction applies to grammar mistakes, vocabulary mistakes, and pronunciation-related text errors
4. THE PromptBuilder SHALL instruct the AI to continue the conversation naturally while modeling correct forms
5. THE PromptBuilder SHALL maintain existing explicit correction rules (Vietnamese usage, inappropriate language, off-topic)

### Requirement 2: Level-Specific Implicit Correction Examples

**User Story:** As a language learner at different proficiency levels, I want error correction appropriate to my level, so that I receive support matched to my abilities.

#### Acceptance Criteria

1. THE PromptBuilder SHALL provide few-shot examples demonstrating implicit correction for A1 level learners
2. THE PromptBuilder SHALL provide few-shot examples demonstrating implicit correction for A2 level learners
3. THE PromptBuilder SHALL provide few-shot examples demonstrating implicit correction for B1 level learners
4. THE PromptBuilder SHALL provide few-shot examples demonstrating implicit correction for B2 level learners
5. THE PromptBuilder SHALL provide few-shot examples demonstrating implicit correction for C1 level learners
6. THE PromptBuilder SHALL provide few-shot examples demonstrating implicit correction for C2 level learners
7. FOR ALL proficiency levels, implicit correction examples SHALL demonstrate natural conversation flow with modeled correct usage
8. FOR ALL proficiency levels, implicit correction examples SHALL avoid explicit correction phrases like "You should say..." or "The correct form is..."

### Requirement 3: Context Parameter for Scaffolding System

**User Story:** As a developer, I want the scaffolding system to accept context parameters, so that hints can be generated based on scenario, learner utterance, and conversation goals.

#### Acceptance Criteria

1. THE ScaffoldingSystem SHALL accept a context parameter containing scenario vocabulary
2. THE ScaffoldingSystem SHALL accept a context parameter containing the learner's last utterance
3. THE ScaffoldingSystem SHALL accept a context parameter containing conversation goals
4. THE ScaffoldingSystem SHALL accept a context parameter containing the current scenario title
5. WHEN context is not provided, THE ScaffoldingSystem SHALL generate generic hints (backward compatibility)
6. THE ScaffoldingSystem SHALL maintain existing hint level logic (gentle prompt, vocabulary hint, sentence starter)

### Requirement 4: Scenario-Specific Vocabulary Hints

**User Story:** As an A1-A2 learner, I want hints that suggest vocabulary relevant to my current scenario, so that I can practice scenario-appropriate language.

#### Acceptance Criteria

1. WHEN generating vocabulary hints for restaurant scenarios, THE ScaffoldingSystem SHALL suggest restaurant-specific phrases (e.g., "I'd like to order...", "Can I have...")
2. WHEN generating vocabulary hints for airport scenarios, THE ScaffoldingSystem SHALL suggest airport-specific phrases (e.g., "I need to check in...", "Where is gate...")
3. WHEN generating vocabulary hints for hotel scenarios, THE ScaffoldingSystem SHALL suggest hotel-specific phrases (e.g., "I have a reservation...", "Can I get a room...")
4. WHEN generating vocabulary hints for shopping scenarios, THE ScaffoldingSystem SHALL suggest shopping-specific phrases (e.g., "How much is...", "I'm looking for...")
5. WHEN scenario vocabulary is not available, THE ScaffoldingSystem SHALL generate generic vocabulary hints (fallback)
6. THE ScaffoldingSystem SHALL maintain bilingual format (Vietnamese + English) for all scenario-specific hints

### Requirement 5: Mistake-Aware Hint Generation

**User Story:** As an A1-A2 learner who makes grammar mistakes, I want hints that help me with the specific grammar pattern I'm struggling with, so that I can improve in targeted areas.

#### Acceptance Criteria

1. WHEN the learner's last utterance contains past tense errors, THE ScaffoldingSystem SHALL include past tense examples in hints
2. WHEN the learner's last utterance contains present tense errors, THE ScaffoldingSystem SHALL include present tense examples in hints
3. WHEN the learner's last utterance contains question formation errors, THE ScaffoldingSystem SHALL include question examples in hints
4. WHEN the learner's last utterance contains vocabulary gaps (very short responses), THE ScaffoldingSystem SHALL suggest relevant vocabulary
5. WHEN the learner's last utterance is not available, THE ScaffoldingSystem SHALL generate generic hints (fallback)
6. THE ScaffoldingSystem SHALL detect grammar patterns using simple heuristics (keyword matching, not complex NLP)

### Requirement 6: Use Case Integration for Context Passing

**User Story:** As a developer, I want the speaking session use case to pass context to the scaffolding system, so that context-aware hints can be generated during conversations.

#### Acceptance Criteria

1. THE SubmitSpeakingTurnUseCase SHALL extract scenario vocabulary from the current scenario
2. THE SubmitSpeakingTurnUseCase SHALL extract the learner's last utterance from the turn history
3. THE SubmitSpeakingTurnUseCase SHALL extract conversation goals from the session
4. THE SubmitSpeakingTurnUseCase SHALL pass context to ScaffoldingSystem when generating hints
5. WHEN scaffolding is not needed (B1+ levels), THE SubmitSpeakingTurnUseCase SHALL NOT call ScaffoldingSystem
6. THE SubmitSpeakingTurnUseCase SHALL maintain existing hint triggering logic (silence detection, hint count)

### Requirement 7: Backward Compatibility

**User Story:** As a system operator, I want these improvements to be backward compatible, so that existing sessions continue to work without disruption.

#### Acceptance Criteria

1. THE PromptBuilder SHALL maintain existing prompt structure and format
2. THE PromptBuilder SHALL maintain existing prompt version tracking
3. THE ScaffoldingSystem SHALL generate valid hints when context parameter is None
4. THE ScaffoldingSystem SHALL generate valid hints when context parameter is empty dict
5. THE SubmitSpeakingTurnUseCase SHALL handle scenarios without vocabulary data
6. THE SubmitSpeakingTurnUseCase SHALL handle sessions without turn history
7. FOR ALL changes, existing API contracts SHALL remain unchanged

### Requirement 8: No Breaking Changes to API

**User Story:** As a frontend developer, I want the API to remain unchanged, so that I don't need to update frontend code.

#### Acceptance Criteria

1. THE Session API endpoints SHALL maintain existing request/response formats
2. THE Turn submission API SHALL maintain existing request/response formats
3. THE Hint generation API SHALL maintain existing response format (BilingualHint)
4. THE Session creation API SHALL maintain existing request/response formats
5. FOR ALL API endpoints, existing field names and types SHALL remain unchanged
6. FOR ALL API endpoints, new fields SHALL be optional or have default values

### Requirement 9: Implicit Correction Prompt Examples

**User Story:** As a prompt engineer, I want concrete examples of implicit correction per level, so that the AI learns the desired behavior through few-shot learning.

#### Acceptance Criteria

1. FOR A1 level, implicit correction examples SHALL demonstrate simple grammar corrections (e.g., "I go beach" → "When you went to the beach, did you swim?")
2. FOR A2 level, implicit correction examples SHALL demonstrate basic tense corrections (e.g., "I am go yesterday" → "That sounds fun! When you went there, what did you do?")
3. FOR B1 level, implicit correction examples SHALL demonstrate intermediate grammar corrections (e.g., "I have went" → "That's interesting! When you went there, did you enjoy it?")
4. FOR B2 level, implicit correction examples SHALL demonstrate advanced grammar corrections (e.g., "If I would have known" → "That's a good point. If you had known earlier, what would you have done?")
5. FOR C1 level, implicit correction examples SHALL demonstrate sophisticated corrections (e.g., subjunctive, conditional perfect)
6. FOR C2 level, implicit correction examples SHALL demonstrate native-level corrections (e.g., idiomatic usage, collocations)
7. FOR ALL levels, examples SHALL show the AI continuing the conversation naturally after modeling correct usage
8. FOR ALL levels, examples SHALL avoid explicit correction phrases

### Requirement 10: Scenario Vocabulary Mapping

**User Story:** As a developer, I want a mapping of common scenarios to relevant vocabulary, so that context-aware hints can suggest appropriate phrases.

#### Acceptance Criteria

1. THE ScaffoldingSystem SHALL define vocabulary mappings for restaurant scenarios
2. THE ScaffoldingSystem SHALL define vocabulary mappings for airport scenarios
3. THE ScaffoldingSystem SHALL define vocabulary mappings for hotel scenarios
4. THE ScaffoldingSystem SHALL define vocabulary mappings for shopping scenarios
5. THE ScaffoldingSystem SHALL define vocabulary mappings for general conversation scenarios
6. FOR ALL scenario mappings, vocabulary SHALL include common phrases at A1-A2 level
7. FOR ALL scenario mappings, vocabulary SHALL include both questions and statements
8. WHEN a scenario is not in the mapping, THE ScaffoldingSystem SHALL use general conversation vocabulary

### Requirement 11: Simple Grammar Pattern Detection

**User Story:** As a developer, I want simple heuristics to detect grammar patterns in learner utterances, so that mistake-aware hints can be generated without complex NLP.

#### Acceptance Criteria

1. THE ScaffoldingSystem SHALL detect past tense patterns using keyword matching (e.g., "yesterday", "last", "ago")
2. THE ScaffoldingSystem SHALL detect present tense patterns using keyword matching (e.g., "now", "today", "always")
3. THE ScaffoldingSystem SHALL detect question patterns using punctuation and question words (e.g., "?", "what", "where", "when")
4. THE ScaffoldingSystem SHALL detect short responses (< 5 words) as potential vocabulary gaps
5. THE ScaffoldingSystem SHALL detect verb form errors using simple regex patterns (e.g., "I go yesterday", "I am go")
6. FOR ALL pattern detection, THE ScaffoldingSystem SHALL use simple string matching (not ML models)
7. WHEN no patterns are detected, THE ScaffoldingSystem SHALL generate generic hints

### Requirement 12: Testing and Validation

**User Story:** As a QA engineer, I want to validate that implicit correction and context-aware scaffolding work correctly, so that learners receive high-quality support.

#### Acceptance Criteria

1. THE PromptBuilder SHALL generate prompts with implicit correction instructions for all CEFR levels
2. THE PromptBuilder SHALL generate prompts with level-appropriate few-shot examples
3. THE ScaffoldingSystem SHALL generate scenario-specific hints when context is provided
4. THE ScaffoldingSystem SHALL generate mistake-aware hints when learner utterance is provided
5. THE ScaffoldingSystem SHALL generate generic hints when context is not provided (backward compatibility)
6. THE SubmitSpeakingTurnUseCase SHALL pass context to ScaffoldingSystem for A1-A2 sessions
7. THE SubmitSpeakingTurnUseCase SHALL NOT call ScaffoldingSystem for B1+ sessions
8. FOR ALL changes, existing unit tests SHALL pass without modification
