# Requirements: Flashcard Review SRS

## Overview

Feature này xây dựng hệ thống ôn tập flashcard theo thuật toán Spaced Repetition System (SRS) cho Lexi backend. Người học có thể xem danh sách thẻ đến hạn, đánh giá mức độ nhớ (forgot/hard/good/easy), và hệ thống tự động tính lịch ôn tập tiếp theo. Ngoài ra, feature cung cấp các endpoint để liệt kê tất cả flashcard và xem chi tiết từng thẻ.

---

## Requirement 1: List Due Cards

**User Story:** As a learner, I want to see the list of flashcards due for review today, so that I know which cards I need to study.

### Acceptance Criteria

1. WHEN a user calls `GET /flashcards/due` THEN the system SHALL return all flashcards where `next_review_at <= now` for that user
2. WHEN there are no due cards THEN the system SHALL return an empty list with HTTP 200
3. WHEN the user is not authenticated THEN the system SHALL return HTTP 401
4. WHEN the query succeeds THEN the system SHALL return each card with fields: `flashcard_id`, `word`, `translation_vi`, `definition_vi`, `phonetic`, `audio_url`, `example_sentence`, `review_count`, `interval_days`, `next_review_at`, `last_reviewed_at`

---

## Requirement 2: Review Flashcard with SRS

**User Story:** As a learner, I want to rate my recall of a flashcard (forgot/hard/good/easy), so that the system can schedule the next review at the right time.

### Acceptance Criteria

1. WHEN a user calls `POST /flashcards/{flashcard_id}/review` with a valid rating THEN the system SHALL update the card's SRS fields and return the updated card
2. WHEN the rating is `forgot` THEN the system SHALL set `interval_days = 1`
3. WHEN the rating is `hard` THEN the system SHALL set `interval_days = max(1, round(current_interval * 1.2))`
4. WHEN the rating is `good` THEN the system SHALL set `interval_days = round(current_interval * 2.5)`
5. WHEN the rating is `easy` THEN the system SHALL set `interval_days = round(current_interval * 3.0)`
6. WHEN a review is submitted THEN the system SHALL set `next_review_at = now + timedelta(days=new_interval_days)`
7. WHEN a review is submitted THEN the system SHALL set `last_reviewed_at = now`
8. WHEN a review is submitted THEN the system SHALL increment `review_count` by 1
9. WHEN the rating value is not one of `forgot`, `hard`, `good`, `easy` THEN the system SHALL return HTTP 400 with an error message
10. WHEN the flashcard does not belong to the authenticated user THEN the system SHALL return HTTP 403
11. WHEN the flashcard does not exist THEN the system SHALL return HTTP 404

---

## Requirement 3: List All Flashcards with Pagination

**User Story:** As a learner, I want to browse all my flashcards with pagination, so that I can manage my vocabulary collection.

### Acceptance Criteria

1. WHEN a user calls `GET /flashcards` THEN the system SHALL return a paginated list of all flashcards belonging to that user
2. WHEN the `limit` query parameter is provided THEN the system SHALL return at most that many cards (default: 20, max: 100)
3. WHEN the `last_key` query parameter is provided THEN the system SHALL return the next page starting after that key
4. WHEN there are more results THEN the system SHALL include a `next_key` in the response for the next page
5. WHEN there are no more results THEN the system SHALL return `next_key` as `null`
6. WHEN the user has no flashcards THEN the system SHALL return an empty list with HTTP 200

---

## Requirement 4: Get Flashcard Detail

**User Story:** As a learner, I want to view the full details of a specific flashcard, so that I can review its content before or after a session.

### Acceptance Criteria

1. WHEN a user calls `GET /flashcards/{flashcard_id}` THEN the system SHALL return the full details of that flashcard
2. WHEN the flashcard does not belong to the authenticated user THEN the system SHALL return HTTP 403
3. WHEN the flashcard does not exist THEN the system SHALL return HTTP 404
4. WHEN the request succeeds THEN the system SHALL return all fields: `flashcard_id`, `word`, `translation_vi`, `definition_vi`, `phonetic`, `audio_url`, `example_sentence`, `review_count`, `interval_days`, `difficulty`, `last_reviewed_at`, `next_review_at`, `source_session_id`, `source_turn_index`

---

## Requirement 5: REST API Endpoint Pattern

**User Story:** As a developer, I want consistent REST API endpoints for flashcard operations, so that the frontend can integrate reliably.

### Acceptance Criteria

1. THE system SHALL expose the following endpoints:
   - `GET /flashcards/due`
   - `POST /flashcards/{flashcard_id}/review`
   - `GET /flashcards`
   - `GET /flashcards/{flashcard_id}`
2. THE system SHALL extract `user_id` from the Cognito JWT `sub` claim via the API Gateway authorizer context — NOT from path parameters
3. WHEN the Cognito JWT is missing or invalid THEN the system SHALL return HTTP 401
4. ALL endpoints SHALL include `Access-Control-Allow-Origin: *` in response headers

---

## Requirement 6: Repository Interface Extension

**User Story:** As a developer, I want the FlashCardRepository interface to support all required data access patterns, so that use cases can be implemented cleanly.

### Acceptance Criteria

1. THE `FlashCardRepository` interface SHALL add method `get_by_user_and_id(user_id: str, flashcard_id: str) -> Optional[FlashCard]`
2. THE `FlashCardRepository` interface SHALL add method `list_by_user(user_id: str, last_key: Optional[dict], limit: int) -> tuple[list[FlashCard], Optional[dict]]`
3. THE `FlashCardRepository` interface SHALL add method `update(card: FlashCard) -> None`
4. WHEN `get_by_user_and_id` is called with a non-existent card THEN it SHALL return `None`
5. WHEN `list_by_user` reaches the last page THEN it SHALL return `None` as the second element of the tuple

---

## Requirement 7: DynamoDB GSI2 Configuration

**User Story:** As a developer, I want the DynamoDB repository to use GSI2 for due-card queries instead of scan, so that queries are efficient and cost-effective.

### Acceptance Criteria

1. WHEN `save()` is called THEN the system SHALL populate `GSI2PK = user_id` and `GSI2SK = next_review_at` (ISO 8601 string) on the DynamoDB item
2. WHEN `list_due_cards()` is called THEN the system SHALL query `GSI2-SRS-ReviewQueue` using `GSI2PK = user_id` and `GSI2SK <= now` instead of scanning the table
3. WHEN `update()` is called THEN the system SHALL update the item and also refresh `GSI2SK = next_review_at`
4. THE GSI2 key mapping SHALL be: `GSI2PK = user_id`, `GSI2SK = next_review_at` (ISO 8601 string, sortable)

---

## Requirement 8: Use Case Layer

**User Story:** As a developer, I want clean use case classes for each flashcard operation, so that business logic is separated from infrastructure.

### Acceptance Criteria

1. THE system SHALL implement `ListDueCardsUC(repo).execute(user_id: str) -> list[FlashCard]`
2. THE system SHALL implement `ReviewFlashcardUC(repo).execute(user_id: str, flashcard_id: str, rating: str) -> FlashCard`
3. THE system SHALL implement `ListUserFlashcardsUC(repo).execute(user_id: str, last_key: Optional[dict], limit: int) -> tuple[list[FlashCard], Optional[dict]]`
4. THE system SHALL implement `GetFlashcardDetailUC(repo).execute(user_id: str, flashcard_id: str) -> FlashCard`
5. WHEN `ReviewFlashcardUC` receives an invalid rating THEN it SHALL raise a `ValueError`
6. WHEN `ReviewFlashcardUC` or `GetFlashcardDetailUC` cannot find the card for that user THEN it SHALL raise a `PermissionError` if the card exists but belongs to another user, or a `KeyError` if the card does not exist

---

## Requirement 9: Lambda Handlers

**User Story:** As a developer, I want Lambda handler functions for each new endpoint, so that API Gateway can route requests correctly.

### Acceptance Criteria

1. THE system SHALL implement `list_due_cards_handler.py` following the same pattern as `create_flashcard_handler.py`
2. THE system SHALL implement `review_flashcard_handler.py` following the same pattern as `create_flashcard_handler.py`
3. THE system SHALL implement `list_flashcards_handler.py` following the same pattern as `create_flashcard_handler.py`
4. THE system SHALL implement `get_flashcard_handler.py` following the same pattern as `create_flashcard_handler.py`
5. EACH handler SHALL extract `user_id` from `event["requestContext"]["authorizer"]["claims"]["sub"]`
6. EACH handler SHALL return appropriate HTTP status codes and JSON bodies for success and error cases

---

## Requirement 10: SAM Template

**User Story:** As a developer, I want the SAM template updated with the new Lambda functions and API routes, so that the feature can be deployed to AWS.

### Acceptance Criteria

1. THE `template.yaml` SHALL add `ListDueCardsFunction` with event `GET /flashcards/due` and `DynamoDBReadPolicy`
2. THE `template.yaml` SHALL add `ReviewFlashcardFunction` with event `POST /flashcards/{flashcard_id}/review` and `DynamoDBCrudPolicy`
3. THE `template.yaml` SHALL add `ListFlashcardsFunction` with event `GET /flashcards` and `DynamoDBReadPolicy`
4. THE `template.yaml` SHALL add `GetFlashcardFunction` with event `GET /flashcards/{flashcard_id}` and `DynamoDBReadPolicy`
5. ALL new functions SHALL use `Runtime: python3.12` and have `LEXI_TABLE_NAME` environment variable

---

## Requirement 11: Error Handling

**User Story:** As a developer, I want consistent error responses across all flashcard endpoints, so that the frontend can handle errors predictably.

### Acceptance Criteria

1. WHEN a request contains an invalid rating value THEN the system SHALL return HTTP 400 with body `{"error": "Invalid rating. Must be one of: forgot, hard, good, easy"}`
2. WHEN a user attempts to access a flashcard belonging to another user THEN the system SHALL return HTTP 403 with body `{"error": "Forbidden"}`
3. WHEN a flashcard is not found THEN the system SHALL return HTTP 404 with body `{"error": "Flashcard not found"}`
4. WHEN an unexpected error occurs THEN the system SHALL return HTTP 500 with body `{"error": "Internal server error"}`
5. ALL error responses SHALL include `Access-Control-Allow-Origin: *` header

---

## Requirement 12: Logging

**User Story:** As a developer, I want structured logging in all new handlers and use cases, so that I can debug issues in production.

### Acceptance Criteria

1. EACH Lambda handler SHALL log the incoming `user_id` and relevant path/query parameters at the start of execution
2. WHEN a review is processed THEN the system SHALL log `flashcard_id`, `rating`, old `interval_days`, and new `interval_days`
3. WHEN an error occurs THEN the system SHALL log the error type and message
4. Logs SHALL use Python's standard `logging` module (not `print`)
