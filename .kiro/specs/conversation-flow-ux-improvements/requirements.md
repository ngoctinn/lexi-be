# Requirements Document: Conversation Flow UX Improvements

## Introduction

This document defines requirements for two critical UX improvements to the Lexi EdTech conversation system based on Duolingo Video Call best practices and user feedback. The improvements address the empty-start problem (no AI greeting) and the oversimplified hint structure (single-sentence hints instead of structured guidance).

The Lexi conversation system currently starts sessions with empty turns, leaving learners uncertain about how to begin. Additionally, the hint system provides only a single sentence ("You could say...") when learners need structured guidance including conversation context, turn goals, example phrases, and grammar tips in bilingual format (Vietnamese + English).

## Glossary

- **Conversation_System**: The Lexi EdTech AI-powered speaking practice system
- **CreateSpeakingSessionUseCase**: Application use case that creates new speaking sessions
- **WebSocket_Handler**: Infrastructure handler that manages WebSocket connections and actions
- **ScaffoldingSystem**: Domain service that provides bilingual hints for A1-A2 learners
- **AI_Greeting**: The initial AI message that starts a conversation session
- **First_Question**: The AI's first question that establishes conversation topic and goals
- **Hint_Dialog**: Frontend UI component that displays structured hints (separate from chat)
- **Structured_Hint**: Enhanced hint format with context, goal, examples, and grammar tips
- **TTS**: Text-to-Speech service (Amazon Polly) for generating AI audio
- **Bedrock**: AWS service for LLM inference (Amazon Nova models)
- **CEFR**: Common European Framework of Reference for Languages (A1-C2)
- **Turn**: A single message in the conversation (user or AI)
- **Session**: A complete conversation practice session with multiple turns

## Requirements

### Requirement 1: Generate AI Greeting on Session Creation

**User Story:** As a learner, I want the AI to greet me when I start a session, so that I know the conversation has begun and feel welcomed.

#### Acceptance Criteria

1. WHEN CreateSpeakingSessionUseCase creates a session, THE Conversation_System SHALL generate an AI greeting
2. THE AI_Greeting SHALL be level-appropriate for the learner's proficiency level (A1-C2)
3. THE AI_Greeting SHALL be saved as the first AI turn with turn_index=0
4. THE Conversation_System SHALL generate audio for the AI_Greeting using TTS
5. THE AI_Greeting SHALL use simple language for A1 (e.g., "Hi! How are you?")
6. THE AI_Greeting SHALL use more sophisticated language for C2 (e.g., "Greetings! How have you been?")
7. THE AI_Greeting SHALL be consistent with the AI's assigned role in the scenario

### Requirement 2: Generate First Question on Session Creation

**User Story:** As a learner, I want the AI to ask me a first question, so that I know what to talk about and can start the conversation confidently.

#### Acceptance Criteria

1. WHEN CreateSpeakingSessionUseCase creates a session, THE Conversation_System SHALL generate a first question
2. THE First_Question SHALL be based on the selected scenario and goals
3. THE First_Question SHALL establish the conversation topic clearly
4. THE First_Question SHALL be level-appropriate for the learner's proficiency level
5. THE First_Question SHALL be saved as part of the first AI turn (turn_index=0)
6. THE Conversation_System SHALL generate audio for the First_Question using TTS
7. THE First_Question SHALL reference the learner's role and scenario context

### Requirement 3: Level-Appropriate Greeting Generation

**User Story:** As a learner, I want greetings that match my proficiency level, so that I can understand and respond appropriately.

#### Acceptance Criteria

1. FOR A1 learners, THE AI_Greeting SHALL use basic vocabulary and simple grammar
2. FOR A2 learners, THE AI_Greeting SHALL use elementary vocabulary with simple sentences
3. FOR B1 learners, THE AI_Greeting SHALL use intermediate vocabulary with compound sentences
4. FOR B2 learners, THE AI_Greeting SHALL use upper-intermediate vocabulary with varied structures
5. FOR C1 learners, THE AI_Greeting SHALL use advanced vocabulary with complex structures
6. FOR C2 learners, THE AI_Greeting SHALL use sophisticated vocabulary with nuanced expressions
7. THE Conversation_System SHALL use Bedrock (Amazon Nova) to generate level-appropriate greetings

### Requirement 4: Enhance Hint Response Structure

**User Story:** As a learner, I want structured hints with context and examples, so that I can understand what to say and how to say it.

#### Acceptance Criteria

1. WHEN WebSocket_Handler receives USE_HINT action, THE Conversation_System SHALL generate a structured hint
2. THE Structured_Hint SHALL include conversation_context (what has been discussed)
3. THE Structured_Hint SHALL include turn_goal (what the learner should accomplish)
4. THE Structured_Hint SHALL include suggested_approach (how to respond)
5. THE Structured_Hint SHALL include example_phrases (2-3 example sentences)
6. THE Structured_Hint SHALL include grammar_tip (relevant grammar point)
7. THE WebSocket_Handler SHALL send the Structured_Hint in the HINT_TEXT event

### Requirement 5: Bilingual Hint Content

**User Story:** As a Vietnamese learner, I want hints in both Vietnamese and English, so that I can understand the guidance clearly.

#### Acceptance Criteria

1. THE conversation_context field SHALL be provided in Vietnamese and English
2. THE turn_goal field SHALL be provided in Vietnamese and English
3. THE suggested_approach field SHALL be provided in Vietnamese and English
4. THE example_phrases field SHALL be provided in Vietnamese and English
5. THE grammar_tip field SHALL be provided in Vietnamese and English
6. THE Conversation_System SHALL use consistent translation quality across all fields
7. THE bilingual format SHALL follow the pattern: Vietnamese text followed by English text

### Requirement 6: Contextual Hint Generation

**User Story:** As a learner, I want hints that are relevant to my current conversation, so that I can continue the dialogue naturally.

#### Acceptance Criteria

1. THE Conversation_System SHALL analyze the last AI turn to generate contextual hints
2. THE Conversation_System SHALL consider the selected goals when generating hints
3. THE Conversation_System SHALL consider the learner's proficiency level when generating hints
4. THE Conversation_System SHALL use ScaffoldingSystem to access scenario vocabulary
5. THE Conversation_System SHALL use Bedrock to generate contextual explanations
6. THE Structured_Hint SHALL be specific to the current conversation state
7. THE Structured_Hint SHALL help the learner progress toward the selected goals

### Requirement 7: Backward Compatibility

**User Story:** As a developer, I want backward compatibility with existing sessions, so that deployed clients continue to work during rollout.

#### Acceptance Criteria

1. THE Conversation_System SHALL support existing sessions without AI greetings
2. THE WebSocket_Handler SHALL support existing hint format for old clients
3. THE Conversation_System SHALL not break existing API contracts
4. THE Conversation_System SHALL handle sessions created before the feature deployment
5. THE Conversation_System SHALL gracefully degrade if greeting generation fails
6. THE Conversation_System SHALL gracefully degrade if structured hint generation fails
7. THE Conversation_System SHALL log errors without breaking the user experience

### Requirement 8: Audio Generation for Greetings

**User Story:** As a learner, I want to hear the AI greeting, so that I can practice listening comprehension from the start.

#### Acceptance Criteria

1. WHEN the AI_Greeting is generated, THE Conversation_System SHALL synthesize audio using TTS
2. THE TTS SHALL use the AI's assigned gender (male/female voice)
3. THE audio file SHALL be stored in S3 with the path pattern: speaking/audio/{session_id}/0.mp3
4. THE audio_url SHALL be saved in the Turn entity for the greeting turn
5. THE Conversation_System SHALL handle TTS failures gracefully (greeting text without audio)
6. THE audio generation SHALL not block session creation (async if possible)
7. THE audio quality SHALL be consistent with other AI turn audio

### Requirement 9: Hint Response Format

**User Story:** As a frontend developer, I want a well-defined hint response format, so that I can display structured hints in the UI.

#### Acceptance Criteria

1. THE HINT_TEXT event SHALL include a "hint" field with the structured hint object
2. THE structured hint object SHALL have the schema: {conversation_context: {vi: string, en: string}, turn_goal: {vi: string, en: string}, suggested_approach: {vi: string, en: string}, example_phrases: {vi: string[], en: string[]}, grammar_tip: {vi: string, en: string}}
3. THE WebSocket_Handler SHALL validate the structured hint before sending
4. THE WebSocket_Handler SHALL handle missing fields gracefully (provide defaults)
5. THE HINT_TEXT event SHALL maintain backward compatibility with simple string hints
6. THE WebSocket_Handler SHALL log hint generation metrics (latency, success rate)
7. THE structured hint SHALL be JSON-serializable without custom encoders

### Requirement 10: Performance and Cost Constraints

**User Story:** As a product owner, I want cost-effective greeting and hint generation, so that we maintain acceptable margins.

#### Acceptance Criteria

1. THE AI_Greeting generation SHALL use Amazon Nova Micro (lowest cost model)
2. THE Structured_Hint generation SHALL use Amazon Nova Micro (lowest cost model)
3. THE greeting generation SHALL complete within 2 seconds (p95)
4. THE hint generation SHALL complete within 2 seconds (p95)
5. THE Conversation_System SHALL cache greeting templates per level (reduce LLM calls)
6. THE Conversation_System SHALL reuse scenario vocabulary from ScaffoldingSystem
7. THE Conversation_System SHALL log cost metrics for greeting and hint generation
