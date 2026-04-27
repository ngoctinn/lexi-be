# Implementation Plan: Flashcard System Upgrade

## Overview

This implementation plan breaks down the flashcard system upgrade into discrete, testable coding tasks. The upgrade implements the SM-2 spaced repetition algorithm, adds missing CRUD operations, improves performance with GSI-based queries, and provides analytics capabilities. The implementation follows a 6-phase approach that builds incrementally, with each phase validated before moving forward.

## Tasks

- [x] 1. Implement SM-2 SRS Engine
  - Create `src/domain/services/srs_engine.py` with SM-2 algorithm implementation
  - Implement `calculate_next_interval()` method following SuperMemo specification
  - Implement `map_rating_to_quality()` for string-to-numeric rating conversion
  - Implement `update_ease_factor()` with minimum 1.3 constraint
  - _Requirements: 1.1, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9_

- [x] 1.1 Write property test for SM-2 algorithm correctness
  - **Property 1: SM-2 Algorithm Correctness**
  - **Validates: Requirements 1.1, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8**
  - Test with 100+ random combinations of quality (0-5), repetition_count, ease_factor (1.3-2.5), previous_interval
  - Verify ease_factor minimum constraint (1.3)
  - Verify interval calculations match SM-2 specification

- [x] 1.2 Write property test for rating mapping consistency
  - **Property 3: Rating Mapping Consistency**
  - **Validates: Requirements 1.9**
  - Test all valid string ratings map to correct quality values
  - Test invalid ratings raise ValueError

- [x] 2. Enhance FlashCard entity with SM-2 support
  - [x] 2.1 Add SM-2 fields to FlashCard entity
    - Add `ease_factor: float = 2.5` field
    - Add `repetition_count: int = 0` field
    - Update `__post_init__()` validation for new fields
    - _Requirements: 1.2, 2.1, 2.2, 2.3_

  - [x] 2.2 Implement `apply_sm2_review()` method
    - Replace existing `apply_review()` with SM-2 algorithm integration
    - Call `SRSEngine.calculate_next_interval()` with current state
    - Update `ease_factor`, `repetition_count`, `interval_days`, `next_review_at`
    - Increment `review_count` for statistics
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9_

  - [x] 2.3 Write property test for flashcard initialization
    - **Property 2: Flashcard Initialization**
    - **Validates: Requirements 1.2**
    - Test new flashcards initialize with ease_factor=2.5 and repetition_count=0

  - [x] 2.4 Write unit tests for apply_sm2_review()
    - Test "forgot" rating resets repetition_count and sets interval to 1
    - Test "hard" rating with quality=3
    - Test "good" rating with quality=4
    - Test "easy" rating with quality=5
    - Test ease_factor updates correctly
    - _Requirements: 1.3, 1.4, 1.5, 1.6, 1.7, 1.8_

- [x] 3. Checkpoint - Verify SM-2 algorithm integration
  - Run all property tests and unit tests
  - Ensure all tests pass, ask the user if questions arise

- [x] 4. Enhance DynamoDB schema with GSI3
  - [x] 4.1 Update DynamoDB table definition
    - Add GSI3 definition to `config/database.yaml`
    - Set GSI3PK as HASH key (user_id)
    - Set GSI3SK as RANGE key (word_lowercase)
    - Configure projection to include: flashcard_id, word, translation_vi, ease_factor, repetition_count
    - _Requirements: 3.1, 3.2_

  - [x] 4.2 Update repository to populate GSI3 fields
    - Modify `save()` method in `src/infrastructure/repositories/dynamodb_flashcard_repository.py`
    - Add `GSI3PK` = user_id to item
    - Add `GSI3SK` = word.lower() to item
    - Add `ease_factor` and `repetition_count` to item structure
    - _Requirements: 2.4, 2.5, 3.1, 3.4_

  - [x] 4.3 Write property test for persistence round-trip
    - **Property 4: Persistence Round-Trip**
    - **Validates: Requirements 2.4, 2.5**
    - Test flashcards with ease_factor and repetition_count persist and retrieve correctly
    - Generate random flashcards with various SRS states

- [x] 5. Implement efficient word lookup
  - [x] 5.1 Replace SCAN with GSI3 query
    - Update `get_by_user_and_word()` method to use GSI3
    - Query with GSI3PK=user_id and GSI3SK=word.lower()
    - Remove SCAN-based implementation
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x] 5.2 Write property test for word normalization
    - **Property 5: Word Normalization Consistency**
    - **Validates: Requirements 3.4**
    - Test mixed-case words produce consistent results
    - Test "Example", "EXAMPLE", "example" all find the same flashcard

  - [x] 5.3 Write performance test for word lookup
    - Test query completes in under 100ms
    - Use DynamoDB Local for integration testing
    - _Requirements: 3.3_

- [x] 6. Checkpoint - Verify data layer enhancements
  - Run all tests including property tests and performance tests
  - Ensure all tests pass, ask the user if questions arise

- [x] 7. Implement data migration script
  - [x] 7.1 Create migration script
    - Create `scripts/migrate_flashcards.py`
    - Implement batch processing (25 items per batch)
    - Add `ease_factor=2.5` to all existing flashcards
    - Derive `repetition_count` from `review_count` using `min(review_count, 3)`
    - Add GSI3PK and GSI3SK fields
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [x] 7.2 Add migration validation
    - Verify all flashcards have ease_factor and repetition_count
    - Verify GSI3 entries exist for all flashcards
    - Log progress and errors to CloudWatch
    - Make script idempotent (safe to run multiple times)
    - _Requirements: 10.6, 10.7_

  - [x] 7.3 Write unit tests for migration logic
    - Test ease_factor initialization
    - Test repetition_count derivation
    - Test GSI3 field creation
    - Test batch processing
    - _Requirements: 10.1, 10.2, 10.3, 10.5_

- [x] 8. Implement UPDATE flashcard operation
  - [x] 8.1 Create UpdateFlashcardUseCase
    - Create `src/application/use_cases/update_flashcard_use_case.py`
    - Implement authorization check (verify user owns flashcard)
    - Implement partial update logic (only update provided fields)
    - Preserve SRS data (ease_factor, repetition_count, interval_days, next_review_at)
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [x] 8.2 Add repository method for update
    - Add `update_content()` method to FlashCardRepository interface
    - Implement in DynamoDBFlashCardRepository using UpdateExpression
    - Support updating: translation_vi, phonetic, audio_url, example_sentence
    - _Requirements: 4.4_

  - [x] 8.3 Create PATCH /flashcards/{id} handler
    - Create `src/infrastructure/handlers/flashcard/update_flashcard_handler.py`
    - Parse request body for optional fields
    - Extract user_id from JWT token
    - Call UpdateFlashcardUseCase
    - Return 200 with updated flashcard or appropriate error codes (403, 404)
    - _Requirements: 4.1, 4.5, 4.6_

  - [x] 8.4 Write property test for partial update preservation
    - **Property 6: Partial Update Preservation**
    - **Validates: Requirements 4.4**
    - Test updating subsets of fields preserves other data
    - Test SRS state is never modified by content updates

  - [x] 8.5 Write unit tests for update operation
    - Test successful update with valid data
    - Test authorization failure (403)
    - Test not found error (404)
    - Test partial updates (only translation_vi, only example_sentence, etc.)
    - _Requirements: 4.1, 4.2, 4.3, 4.5, 4.6_

- [x] 9. Implement DELETE flashcard operation
  - [x] 9.1 Create DeleteFlashcardUseCase
    - Create `src/application/use_cases/delete_flashcard_use_case.py`
    - Implement authorization check (verify user owns flashcard)
    - Call repository delete method
    - _Requirements: 5.1, 5.2_

  - [x] 9.2 Add repository method for delete
    - Add `delete()` method to FlashCardRepository interface
    - Implement in DynamoDBFlashCardRepository using DeleteItem
    - Return boolean indicating success
    - _Requirements: 5.3_

  - [x] 9.3 Create DELETE /flashcards/{id} handler
    - Create `src/infrastructure/handlers/flashcard/delete_flashcard_handler.py`
    - Extract user_id from JWT token
    - Call DeleteFlashcardUseCase
    - Return 204 on success or appropriate error codes (403, 404)
    - _Requirements: 5.1, 5.4, 5.5_

  - [x] 9.4 Write unit tests for delete operation
    - Test successful deletion
    - Test authorization failure (403)
    - Test not found error (404)
    - Test idempotency (deleting non-existent flashcard)
    - _Requirements: 5.1, 5.2, 5.4, 5.5_

- [x] 10. Checkpoint - Verify CRUD operations
  - Run all tests for UPDATE and DELETE operations
  - Test authorization and error handling
  - Ensure all tests pass, ask the user if questions arise

- [x] 11. Implement bulk export functionality
  - [x] 11.1 Create ExportFlashcardsUseCase
    - Create `src/application/use_cases/export_flashcards_use_case.py`
    - Implement cursor-based pagination (limit 1000 per page)
    - Call repository export method
    - _Requirements: 6.1, 6.2, 6.4_

  - [x] 11.2 Add repository method for export
    - Add `export_user_flashcards()` method to FlashCardRepository interface
    - Implement in DynamoDBFlashCardRepository using Query with pagination
    - Return tuple of (flashcard_list, next_cursor)
    - Include all fields in export: word, translation_vi, phonetic, audio_url, example_sentence, ease_factor, repetition_count, interval_days, review_count, last_reviewed_at, next_review_at
    - _Requirements: 6.2, 6.3, 6.4_

  - [x] 11.3 Create GET /flashcards/export handler
    - Create `src/infrastructure/handlers/flashcard/export_flashcards_handler.py`
    - Extract user_id from JWT token
    - Parse optional cursor query parameter
    - Call ExportFlashcardsUseCase
    - Return JSON with flashcards array and next_cursor
    - _Requirements: 6.1, 6.2, 6.4, 6.5_

  - [x] 11.4 Write property test for export completeness
    - **Property 7: Export Completeness**
    - **Validates: Requirements 6.3**
    - Test all required fields are included in export
    - Generate random flashcards and verify export contains all fields

  - [x] 11.5 Write unit tests for export operation
    - Test export with no flashcards (empty array)
    - Test export with pagination (cursor handling)
    - Test export includes all required fields
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 12. Implement bulk import functionality
  - [x] 12.1 Create ImportFlashcardsUseCase
    - Create `src/application/use_cases/import_flashcards_use_case.py`
    - Implement JSON schema validation
    - Implement duplicate word detection (skip existing words)
    - Implement batch processing (limit 1000 per request)
    - Return ImportResult with counts (imported, skipped, failed) and errors
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.6_

  - [x] 12.2 Add repository method for import
    - Add `import_flashcards()` method to FlashCardRepository interface
    - Implement in DynamoDBFlashCardRepository using BatchWriteItem
    - Handle duplicate detection via get_by_user_and_word()
    - _Requirements: 7.1, 7.3_

  - [x] 12.3 Create POST /flashcards/import handler
    - Create `src/infrastructure/handlers/flashcard/import_flashcards_handler.py`
    - Extract user_id from JWT token
    - Parse and validate JSON request body
    - Call ImportFlashcardsUseCase
    - Return 200 with import summary or 400 for validation errors
    - _Requirements: 7.1, 7.2, 7.5, 7.6_

  - [x] 12.4 Write property test for import duplicate handling
    - **Property 8: Import Duplicate Handling**
    - **Validates: Requirements 7.3**
    - Test import with duplicate words skips existing and continues
    - Generate random flashcard sets with intentional duplicates

  - [x] 12.5 Write property test for export-import round-trip
    - **Property 12: Export-Import Round-Trip**
    - **Validates: Requirements 13.1, 13.4**
    - Test exporting then importing produces equivalent flashcards
    - Verify SRS state preservation (ease_factor, repetition_count, interval_days)
    - Allow 1 second tolerance for next_review_at timestamps

  - [x] 12.6 Write unit tests for import operation
    - Test successful import with valid data
    - Test JSON schema validation errors (400)
    - Test duplicate word handling (skip and continue)
    - Test import limit enforcement (1000 max)
    - Test import summary accuracy
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [x] 13. Checkpoint - Verify bulk operations
  - Run all tests for export and import
  - Test round-trip property (export then import)
  - Ensure all tests pass, ask the user if questions arise

- [x] 14. Implement learning statistics
  - [x] 14.1 Create GetStatisticsUseCase
    - Create `src/application/use_cases/get_statistics_use_case.py`
    - Calculate total flashcard count
    - Calculate due today count (next_review_at <= now)
    - Calculate reviewed last 7 days count
    - Calculate maturity counts (new: repetition_count=0, learning: 1-2, mature: >=3)
    - Calculate average ease_factor
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

  - [x] 14.2 Add repository method for statistics
    - Add `get_user_statistics()` method to FlashCardRepository interface
    - Implement in DynamoDBFlashCardRepository using Query and aggregation
    - Optimize for sub-200ms response time
    - _Requirements: 8.1, 8.7_

  - [x] 14.3 Create GET /flashcards/statistics handler
    - Create `src/infrastructure/handlers/flashcard/get_statistics_handler.py`
    - Extract user_id from JWT token
    - Call GetStatisticsUseCase
    - Return JSON with statistics object
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

  - [x] 14.4 Write unit tests for statistics calculation
    - Test with no flashcards (all counts zero)
    - Test with mixed maturity levels
    - Test due today calculation
    - Test reviewed last 7 days calculation
    - Test average ease_factor calculation
    - _Requirements: 8.2, 8.3, 8.4, 8.5, 8.6_

  - [x] 14.5 Write performance test for statistics
    - Test statistics endpoint responds in under 200ms
    - Test with 10,000 flashcards
    - _Requirements: 8.7_

- [x] 15. Implement search and filter functionality
  - [x] 15.1 Create SearchFlashcardsUseCase
    - Create `src/application/use_cases/search_flashcards_use_case.py`
    - Implement word_prefix filter (case-insensitive)
    - Implement min_interval and max_interval filters
    - Implement maturity_level filter (new/learning/mature)
    - Implement cursor-based pagination (default limit 50)
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

  - [x] 15.2 Add repository method for search
    - Add `search_flashcards()` method to FlashCardRepository interface
    - Implement in DynamoDBFlashCardRepository using Query with FilterExpression
    - Support all filter combinations
    - Return SearchResult with flashcards and next_cursor
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

  - [x] 15.3 Create GET /flashcards handler (search endpoint)
    - Update existing `src/infrastructure/handlers/flashcard/list_flashcards_handler.py`
    - Parse query parameters: word_prefix, min_interval, max_interval, maturity_level, cursor, limit
    - Call SearchFlashcardsUseCase
    - Return JSON with flashcards array, next_cursor, and total_count
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

  - [x] 15.4 Write unit tests for search functionality
    - Test word_prefix filter (case-insensitive)
    - Test min_interval and max_interval filters
    - Test maturity_level filter
    - Test pagination with cursor
    - Test no filters (return all flashcards)
    - Test filter combinations
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

- [x] 16. Implement improved validation
  - [x] 16.1 Update FlashCard entity validation
    - Update `__post_init__()` to accept multi-word expressions (spaces, hyphens, apostrophes)
    - Add validation for maximum word length (100 characters)
    - Add validation to reject whitespace-only words
    - Add automatic whitespace trimming
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_

  - [x] 16.2 Write property test for multi-word validation
    - **Property 9: Multi-Word Validation**
    - **Validates: Requirements 11.1, 11.2, 11.3**
    - Test words with spaces, hyphens, apostrophes are accepted
    - Generate random multi-word expressions

  - [x] 16.3 Write property test for whitespace rejection
    - **Property 10: Whitespace Rejection**
    - **Validates: Requirements 11.5**
    - Test strings with only whitespace are rejected
    - Generate random whitespace-only strings

  - [x] 16.4 Write property test for whitespace trimming
    - **Property 11: Whitespace Trimming**
    - **Validates: Requirements 11.6**
    - Test words with leading/trailing whitespace are trimmed
    - Generate random words with various whitespace patterns

  - [x] 16.5 Write unit tests for validation rules
    - Test multi-word expressions (phrasal verbs, idioms)
    - Test maximum length enforcement (100 characters)
    - Test whitespace-only rejection
    - Test whitespace trimming
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_

- [x] 17. Update SAM template with new endpoints
  - [x] 17.1 Add Lambda functions for new endpoints
    - Add UpdateFlashcardFunction with PATCH /flashcards/{id} event
    - Add DeleteFlashcardFunction with DELETE /flashcards/{id} event
    - Add ExportFlashcardsFunction with GET /flashcards/export event
    - Add ImportFlashcardsFunction with POST /flashcards/import event
    - Add GetStatisticsFunction with GET /flashcards/statistics event
    - Configure environment variables (LEXI_TABLE_NAME)
    - Configure DynamoDB policies (read/write as appropriate)
    - _Requirements: 4.1, 5.1, 6.1, 7.1, 8.1, 9.1_

  - [x] 17.2 Update existing ReviewFlashcardFunction
    - Update handler to use new `apply_sm2_review()` method
    - Ensure backward compatibility with existing API contract
    - _Requirements: 1.1, 1.2_

- [x] 18. Checkpoint - Verify all features integrated
  - Run full test suite (unit tests, property tests, integration tests)
  - Test all API endpoints manually or with integration tests
  - Verify performance requirements (review <100ms, list due <150ms, create <200ms, statistics <200ms)
  - Ensure all tests pass, ask the user if questions arise

- [ ] 19. Add comprehensive error handling
  - [ ] 19.1 Implement domain-level error handling
    - Add validation errors for FlashCard entity
    - Add validation errors for SRSEngine inputs
    - Ensure all ValueError exceptions have clear messages
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_

  - [ ] 19.2 Implement application-level error handling
    - Add authorization errors (403) for all use cases
    - Add not found errors (404) for all use cases
    - Add conflict errors (409) for duplicate words
    - Add validation errors (400) for invalid inputs
    - _Requirements: 4.5, 4.6, 5.4, 5.5, 7.5_

  - [ ] 19.3 Implement infrastructure-level error handling
    - Add error response formatting in all handlers
    - Add DynamoDB error handling (throttling, service errors)
    - Add Lambda timeout handling
    - Log all errors to CloudWatch
    - _Requirements: 10.6_

  - [ ] 19.4 Write unit tests for error scenarios
    - Test validation errors return 400 with details
    - Test authorization errors return 403
    - Test not found errors return 404
    - Test conflict errors return 409
    - Test system errors return 500

- [ ] 20. Final checkpoint and integration verification
  - Run complete test suite (all unit tests, property tests, integration tests)
  - Verify all 13 requirements are covered by implementation
  - Verify all 12 correctness properties are tested
  - Test end-to-end workflows (create → review → update → export → import → delete)
  - Verify performance requirements met
  - Ensure all tests pass, ask the user if questions arise

## Notes

- Tasks marked with `*` are optional property-based and unit tests that can be skipped for faster MVP delivery
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties using Hypothesis library
- Unit tests validate specific examples and edge cases
- The implementation uses Python 3.12 as specified in the existing codebase
- All code follows Clean Architecture principles with clear separation of concerns
- Migration script (task 7) should be run before deploying new Lambda functions to production
- Performance requirements: review <100ms, list due <150ms, create <200ms, statistics <200ms (95th percentile)
