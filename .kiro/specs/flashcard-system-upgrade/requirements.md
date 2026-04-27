# Requirements Document

## Introduction

This document specifies requirements for upgrading the flashcard system to implement a correct Spaced Repetition System (SRS) algorithm, improve data access performance, add missing CRUD operations, and provide learning progress tracking. The current system has critical algorithmic flaws, performance issues, and missing business functionality that prevent effective vocabulary learning.

## Glossary

- **Flashcard_System**: The vocabulary learning subsystem that manages flashcards and spaced repetition scheduling
- **SRS_Engine**: The component responsible for calculating review intervals using the SM-2 algorithm
- **Flashcard**: A vocabulary learning card containing a word, translation, phonetic, audio URL, and example sentence
- **Ease_Factor**: A value between 1.3 and 2.5 that represents card difficulty in the SM-2 algorithm
- **Repetition_Count**: The number of consecutive successful reviews for a flashcard
- **Review_Interval**: The number of days until the next review is due
- **Quality_Rating**: A user's assessment of recall difficulty, mapped from string ratings (forgot/hard/good/easy) to numeric values (0-5)
- **Repository**: The data access layer that queries and persists flashcards in DynamoDB
- **GSI**: Global Secondary Index in DynamoDB used for efficient querying
- **Migration_Script**: A utility that transforms existing flashcard data to the new schema

## Requirements

### Requirement 1: SM-2 Algorithm Implementation

**User Story:** As a language learner, I want the system to use a proven spaced repetition algorithm, so that my review intervals are scientifically optimized for long-term retention.

#### Acceptance Criteria

1. THE SRS_Engine SHALL implement the SM-2 algorithm as specified in the SuperMemo documentation
2. WHEN a flashcard is created, THE SRS_Engine SHALL initialize ease_factor to 2.5 and repetition_count to 0
3. WHEN a user reviews a flashcard with quality < 3, THE SRS_Engine SHALL reset repetition_count to 0 and set interval to 1 day
4. WHEN a user reviews a flashcard with quality >= 3 AND repetition_count is 0, THE SRS_Engine SHALL set interval to 1 day and increment repetition_count
5. WHEN a user reviews a flashcard with quality >= 3 AND repetition_count is 1, THE SRS_Engine SHALL set interval to 6 days and increment repetition_count
6. WHEN a user reviews a flashcard with quality >= 3 AND repetition_count >= 2, THE SRS_Engine SHALL calculate interval as previous_interval * ease_factor and increment repetition_count
7. WHEN a user reviews a flashcard, THE SRS_Engine SHALL update ease_factor using the formula: EF + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
8. THE SRS_Engine SHALL enforce a minimum ease_factor of 1.3
9. WHEN a user provides a string rating, THE SRS_Engine SHALL map "forgot" to quality 0, "hard" to quality 3, "good" to quality 4, and "easy" to quality 5

### Requirement 2: Data Model Enhancement

**User Story:** As a developer, I want the flashcard data model to support the SM-2 algorithm, so that all required parameters are persisted correctly.

#### Acceptance Criteria

1. THE Flashcard SHALL include an ease_factor field with default value 2.5
2. THE Flashcard SHALL include a repetition_count field with default value 0
3. THE Flashcard SHALL maintain backward compatibility with existing difficulty field
4. WHEN a flashcard is persisted, THE Repository SHALL store ease_factor and repetition_count in DynamoDB
5. WHEN a flashcard is retrieved, THE Repository SHALL load ease_factor and repetition_count from DynamoDB

### Requirement 3: Efficient Word Lookup

**User Story:** As a user, I want duplicate word detection to be fast, so that I can create flashcards without delays.

#### Acceptance Criteria

1. THE Repository SHALL use a GSI to query flashcards by user_id and word
2. THE Repository SHALL NOT use SCAN operations for get_by_user_and_word queries
3. WHEN querying by user_id and word, THE Repository SHALL return results in under 100ms for tables with up to 100,000 flashcards
4. THE Repository SHALL normalize word values to lowercase before querying

### Requirement 4: Update Flashcard Content

**User Story:** As a user, I want to edit my flashcard translations and examples, so that I can correct mistakes or improve clarity.

#### Acceptance Criteria

1. THE Flashcard_System SHALL provide an update endpoint that accepts flashcard_id, user_id, and optional fields (translation_vi, phonetic, audio_url, example_sentence)
2. WHEN a user updates a flashcard, THE Flashcard_System SHALL verify the user owns the flashcard
3. WHEN a user updates a flashcard, THE Flashcard_System SHALL preserve SRS data (ease_factor, repetition_count, interval_days, next_review_at)
4. WHEN a user updates a flashcard, THE Repository SHALL update only the provided fields
5. IF a flashcard does not exist, THEN THE Flashcard_System SHALL return a 404 error
6. IF a user attempts to update another user's flashcard, THEN THE Flashcard_System SHALL return a 403 error

### Requirement 5: Delete Flashcard

**User Story:** As a user, I want to delete flashcards I no longer need, so that my review queue stays relevant.

#### Acceptance Criteria

1. THE Flashcard_System SHALL provide a delete endpoint that accepts flashcard_id and user_id
2. WHEN a user deletes a flashcard, THE Flashcard_System SHALL verify the user owns the flashcard
3. WHEN a user deletes a flashcard, THE Repository SHALL remove the flashcard from DynamoDB
4. IF a flashcard does not exist, THEN THE Flashcard_System SHALL return a 404 error
5. IF a user attempts to delete another user's flashcard, THEN THE Flashcard_System SHALL return a 403 error

### Requirement 6: Bulk Export Flashcards

**User Story:** As a user, I want to export all my flashcards to JSON, so that I can back up my data or migrate to another system.

#### Acceptance Criteria

1. THE Flashcard_System SHALL provide an export endpoint that accepts user_id
2. WHEN a user exports flashcards, THE Flashcard_System SHALL return all flashcards owned by the user in JSON format
3. THE exported JSON SHALL include all flashcard fields (word, translation_vi, phonetic, audio_url, example_sentence, ease_factor, repetition_count, interval_days, review_count, last_reviewed_at, next_review_at)
4. WHEN a user has more than 1000 flashcards, THE Flashcard_System SHALL paginate the export using cursor-based pagination
5. THE exported JSON SHALL be valid according to a documented schema

### Requirement 7: Bulk Import Flashcards

**User Story:** As a user, I want to import flashcards from JSON, so that I can restore backups or migrate from another system.

#### Acceptance Criteria

1. THE Flashcard_System SHALL provide an import endpoint that accepts user_id and a JSON array of flashcards
2. WHEN a user imports flashcards, THE Flashcard_System SHALL validate each flashcard against the documented schema
3. WHEN a user imports a flashcard with a word that already exists, THE Flashcard_System SHALL skip that flashcard and continue processing
4. WHEN a user imports flashcards, THE Flashcard_System SHALL return a summary showing counts of imported, skipped, and failed flashcards
5. IF the JSON is invalid, THEN THE Flashcard_System SHALL return a 400 error with details about the validation failure
6. THE Flashcard_System SHALL limit imports to 1000 flashcards per request

### Requirement 8: Learning Statistics

**User Story:** As a user, I want to see my learning progress statistics, so that I can track my vocabulary growth and retention.

#### Acceptance Criteria

1. THE Flashcard_System SHALL provide a statistics endpoint that accepts user_id
2. WHEN a user requests statistics, THE Flashcard_System SHALL return total flashcard count
3. WHEN a user requests statistics, THE Flashcard_System SHALL return count of flashcards due for review today
4. WHEN a user requests statistics, THE Flashcard_System SHALL return count of flashcards reviewed in the last 7 days
5. WHEN a user requests statistics, THE Flashcard_System SHALL return count of flashcards by maturity level (new: repetition_count = 0, learning: repetition_count 1-2, mature: repetition_count >= 3)
6. WHEN a user requests statistics, THE Flashcard_System SHALL return average ease_factor across all flashcards
7. THE statistics endpoint SHALL return results in under 200ms for users with up to 10,000 flashcards

### Requirement 9: Search and Filter Flashcards

**User Story:** As a user, I want to search and filter my flashcards, so that I can quickly find specific vocabulary.

#### Acceptance Criteria

1. THE Flashcard_System SHALL provide a search endpoint that accepts user_id and optional query parameters (word_prefix, min_interval, max_interval, maturity_level)
2. WHEN a user searches by word_prefix, THE Flashcard_System SHALL return flashcards where the word starts with the prefix (case-insensitive)
3. WHEN a user filters by min_interval, THE Flashcard_System SHALL return flashcards with interval_days >= min_interval
4. WHEN a user filters by max_interval, THE Flashcard_System SHALL return flashcards with interval_days <= max_interval
5. WHEN a user filters by maturity_level, THE Flashcard_System SHALL return flashcards matching the maturity criteria (new/learning/mature)
6. THE search endpoint SHALL support cursor-based pagination with a default limit of 50 results
7. WHEN no filters are provided, THE search endpoint SHALL return all user flashcards (paginated)

### Requirement 10: Data Migration

**User Story:** As a system administrator, I want to migrate existing flashcards to the new schema, so that users retain their learning progress.

#### Acceptance Criteria

1. THE Migration_Script SHALL add ease_factor field with value 2.5 to all existing flashcards
2. THE Migration_Script SHALL add repetition_count field with value derived from review_count (min(review_count, 3))
3. THE Migration_Script SHALL create GSI3 entries for word lookup (GSI3PK = user_id, GSI3SK = word_lowercase)
4. THE Migration_Script SHALL preserve all existing flashcard data (word, translation_vi, phonetic, audio_url, example_sentence, interval_days, review_count, last_reviewed_at, next_review_at)
5. THE Migration_Script SHALL process flashcards in batches of 25 to avoid DynamoDB throttling
6. THE Migration_Script SHALL log progress and errors to CloudWatch
7. THE Migration_Script SHALL be idempotent (safe to run multiple times)

### Requirement 11: Improved Validation

**User Story:** As a user, I want to create flashcards for phrasal verbs and idioms, so that I can learn multi-word expressions.

#### Acceptance Criteria

1. WHEN a user creates a flashcard, THE Flashcard_System SHALL accept words containing spaces (e.g., "give up", "break down")
2. WHEN a user creates a flashcard, THE Flashcard_System SHALL accept words containing hyphens (e.g., "well-known", "state-of-the-art")
3. WHEN a user creates a flashcard, THE Flashcard_System SHALL accept words containing apostrophes (e.g., "don't", "it's")
4. THE Flashcard_System SHALL reject words longer than 100 characters
5. THE Flashcard_System SHALL reject words containing only whitespace
6. THE Flashcard_System SHALL trim leading and trailing whitespace from words

### Requirement 12: API Response Time

**User Story:** As a user, I want flashcard operations to be fast, so that my learning flow is not interrupted.

#### Acceptance Criteria

1. WHEN a user reviews a flashcard, THE Flashcard_System SHALL respond in under 100ms at the 95th percentile
2. WHEN a user lists due flashcards, THE Flashcard_System SHALL respond in under 150ms at the 95th percentile
3. WHEN a user creates a flashcard, THE Flashcard_System SHALL respond in under 200ms at the 95th percentile
4. THE Flashcard_System SHALL use DynamoDB batch operations where applicable to minimize latency

### Requirement 13: Round-Trip Property for Export/Import

**User Story:** As a developer, I want to ensure data integrity during export/import, so that users never lose flashcard data.

#### Acceptance Criteria

1. FOR ALL valid flashcard sets, exporting then importing SHALL produce equivalent flashcards (same word, translation_vi, phonetic, audio_url, example_sentence, ease_factor, repetition_count, interval_days)
2. THE import parser SHALL handle all valid JSON structures produced by the export endpoint
3. THE export formatter SHALL produce JSON that the import parser can consume without errors
4. WHEN a flashcard is exported and imported, THE SRS state SHALL be preserved (ease_factor, repetition_count, interval_days, next_review_at within 1 second tolerance)

