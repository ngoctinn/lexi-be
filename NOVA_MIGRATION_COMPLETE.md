# Nova Migration Complete - Summary

**Date**: 2026-04-25  
**Status**: ✅ COMPLETE

---

## 🎯 Objective

Migrate toàn bộ hệ thống sang **Amazon Nova Micro** (`amazon.nova-micro-v1:0`), loại bỏ hoàn toàn Anthropic Claude models.

---

## ⚠️ Issues Found

### 1. websocket_handler.py - use_hint() method (Line 377)
**Before**:
```python
modelId="anthropic.claude-3-haiku-20240307-v1:0"
body = dumps({
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 60,
    "messages": [{"role": "user", "content": hint_prompt}],
})
```

**Impact**: User click "hint" → 400 ValidationException

### 2. bedrock_scorer_adapter.py - score_session() method (Line 110)
**Before**:
```python
modelId="anthropic.claude-3-5-sonnet-20241022"
body = dumps({
    "anthropic_version": "bedrock-2023-05-31",
    "system": system_content,
    "messages": [{"role": "user", "content": "Please score..."}],
})
```

**Impact**: Complete session → scoring fail → no feedback

---

## ✅ Solutions Implemented

### Nova Request Format (AWS Official)
Per [AWS Nova Documentation](https://docs.aws.amazon.com/nova/latest/userguide/complete-request-schema.html):

```json
{
  "system": [{"text": "string"}],
  "messages": [
    {
      "role": "user",
      "content": [{"text": "string"}]
    }
  ],
  "inferenceConfig": {
    "maxTokens": int,
    "temperature": float
  }
}
```

### Nova Response Format
```json
{
  "output": {
    "message": {
      "content": [{"text": "response text"}],
      "role": "assistant"
    }
  },
  "stopReason": "end_turn",
  "usage": {
    "inputTokens": 71,
    "outputTokens": 17,
    "totalTokens": 88
  }
}
```

---

## 📝 Changes Made

### 1. websocket_handler.py
**File**: `src/infrastructure/handlers/websocket_handler.py`  
**Method**: `_generate_contextual_hint()`  
**Lines**: 355-390

**Changes**:
- ✅ Model ID: `anthropic.claude-3-haiku-20240307-v1:0` → `amazon.nova-micro-v1:0`
- ✅ Request format: Anthropic → Nova
- ✅ Response parsing: `result["content"][0]["text"]` → `result["output"]["message"]["content"][0]["text"]`
- ✅ Added error logging

### 2. bedrock_scorer_adapter.py
**File**: `src/infrastructure/services/bedrock_scorer_adapter.py`  
**Method**: `score()`  
**Lines**: 95-125

**Changes**:
- ✅ Model ID: `anthropic.claude-3-5-sonnet-20241022` → `amazon.nova-micro-v1:0`
- ✅ Request format: Anthropic → Nova
- ✅ Response parsing: `response_body["content"][0]["text"]` → `response_body["output"]["message"]["content"][0]["text"]`
- ✅ Removed prompt caching (Anthropic-specific feature)
- ✅ Updated docstrings

---

## 🧪 Verification

### Test Script
**File**: `scripts/test_nova_hint_scoring.py`

**Test 1: Hint Generation**
```
✅ PASS
Model: amazon.nova-micro-v1:0
Input: 71 tokens
Output: 17 tokens
Response: "You could say: 'I'd like to order some food, please.'"
```

**Test 2: Scoring**
```
✅ PASS
Model: amazon.nova-micro-v1:0
Input: 200+ tokens
Output: 150+ tokens
Scores: Fluency=85, Pronunciation=90, Grammar=95, Vocabulary=85, Overall=88
Feedback: Vietnamese feedback generated correctly
```

---

## 📊 Key Differences: Anthropic vs Nova

| Feature | Anthropic Claude | Amazon Nova |
|---------|------------------|-------------|
| **Model ID** | `anthropic.claude-3-*` | `amazon.nova-micro-v1:0` |
| **Request Format** | `anthropic_version` required | No version field |
| **System Prompt** | `"system": "string"` or list with cache | `"system": [{"text": "string"}]` |
| **Messages Content** | `"content": "string"` | `"content": [{"text": "string"}]` |
| **Parameters** | Top-level (`max_tokens`, `temperature`) | `inferenceConfig` object |
| **Response Path** | `["content"][0]["text"]` | `["output"]["message"]["content"][0]["text"]` |
| **Prompt Caching** | ✅ Supported (ephemeral cache) | ❌ Not supported |
| **Cost** | $0.25/1M input (Haiku) | $0.03/1M input (Micro) |

---

## 💰 Cost Impact

**Before** (mixed models):
- Hint: Claude Haiku ($0.25/1M input)
- Scoring: Claude Sonnet ($3.00/1M input)
- Main conversation: Nova Micro ($0.03/1M input)

**After** (Nova Micro only):
- Hint: Nova Micro ($0.03/1M input) → **88% cheaper**
- Scoring: Nova Micro ($0.03/1M input) → **99% cheaper**
- Main conversation: Nova Micro ($0.03/1M input) → unchanged

**Estimated savings**: ~95% on hint + scoring operations

---

## 🚀 Deployment Checklist

- [x] Fix websocket_handler.py
- [x] Fix bedrock_scorer_adapter.py
- [x] Update docstrings
- [x] Create test script
- [x] Verify format with AWS docs
- [x] Run local tests (✅ PASS)
- [ ] Deploy to AWS
- [ ] Test in staging
- [ ] Monitor CloudWatch logs
- [ ] Verify production metrics

---

## 📚 References

- [Amazon Nova Complete Request Schema](https://docs.aws.amazon.com/nova/latest/userguide/complete-request-schema.html)
- [Amazon Nova Model Parameters](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-nova.html)
- [Bedrock InvokeModel API](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_InvokeModel.html)

---

## ✅ Verification Commands

```bash
# Run test script
python3 scripts/test_nova_hint_scoring.py

# Expected output:
# ✅ Hint Generation: PASS
# ✅ Scoring: PASS
# 🎉 All tests passed!

# Deploy
sam build
sam deploy

# Monitor logs
sam logs -n SpeakingWebSocketFunction --tail
sam logs -n SpeakingSessionFunction --tail
```

---

## 🎉 Result

**Status**: ✅ Migration complete  
**Models used**: Amazon Nova Micro only  
**Anthropic models**: Completely removed  
**Tests**: All passing  
**Cost savings**: ~95% on hint + scoring

**Next steps**: Deploy to AWS and monitor production metrics.
