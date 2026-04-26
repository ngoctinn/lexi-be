# Requirements Document: Vocabulary API Upgrade with Dictionary API + AWS Translate

## Introduction

Upgrade `/vocabulary/translate` endpoint to fetch word information from Dictionary API (https://dictionaryapi.dev/) and translate to Vietnamese using AWS Translate.

**Current:** Returns `{ word, translate_vi }`  
**New:** Returns `{ word, translate_vi, phonetic, audio_url, meanings[] }`

The upgrade maintains backward compatibility with existing clients.

---

## Glossary

- **Dictionary_API**: External service at https://dictionaryapi.dev/ that provides English word definitions, pronunciations, and examples
- **AWS_Translate**: AWS service that translates text from English to Vietnamese
- **Vocabulary**: Domain entity containing word information (word, phonetic, meanings, audio)
- **Meaning**: Part of speech with definition and example
- **Response_Time**: Time from request to response (milliseconds)

---

## API Response Structure

```json
{
  "word": "hello",
  "translate_vi": "xin chào",
  "phonetic": "həˈləʊ",
  "audio_url": "//ssl.gstatic.com/dictionary/static/sounds/20200429/hello--_gb_1.mp3",
  "meanings": [
    {
      "part_of_speech": "exclamation",
      "definition": "used as a greeting or to begin a phone conversation",
      "definition_vi": "được dùng để chào hỏi hoặc bắt đầu cuộc gọi điện thoại",
      "example": "hello there, Katie!",
      "example_vi": "xin chào Katie!"
    },
    {
      "part_of_speech": "noun",
      "definition": "an utterance of 'hello'; a greeting",
      "definition_vi": "lời chào",
      "example": "she was getting polite nods and hellos from people",
      "example_vi": "cô ấy nhận được những cái gật đầu lịch sự và lời chào từ mọi người"
    }
  ]
}
```

---

## Requirements

### Requirement 1: Fetch Word Definitions from Dictionary API

**User Story:** As a learner, I want to see word pronunciation, definitions, and examples, so I can understand how to use the word correctly.

#### Acceptance Criteria

1. WHEN a valid English word is requested via POST `/vocabulary/translate`, THE system SHALL fetch word data from Dictionary API endpoint `https://api.dictionaryapi.dev/api/v2/entries/en/{word}`

2. WHEN Dictionary API returns HTTP 200, THE system SHALL extract:
   - `word` (string)
   - `phonetic` (string) - primary phonetic from top-level field
   - `audio_url` (string) - first audio URL from `phonetics[0].audio`
   - `meanings` (array) - ALL meanings from response

3. FOR EACH meaning, THE system SHALL extract:
   - `part_of_speech` (string) - from `meanings[i].partOfSpeech`
   - `definition` (string) - FIRST definition only from `meanings[i].definitions[0].definition`
   - `example` (string, optional) - FIRST example only from `meanings[i].definitions[0].example`

4. WHEN Dictionary API returns HTTP 404 (word not found), THE system SHALL return HTTP 404 with error message "Word not found"

5. WHEN Dictionary API is unavailable or returns HTTP 5xx, THE system SHALL return HTTP 503 with error message "Dictionary service temporarily unavailable"

6. WHEN Dictionary API response exceeds 30 seconds, THE system SHALL timeout and return HTTP 503

7. THE system SHALL implement exponential backoff retry with maximum 2 retries for transient failures (HTTP 429, 5xx):
   - First retry: 1 second delay
   - Second retry: 2 seconds delay

---

### Requirement 2: Translate Definitions and Examples to Vietnamese

**User Story:** As a learner, I want definitions and examples in Vietnamese, so I can understand the meaning in my native language.

#### Acceptance Criteria

1. WHEN word data is retrieved from Dictionary API, THE system SHALL translate using AWS Translate:
   - Word → `translate_vi`
   - Each `definition` → `definition_vi`
   - Each `example` → `example_vi` (if example exists)

2. WHEN AWS Translate translation succeeds, THE system SHALL include both English and Vietnamese text in response

3. WHEN AWS Translate translation fails, THE system SHALL return empty string for `*_vi` fields and continue (graceful degradation)

4. WHEN translating multiple items, THE system SHALL batch translate them in a single AWS Translate call to optimize performance

5. THE system SHALL complete the entire workflow (fetch + translate) within 2000 milliseconds

---

### Requirement 3: Return Enriched Vocabulary Response

**User Story:** As a learner, I want to receive complete word information in a single response, so I can learn effectively.

#### Acceptance Criteria

1. WHEN POST `/vocabulary/translate` is called with a valid word, THE API SHALL return HTTP 200 with response containing:
   - `word` (string) - original English word
   - `translate_vi` (string) - Vietnamese translation
   - `phonetic` (string) - IPA notation
   - `audio_url` (string, optional) - pronunciation audio URL
   - `meanings` (array) - all meanings with translations

2. EACH meaning in `meanings` array SHALL contain:
   - `part_of_speech` (string)
   - `definition` (string) - English definition
   - `definition_vi` (string) - Vietnamese translation
   - `example` (string, optional) - English example
   - `example_vi` (string, optional) - Vietnamese translation

3. WHEN a meaning has no example, THE `example` and `example_vi` fields SHALL be empty strings

4. WHEN audio is not available, THE `audio_url` field SHALL be null or empty string

5. THE response SHALL maintain backward compatibility by including `word` and `translate_vi` at top level

---

### Requirement 4: Handle Dictionary API Errors Gracefully

**User Story:** As a system, I want to handle errors gracefully, so users receive clear error messages.

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

3. WHEN Dictionary API returns rate limit error (HTTP 429), THE system SHALL retry with exponential backoff (1s, 2s) before returning error

4. WHEN AWS Translate fails but Dictionary API succeeds, THE API SHALL return HTTP 200 with word data and empty strings for untranslated fields

5. WHEN both Dictionary API and AWS Translate fail, THE API SHALL return HTTP 503

---

### Requirement 5: Maintain Backward Compatibility

**User Story:** As an existing client, I want the API to continue working, so I don't need to update my code.

#### Acceptance Criteria

1. THE POST `/vocabulary/translate` endpoint SHALL accept the same request format:
   ```json
   {
     "word": "hello"
   }
   ```

2. THE response SHALL include `word` and `translate_vi` fields at top level with same data types

3. THE response SHALL include new fields (`phonetic`, `audio_url`, `meanings`) that existing clients can safely ignore

4. WHEN an existing client only reads `word` and `translate_vi` fields, THE API SHALL function correctly without requiring code changes

5. THE POST `/vocabulary/translate-sentence` endpoint SHALL remain unchanged

---

### Requirement 6: Implement Caching for Performance

**User Story:** As a system, I want to cache responses, so repeated requests are fast.

#### Acceptance Criteria

1. THE system SHALL implement two-tier caching:
   - In-memory cache for Lambda warm starts
   - DynamoDB fallback for persistent caching across invocations

2. THE system SHALL cache successful Dictionary API responses for 24 hours

3. THE cache key format SHALL be: `vocabulary:definition:{word_lowercase}`

4. WHEN a word is cached, THE response time SHALL be less than 500 milliseconds

5. WHEN cache storage fails, THE system SHALL continue without caching (graceful degradation)

6. THE system SHALL log cache hits and misses for monitoring

---

### Requirement 7: Performance and Response Time

**User Story:** As a learner, I want fast responses, so the learning experience is smooth.

#### Acceptance Criteria

1. THE POST `/vocabulary/translate` endpoint SHALL return response within 2000 milliseconds for 95% of requests (non-cached)

2. WHEN a word is cached, THE response time SHALL be less than 500 milliseconds

3. THE system SHALL log response times for all requests for performance monitoring

---

### Requirement 8: Error Handling and Logging

**User Story:** As an operator, I want comprehensive logging, so I can debug issues and monitor system health.

#### Acceptance Criteria

1. THE system SHALL log all Dictionary API calls with: word, response status, response time, error details (if any)

2. THE system SHALL log all translation operations with: word, translation status, error details (if any)

3. WHEN an error occurs, THE system SHALL include error code and descriptive message in response

4. THE system SHALL NOT log sensitive user data (user IDs, authentication tokens)

5. ALL errors from external services SHALL be caught and converted to appropriate HTTP status codes

---

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

