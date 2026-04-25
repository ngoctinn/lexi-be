# Spec: Vocabulary Enrichment with Dictionary API

**Status**: In Progress  
**Priority**: High  
**Scope**: Backend API Enhancement  
**Owner**: Senior Full-stack Engineer

---

## 1. Business Objective

Cung cấp dữ liệu từ vựng **đầy đủ** cho học viên:
- Định nghĩa (definitions)
- Phát âm (phonetic + audio)
- Loại từ (part of speech)
- Ví dụ ngữ cảnh (examples)
- Từ đồng nghĩa (synonyms)
- Bản dịch VI chính xác

**Kết quả mong đợi**: Học viên hiểu từ sâu hơn, phát âm đúng, dùng từ chính xác.

---

## 2. Technical Objectives

### 2.1 Architecture
```
User Request
    ↓
TranslateVocabularyUseCase
    ↓
DictionaryService (Dictionary API)  ← Lấy dữ liệu EN
    ↓
TranslationService (AWS Translate)  ← Dịch VI
    ↓
Response (EN + VI + Metadata)
```

### 2.2 Data Flow
```
Input: { word: "hello" }

Step 1: DictionaryService.get_word_data("hello")
  → { definitions, phonetic, examples, synonyms, ... }

Step 2: TranslationService.translate_en_to_vi(word + examples)
  → { translation_vi, examples_vi, ... }

Step 3: Merge & Return
  → { word, translation_vi, phonetic, definitions, examples, ... }
```

### 2.3 External APIs
- **Dictionary API**: https://dictionaryapi.dev/
  - Endpoint: `GET /api/v2/entries/en/{word}`
  - Rate limit: Unlimited (free)
  - Response: Definitions, phonetic, examples, synonyms, antonyms

- **AWS Translate**: Existing
  - Dịch từ chính + ví dụ sang VI

---

## 3. Design Decisions

### 3.1 Why Dictionary API?
| Tiêu chí | Dictionary API | AWS Translate | Bedrock |
|----------|---|---|---|
| Dữ liệu ngôn ngữ học | ✅ Đầy đủ | ❌ Chỉ dịch | ⚠️ Chậm |
| Phát âm | ✅ Có | ❌ Không | ❌ Không |
| Chi phí | ✅ Miễn phí | ⚠️ $15/M | ❌ Đắt |
| Tốc độ | ✅ Nhanh | ✅ Nhanh | ❌ Chậm |

### 3.2 Caching Strategy
- **Cache Dictionary API**: 24h (từ vựng ít thay đổi)
- **Cache AWS Translate**: 24h (bản dịch ổn định)
- **Storage**: DynamoDB (existing)

### 3.3 Error Handling
```
Dictionary API unavailable
  → Fallback: AWS Translate only
  
AWS Translate unavailable
  → Fallback: Dictionary API (EN only)
  
Both unavailable
  → Return cached data or error
```

---

## 4. API Response Design

### 4.1 Current Response
```json
{
  "word": "hello",
  "translation_vi": "xin chào"
}
```

### 4.2 New Response (Enhanced)
```json
{
  "word": "hello",
  "translation_vi": "xin chào",
  "phonetic": "həˈloʊ",
  "phonetic_text": "huh-LOH",
  "audio_url": "https://...",
  "part_of_speech": "interjection",
  "definitions": [
    {
      "definition": "used as a greeting or to begin a conversation",
      "definition_vi": "được dùng để chào hỏi hoặc bắt đầu cuộc trò chuyện",
      "example": "hello, how are you?",
      "example_vi": "xin chào, bạn khỏe không?"
    }
  ],
  "synonyms": ["hi", "hey", "greetings"],
  "synonyms_vi": ["chào", "này", "lời chào"],
  "antonyms": ["goodbye"],
  "antonyms_vi": ["tạm biệt"]
}
```

### 4.3 Backward Compatibility
- Old clients: Chỉ dùng `word` + `translation_vi`
- New clients: Dùng toàn bộ fields

---

## 5. Implementation Tasks

### Task 1: Create DictionaryService Port
**File**: `src/application/service_ports/dictionary_service.py`
**Scope**: Define interface for Dictionary API

### Task 2: Create DictionaryService Adapter
**File**: `src/infrastructure/services/dictionary_api_service.py`
**Scope**: Implement Dictionary API client + caching

### Task 3: Update TranslateVocabularyUseCase
**File**: `src/application/use_cases/vocabulary_use_cases.py`
**Scope**: Integrate DictionaryService + TranslationService

### Task 4: Update DTOs
**File**: `src/application/dtos/vocabulary_dtos.py`
**Scope**: Add new fields to response

### Task 5: Update API Handler
**File**: `src/interfaces/handlers/vocabulary_handler.py`
**Scope**: Return new response format

### Task 6: Add Tests
**File**: `tests/test_vocabulary_enrichment.py`
**Scope**: Unit + integration tests

### Task 7: Update API Documentation
**File**: `API_DOCUMENTATION.md`
**Scope**: Document new response format

---

## 6. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Dictionary API down | No word data | Fallback to AWS Translate |
| Rate limit exceeded | Slow response | Implement caching (24h) |
| Translation cost ↑ | Budget | Cache translations, batch requests |
| Breaking change | Old clients fail | Backward compatible response |

---

## 7. Success Criteria

- ✅ Dictionary API integrated
- ✅ AWS Translate for VI translation
- ✅ Response includes: phonetic, definitions, examples, synonyms
- ✅ Caching implemented (24h)
- ✅ Error handling (fallback)
- ✅ Backward compatible
- ✅ Tests pass (>90% coverage)
- ✅ API docs updated

---

## 8. Timeline

| Task | Duration | Status |
|------|----------|--------|
| Design & Spec | ✅ Done | Complete |
| DictionaryService | 1h | TODO |
| TranslateVocabularyUseCase | 1h | TODO |
| DTOs & Handler | 30m | TODO |
| Tests | 1h | TODO |
| Documentation | 30m | TODO |
| **Total** | **~4.5h** | **TODO** |

---

## 9. References

- Dictionary API Docs: https://dictionaryapi.dev/
- AWS Translate: https://docs.aws.amazon.com/translate/
- Current Implementation: `src/infrastructure/services/aws_translate_service.py`
