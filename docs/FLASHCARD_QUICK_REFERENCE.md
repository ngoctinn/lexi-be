# Flashcard API - Quick Reference Guide

## Endpoints Summary

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| POST | `/flashcards` | Create flashcard | ✓ |
| GET | `/flashcards` | List/Search flashcards | ✓ |
| GET | `/flashcards/{id}` | Get single flashcard | ✓ |
| PATCH | `/flashcards/{id}` | Update flashcard | ✓ |
| DELETE | `/flashcards/{id}` | Delete flashcard | ✓ |
| POST | `/flashcards/{id}/review` | Review flashcard (SM-2) | ✓ |
| GET | `/flashcards/due` | Get cards due today | ✓ |
| GET | `/flashcards/statistics` | Get learning stats | ✓ |
| GET | `/flashcards/export` | Export all cards | ✓ |
| POST | `/flashcards/import` | Import cards | ✓ |

## Quick Examples

### Create Flashcard
```bash
curl -X POST https://api.example.com/flashcards \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "word": "example",
    "translation_vi": "ví dụ",
    "phonetic": "/ɪɡˈzæmpəl/",
    "audio_url": "https://example.com/audio.mp3",
    "example_sentence": "This is an example."
  }'
```

### Update Flashcard
```bash
curl -X PATCH https://api.example.com/flashcards/card-001 \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "translation_vi": "ví dụ mới",
    "example_sentence": "New example sentence."
  }'
```

### Delete Flashcard
```bash
curl -X DELETE https://api.example.com/flashcards/card-001 \
  -H "Authorization: Bearer TOKEN"
```

### Review Flashcard
```bash
curl -X POST https://api.example.com/flashcards/card-001/review \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"rating": "good"}'
```

### Get Statistics
```bash
curl -X GET https://api.example.com/flashcards/statistics \
  -H "Authorization: Bearer TOKEN"
```

### Search Flashcards
```bash
# Find learning cards starting with "app"
curl -X GET "https://api.example.com/flashcards?word_prefix=app&maturity_level=learning" \
  -H "Authorization: Bearer TOKEN"

# Find cards due in 3-10 days
curl -X GET "https://api.example.com/flashcards?min_interval=3&max_interval=10" \
  -H "Authorization: Bearer TOKEN"
```

### Export Flashcards
```bash
curl -X GET https://api.example.com/flashcards/export \
  -H "Authorization: Bearer TOKEN"
```

### Import Flashcards
```bash
curl -X POST https://api.example.com/flashcards/import \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "flashcards": [
      {
        "word": "example",
        "translation_vi": "ví dụ",
        "phonetic": "/ɪɡˈzæmpəl/",
        "audio_url": "https://example.com/audio.mp3",
        "example_sentence": "This is an example."
      }
    ]
  }'
```

## Rating Values (SM-2 Algorithm)

| Rating | Quality | Meaning |
|--------|---------|---------|
| `forgot` | 0 | Forgot the answer |
| `hard` | 3 | Difficult to recall |
| `good` | 4 | Correct with effort |
| `easy` | 5 | Correct immediately |

## Maturity Levels

| Level | Meaning | Repetition Count |
|-------|---------|------------------|
| `new` | Never reviewed | 0 |
| `learning` | In learning phase | 1-2 |
| `mature` | Well learned | ≥ 3 |

## Word Validation Rules

✅ **Allowed:**
- Letters: a-z, A-Z
- Numbers: 0-9
- Spaces: "give up"
- Hyphens: "well-known"
- Apostrophes: "don't"
- Forward slashes: "24/7"

❌ **Not Allowed:**
- Special characters: @, !, ?, #, etc.
- Whitespace-only strings
- Longer than 100 characters

## Response Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 204 | Success (no content) |
| 400 | Bad request (validation error) |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (don't own resource) |
| 404 | Not found |
| 409 | Conflict (duplicate) |
| 413 | Payload too large |
| 500 | Server error |

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "Word contains invalid characters" | Invalid character in word | Use only allowed characters |
| "Word exceeds 100 characters" | Word too long | Shorten the word |
| "Ease factor must be 1.3-2.5" | Invalid ease_factor | Don't set manually; let SM-2 manage |
| "Duplicate word" | Word already exists | Use PATCH to update instead |
| "User does not own this flashcard" | Wrong user | Verify flashcard_id and user_id |
| "Flashcard not found" | ID doesn't exist | Check flashcard_id |

## SM-2 Algorithm Intervals

| Review # | Quality | Interval |
|----------|---------|----------|
| 1st | ≥ 3 | 1 day |
| 2nd | ≥ 3 | 6 days |
| 3rd+ | ≥ 3 | previous × ease_factor |
| Any | < 3 | 1 day (reset) |

## Pagination

**Cursor-based pagination:**
```
GET /flashcards?limit=50&cursor=next-page-cursor
```

- Default limit: 50
- Max limit: 100
- Use `next_cursor` from response for next page
- `next_cursor` is null on last page

## Rate Limiting

- No explicit rate limits documented
- Recommended: Max 1000 cards per import request
- Recommended: Cache statistics for 5 minutes

## Authentication

All endpoints require JWT token in Authorization header:
```
Authorization: Bearer <jwt_token>
```

Token should contain `sub` claim with user_id.

## TypeScript Types

```typescript
interface Flashcard {
  flashcard_id: string;
  user_id: string;
  word: string;
  translation_vi: string;
  phonetic: string;
  audio_url: string;
  example_sentence: string;
  ease_factor: number;        // 1.3-2.5
  repetition_count: number;   // 0+
  interval_days: number;
  review_count: number;
  last_reviewed_at: string;   // ISO 8601
  next_review_at: string;     // ISO 8601
}

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

interface ImportResult {
  imported: number;
  skipped: number;
  failed: number;
  errors: Array<{
    index: number;
    word: string;
    reason: string;
  }>;
}
```

## React Hook Example

```typescript
import { useState, useEffect } from 'react';

function useFlashcards() {
  const [cards, setCards] = useState<Flashcard[]>([]);
  const [stats, setStats] = useState<Statistics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const token = localStorage.getItem('token');

  const fetchCards = async (filters?: any) => {
    setLoading(true);
    try {
      const url = new URL('/flashcards', window.location.origin);
      if (filters?.word_prefix) {
        url.searchParams.append('word_prefix', filters.word_prefix);
      }
      if (filters?.maturity_level) {
        url.searchParams.append('maturity_level', filters.maturity_level);
      }

      const response = await fetch(url.toString(), {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) throw new Error('Failed to fetch');
      const data = await response.json();
      setCards(data.data.flashcards);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch('/flashcards/statistics', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) throw new Error('Failed to fetch stats');
      const data = await response.json();
      setStats(data.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  const reviewCard = async (cardId: string, rating: string) => {
    try {
      const response = await fetch(`/flashcards/${cardId}/review`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ rating })
      });
      
      if (!response.ok) throw new Error('Failed to review');
      await fetchCards();
      await fetchStats();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  return { cards, stats, loading, error, fetchCards, fetchStats, reviewCard };
}
```

## Vue 3 Composable Example

```typescript
import { ref, computed } from 'vue';

export function useFlashcards() {
  const cards = ref<Flashcard[]>([]);
  const stats = ref<Statistics | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const token = localStorage.getItem('token');

  const fetchCards = async (filters?: any) => {
    loading.value = true;
    try {
      const url = new URL('/flashcards', window.location.origin);
      Object.entries(filters || {}).forEach(([key, value]) => {
        if (value) url.searchParams.append(key, String(value));
      });

      const response = await fetch(url.toString(), {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) throw new Error('Failed to fetch');
      const data = await response.json();
      cards.value = data.data.flashcards;
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error';
    } finally {
      loading.value = false;
    }
  };

  const dueToday = computed(() => stats.value?.due_today ?? 0);
  const totalCards = computed(() => stats.value?.total_count ?? 0);

  return { cards, stats, loading, error, fetchCards, dueToday, totalCards };
}
```

## Debugging Tips

1. **Check token validity:**
   ```typescript
   const decoded = JSON.parse(atob(token.split('.')[1]));
   console.log('User ID:', decoded.sub);
   ```

2. **Log API responses:**
   ```typescript
   const response = await fetch(url, options);
   console.log('Status:', response.status);
   console.log('Body:', await response.json());
   ```

3. **Validate word format:**
   ```typescript
   const isValidWord = /^[a-zA-Z0-9\s\-'/]+$/.test(word) && word.trim().length > 0;
   ```

4. **Check ease factor range:**
   ```typescript
   const isValidEase = ease_factor >= 1.3 && ease_factor <= 2.5;
   ```

## Migration Checklist

- [ ] Update review endpoint to handle SM-2 response fields
- [ ] Add update (PATCH) functionality to UI
- [ ] Add delete functionality to UI
- [ ] Add statistics display
- [ ] Add search/filter UI
- [ ] Add import/export buttons
- [ ] Update word validation in forms
- [ ] Handle new error responses
- [ ] Test with new endpoints
- [ ] Update documentation

