# Flashcard API Migration Guide v2.0

**Date:** 2026-04-26  
**Status:** ✅ COMPLETED  
**Breaking Changes:** YES

---

## 🎯 Summary

Flashcard API has been updated to improve consistency with Vocabulary API and remove unused fields.

### **Key Changes:**
1. ✅ `vocab` → `word` (renamed for consistency)
2. ✅ `source_api` removed (unused field)
3. ✅ Validation messages improved

---

## 📋 Migration Checklist

### **For Frontend Developers:**

- [ ] Update flashcard creation payload: `vocab` → `word`
- [ ] Remove `source_api` from payload (if used)
- [ ] Update error handling for new validation messages
- [ ] Test flashcard creation flow
- [ ] Test flashcard list/review flows (no changes)

### **For Backend Developers:**

- [x] Update DTOs
- [x] Update mappers
- [x] Update use cases
- [x] Update tests
- [x] Update API documentation

---

## 🔄 API Changes

### **Before (v1.x):**

```json
POST /flashcards
{
  "vocab": "run",
  "vocab_type": "verb",
  "translation_vi": "chạy",
  "phonetic": "/rʌn/",
  "audio_url": "https://example.com/audio.mp3",
  "example_sentence": "I run every morning.",
  "source_api": "internal"  // ❌ Removed
}
```

### **After (v2.0):**

```json
POST /flashcards
{
  "word": "run",  // ✅ Renamed from "vocab"
  "vocab_type": "verb",
  "translation_vi": "chạy",
  "phonetic": "/rʌn/",
  "audio_url": "https://example.com/audio.mp3",
  "example_sentence": "I run every morning."
  // "source_api" removed
}
```

---

## 📝 Validation Changes

### **Error Messages Updated:**

**Before:**
```
"Vocabulary should only contain letters, spaces, or hyphens"
"Vocabulary too long (max 50 characters)"
```

**After:**
```
"Word should only contain letters, spaces, hyphens (-), apostrophes ('), or dots (.)"
"Word too long (max 50 characters)"
```

### **New Validations:**

1. **Sentence detection:**
   - Rejects: `"Hello! I'm Sarah."`
   - Error: `"Word should not contain sentence punctuation (!?;:,)"`

2. **Length check:**
   - Max: 50 characters
   - Error: `"Word too long (max 50 characters). Please enter a single word or short phrase."`

3. **Multiple sentences:**
   - Rejects: `"Hello. How are you."`
   - Error: `"Word should be a single word or phrase, not multiple sentences."`

---

## 🛠 Frontend Migration Steps

### **Step 1: Update Vocabulary → Flashcard Flow**

**Before:**
```typescript
// After calling /vocabulary/translate
const translateResponse = await api.post('/vocabulary/translate', {
  word: 'run'
});

const flashcardPayload = {
  vocab: translateResponse.data.word,  // ❌ Old
  vocab_type: translateResponse.data.definitions[0].part_of_speech,
  translation_vi: translateResponse.data.translation_vi,
  phonetic: translateResponse.data.phonetic,
  audio_url: translateResponse.data.audio_url,
  example_sentence: translateResponse.data.definitions[0].example_en
};
```

**After:**
```typescript
// After calling /vocabulary/translate
const translateResponse = await api.post('/vocabulary/translate', {
  word: 'run'
});

const flashcardPayload = {
  word: translateResponse.data.word,  // ✅ New
  vocab_type: translateResponse.data.definitions[0].part_of_speech,
  translation_vi: translateResponse.data.translation_vi,
  phonetic: translateResponse.data.phonetic,
  audio_url: translateResponse.data.audio_url,
  example_sentence: translateResponse.data.definitions[0].example_en
};
```

### **Step 2: Update Error Handling**

```typescript
try {
  await api.post('/flashcards', flashcardPayload);
} catch (error) {
  if (error.response?.data?.error === 'VALIDATION_ERROR') {
    const message = error.response.data.message;
    
    // Handle new error messages
    if (message.includes('Word too long')) {
      showError('Please enter a shorter word or phrase (max 50 characters)');
    } else if (message.includes('sentence punctuation')) {
      showError('Please enter only the word, not a full sentence');
    } else {
      showError(message);
    }
  }
}
```

---

## 🧪 Testing

### **Test Cases:**

1. **Valid word:**
   ```json
   {"word": "run", "vocab_type": "verb", "translation_vi": "chạy"}
   ```
   Expected: ✅ 201 Created

2. **Valid phrase:**
   ```json
   {"word": "phrasal verb", "vocab_type": "phrase", "translation_vi": "cụm động từ"}
   ```
   Expected: ✅ 201 Created

3. **Valid contraction:**
   ```json
   {"word": "don't", "vocab_type": "verb", "translation_vi": "không"}
   ```
   Expected: ✅ 201 Created

4. **Invalid: Full sentence:**
   ```json
   {"word": "Hello! I'm Sarah.", "vocab_type": "phrase", "translation_vi": "..."}
   ```
   Expected: ❌ 400 Bad Request
   Error: `"Word should not contain sentence punctuation"`

5. **Invalid: Too long:**
   ```json
   {"word": "This is a very long sentence that exceeds fifty characters", ...}
   ```
   Expected: ❌ 400 Bad Request
   Error: `"Word too long (max 50 characters)"`

---

## 📊 Impact Analysis

### **Breaking Changes:**
- ✅ Field rename: `vocab` → `word`
- ✅ Field removed: `source_api`

### **Non-Breaking Changes:**
- ✅ Validation improvements (better error messages)
- ✅ Response format unchanged

### **Affected Endpoints:**
- `POST /flashcards` (create) - **BREAKING**
- `GET /flashcards` (list) - No change
- `GET /flashcards/{id}` (get) - No change
- `POST /flashcards/{id}/review` (review) - No change

---

## 🚀 Deployment Plan

### **Phase 1: Backend Deployment**
1. ✅ Deploy backend with new API
2. ✅ Monitor error logs for validation issues
3. ✅ Verify tests pass

### **Phase 2: Frontend Migration**
1. Update frontend code
2. Test in staging
3. Deploy to production

### **Phase 3: Monitoring**
1. Monitor API error rates
2. Check for validation errors
3. Verify flashcard creation success rate

---

## 📞 Support

### **Questions?**
- Check API_DOCUMENTATION.md for latest API spec
- Run tests: `pytest tests/integration/test_flashcard.py -v`
- Check logs for validation errors

### **Issues?**
- Validation error: Check error message for specific issue
- 400 Bad Request: Verify payload matches new format
- 500 Internal Error: Check backend logs

---

## ✅ Checklist for Go-Live

- [x] Backend code updated
- [x] Tests updated and passing
- [x] API documentation updated
- [x] Migration guide created
- [ ] Frontend code updated
- [ ] Staging tested
- [ ] Production deployed
- [ ] Monitoring in place

---

**Version:** 2.0  
**Last Updated:** 2026-04-26  
**Status:** Ready for frontend migration
