# Design Document: Vocabulary API Upgrade with Dictionary API + AWS Translate

## Overview

This design describes the architecture for upgrading the vocabulary translation endpoint to fetch word information from Dictionary API (https://dictionaryapi.dev/) and translate to Vietnamese using AWS Translate.

**Key Design Principles:**
- **Clean Architecture**: Separation of concerns with DictionaryService as a port
- **Backward Compatibility**: Existing clients continue working
- **Performance**: Response time < 2s (95th percentile), cached < 500ms
- **Graceful Degradation**: Partial success when translation fails
- **Caching Strategy**: In-memory + DynamoDB, 24-hour TTL

---

## Architecture

### High-Level Data Flow

```
Client Request
    ↓
[VocabularyController]
    ↓
[TranslateVocabularyUseCase]
    ├─→ [DictionaryService Port]
    │   └─→ [DictionaryServiceAdapter]
    │       ├─→ [CacheService] (in-memory + DynamoDB)
    │       └─→ [Dictionary API] (with retry)
    │
    └─→ [TranslationService Port]
        └─→ [AwsTranslateService]
            └─→ [AWS Translate] (batch)
    ↓
[Response Mapper]
    ↓
Client Response (HTTP 200/404/503)
```

### Layered Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Interfaces Layer (Controllers, Mappers)                 │
│ - VocabularyController: HTTP request handling           │
│ - VocabularyMapper: DTO ↔ Domain mapping               │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Application Layer (Use Cases, DTOs, Ports)              │
│ - TranslateVocabularyUseCase: Orchestration             │
│ - TranslateVocabularyCommand/Response: DTOs             │
│ - DictionaryService: Port (abstraction)                 │
│ - TranslationService: Port (existing)                   │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Domain Layer (Entities)                                 │
│ - Vocabulary: Domain entity                             │
│ - Meaning: Value object                                 │
│ - Phonetic: Value object                                │
│ - DefinitionItem: Value object                          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Infrastructure Layer (Adapters, Services)               │
│ - DictionaryServiceAdapter: Dictionary API integration  │
│ - CacheService: In-memory + DynamoDB caching           │
│ - AwsTranslateService: AWS Translate adapter           │
│ - RetryService: Exponential backoff retry              │
└─────────────────────────────────────────────────────────┘
```

---

## Components and Interfaces

### 1. DictionaryService Port (Application Layer)

**Purpose**: Abstract interface for fetching word definitions.

```python
from abc import ABC, abstractmethod
from domain.entities.vocabulary import Vocabulary

class DictionaryService(ABC):
    """Port: Dictionary service abstraction."""
    
    @abstractmethod
    def get_word_definition(self, word: str) -> Vocabulary:
        """
        Fetch word definition from dictionary.
        
        Args:
            word: English word (e.g., "hello")
        
        Returns:
            Vocabulary with phonetic, meanings, audio
        
        Raises:
            WordNotFoundError: Word not found
            DictionaryServiceError: Service unavailable
            TimeoutError: Request exceeded 30 seconds
        """
        ...
```

### 2. DictionaryServiceAdapter (Infrastructure Layer)

**Purpose**: Implement DictionaryService by calling Dictionary API.

**Key Features:**
- Calls `https://api.dictionaryapi.dev/api/v2/entries/en/{word}`
- Caches responses for 24 hours
- Retry: max 2 retries (1s, 2s backoff)
- Timeout: 30 seconds
- Logs all API calls

```python
class DictionaryServiceAdapter(DictionaryService):
    """Adapter: Dictionary API → DictionaryService port."""
    
    def __init__(
        self,
        cache_service: CacheService,
        retry_service: RetryService,
        logger: Logger
    ):
        self._cache = cache_service
        self._retry = retry_service
        self._logger = logger
    
    def get_word_definition(self, word: str) -> Vocabulary:
        # 1. Check cache
        # 2. If miss, call Dictionary API with retry
        # 3. Parse response into Vocabulary entity
        # 4. Cache result
        # 5. Return Vocabulary
        ...
```

### 3. CacheService (Infrastructure Layer)

**Purpose**: Two-tier caching (in-memory + DynamoDB).

**Strategy:**
- **In-Memory**: Fast access for Lambda warm starts
- **DynamoDB**: Persistent across invocations
- **TTL**: 24 hours
- **Key Format**: `vocabulary:definition:{word_lowercase}`

```python
class CacheService:
    """Two-tier cache: in-memory + DynamoDB."""
    
    def get(self, key: str) -> dict | None:
        # 1. Try in-memory cache
        # 2. If miss, try DynamoDB
        # 3. Return cached value or None
        ...
    
    def set(self, key: str, value: dict, ttl_seconds: int = 86400):
        # 1. Store in in-memory cache
        # 2. Store in DynamoDB with TTL
        ...
```

### 4. RetryService (Infrastructure Layer)

**Purpose**: Exponential backoff retry for transient failures.

**Strategy:**
- Retry on: HTTP 429, 5xx
- Max retries: 2
- Backoff: 1s, 2s
- No retry on: 404, 4xx

```python
class RetryService:
    """Exponential backoff retry logic."""
    
    def execute_with_retry(
        self,
        func: Callable,
        max_retries: int = 2,
        backoff_delays: List[int] = [1, 2]
    ) -> Any:
        # 1. Try to execute func()
        # 2. On transient error, wait and retry
        # 3. Return result or raise error
        ...
```

### 5. TranslateVocabularyUseCase (Application Layer)

**Purpose**: Orchestrate vocabulary translation workflow.

**Workflow:**
1. Receive TranslateVocabularyCommand (word)
2. Call DictionaryService.get_word_definition(word)
3. Batch translate: word, definitions, examples
4. Combine into TranslateVocabularyResponse
5. Return response

```python
class TranslateVocabularyUseCase:
    """Orchestrate vocabulary translation workflow."""
    
    def __init__(
        self,
        dictionary_service: DictionaryService,
        translation_service: TranslationService,
        logger: Logger
    ):
        self._dictionary = dictionary_service
        self._translation = translation_service
        self._logger = logger
    
    def execute(
        self,
        command: TranslateVocabularyCommand
    ) -> Result[TranslateVocabularyResponse, Exception]:
        # 1. Fetch word from Dictionary API
        # 2. Batch translate all text items
        # 3. Handle partial failures
        # 4. Return enriched response
        ...
```

---

## Data Models

### Domain Entities

#### Vocabulary (Domain Entity)

```python
@dataclass
class Vocabulary:
    """Complete vocabulary information from Dictionary API + AWS Translate."""
    word: str  # English word (original or detected phrasal verb)
    translate_vi: str  # Vietnamese translation of the word
    phonetic: str  # Primary phonetic (IPA notation)
    audio_url: Optional[str] = None  # Audio URL (from first phonetic)
    meanings: List[Meaning] = field(default_factory=list)  # All meanings with translations
    origin: Optional[str] = None  # Word origin (if available)
```

#### Meaning (Value Object)

```python
@dataclass
class Meaning:
    """
    Meaning for a specific part of speech with translations.
    Contains ONE definition and ONE example per meaning.
    """
    part_of_speech: str  # "noun", "verb", "adjective", etc.
    definition: str  # English definition (FIRST from API)
    definition_vi: str = ""  # Vietnamese translation of definition
    example: str = ""  # English example (FIRST from API, if exists)
    example_vi: str = ""  # Vietnamese translation of example
```

#### Phonetic (Value Object)

```python
@dataclass
class Phonetic:
    """Phonetic representation with audio."""
    text: str  # IPA notation
    audio: Optional[str] = None  # Audio URL
```

### DTOs (Application Layer)

#### TranslateVocabularyCommand (Input)

```python
class TranslateVocabularyCommand(BaseDTO):
    word: str = Field(min_length=1, max_length=100)
```

#### TranslateVocabularyResponse (Output)

```python
class TranslateVocabularyResponse(BaseDTO):
    # Backward compatibility
    word: str
    translate_vi: str
    
    # New fields
    phonetic: str
    audio_url: Optional[str] = None
    meanings: List[MeaningDTO]
```

#### MeaningDTO

```python
class MeaningDTO(BaseDTO):
    part_of_speech: str
    definition: str
    definition_vi: str
    example: str = ""
    example_vi: str = ""
```

---

## Dictionary API Response Parsing

### API Response Structure

```json
{
  "word": "hello",
  "phonetic": "həˈləʊ",
  "phonetics": [
    {
      "text": "həˈləʊ",
      "audio": "//ssl.gstatic.com/dictionary/static/sounds/20200429/hello--_gb_1.mp3"
    }
  ],
  "meanings": [
    {
      "partOfSpeech": "exclamation",
      "definitions": [
        {
          "definition": "used as a greeting",
          "example": "hello there, Katie!"
        }
      ]
    }
  ]
}
```

### Extraction Rules

1. **word**: Use top-level `word` field
2. **phonetic**: Use top-level `phonetic` field
3. **audio_url**: Use `phonetics[0].audio` (first audio)
4. **meanings**: Process ALL meanings
5. **Per meaning**:
   - `part_of_speech`: Use `meanings[i].partOfSpeech`
   - `definition`: Use `meanings[i].definitions[0].definition` (FIRST only)
   - `example`: Use `meanings[i].definitions[0].example` (FIRST only, if exists)

---

## Batch Translation Strategy

### AWS Translate Batch Processing

**Strategy**: Batch translate all items in single call.

```python
# Items to translate
items = [
    word,  # "hello"
    meaning1_definition,  # "used as a greeting"
    meaning1_example,  # "hello there, Katie!"
    meaning2_definition,  # "an utterance of 'hello'"
    meaning2_example,  # "she was getting hellos"
]

# Single AWS Translate call
translations = translate_service.translate_batch(
    texts=items,
    source_language="en",
    target_language="vi"
)

# Result: ["xin chào", "được dùng để chào hỏi", ...]
```

### Fallback Behavior

If AWS Translate fails:
- Return empty string for `*_vi` fields
- Log error
- Continue (graceful degradation)
- Return HTTP 200

---

## Caching Implementation

### Cache Strategy

**Two-Tier:**
1. **In-Memory** (Lambda memory): Fast, survives warm starts
2. **DynamoDB** (Persistent): Survives cold starts, shared

### Cache Key Format

```
vocabulary:definition:{word_lowercase}
```

Example: `vocabulary:definition:hello`

### DynamoDB Schema

```
Table: VocabularyCache
├── PK: cache_key (String)
├── word (String)
├── definition_json (String) = serialized Vocabulary
├── ttl (Number) = Unix timestamp (24h from now)
└── created_at (Number) = Unix timestamp
```

### Performance Impact

- **Cache Hit**: < 500ms
- **Cache Miss**: < 2000ms

---

## Error Handling

### Error Hierarchy

```
Exception
├── WordNotFoundError (HTTP 404)
├── DictionaryServiceError (HTTP 503)
└── TranslationError (HTTP 200 with empty *_vi)
```

### Error Responses

**Word Not Found (HTTP 404):**
```json
{
  "success": false,
  "message": "Word not found in dictionary",
  "error": "WORD_NOT_FOUND"
}
```

**Service Unavailable (HTTP 503):**
```json
{
  "success": false,
  "message": "Dictionary service temporarily unavailable",
  "error": "DICTIONARY_SERVICE_ERROR"
}
```

---

## Performance Considerations

### Response Time SLA

- **95th percentile**: < 2000ms (non-cached)
- **Cached**: < 500ms
- **P99**: < 3000ms

### Optimization

1. **Caching**: 24-hour TTL reduces API calls
2. **Batch Translation**: Single AWS Translate call
3. **Connection Pooling**: Reuse HTTP connections
4. **Lambda Warm Start**: In-memory cache survives

---

## Sequence Diagrams

### Happy Path: Cache Hit

```
Client → VocabularyController → TranslateVocabularyUseCase
  → DictionaryService → CacheService.get()
  → Return cached Vocabulary (45ms)
  → Return Response (HTTP 200)
```

### Happy Path: Cache Miss

```
Client → VocabularyController → TranslateVocabularyUseCase
  → DictionaryService → CacheService.get() [miss]
  → RetryService → Dictionary API (800ms)
  → Parse response → CacheService.set()
  → TranslationService.translate_batch() (400ms)
  → Return Response (HTTP 200, 1200ms total)
```

### Error Path: Word Not Found

```
Client → VocabularyController → TranslateVocabularyUseCase
  → DictionaryService → Dictionary API (HTTP 404)
  → Raise WordNotFoundError
  → Return HTTP 404 Error Response
```

---

## Configuration

### Environment Variables

```bash
# Dictionary API
DICTIONARY_API_BASE_URL=https://api.dictionaryapi.dev/api/v2
DICTIONARY_API_TIMEOUT_SECONDS=30

# Caching
CACHE_TTL_SECONDS=86400  # 24 hours
CACHE_ENABLED=true

# Retry
RETRY_MAX_ATTEMPTS=2
RETRY_BACKOFF_DELAYS=1,2

# AWS
AWS_REGION=us-east-1
LEXI_TABLE_NAME=lexi-vocabulary-cache
```

### DynamoDB Table

```yaml
Table: lexi-vocabulary-cache
Attributes:
  - cache_key (String, PK)
  - word (String)
  - definition_json (String)
  - ttl (Number, TTL attribute)
  - created_at (Number)

TTL:
  - Attribute: ttl
  - Enabled: true
  - Auto-delete after 24 hours

Billing: PAY_PER_REQUEST
```

---

## Backward Compatibility

### Existing Response Fields

```json
{
  "word": "hello",              // Existing
  "translate_vi": "xin chào",   // Existing
  
  // New fields (clients can ignore)
  "phonetic": "həˈləʊ",
  "audio_url": "...",
  "meanings": [...]
}
```

### Existing Clients

Clients reading only `word` and `translate_vi` continue working:

```python
# Old client code (still works)
response = requests.post("/vocabulary/translate", json={"word": "hello"})
word = response["word"]
translation = response["translate_vi"]
```

---

## Testing Strategy

### Unit Tests

- DTO validation
- Error handling (404, 503, timeout)
- Caching (hit, miss, TTL)
- Retry logic (429, 5xx, backoff)

### Integration Tests

- Dictionary API (success, 404, timeout)
- AWS Translate (success, failure)
- End-to-end workflow
- Performance validation (< 2000ms)

### Property-Based Tests

- Response parsing preserves data
- Batch translation completes all items
- Graceful degradation on translation failure
- Required fields always present
- Caching idempotence

---

## Implementation Roadmap

### Phase 1: Core Infrastructure
1. Create DictionaryService port
2. Create CacheService
3. Create RetryService
4. Create DictionaryServiceAdapter

### Phase 2: Use Case & DTOs
1. Update TranslateVocabularyUseCase
2. Create DTOs (MeaningDTO)
3. Update TranslateVocabularyResponse

### Phase 3: Integration & Testing
1. Integrate with VocabularyController
2. Add unit tests
3. Add integration tests
4. Performance testing

---

## Phrasal Verbs Handling (Context-Aware)

### Problem Statement

**User Scenarios:**

1. **Phrasal verb with particle click:**
   - User reads: "I got off the bus"
   - User clicks: **"off"**
   - Expected: "get off" = "xuống xe" (not "off" = "tắt")

2. **Phrasal verb with inflected verb click:**
   - User reads: "I looked up the word"
   - User clicks: **"looked"** (V-ed form)
   - Expected: "look up" = "tra cứu" (not "looked" alone)

3. **Inflected verb alone:**
   - User reads: "I got a book"
   - User clicks: **"got"** (V2 form)
   - Expected: "got" = "lấy, nhận" (lemmatize to "get")

**Challenges:**
- User can click ANY word (verb, particle, inflected form)
- Need to detect phrasal verbs from inflected forms ("got off" → "get off")
- Need to lemmatize verbs when no phrasal verb exists ("looked" → "look")

### Solution: Phrasal Verb Detection + Lemmatization + Fallback

**Validated Approach** (tested with Dictionary API + Simplemma):

1. **Lemmatize** clicked word using Simplemma (handles V2/V3/V-ed/V-ing)
2. **Generate phrasal verb candidates** (lemmatized verb + particle combinations)
3. **Try Dictionary API** with all candidates in priority order
4. **Return first successful match**

**Why Simplemma?**
- ✓ Pure Python, no dependencies (67MB package)
- ✓ Dictionary-based lookup (no ML model needed)
- ✓ Fast and lightweight for AWS Lambda
- ✓ Handles irregular verbs: "got" → "get", "went" → "go", "better" → "good"
- ✓ Works without POS tagging

### Implementation Strategy

#### Step 1: Lemmatize Using Simplemma

```python
import simplemma

def lemmatize_word(word: str) -> list[str]:
    """
    Lemmatize word using Simplemma.
    
    Args:
        word: Word to lemmatize
    
    Returns:
        List of candidates [original, lemma] (if different)
    """
    word_lower = word.lower()
    lemma = simplemma.lemmatize(word_lower, lang='en')
    
    # Return both original and lemma
    if lemma != word_lower:
        return [word_lower, lemma]
    return [word_lower]
```

#### Step 2: Generate Phrasal Verb Candidates

```python
PARTICLES = [
    "up", "down", "off", "on", "out", "in",
    "away", "back", "over", "through", "around",
    "along", "by", "into", "onto", "upon"
]

def find_phrasal_verb_candidates(word: str, context: str) -> list[str]:
    """
    Find phrasal verb candidates with lemmatization.
    
    Args:
        word: Word user clicked (could be verb OR particle, inflected OR base)
        context: Full sentence
    
    Returns:
        List of candidates to try (ordered by priority)
    """
    words = context.lower().split()
    
    try:
        idx = words.index(word.lower())
    except ValueError:
        return lemmatize_word(word)
    
    candidates = []
    
    # Get lemmas for clicked word
    word_lemmas = lemmatize_word(word)
    
    # Case 1: User clicked VERB → check next word
    # Example: "got" in "I got off" → try ["got off", "get off"]
    if idx + 1 < len(words):
        next_word = words[idx + 1]
        if next_word in PARTICLES:
            for lemma in word_lemmas:
                candidates.append(f"{lemma} {next_word}")
    
    # Case 2: User clicked PARTICLE → check previous word
    # Example: "off" in "I got off" → try ["got off", "get off"]
    if idx > 0 and word.lower() in PARTICLES:
        prev_word = words[idx - 1]
        prev_lemmas = lemmatize_word(prev_word)
        for lemma in prev_lemmas:
            candidates.append(f"{lemma} {word}")
    
    # Fallback: standalone word lemmas
    candidates.extend(word_lemmas)
    
    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique.append(c)
    
    return unique
```

#### Step 3: Try Dictionary API with Fallback

```python
def get_word_definition(self, word: str, context: Optional[str] = None) -> Vocabulary:
    """
    Fetch word definition with phrasal verb detection and lemmatization.
    
    Args:
        word: Word user clicked (any form: base, V2, V3, V-ed, V-ing)
        context: Sentence containing the word
    
    Returns:
        Vocabulary for the detected word/phrase
    """
    # Generate candidates with lemmatization
    if context:
        candidates = find_phrasal_verb_candidates(word, context)
    else:
        candidates = lemmatize_word(word)
    
    # Try each candidate in order
    last_error = None
    for candidate in candidates:
        try:
            return self._fetch_from_api(candidate)
        except WordNotFoundError as e:
            last_error = e
            continue  # Try next candidate
    
    # All candidates failed
    raise last_error
```

### API Request Flow (Validated with Simplemma)

**Example 1: User clicks "off" in "I got off the bus"**
```
Input: word="off", context="I got off the bus"
  ↓
Lemmatize: "off" → ["off"] (particle, no lemma)
Detect phrasal verb: prev_word="got" → lemmatize → ["got", "get"]
  ↓
Generate candidates: ["got off", "get off", "off"]
  ↓
Try #1: GET /entries/en/got%20off → 404 (not in API)
Try #2: GET /entries/en/get%20off → 200 OK ✓
  ↓
Return: "get off" = "xuống xe"
```

**Example 2: User clicks "looked" in "I looked up the word"**
```
Input: word="looked", context="I looked up the word"
  ↓
Lemmatize: "looked" → ["looked", "look"]
Detect phrasal verb: next_word="up" (particle)
  ↓
Generate candidates: ["looked up", "look up", "looked", "look"]
  ↓
Try #1: GET /entries/en/looked%20up → 404 (not in API)
Try #2: GET /entries/en/look%20up → 200 OK ✓
  ↓
Return: "look up" = "tra cứu"
```

**Example 3: User clicks "got" in "I got a book" (no phrasal verb)**
```
Input: word="got", context="I got a book"
  ↓
Lemmatize: "got" → ["got", "get"]
Check next word: "a" (not a particle)
  ↓
Generate candidates: ["got", "get"]
  ↓
Try #1: GET /entries/en/got → 200 OK ✓
  ↓
Return: "got" = "lấy, nhận"
```

**Example 4: User clicks "running" alone**
```
Input: word="running", context="I am running fast"
  ↓
Lemmatize: "running" → ["running", "run"]
Check next word: "fast" (not a particle)
  ↓
Generate candidates: ["running", "run"]
  ↓
Try #1: GET /entries/en/running → 200 OK ✓
  ↓
Return: "running" = "chạy"
```

### Updated Request DTO

```python
class TranslateVocabularyCommand(BaseDTO):
    word: str = Field(min_length=1, max_length=100)
    context: Optional[str] = Field(default=None, max_length=500)  # NEW
```

**API Request Example:**
```json
{
  "word": "off",
  "context": "I get off the bus"
}
```

### Cache Key Strategy

Cache each successful lookup separately:
- `vocabulary:definition:get off` (phrasal verb)
- `vocabulary:definition:off` (particle alone)
- `vocabulary:definition:get` (base verb)

This allows fast lookup for both phrasal verbs and individual words.

### Validation Results

**Tested with Dictionary API + Simplemma:**
- ✓ "got off" (V2 + particle) → "get off" (definition found)
- ✓ "looked up" (V-ed + particle) → "look up" (definition found)
- ✓ "got up" (V2 + particle) → "get up" (definition found)
- ✓ Click on particle "off" → detects "get off"
- ✓ Click on particle "up" → detects "look up"
- ✓ "got" alone → "got" (definition found, fallback to "get" if needed)
- ✓ "running" alone → "running" (definition found)

**Simplemma Lemmatization Accuracy:**
- ✓ "got" → "get"
- ✓ "looked" → "look"
- ✓ "running" → "run"
- ✓ "taken" → "take"
- ✓ "better" → "good"
- ✓ "children" → "child"
- ⚠️ "went" → "wend" (minor issue, but "went" exists in Dictionary API)

**Edge Cases Handled:**
- User clicks verb → tries phrasal verb first
- User clicks particle → tries phrasal verb first
- No particle after verb → uses base word only
- Phrasal verb not in API → falls back to base word
- Inflected forms automatically lemmatized

### Dependencies

**New Dependency:**
```
simplemma==1.1.2  # Pure Python, dictionary-based lemmatization (67MB)
```

**Installation:**
```bash
pip install simplemma
```

**Lambda Layer Considerations:**
- Package size: ~67MB (acceptable for Lambda)
- No binary dependencies
- No ML models to download
- Works in Lambda without additional configuration

---

## Assumptions & Constraints

### Assumptions

1. Dictionary API is available (99.9% uptime)
2. AWS Translate is available
3. DynamoDB is available
4. Lambda has 512MB+ memory

### Constraints

1. Dictionary API rate limit: 100 requests/minute (free tier)
2. AWS Translate: 10,000 bytes per request
3. Lambda timeout: 30 seconds
4. Response time SLA: < 2000ms (95th percentile)
