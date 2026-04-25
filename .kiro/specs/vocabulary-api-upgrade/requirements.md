# Requirements Document: Vocabulary API Upgrade with Dictionary API + AWS Translate

## Introduction

This feature upgrades the vocabulary translation endpoint to provide comprehensive word information by integrating Dictionary API (https://dictionaryapi.dev/) with AWS Translate. Currently, the system only translates words using AWS Translate. The upgrade will enrich responses with pronunciation (IPA), part of speech, contextual examples, and synonyms—all translated to Vietnamese—enabling learners to understand word usage more deeply.

The upgrade maintains backward compatibility with existing endpoints while enhancing the `/vocabulary/translate` endpoint to return richer data structures.

---

## Glossary

- **Dictionary_API**: External service at https://dictionaryapi.dev/ that provides English word definitions, pronunciations, examples, and synonyms
- **AWS_Translate**: AWS service that translates text between languages (English to Vietnamese)
- **TranslationService**: Port (abstraction) in Clean Architecture that defines translation contract
- **DictionaryService**: New port that defines contract for fetching word definitions from Dictionary API
- **TranslateVocabularyUseCase**: Use case that orchestrates vocabulary translation workflow
- **Word_Definition**: Complete word information including pronunciation, part of speech, definitions, examples, and synonyms
- **IPA_Phonetic**: International Phonetic Alphabet representation of word pronunciation
- **Part_of_Speech**: Grammatical category (noun, verb, adjective, adverb, etc.)
- **Example_Sentence**: Contextual usage of a word in a sentence
- **Synonym**: Word with similar meaning
- **Response_Time**: Time from request receipt to response transmission (measured in milliseconds)
- **Backward_Compatible**: API changes that do not break existing client implementations

---

## Requirements

### Requirement 1: Fetch Word Definitions from Dictionary API

**User Story:** As a learner, I want to see comprehensive word information (pronunciation, part of speech, examples), so that I can understand how to use the word correctly in context.

#### Acceptance Criteria

1. WHEN a valid English word is requested via POST `/vocabulary/translate`, THE DictionaryService SHALL fetch word definition data from Dictionary API endpoint `https://dictionaryapi.dev/api/v2/entries/en/{word}`

2. WHEN Dictionary API returns a successful response (HTTP 200), THE DictionaryService SHALL extract and return the following data:
   - Word phonetic (IPA notation from first meaning)
   - All parts of speech (noun, verb, adjective, etc., maximum 3)
   - Example sentences for each part of speech (maximum 1 per part of speech)
   - Synonyms (if available, maximum 5 total)

3. WHEN Dictionary API returns HTTP 404 (word not found), THE DictionaryService SHALL return a structured error indicating the word does not exist in the dictionary

4. WHEN Dictionary API is unavailable or returns HTTP 5xx, THE DictionaryService SHALL return a structured error indicating the external service is temporarily unavailable

5. WHEN Dictionary API response exceeds 30 seconds, THE DictionaryService SHALL timeout and return a structured error

6. THE DictionaryService SHALL implement exponential backoff retry logic with maximum 2 retries for transient failures (HTTP 429, 5xx):
   - First retry: 1 second delay
   - Second retry: 2 seconds delay

---

### Requirement 2: Translate Word and Examples to Vietnamese

**User Story:** As a learner, I want word definitions and examples translated to Vietnamese, so that I can understand the meaning and usage in my native language.

#### Acceptance Criteria

1. WHEN word definition data is retrieved from Dictionary API, THE TranslateVocabularyUseCase SHALL translate the following to Vietnamese using AWS_Translate:
   - Primary word definition (first definition for each part of speech)
   - Example sentences (maximum 1 example per part of speech, up to 3 examples total across all parts of speech)
   - Synonyms (all available synonyms, maximum 5 total)

2. WHEN AWS_Translate translation succeeds, THE TranslateVocabularyUseCase SHALL preserve the original English text alongside Vietnamese translation

3. WHEN AWS_Translate translation fails, THE TranslateVocabularyUseCase SHALL return the original English text and log the error without failing the entire request

4. WHEN translating multiple items (examples, synonyms), THE TranslateVocabularyUseCase SHALL batch translate them in a single AWS_Translate call to optimize performance

5. THE TranslateVocabularyUseCase SHALL complete the entire translation workflow (fetch + translate) within 2000 milliseconds

---

### Requirement 3: Return Enriched Vocabulary Response

**User Story:** As a learner, I want to receive complete word information in a single response, so that I can access pronunciation, definitions, examples, and synonyms without additional requests.

#### Acceptance Criteria

1. WHEN POST `/vocabulary/translate` is called with a valid word, THE API SHALL return HTTP 200 with response containing:
   - Original word (English)
   - IPA phonetic notation (from first part of speech)
   - Array of definitions (one per part of speech, maximum 3)
   - Synonyms (English and Vietnamese, maximum 5)
   - Translation of the word (Vietnamese)

2. THE response structure SHALL follow this format:
   ```json
   {
     "word": "hello",
     "phonetic": "/həˈloʊ/",
     "translation_vi": "xin chào",
     "definitions": [
       {
         "part_of_speech": "interjection",
         "definition_en": "used as a greeting or to begin a conversation",
         "definition_vi": "được dùng để chào hỏi hoặc bắt đầu cuộc trò chuyện",
         "example_en": "Hello, how are you?",
         "example_vi": "Xin chào, bạn khỏe không?"
       }
     ],
     "synonyms": [
       {"en": "hi", "vi": "chào"},
       {"en": "greetings", "vi": "lời chào"}
     ]
   }
   ```

3. WHEN a word has multiple parts of speech, THE API SHALL return all parts of speech (maximum 3) in the definitions array, ordered by frequency in Dictionary API response

4. WHEN a word has no examples available for a definition, THE API SHALL return empty strings for example_en and example_vi fields

5. WHEN a word has no synonyms available, THE API SHALL return an empty array for synonyms field

6. THE response SHALL maintain backward compatibility by including word and translation_vi fields at top level

---

### Requirement 4: Handle Dictionary API Errors Gracefully

**User Story:** As a system, I want to handle missing or unavailable words gracefully, so that users receive clear error messages instead of system failures.

#### Acceptance Criteria

1. WHEN Dictionary API returns HTTP 404 (word not found), THE API SHALL return HTTP 404 with error response:
   ```json
   {
     "success": false,
     "message": "Word not found in dictionary",
     "error": "WORD_NOT_FOUND"
   }
   ```

2. WHEN Dictionary API is unavailable (HTTP 5xx or timeout), THE API SHALL return HTTP 503 with error response:
   ```json
   {
     "success": false,
     "message": "Dictionary service temporarily unavailable",
     "error": "DICTIONARY_SERVICE_ERROR"
   }
   ```

3. WHEN Dictionary API returns rate limit error (HTTP 429), THE DictionaryService SHALL retry with exponential backoff (1s, 2s) before returning error

4. WHEN AWS_Translate fails but Dictionary API succeeds, THE API SHALL return HTTP 200 with word data and original English text for untranslated fields

5. WHEN both Dictionary API and AWS_Translate fail, THE API SHALL return HTTP 503 with error message indicating service unavailability

---

### Requirement 5: Maintain Backward Compatibility

**User Story:** As an existing client, I want the API to continue working with my current implementation, so that I don't need to update my code immediately.

#### Acceptance Criteria

1. THE POST `/vocabulary/translate` endpoint SHALL accept the same request format as before:
   ```json
   {
     "word": "hello"
   }
   ```

2. THE response SHALL include all previous fields (word, translation_vi) with same data types and values at top level

3. THE response SHALL include new fields (phonetic, definitions, synonyms) that existing clients can safely ignore if they only use word and translation_vi

4. WHEN an existing client only reads word and translation_vi fields, THE API SHALL function correctly without requiring code changes

5. THE POST `/vocabulary/translate-sentence` endpoint SHALL remain unchanged in behavior and response format

6. THE response structure SHALL be designed such that old clients reading only word and translation_vi fields will continue to work without modification

---

### Requirement 6: Implement DictionaryService Port and Adapter

**User Story:** As a developer, I want a clean abstraction for Dictionary API integration, so that the system can be tested independently and adapted to different dictionary sources.

#### Acceptance Criteria

1. THE DictionaryService port SHALL define abstract method `get_word_definition(word: str) -> WordDefinition` that returns complete word information

2. THE DictionaryServiceAdapter SHALL implement DictionaryService by calling Dictionary API with proper error handling

3. THE DictionaryServiceAdapter SHALL cache successful responses for 24 hours using in-memory cache with DynamoDB fallback to reduce API calls and improve performance

4. THE DictionaryServiceAdapter SHALL implement timeout of 30 seconds for Dictionary API calls

5. THE DictionaryServiceAdapter SHALL implement exponential backoff retry logic with maximum 2 retries for transient failures (HTTP 429, 5xx):
   - First retry: 1 second delay
   - Second retry: 2 seconds delay

6. THE DictionaryServiceAdapter SHALL log all API calls (word, response status, response time) for monitoring and debugging

7. THE DictionaryServiceAdapter SHALL be injectable into TranslateVocabularyUseCase via constructor dependency injection

---

### Requirement 7: Update TranslateVocabularyUseCase

**User Story:** As a system, I want the vocabulary translation workflow to orchestrate both Dictionary API and AWS Translate, so that learners receive complete word information.

#### Acceptance Criteria

1. THE TranslateVocabularyUseCase SHALL accept TranslateVocabularyCommand with word and optional sentence fields

2. WHEN TranslateVocabularyUseCase.execute() is called, THE use case SHALL:
   - Call DictionaryService.get_word_definition(word)
   - Translate word definition and examples using TranslationService
   - Return TranslateVocabularyResponse with complete data

3. WHEN DictionaryService returns error, THE use case SHALL return Result.failure() with appropriate error

4. WHEN TranslationService returns error, THE use case SHALL return Result.success() with English text for untranslated fields

5. THE use case SHALL NOT modify existing TranslateSentenceUseCase behavior

---

### Requirement 8: Update Vocabulary DTOs

**User Story:** As a developer, I want clear data structures for vocabulary requests and responses, so that the API contract is well-defined and validated.

#### Acceptance Criteria

1. THE TranslateVocabularyResponse DTO SHALL include all fields defined in Requirement 3 with appropriate types and validation

2. THE TranslateVocabularyResponse DTO SHALL validate that word field is non-empty string

3. THE TranslateVocabularyResponse DTO SHALL allow optional fields (phonetic, definition_vi, example_en, example_vi, synonyms) to be empty or null

4. THE Synonym DTO SHALL contain two fields: `en` (English synonym) and `vi` (Vietnamese translation)

5. THE TranslateVocabularyCommand DTO SHALL remain backward compatible with existing requests

---

### Requirement 9: Performance and Response Time

**User Story:** As a learner, I want fast responses when translating words, so that the learning experience is smooth and responsive.

#### Acceptance Criteria

1. THE POST `/vocabulary/translate` endpoint SHALL return response within 2000 milliseconds for 95% of requests

2. WHEN a word definition is cached, THE response time SHALL be less than 500 milliseconds

3. WHEN a word definition is not cached, THE response time SHALL be less than 2000 milliseconds including Dictionary API and AWS_Translate calls

4. THE DictionaryServiceAdapter SHALL implement caching with 24-hour TTL to improve response times for repeated requests

5. THE system SHALL log response times for all vocabulary translation requests for performance monitoring

---

### Requirement 10: Error Handling and Logging

**User Story:** As an operator, I want comprehensive logging and error tracking, so that I can debug issues and monitor system health.

#### Acceptance Criteria

1. THE DictionaryService SHALL log all API calls with: word, response status, response time, error details (if any)

2. THE TranslateVocabularyUseCase SHALL log all translation operations with: word, source (Dictionary API), translation status, error details (if any)

3. WHEN an error occurs, THE system SHALL include error code and descriptive message in response

4. THE system SHALL NOT log sensitive user data (user IDs, authentication tokens)

5. ALL errors from external services (Dictionary API, AWS_Translate) SHALL be caught and converted to appropriate HTTP status codes

---

### Requirement 11: Support Phrasal Verbs and Multi-Word Expressions

**User Story:** As a learner, I want to translate phrasal verbs (e.g., "get off", "look up") as complete expressions, not individual words, so that I understand their idiomatic meanings correctly.

#### Acceptance Criteria

1. WHEN a user requests translation of a phrasal verb (e.g., "get off", "look up", "run into"), THE DictionaryService SHALL treat it as a single unit and query Dictionary API with the complete phrase

2. WHEN Dictionary API returns a successful response for a phrasal verb, THE response SHALL include:
   - Phrasal verb definition (idiomatic meaning)
   - Examples showing phrasal verb usage
   - Synonyms (if available)

3. WHEN a phrasal verb is not found in Dictionary API, THE system SHALL attempt to translate it using AWS_Translate as a fallback

4. THE system SHALL NOT split phrasal verbs into individual words (e.g., "get off" should not be translated as "get" + "off")

5. WHEN translating example sentences containing phrasal verbs, THE system SHALL preserve the phrasal verb as a unit during translation

6. THE system SHALL support common phrasal verbs (minimum 100+ phrasal verbs from Dictionary API)

---

### Requirement 12: Optional - Flashcard Enrichment

**User Story:** As a learner, I want flashcards to include pronunciation and examples from Dictionary API, so that I can learn words more effectively.

#### Acceptance Criteria

1. WHEN creating a flashcard via POST `/flashcards`, IF the word exists in Dictionary API, THE system MAY enrich the flashcard with:
   - Phonetic pronunciation (IPA)
   - Example sentence (English)
   - Part of speech

2. WHEN enriching a flashcard, THE system SHALL use cached Dictionary API data if available (no additional API call)

3. WHEN Dictionary API enrichment fails, THE system SHALL create the flashcard with user-provided data only (graceful degradation)

4. THIS requirement is OPTIONAL and SHALL NOT block flashcard creation if Dictionary API is unavailable

5. WHEN a flashcard is enriched, THE system SHALL store enrichment metadata for future reference

---

## Acceptance Criteria Testing Strategy

### Property-Based Testing Candidates

1. **Round-Trip Property (Serialization)**: For any valid word definition, parsing Dictionary API response and serializing to DTO should preserve all data
   - Test: `parse(serialize(word_definition)) == word_definition`

2. **Idempotence Property**: Calling translate on the same word multiple times should return identical results (due to caching)
   - Test: `translate(word) == translate(word)` for cached results

3. **Invariant Property**: Response always contains original word and translation_vi fields
   - Test: `response.word == request.word` and `response.translation_vi != ""`

### Integration Testing Candidates

1. **Dictionary API Not Found**: Test with non-existent word (1-2 examples)
2. **Dictionary API Timeout**: Test with mocked timeout (1-2 examples)
3. **AWS Translate Failure**: Test with mocked translation failure (1-2 examples)
4. **Successful End-to-End**: Test with real Dictionary API and mocked AWS Translate (1-2 examples)

### Unit Testing Candidates

1. **DTO Validation**: Invalid word formats, empty strings, special characters
2. **Error Handling**: Proper error codes and messages for each failure scenario
3. **Caching Logic**: Cache hit/miss, TTL expiration
4. **Retry Logic**: Exponential backoff for transient failures

---

## Implementation Notes

- **Clean Architecture**: Maintain separation of concerns with DictionaryService as port, adapter in infrastructure layer
- **Dependency Injection**: Use existing service factory pattern for injecting DictionaryService and TranslationService
- **Error Handling**: Use existing Result<T, E> pattern for error propagation
- **Logging**: Use existing logger configuration with appropriate log levels
- **Testing**: Follow existing test patterns in the codebase
- **Backward Compatibility**: Ensure existing clients continue to work without changes

