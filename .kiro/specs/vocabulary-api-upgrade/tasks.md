# Implementation Plan: Vocabulary API Upgrade with Dictionary API + AWS Translate

## Overview

This implementation plan breaks down the vocabulary API upgrade into sequential, executable tasks following Clean Architecture principles. The upgrade integrates Dictionary API for comprehensive word information (pronunciation, definitions, examples, synonyms) with AWS Translate for Vietnamese translations. All tasks maintain backward compatibility and follow the existing codebase patterns.

**Total Estimated Effort:** 23-28 hours
- Infrastructure Layer: 4-5 hours
- Adapter Layer: 6-7 hours (includes Simplemma integration and phrasal verb detection)
- Application Layer: 3-4 hours
- Interface Layer: 2-3 hours
- Testing: 5.5-6.5 hours (includes phrasal verb tests)
- Documentation: 1-2 hours

---

## Phase 1: Infrastructure Layer (Foundation)

### Task 1.1: Create CacheService (In-Memory + DynamoDB)

**Objective:** Implement two-tier caching service for Dictionary API responses.

**Description:**
Create `src/infrastructure/services/cache_service.py` with CacheService class that provides:
- In-memory cache for fast access (Lambda warm starts)
- DynamoDB fallback for persistent caching across Lambda invocations
- 24-hour TTL for all cached entries
- Cache key format: `vocabulary:definition:{word_lowercase}`

**Acceptance Criteria:**
- [x] CacheService class with `get(key: str) -> WordDefinition | None` method
- [x] CacheService class with `set(key: str, value: WordDefinition, ttl_seconds: int = 86400)` method
- [x] In-memory cache implementation (dict-based or requests-cache)
- [x] DynamoDB integration using boto3 with proper error handling
- [x] TTL attribute configured on DynamoDB table
- [x] Logging for cache hits/misses
- [x] Unit tests for cache operations

**Dependencies:** None

**Files to Create/Modify:**
- Create: `src/infrastructure/services/cache_service.py`
- Modify: `src/infrastructure/services/__init__.py` (add import)

**Estimated Effort:** 2 hours

---

### Task 1.2: Create RetryService (Exponential Backoff)

**Objective:** Implement retry logic with exponential backoff for transient failures.

**Description:**
Create `src/infrastructure/services/retry_service.py` with RetryService class that provides:
- Exponential backoff retry: 1s, 2s (max 2 retries)
- Retry on: HTTP 429 (rate limit), 5xx (server errors)
- No retry on: 404 (not found), 4xx (client errors)
- Timeout handling
- Logging for retry attempts

**Acceptance Criteria:**
- [x] RetryService class with `execute_with_retry(func, max_retries=2, backoff_delays=[1, 2])` method
- [x] Proper exception handling for transient vs permanent errors
- [x] Exponential backoff implementation with configurable delays
- [x] Logging for each retry attempt
- [x] Unit tests for retry logic

**Dependencies:** None

**Files to Create/Modify:**
- Create: `src/infrastructure/services/retry_service.py`
- Modify: `src/infrastructure/services/__init__.py` (add import)

**Estimated Effort:** 1.5 hours

---

### Task 1.3: Create DictionaryService Port

**Objective:** Define abstract interface for Dictionary API integration.

**Description:**
Create `src/application/service_ports/dictionary_service.py` with DictionaryService abstract class that defines:
- `get_word_definition(word: str) -> WordDefinition` method
- Exception types: WordNotFoundError, DictionaryServiceError, TimeoutError
- Docstrings with clear contract

**Acceptance Criteria:**
- [x] DictionaryService abstract base class
- [x] `get_word_definition()` abstract method with proper signature
- [x] Custom exception classes (WordNotFoundError, DictionaryServiceError)
- [x] Clear docstrings explaining contract and exceptions
- [x] Follows existing port pattern (similar to TranslationService)

**Dependencies:** None

**Files to Create/Modify:**
- Create: `src/application/service_ports/dictionary_service.py`
- Create: `src/domain/exceptions/dictionary_exceptions.py` (exception classes)
- Modify: `src/application/service_ports/__init__.py` (add import)

**Estimated Effort:** 1 hour

---

## Phase 2: Adapter Layer (Implementation)

### Task 2.1: Install Simplemma Dependency

**Objective:** Add Simplemma library for lemmatization support.

**Description:**
Add Simplemma to project dependencies for dictionary-based lemmatization:
- Add `simplemma==1.1.2` to requirements or dependencies file
- Verify package size (~67MB) is acceptable for Lambda
- Test import and basic usage

**Acceptance Criteria:**
- [x] Simplemma added to project dependencies
- [x] Package successfully installed
- [x] Import test passes: `import simplemma`
- [x] Basic lemmatization test passes: `simplemma.lemmatize('running', lang='en')` → 'run'

**Dependencies:** None

**Files to Create/Modify:**
- Modify: `requirements.txt` or `pyproject.toml` (add simplemma==1.1.2)

**Estimated Effort:** 0.5 hours

---

### Task 2.2: Create DictionaryServiceAdapter (Dictionary API Integration)

**Objective:** Implement DictionaryService by calling Dictionary API with proper error handling.

**Description:**
Create `src/infrastructure/adapters/dictionary_service_adapter.py` with DictionaryServiceAdapter class that:
- Calls Dictionary API: `https://dictionaryapi.dev/api/v2/entries/en/{word}`
- Parses response into Vocabulary domain entity
- Handles HTTP errors (404, 5xx, timeout)
- Logs all API calls (word, status, response time)
- Supports phrasal verbs (multi-word expressions)
- 30-second timeout per request

**Acceptance Criteria:**
- [x] DictionaryServiceAdapter implements DictionaryService port
- [x] HTTP client with 30-second timeout
- [x] Proper error handling for 404, 5xx, timeout
- [x] Response parsing into Vocabulary entity
- [x] Logging for all API calls
- [x] Support for phrasal verbs (spaces, hyphens, apostrophes)
- [x] Unit tests for successful response, 404, timeout, 5xx

**Dependencies:** Task 1.3 (DictionaryService port)

**Files to Create/Modify:**
- Create: `src/infrastructure/adapters/dictionary_service_adapter.py`
- Modify: `src/domain/entities/vocabulary.py` (ensure correct structure)
- Modify: `src/infrastructure/adapters/__init__.py` (add import)

**Estimated Effort:** 2 hours

---

### Task 2.3: Implement Phrasal Verb Detection with Lemmatization

**Objective:** Add context-aware phrasal verb detection with Simplemma lemmatization.

**Description:**
Update DictionaryServiceAdapter to support phrasal verb detection:
- Add `context: Optional[str]` parameter to `get_word_definition()`
- Implement `lemmatize_word()` using Simplemma
- Implement `find_phrasal_verb_candidates()` for bidirectional detection
- Generate candidates: phrasal verbs (lemmatized) + standalone word (lemmatized)
- Try Dictionary API with each candidate in priority order
- Fallback to next candidate on 404

**Implementation Details:**
```python
# Lemmatization
def lemmatize_word(word: str) -> list[str]:
    word_lower = word.lower()
    lemma = simplemma.lemmatize(word_lower, lang='en')
    if lemma != word_lower:
        return [word_lower, lemma]
    return [word_lower]

# Phrasal verb detection
PARTICLES = ["up", "down", "off", "on", "out", "in", "away", "back", ...]

def find_phrasal_verb_candidates(word: str, context: str) -> list[str]:
    # Case 1: User clicked VERB → check next word for particle
    # Case 2: User clicked PARTICLE → check previous word
    # Return: [phrasal_verb_lemmas..., word_lemmas...]
```

**Acceptance Criteria:**
- [x] `get_word_definition()` accepts optional `context` parameter
- [x] `lemmatize_word()` function using Simplemma
- [x] `find_phrasal_verb_candidates()` function with bidirectional detection
- [x] PARTICLES list with common particles (up, down, off, on, out, in, etc.)
- [x] Candidate generation: phrasal verbs + standalone word
- [x] Fallback logic: try each candidate, return first success
- [x] Unit tests for lemmatization (got→get, looked→look, running→run)
- [x] Unit tests for phrasal verb detection (click verb, click particle)
- [x] Unit tests for fallback scenarios
- [x] Integration tests with real Dictionary API

**Test Cases:**
- "got off" (V2 + particle) → candidates: ["got off", "get off", "got", "get"] → finds "get off"
- "looked up" (V-ed + particle) → candidates: ["looked up", "look up", "looked", "look"] → finds "look up"
- Click "off" in "I got off" → candidates: ["got off", "get off", "off"] → finds "get off"
- Click "up" in "I looked up" → candidates: ["looked up", "look up", "up"] → finds "look up"
- "got" alone → candidates: ["got", "get"] → finds "got"

**Dependencies:** Task 2.1 (Simplemma), Task 2.2 (DictionaryServiceAdapter)

**Files to Create/Modify:**
- Modify: `src/infrastructure/adapters/dictionary_service_adapter.py`
- Modify: `src/application/service_ports/dictionary_service.py` (add context parameter)

**Estimated Effort:** 3 hours

---

### Task 2.4: Integrate CacheService into DictionaryServiceAdapter

**Objective:** Add caching layer to DictionaryServiceAdapter for performance optimization.

**Description:**
Update DictionaryServiceAdapter to:
- Inject CacheService via constructor
- Check cache before calling Dictionary API
- Cache successful responses with 24-hour TTL
- Log cache hits/misses
- Handle cache failures gracefully (continue without caching)

**Acceptance Criteria:**
- [x] CacheService injected into DictionaryServiceAdapter
- [x] Cache lookup before API call
- [x] Cache storage after successful API call
- [x] Cache key format: `vocabulary:definition:{word_lowercase}`
- [x] Logging for cache operations
- [x] Unit tests for cache hit/miss scenarios
- [x] Integration tests with mocked cache

**Dependencies:** Task 1.1 (CacheService), Task 2.3 (Phrasal verb detection)

**Files to Create/Modify:**
- Modify: `src/infrastructure/adapters/dictionary_service_adapter.py`

**Estimated Effort:** 1.5 hours

---

### Task 2.5: Integrate RetryService into DictionaryServiceAdapter

**Objective:** Add retry logic to DictionaryServiceAdapter for resilience.

**Description:**
Update DictionaryServiceAdapter to:
- Inject RetryService via constructor
- Wrap Dictionary API calls with retry logic
- Retry on HTTP 429, 5xx
- No retry on 404, 4xx
- Log retry attempts and backoff delays

**Acceptance Criteria:**
- [x] RetryService injected into DictionaryServiceAdapter
- [x] Dictionary API calls wrapped with retry logic
- [x] Exponential backoff: 1s, 2s (max 2 retries)
- [x] Proper error handling after max retries
- [x] Logging for retry attempts
- [x] Unit tests for retry scenarios (429, 5xx, success on retry)
- [x] Integration tests with mocked API returning transient errors

**Dependencies:** Task 1.2 (RetryService), Task 2.4 (Cache integration)

**Files to Create/Modify:**
- Modify: `src/infrastructure/adapters/dictionary_service_adapter.py`

**Estimated Effort:** 1.5 hours

---

## Phase 3: Application Layer (Business Logic)

### Task 3.1: Update Domain Entities (Vocabulary, Meaning)

**Objective:** Update domain entities for word information with translations.

**Description:**
Update domain entities in `src/domain/entities/vocabulary.py`:
- **Vocabulary**: word, translate_vi, phonetic, audio_url, meanings[], origin
- **Meaning**: part_of_speech, definition, definition_vi, example, example_vi
- **Phonetic**: text, audio (keep existing)

**Key Changes:**
- Remove `DefinitionItem` (flatten into Meaning)
- Remove `phonetics` list from Vocabulary (use single audio_url)
- Add translation fields to Meaning: definition_vi, example_vi
- Meaning contains ONE definition and ONE example (FIRST from API)

**Acceptance Criteria:**
- [x] Vocabulary dataclass with fields: word, translate_vi, phonetic, audio_url, meanings, origin
- [x] Meaning dataclass with fields: part_of_speech, definition, definition_vi, example, example_vi
- [x] Phonetic dataclass unchanged (text, audio)
- [x] Proper type hints and validation
- [x] Docstrings explaining each entity
- [x] Unit tests for entity creation and validation

**Dependencies:** None

**Files to Create/Modify:**
- Modify: `src/domain/entities/vocabulary.py`

**Estimated Effort:** 1 hour

---

### Task 3.2: Create/Update Vocabulary DTOs (MeaningDTO)

**Objective:** Define DTOs for API request/response with proper validation.

**Description:**
Update `src/application/dtos/vocabulary_dtos.py` to:
- Add `context: Optional[str]` field to TranslateVocabularyCommand
- Create MeaningDTO with fields: part_of_speech, definition, definition_vi, example, example_vi
- Update TranslateVocabularyResponse to include: phonetic, audio_url, meanings[]
- Maintain backward compatibility (word, translate_vi at top level)
- Add validation for all fields

**Acceptance Criteria:**
- [x] TranslateVocabularyCommand has `context: Optional[str]` field
- [x] MeaningDTO class with proper validation
- [x] TranslateVocabularyResponse updated with new fields
- [x] Backward compatibility maintained (word, translate_vi)
- [x] Optional fields handled correctly (empty strings/arrays)
- [x] Pydantic validation for all fields
- [x] Unit tests for DTO validation

**Dependencies:** Task 3.1 (Domain entities)

**Files to Create/Modify:**
- Modify: `src/application/dtos/vocabulary_dtos.py`

**Estimated Effort:** 1 hour

---

### Task 3.3: Update TranslateVocabularyUseCase (Orchestration)

**Objective:** Implement vocabulary translation workflow orchestrating Dictionary API and AWS Translate.

**Description:**
Update `src/application/use_cases/translate_vocabulary_use_case.py` to:
- Inject DictionaryService and TranslationService
- Fetch word definition from DictionaryService
- Batch translate definitions, examples, synonyms using TranslationService
- Handle partial failures (graceful degradation)
- Return TranslateVocabularyResponse with complete data
- Log all operations

**Acceptance Criteria:**
- [x] DictionaryService and TranslationService injected
- [x] Workflow: fetch definition → batch translate → return response
- [x] Batch translation of definitions, examples, synonyms
- [x] Graceful degradation: return English if translation fails
- [x] Error handling: WordNotFoundError → HTTP 404, DictionaryServiceError → HTTP 503
- [x] Logging for all operations
- [x] Unit tests for successful flow, error scenarios
- [x] Integration tests with mocked services

**Dependencies:** Task 2.2 (DictionaryServiceAdapter), Task 3.2 (DTOs)

**Files to Create/Modify:**
- Create: `src/application/use_cases/translate_vocabulary_use_case.py` (if not exists)
- Modify: `src/application/use_cases/__init__.py` (add import)

**Estimated Effort:** 2 hours

---

### Task 3.4: Implement Batch Translation Logic

**Objective:** Optimize translation by batching multiple items in single AWS Translate call.

**Description:**
Update TranslateVocabularyUseCase to:
- Collect all items to translate: word, definitions, examples (FIRST only per meaning)
- Batch translate in single AWS Translate call
- Map translations back to original items
- Handle partial failures (some items translated, some not)
- Return original English if translation fails

**Acceptance Criteria:**
- [x] Batch collection of items to translate (word + FIRST definition + FIRST example per meaning)
- [x] Single AWS Translate call for all items
- [x] Proper mapping of translations to items
- [x] Partial failure handling
- [x] Fallback to English on translation failure
- [x] Unit tests for batch translation
- [x] Integration tests with mocked AWS Translate

**Dependencies:** Task 3.3 (TranslateVocabularyUseCase)

**Files to Create/Modify:**
- Modify: `src/application/use_cases/translate_vocabulary_use_case.py`

**Estimated Effort:** 1.5 hours

---

## Phase 4: Interface Layer (API)

### Task 4.1: Update VocabularyController

**Objective:** Update HTTP endpoint to handle new vocabulary translation workflow.

**Description:**
Update `src/interfaces/http/controllers/vocabulary_controller.py` to:
- Inject TranslateVocabularyUseCase
- Handle POST `/vocabulary/translate` requests
- Map HTTP request to TranslateVocabularyCommand
- Call use case and handle Result<Response, Error>
- Return appropriate HTTP status codes (200, 404, 503, 400)
- Log all requests

**Acceptance Criteria:**
- [x] TranslateVocabularyUseCase injected
- [x] POST `/vocabulary/translate` endpoint updated
- [x] Request mapping to TranslateVocabularyCommand
- [x] Result handling with proper HTTP status codes
- [x] Error response formatting
- [x] Logging for all requests
- [x] Unit tests for successful request, error scenarios

**Dependencies:** Task 3.3 (TranslateVocabularyUseCase)

**Files to Create/Modify:**
- Modify: `src/interfaces/http/controllers/vocabulary_controller.py`

**Estimated Effort:** 1 hour

---

### Task 4.2: Update VocabularyMapper

**Objective:** Map between DTOs and domain entities.

**Description:**
Update `src/interfaces/http/mappers/vocabulary_mapper.py` to:
- Map TranslateVocabularyResponse DTO to HTTP response JSON
- Map WordDefinition domain entity to TranslateVocabularyResponse DTO
- Handle optional fields (empty strings/arrays)
- Maintain backward compatibility

**Acceptance Criteria:**
- [x] Mapper methods for DTO ↔ domain entity conversion
- [x] Proper handling of optional fields
- [x] Backward compatibility maintained
- [x] Unit tests for mapping logic

**Dependencies:** Task 3.2 (DTOs), Task 3.1 (Domain entities)

**Files to Create/Modify:**
- Create: `src/interfaces/http/mappers/vocabulary_mapper.py` (if not exists)
- Modify: `src/interfaces/http/mappers/__init__.py` (add import)

**Estimated Effort:** 1 hour

---

### Task 4.3: Update API Response Format and Documentation

**Objective:** Document new API response format and update API documentation.

**Description:**
Update `API_DOCUMENTATION.md` to:
- Document new `/vocabulary/translate` response format
- Include example responses (successful, error scenarios)
- Document new fields (phonetic, definitions, synonyms)
- Maintain backward compatibility notes
- Document error codes and messages

**Acceptance Criteria:**
- [x] API documentation updated with new response format
- [x] Example responses for successful requests
- [x] Example responses for error scenarios (404, 503, 400)
- [x] Backward compatibility notes
- [x] Error code documentation
- [x] Performance SLA documented (< 2000ms)

**Dependencies:** Task 4.1 (VocabularyController)

**Files to Create/Modify:**
- Modify: `API_DOCUMENTATION.md`

**Estimated Effort:** 1 hour

---

## Phase 5: Testing (Quality Assurance)

### Task 5.1: Unit Tests - CacheService and RetryService

**Objective:** Test infrastructure services in isolation.

**Description:**
Create unit tests in `tests/infrastructure/services/`:
- CacheService: cache hit, cache miss, TTL expiration, DynamoDB fallback
- RetryService: successful execution, retry on transient error, no retry on permanent error, exponential backoff

**Acceptance Criteria:**
- [x] CacheService unit tests (hit, miss, TTL, DynamoDB)
- [x] RetryService unit tests (success, retry, backoff)
- [x] Mocked dependencies (boto3, HTTP client)
- [x] All tests passing
- [x] Code coverage > 80%

**Dependencies:** Task 1.1 (CacheService), Task 1.2 (RetryService)

**Files to Create/Modify:**
- Create: `tests/infrastructure/services/test_cache_service.py`
- Create: `tests/infrastructure/services/test_retry_service.py`

**Estimated Effort:** 1.5 hours

---

### Task 5.2: Unit Tests - Simplemma Lemmatization and Phrasal Verb Detection

**Objective:** Test lemmatization and phrasal verb detection logic in isolation.

**Description:**
Create unit tests for lemmatization and phrasal verb detection functions:
- Test `lemmatize_word()` with various word forms
- Test `find_phrasal_verb_candidates()` with different contexts
- Test particle detection (click verb, click particle)
- Test fallback scenarios

**Acceptance Criteria:**
- [x] Unit tests for lemmatization: "got"→"get", "looked"→"look", "running"→"run", "better"→"good"
- [x] Unit tests for phrasal verb detection when clicking verb
- [x] Unit tests for phrasal verb detection when clicking particle
- [x] Unit tests for no phrasal verb scenario (next word not particle)
- [x] Unit tests for candidate generation order
- [x] All tests passing
- [x] Code coverage > 80%

**Test Cases:**
- Lemmatization: "got" → ["got", "get"], "looked" → ["looked", "look"], "running" → ["running", "run"]
- Click verb: "got" in "I got off" → ["got off", "get off", "got", "get"]
- Click particle: "off" in "I got off" → ["got off", "get off", "off"]
- No phrasal: "got" in "I got a book" → ["got", "get"]

**Dependencies:** Task 2.3 (Phrasal verb detection implementation)

**Files to Create/Modify:**
- Create: `tests/unit/test_phrasal_verb_detection.py`

**Estimated Effort:** 1.5 hours

---

### Task 5.3: Unit Tests - DictionaryServiceAdapter

**Objective:** Test Dictionary API adapter in isolation.

**Description:**
Create unit tests in `tests/infrastructure/adapters/`:
- Successful response parsing
- 404 error handling
- 5xx error handling
- Timeout handling
- Retry logic (429, 5xx)
- Cache integration
- Logging

**Acceptance Criteria:**
- [x] Unit tests for successful response
- [x] Unit tests for 404 error
- [x] Unit tests for 5xx error
- [x] Unit tests for timeout
- [x] Unit tests for retry scenarios
- [x] Unit tests for cache integration
- [x] Mocked HTTP client and cache
- [x] All tests passing
- [x] Code coverage > 80%

**Dependencies:** Task 2.5 (DictionaryServiceAdapter with retry, cache, and phrasal verbs)

**Files to Create/Modify:**
- Create: `tests/infrastructure/adapters/test_dictionary_service_adapter.py`

**Estimated Effort:** 2 hours

---

### Task 5.4: Unit Tests - TranslateVocabularyUseCase

**Objective:** Test vocabulary translation use case in isolation.

**Description:**
Create unit tests in `tests/application/use_cases/`:
- Successful translation workflow
- Dictionary API error (404, 503)
- AWS Translate error (graceful degradation)
- Batch translation logic
- Logging

**Acceptance Criteria:**
- [x] Unit tests for successful workflow
- [x] Unit tests for Dictionary API 404
- [x] Unit tests for Dictionary API 503
- [x] Unit tests for AWS Translate failure
- [x] Unit tests for batch translation
- [x] Mocked DictionaryService and TranslationService
- [x] All tests passing
- [x] Code coverage > 80%

**Dependencies:** Task 3.4 (TranslateVocabularyUseCase with batch translation)

**Files to Create/Modify:**
- Create: `tests/application/use_cases/test_translate_vocabulary_use_case.py`

**Estimated Effort:** 2 hours

---

### Task 5.5: Property-Based Tests for Correctness Properties

**Objective:** Test universal correctness properties using property-based testing.

**Description:**
Create property-based tests using Hypothesis for:
- **Property 1**: Dictionary API response parsing preserves all data
- **Property 2**: Batch translation completes all items
- **Property 3**: English fallback on translation failure
- **Property 4**: Response contains required fields
- **Property 5**: Caching idempotence
- **Property 6**: Retry logic on transient errors
- **Property 7**: Phrasal verb preservation
- **Property 8**: Backward compatibility
- **Property 9**: Error response structure
- **Property 10**: Performance SLA - cached response < 500ms
- **Property 11**: Performance SLA - non-cached response < 2000ms
- **Property 12**: Logging completeness
- **Property 13**: Optional fields handling

**Acceptance Criteria:**
- [x] Property test for round-trip serialization (Property 1)
- [x] Property test for batch translation completeness (Property 2)
- [x] Property test for English fallback (Property 3)
- [x] Property test for required fields (Property 4)
- [x] Property test for caching idempotence (Property 5)
- [x] Property test for retry logic (Property 6)
- [x] Property test for phrasal verb preservation (Property 7)
- [x] Property test for backward compatibility (Property 8)
- [x] Property test for error response structure (Property 9)
- [x] Property test for cached response performance (Property 10)
- [x] Property test for non-cached response performance (Property 11)
- [x] Property test for logging completeness (Property 12)
- [x] Property test for optional fields handling (Property 13)
- [x] All property tests passing

**Dependencies:** Task 5.4 (Unit tests)

**Files to Create/Modify:**
- Create: `tests/properties/test_vocabulary_properties.py`

**Estimated Effort:** 2.5 hours

---

### Task 5.6: Integration Tests - Dictionary API and AWS Translate

**Objective:** Test integration with external services.

**Description:**
Create integration tests in `tests/integration/`:
- Dictionary API successful response
- Dictionary API 404 error
- Dictionary API timeout
- AWS Translate successful translation
- AWS Translate failure (graceful degradation)
- End-to-end workflow (fetch + translate)
- Performance validation (< 2000ms)

**Acceptance Criteria:**
- [x] Integration test for successful Dictionary API response
- [x] Integration test for Dictionary API 404
- [x] Integration test for Dictionary API timeout
- [x] Integration test for AWS Translate success
- [x] Integration test for AWS Translate failure
- [x] Integration test for end-to-end workflow
- [x] Performance validation tests
- [x] Mocked external services (or use test fixtures)
- [x] All tests passing

**Dependencies:** Task 5.5 (Property-based tests)

**Files to Create/Modify:**
- Create: `tests/integration/test_vocabulary_integration.py`

**Estimated Effort:** 2 hours

---

### Task 5.7: Checkpoint - Ensure All Tests Pass

**Objective:** Verify all tests pass and code quality is acceptable.

**Description:**
Run all tests and verify:
- All unit tests pass
- All property-based tests pass
- All integration tests pass
- Code coverage > 80%
- No linting errors
- No type checking errors

**Acceptance Criteria:**
- [x] All unit tests passing
- [x] All property-based tests passing
- [x] All integration tests passing
- [x] Code coverage > 80%
- [x] Linting passes (pylint, flake8)
- [x] Type checking passes (mypy)
- [x] No warnings or errors

**Dependencies:** Task 5.6 (Integration tests)

**Files to Create/Modify:** None

**Estimated Effort:** 1 hour

---

## Phase 6: Documentation and Deployment

### Task 6.1: Update API Documentation

**Objective:** Document new API features and usage.

**Description:**
Update documentation files:
- `API_DOCUMENTATION.md`: New response format, examples, error codes
- `API_EXAMPLES.md`: Example requests and responses
- `README.md`: Feature overview and usage

**Acceptance Criteria:**
- [x] API_DOCUMENTATION.md updated with new response format
- [x] Example requests and responses documented
- [x] Error codes and messages documented
- [x] Performance SLA documented
- [x] Backward compatibility notes included
- [x] README.md updated with feature overview

**Dependencies:** Task 4.3 (API response format)

**Files to Create/Modify:**
- Modify: `API_DOCUMENTATION.md`
- Modify: `API_EXAMPLES.md`
- Modify: `README.md`

**Estimated Effort:** 1 hour

---

### Task 6.2: Create Migration Guide (If Needed)

**Objective:** Document migration path for existing clients.

**Description:**
Create migration guide documenting:
- Backward compatibility (no changes required)
- New optional fields available
- How to use new fields (phonetic, definitions, synonyms)
- Performance improvements from caching

**Acceptance Criteria:**
- [x] Migration guide created (or documented in README)
- [x] Backward compatibility clearly stated
- [x] New features documented
- [x] Usage examples provided
- [x] Performance improvements documented

**Dependencies:** Task 6.1 (API documentation)

**Files to Create/Modify:**
- Create: `VOCABULARY_API_MIGRATION.md` (or update README)

**Estimated Effort:** 0.5 hours

---

### Task 6.3: Checkpoint - Ensure All Tests Pass and Documentation Complete

**Objective:** Final verification before deployment.

**Description:**
Verify:
- All tests pass
- Documentation complete and accurate
- Code quality acceptable
- No outstanding issues

**Acceptance Criteria:**
- [x] All tests passing
- [x] Documentation complete
- [x] Code review completed
- [x] No outstanding issues
- [x] Ready for deployment

**Dependencies:** Task 6.2 (Migration guide)

**Files to Create/Modify:** None

**Estimated Effort:** 0.5 hours

---

## Summary

This implementation plan provides a structured approach to upgrading the vocabulary API with Dictionary API integration and AWS Translate. The tasks are organized into logical phases:

1. **Infrastructure Layer** (Tasks 1.1-1.3): Foundation services (cache, retry, port)
2. **Adapter Layer** (Tasks 2.1-2.3): Dictionary API integration with caching and retry
3. **Application Layer** (Tasks 3.1-3.4): Domain entities, DTOs, use case, batch translation
4. **Interface Layer** (Tasks 4.1-4.3): Controller, mapper, API documentation
5. **Testing** (Tasks 5.1-5.6): Unit tests, property-based tests, integration tests
6. **Documentation** (Tasks 6.1-6.3): API documentation, migration guide, final checkpoint

**Key Features:**
- Clean Architecture separation of concerns
- **Context-aware phrasal verb detection with Simplemma lemmatization**
- **Support for inflected verb forms (V2, V3, V-ed, V-ing)**
- Comprehensive error handling and graceful degradation
- Performance optimization through caching and batch translation
- Backward compatibility maintained
- Extensive testing including property-based tests
- Clear logging for monitoring and debugging

**Notes:**
- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task builds on previous tasks with clear dependencies
- All tasks focus on code implementation (no deployment to production)
- Property-based tests validate universal correctness properties from design document
