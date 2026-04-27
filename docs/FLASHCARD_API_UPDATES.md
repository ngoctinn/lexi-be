# Flashcard System API Updates - Frontend Documentation

## Overview

The flashcard system has been upgraded with new endpoints, improved validation, and SM-2 spaced repetition algorithm support. This document provides frontend developers with all necessary information to integrate these updates.

## Table of Contents

1. [New Endpoints](#new-endpoints)
2. [Updated Endpoints](#updated-endpoints)
3. [Data Models](#data-models)
4. [Validation Rules](#validation-rules)
5. [Error Handling](#error-handling)
6. [Code Examples](#code-examples)
7. [Migration Guide](#migration-guide)

---

## New Endpoints

### 1. Update Flashcard (PATCH)

**Endpoint:** `PATCH /flashcards/{flashcard_id}`

**Description:** Update flashcard content (translation, phonetic, audio URL, example sentence). SRS data is preserved.

**Authentication:** Required (JWT token)

**Request Headers:**
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "translation_vi": "ví dụ (optional)",
  "phonetic": "/ɪɡˈzæmpəl/ (optional)",
  "audio_url": "https://example.com/audio.mp3 (optional)",
  "example_sentence": "This is an example. (optional)"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "flashcard_id": "card-001",
    "word": "example",
    "translation_vi": "ví dụ",
    "phonetic": "/ɪɡˈzæmpəl/",
    "audio_url": "https://example.com/audio.mp3",
    "example_sentence": "This is an example.",
    "ease_factor": 2.5,
    "repetition_count": 0,
    "interval_days": 1,
    "next_review_at": "2026-04-28T10:00:00Z"
  }
}
```

**Error Responses:**
- `400 Bad Request` - Invalid input data
- `403 Forbidden` - User doesn't own this flashcard
- `404 Not Found` - Flashcard doesn't exist

---

### 2. Delete Flashcard (DELETE)

**Endpoint:** `DELETE /flashcards/{flashcard_id}`

**Description:** Delete a flashcard permanently.

**Authentication:** Required (JWT token)

**Request Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response (204 No Content):** Empty response on success

**Error Responses:**
- `403 Forbidden` - User doesn't own this flashcard
- `404 Not Found` - Flashcard doesn't exist

---

### 3. Export Flashcards (GET)

**Endpoint:** `GET /flashcards/export?cursor=<optional_cursor>`

**Description:** Export all user's flashcards in JSON format with pagination support.

**Authentication:** Required (JWT token)

**Query Parameters:**
- `cursor` (optional): Pagination cursor for next page
- Default limit: 1000 flashcards per page

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "flashcards": [
      {
        "flashcard_id": "card-001",
        "word": "example",
        "translation_vi": "ví dụ",
        "phonetic": "/ɪɡˈzæmpəl/",
        "audio_url": "https://example.com/audio.mp3",
        "example_sentence": "This is an example.",
        "ease_factor": 2.5,
        "repetition_count": 0,
        "interval_days": 1,
        "review_count": 5,
        "last_reviewed_at": "2026-04-27T10:00:00Z",
        "next_review_at": "2026-04-28T10:00:00Z"
      }
    ],
    "next_cursor": "cursor-for-next-page",
    "total_count": 150
  }
}
```

**Use Cases:**
- Backup user data
- Migrate to another system
- Bulk analysis

---

### 4. Import Flashcards (POST)

**Endpoint:** `POST /flashcards/import`

**Description:** Import flashcards from JSON. Duplicate words are skipped.

**Authentication:** Required (JWT token)

**Request Headers:**
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "flashcards": [
    {
      "word": "example",
      "translation_vi": "ví dụ",
      "phonetic": "/ɪɡˈzæmpəl/",
      "audio_url": "https://example.com/audio.mp3",
      "example_sentence": "This is an example."
    },
    {
      "word": "test",
      "translation_vi": "bài kiểm tra",
      "phonetic": "/test/",
      "audio_url": "https://example.com/test.mp3",
      "example_sentence": "This is a test."
    }
  ]
}
```

**Constraints:**
- Maximum 1000 flashcards per request
- Duplicate words (case-insensitive) are skipped
- Invalid entries are reported in errors array

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "imported": 2,
    "skipped": 1,
    "failed": 0,
    "errors": [
      {
        "index": 2,
        "word": "example",
        "reason": "Duplicate word"
      }
    ]
  }
}
```

**Error Responses:**
- `400 Bad Request` - Invalid JSON or schema validation failed
- `413 Payload Too Large` - More than 1000 flashcards

---

### 5. Get Statistics (GET)

**Endpoint:** `GET /flashcards/statistics`

**Description:** Get learning progress statistics.

**Authentication:** Required (JWT token)

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "total_count": 150,
    "due_today": 12,
    "reviewed_last_7_days": 45,
    "maturity": {
      "new": 30,
      "learning": 60,
      "mature": 60
    },
    "average_ease_factor": 2.35
  }
}
```

**Field Descriptions:**
- `total_count`: Total number of flashcards
- `due_today`: Flashcards due for review today
- `reviewed_last_7_days`: Flashcards reviewed in last 7 days
- `maturity.new`: Cards with 0 reviews (repetition_count = 0)
- `maturity.learning`: Cards in learning phase (repetition_count 1-2)
- `maturity.mature`: Cards in mature phase (repetition_count ≥ 3)
- `average_ease_factor`: Average difficulty factor (1.3-2.5)

---

### 6. Search/Filter Flashcards (GET)

**Endpoint:** `GET /flashcards?word_prefix=<prefix>&min_interval=<days>&max_interval=<days>&maturity_level=<level>&cursor=<cursor>&limit=<limit>`

**Description:** Search and filter flashcards with multiple criteria.

**Authentication:** Required (JWT token)

**Query Parameters:**
- `word_prefix` (optional): Filter by word prefix (case-insensitive)
  - Example: `word_prefix=app` matches "apple", "application"
- `min_interval` (optional): Minimum days until next review
- `max_interval` (optional): Maximum days until next review
- `maturity_level` (optional): Filter by maturity level
  - Values: `new`, `learning`, `mature`
- `cursor` (optional): Pagination cursor
- `limit` (optional): Results per page (default: 50, max: 100)

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "flashcards": [
      {
        "flashcard_id": "card-001",
        "word": "apple",
        "translation_vi": "quả táo",
        "phonetic": "/ˈæpəl/",
        "audio_url": "https://example.com/apple.mp3",
        "example_sentence": "An apple a day.",
        "ease_factor": 2.5,
        "repetition_count": 0,
        "interval_days": 1,
        "next_review_at": "2026-04-28T10:00:00Z"
      }
    ],
    "next_cursor": "cursor-for-next-page",
    "total_count": 5,
    "count": 1
  }
}
```

**Example Queries:**
```
# Find all "app" words
GET /flashcards?word_prefix=app

# Find learning cards due in 3-10 days
GET /flashcards?maturity_level=learning&min_interval=3&max_interval=10

# Find mature cards with pagination
GET /flashcards?maturity_level=mature&limit=20&cursor=next-page-cursor
```

---

## Updated Endpoints

### Review Flashcard (POST) - Updated

**Endpoint:** `POST /flashcards/{flashcard_id}/review`

**Changes:**
- Now uses SM-2 algorithm instead of simplified SRS
- Returns updated `ease_factor` and `repetition_count`

**Request Body:**
```json
{
  "rating": "good"
}
```

**Valid Ratings:**
- `"forgot"` - Quality 0: Forgot the answer
- `"hard"` - Quality 3: Difficult to recall
- `"good"` - Quality 4: Correct with effort
- `"easy"` - Quality 5: Correct immediately

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "flashcard_id": "card-001",
    "word": "example",
    "ease_factor": 2.45,
    "repetition_count": 1,
    "interval_days": 6,
    "next_review_at": "2026-05-03T10:00:00Z",
    "review_count": 5
  }
}
```

**SM-2 Algorithm Details:**
- First review (quality ≥ 3): interval = 1 day
- Second review (quality ≥ 3): interval = 6 days
- Subsequent reviews: interval = previous_interval × ease_factor
- Forgot (quality < 3): resets to interval = 1 day, repetition_count = 0
- Ease factor adjusts based on quality (minimum 1.3, maximum 2.5)

---

## Data Models

### Flashcard Object

```typescript
interface Flashcard {
  flashcard_id: string;           // Unique identifier (ULID)
  user_id: string;                // Owner's user ID
  word: string;                   // Vocabulary word (1-100 chars)
  translation_vi: string;         // Vietnamese translation
  phonetic: string;               // Phonetic pronunciation
  audio_url: string;              // URL to audio file
  example_sentence: string;       // Example usage
  
  // SRS Fields
  ease_factor: number;            // SM-2 difficulty (1.3-2.5)
  repetition_count: number;       // Consecutive successful reviews
  interval_days: number;          // Days until next review
  review_count: number;           // Total reviews
  
  // Timestamps
  last_reviewed_at: string;       // ISO 8601 timestamp
  next_review_at: string;         // ISO 8601 timestamp
  created_at?: string;            // ISO 8601 timestamp
  updated_at?: string;            // ISO 8601 timestamp
}
```

### Statistics Object

```typescript
interface Statistics {
  total_count: number;
  due_today: number;
  reviewed_last_7_days: number;
  maturity: {
    new: number;
    learning: number;
    mature: number;
  };
  average_ease_factor: number;
}
```

### Import Result Object

```typescript
interface ImportResult {
  imported: number;               // Successfully imported
  skipped: number;                // Duplicate words
  failed: number;                 // Validation errors
  errors: Array<{
    index: number;                // Position in input array
    word: string;                 // The word that failed
    reason: string;               // Error reason
  }>;
}
```

---

## Validation Rules

### Word Validation

**Accepted Characters:**
- Letters: a-z, A-Z
- Numbers: 0-9
- Spaces: for multi-word expressions
- Hyphens: for hyphenated words (e.g., "well-known")
- Apostrophes: for contractions (e.g., "don't")
- Forward slashes: for fractions (e.g., "24/7")

**Rules:**
- Length: 1-100 characters
- Must not be whitespace-only
- Leading/trailing whitespace is automatically trimmed
- Case-insensitive for duplicate detection

**Valid Examples:**
```
"apple"                    // Single word
"give up"                  // Phrasal verb
"well-known"               // Hyphenated
"don't"                    // Contraction
"state-of-the-art"         // Complex expression
"24/7"                     // With numbers and slash
```

**Invalid Examples:**
```
"apple!"                   // Special characters not allowed
"apple@"                   // @ symbol not allowed
"   "                      // Whitespace-only
"a" * 101                  // Exceeds 100 characters
```

### Ease Factor Validation

- Range: 1.3 to 2.5
- Default for new cards: 2.5
- Automatically adjusted by SM-2 algorithm

### Repetition Count Validation

- Range: 0 to unlimited
- Default for new cards: 0
- Incremented on successful reviews
- Reset to 0 on "forgot" rating

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Flashcard updated |
| 204 | No Content | Flashcard deleted |
| 400 | Bad Request | Invalid word format |
| 401 | Unauthorized | Missing JWT token |
| 403 | Forbidden | User doesn't own flashcard |
| 404 | Not Found | Flashcard doesn't exist |
| 409 | Conflict | Duplicate word |
| 413 | Payload Too Large | Import > 1000 cards |
| 500 | Server Error | Internal error |

### Error Response Format

```json
{
  "error": "Error message",
  "details": {
    "field": "word",
    "reason": "Word exceeds 100 characters"
  }
}
```

### Common Error Scenarios

**Invalid Word Format:**
```json
{
  "error": "Validation failed",
  "details": {
    "field": "word",
    "reason": "Word contains invalid characters: @"
  }
}
```

**Duplicate Word on Import:**
```json
{
  "success": true,
  "data": {
    "imported": 1,
    "skipped": 1,
    "failed": 0,
    "errors": [
      {
        "index": 1,
        "word": "example",
        "reason": "Duplicate word"
      }
    ]
  }
}
```

**Unauthorized Access:**
```json
{
  "error": "Unauthorized",
  "details": {
    "reason": "User does not own this flashcard"
  }
}
```

---

## Code Examples

### JavaScript/TypeScript Examples

#### 1. Update Flashcard

```typescript
async function updateFlashcard(
  flashcardId: string,
  updates: Partial<Flashcard>
): Promise<Flashcard> {
  const response = await fetch(`/flashcards/${flashcardId}`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${getToken()}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(updates)
  });

  if (!response.ok) {
    throw new Error(`Update failed: ${response.statusText}`);
  }

  const data = await response.json();
  return data.data;
}

// Usage
await updateFlashcard('card-001', {
  translation_vi: 'ví dụ',
  example_sentence: 'This is an example.'
});
```

#### 2. Delete Flashcard

```typescript
async function deleteFlashcard(flashcardId: string): Promise<void> {
  const response = await fetch(`/flashcards/${flashcardId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${getToken()}`
    }
  });

  if (!response.ok) {
    throw new Error(`Delete failed: ${response.statusText}`);
  }
}

// Usage
await deleteFlashcard('card-001');
```

#### 3. Export Flashcards

```typescript
async function exportAllFlashcards(): Promise<Flashcard[]> {
  const allCards: Flashcard[] = [];
  let cursor: string | null = null;

  do {
    const url = new URL('/flashcards/export', window.location.origin);
    if (cursor) {
      url.searchParams.append('cursor', cursor);
    }

    const response = await fetch(url.toString(), {
      headers: {
        'Authorization': `Bearer ${getToken()}`
      }
    });

    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`);
    }

    const data = await response.json();
    allCards.push(...data.data.flashcards);
    cursor = data.data.next_cursor;
  } while (cursor);

  return allCards;
}

// Usage
const cards = await exportAllFlashcards();
console.log(`Exported ${cards.length} flashcards`);
```

#### 4. Import Flashcards

```typescript
async function importFlashcards(
  flashcards: Array<Partial<Flashcard>>
): Promise<ImportResult> {
  const response = await fetch('/flashcards/import', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${getToken()}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ flashcards })
  });

  if (!response.ok) {
    throw new Error(`Import failed: ${response.statusText}`);
  }

  const data = await response.json();
  return data.data;
}

// Usage
const result = await importFlashcards([
  {
    word: 'example',
    translation_vi: 'ví dụ',
    phonetic: '/ɪɡˈzæmpəl/',
    audio_url: 'https://example.com/audio.mp3',
    example_sentence: 'This is an example.'
  }
]);

console.log(`Imported: ${result.imported}, Skipped: ${result.skipped}`);
```

#### 5. Get Statistics

```typescript
async function getStatistics(): Promise<Statistics> {
  const response = await fetch('/flashcards/statistics', {
    headers: {
      'Authorization': `Bearer ${getToken()}`
    }
  });

  if (!response.ok) {
    throw new Error(`Statistics failed: ${response.statusText}`);
  }

  const data = await response.json();
  return data.data;
}

// Usage
const stats = await getStatistics();
console.log(`Total cards: ${stats.total_count}`);
console.log(`Due today: ${stats.due_today}`);
console.log(`Mature cards: ${stats.maturity.mature}`);
```

#### 6. Search Flashcards

```typescript
async function searchFlashcards(
  filters: {
    word_prefix?: string;
    min_interval?: number;
    max_interval?: number;
    maturity_level?: 'new' | 'learning' | 'mature';
    limit?: number;
    cursor?: string;
  }
): Promise<{ flashcards: Flashcard[]; nextCursor: string | null }> {
  const url = new URL('/flashcards', window.location.origin);
  
  if (filters.word_prefix) {
    url.searchParams.append('word_prefix', filters.word_prefix);
  }
  if (filters.min_interval !== undefined) {
    url.searchParams.append('min_interval', filters.min_interval.toString());
  }
  if (filters.max_interval !== undefined) {
    url.searchParams.append('max_interval', filters.max_interval.toString());
  }
  if (filters.maturity_level) {
    url.searchParams.append('maturity_level', filters.maturity_level);
  }
  if (filters.limit) {
    url.searchParams.append('limit', filters.limit.toString());
  }
  if (filters.cursor) {
    url.searchParams.append('cursor', filters.cursor);
  }

  const response = await fetch(url.toString(), {
    headers: {
      'Authorization': `Bearer ${getToken()}`
    }
  });

  if (!response.ok) {
    throw new Error(`Search failed: ${response.statusText}`);
  }

  const data = await response.json();
  return {
    flashcards: data.data.flashcards,
    nextCursor: data.data.next_cursor
  };
}

// Usage
const { flashcards, nextCursor } = await searchFlashcards({
  word_prefix: 'app',
  maturity_level: 'learning',
  limit: 20
});

console.log(`Found ${flashcards.length} learning cards starting with 'app'`);
```

#### 7. Review Flashcard with SM-2

```typescript
async function reviewFlashcard(
  flashcardId: string,
  rating: 'forgot' | 'hard' | 'good' | 'easy'
): Promise<Flashcard> {
  const response = await fetch(`/flashcards/${flashcardId}/review`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${getToken()}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ rating })
  });

  if (!response.ok) {
    throw new Error(`Review failed: ${response.statusText}`);
  }

  const data = await response.json();
  return data.data;
}

// Usage
const updated = await reviewFlashcard('card-001', 'good');
console.log(`Next review in ${updated.interval_days} days`);
console.log(`Ease factor: ${updated.ease_factor}`);
```

---

## Migration Guide

### For Existing Frontend Code

#### 1. Update Review Endpoint Usage

**Before (Old SRS):**
```typescript
// Old endpoint still works but uses simplified algorithm
await fetch(`/flashcards/${id}/review`, {
  method: 'POST',
  body: JSON.stringify({ rating: 'good' })
});
```

**After (SM-2 Algorithm):**
```typescript
// Same endpoint, now uses SM-2 algorithm
// Response includes ease_factor and repetition_count
const response = await fetch(`/flashcards/${id}/review`, {
  method: 'POST',
  body: JSON.stringify({ rating: 'good' })
});
const { ease_factor, repetition_count, interval_days } = await response.json();
```

#### 2. Add New UI Components

**Update Flashcard Dialog:**
```typescript
// Add form fields for updating flashcard content
<form onSubmit={handleUpdate}>
  <input name="translation_vi" placeholder="Vietnamese translation" />
  <input name="phonetic" placeholder="Phonetic pronunciation" />
  <input name="audio_url" placeholder="Audio URL" />
  <textarea name="example_sentence" placeholder="Example sentence" />
  <button type="submit">Update</button>
</form>
```

**Statistics Dashboard:**
```typescript
// Display new statistics
<div className="statistics">
  <div>Total: {stats.total_count}</div>
  <div>Due Today: {stats.due_today}</div>
  <div>New: {stats.maturity.new}</div>
  <div>Learning: {stats.maturity.learning}</div>
  <div>Mature: {stats.maturity.mature}</div>
  <div>Avg Ease: {stats.average_ease_factor.toFixed(2)}</div>
</div>
```

**Search/Filter UI:**
```typescript
// Add search and filter controls
<div className="search-filters">
  <input 
    type="text" 
    placeholder="Search by word prefix..."
    onChange={(e) => setWordPrefix(e.target.value)}
  />
  <select onChange={(e) => setMaturityLevel(e.target.value)}>
    <option value="">All Levels</option>
    <option value="new">New</option>
    <option value="learning">Learning</option>
    <option value="mature">Mature</option>
  </select>
  <input 
    type="number" 
    placeholder="Min interval (days)"
    onChange={(e) => setMinInterval(parseInt(e.target.value))}
  />
  <input 
    type="number" 
    placeholder="Max interval (days)"
    onChange={(e) => setMaxInterval(parseInt(e.target.value))}
  />
</div>
```

#### 3. Update Data Display

**Show SM-2 Fields:**
```typescript
// Display ease_factor and repetition_count
<div className="flashcard-info">
  <div>Word: {card.word}</div>
  <div>Translation: {card.translation_vi}</div>
  <div>Ease Factor: {card.ease_factor.toFixed(2)}</div>
  <div>Repetition Count: {card.repetition_count}</div>
  <div>Days Until Review: {card.interval_days}</div>
  <div>Next Review: {new Date(card.next_review_at).toLocaleDateString()}</div>
</div>
```

#### 4. Add Import/Export Features

**Export Button:**
```typescript
async function handleExport() {
  const cards = await exportAllFlashcards();
  const json = JSON.stringify(cards, null, 2);
  const blob = new Blob([json], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `flashcards-${new Date().toISOString()}.json`;
  a.click();
}
```

**Import Button:**
```typescript
async function handleImport(file: File) {
  const text = await file.text();
  const data = JSON.parse(text);
  const result = await importFlashcards(data.flashcards || data);
  alert(`Imported: ${result.imported}, Skipped: ${result.skipped}`);
}
```

---

## Performance Considerations

### Pagination

- Use cursor-based pagination for large datasets
- Default limit: 50 items per page
- Maximum limit: 100 items per page

```typescript
// Efficient pagination
let cursor: string | null = null;
const allCards: Flashcard[] = [];

while (true) {
  const { flashcards, nextCursor } = await searchFlashcards({
    limit: 100,
    cursor
  });
  
  allCards.push(...flashcards);
  
  if (!nextCursor) break;
  cursor = nextCursor;
}
```

### Caching

- Cache statistics for 5 minutes
- Cache search results with filter parameters
- Invalidate cache on create/update/delete

```typescript
const cache = new Map<string, { data: any; timestamp: number }>();

async function getCachedStatistics(): Promise<Statistics> {
  const key = 'statistics';
  const cached = cache.get(key);
  
  if (cached && Date.now() - cached.timestamp < 5 * 60 * 1000) {
    return cached.data;
  }
  
  const stats = await getStatistics();
  cache.set(key, { data: stats, timestamp: Date.now() });
  return stats;
}
```

### Batch Operations

- Import up to 1000 flashcards per request
- Use batch import for better performance than individual creates

```typescript
// Good: Batch import
const result = await importFlashcards(largeArray);

// Avoid: Individual creates
for (const card of largeArray) {
  await createFlashcard(card);  // Slow!
}
```

---

## Troubleshooting

### Common Issues

**Issue: "Word contains invalid characters"**
- Solution: Check word contains only letters, numbers, spaces, hyphens, apostrophes, forward slashes
- Example: Remove special characters like @, !, ?, etc.

**Issue: "Ease factor must be between 1.3 and 2.5"**
- Solution: Don't manually set ease_factor; let SM-2 algorithm manage it
- The algorithm automatically adjusts based on review ratings

**Issue: "Duplicate word"**
- Solution: Word already exists for this user (case-insensitive)
- Use update endpoint to modify existing card instead

**Issue: "User does not own this flashcard"**
- Solution: Verify flashcard_id belongs to current user
- Check JWT token is valid and contains correct user_id

**Issue: Import returns 413 Payload Too Large**
- Solution: Split import into multiple requests with max 1000 cards each

---

## Support & Questions

For issues or questions:
1. Check this documentation
2. Review error messages and troubleshooting section
3. Contact backend team with error details and request body

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-27 | Initial release with SM-2 algorithm, CRUD operations, search, import/export |

