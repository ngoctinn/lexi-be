# Bedrock Streaming Fix - Summary

## 🔍 Root Causes Found & Fixed

### Issue #1: Missing IAM Permission ❌ → ✅
**Problem**: Lambda functions had `bedrock:InvokeModel` but NOT `bedrock:InvokeModelWithResponseStream`
- Code calls streaming API but IAM policy only allowed non-streaming
- Result: 403 Forbidden → fallback response returned

**Fix**: Updated `template.yaml`
```yaml
# SpeakingSessionFunction & SpeakingWebSocketFunction
- bedrock:InvokeModel
- bedrock:InvokeModelWithResponseStream  # ← ADDED
```

### Issue #2: Wrong Request Format ❌ → ✅
**Problem**: Code sent Anthropic Claude format but model is Amazon Nova
- Sent: `{"anthropic_version": "bedrock-2023-05-31", "max_tokens": 150, ...}`
- Nova expects: `{"system": [...], "messages": [...], "inferenceConfig": {"maxTokens": 150, ...}}`

**Fix**: Updated `src/infrastructure/services/speaking_pipeline_services.py`
```python
# OLD (Anthropic format)
body = dumps({
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 150,
    "system": system_content,
    "messages": messages,
    "temperature": 0.7,
})

# NEW (Nova format)
body = dumps({
    "system": system_content,
    "messages": messages,
    "inferenceConfig": {
        "maxTokens": 150,
        "temperature": 0.7,
    }
})
```

### Issue #3: Wrong Response Parsing ❌ → ✅
**Problem**: Code looked for `content_block_delta` but Nova sends `contentBlockDelta`
- Anthropic format: `chunk["delta"]["text"]`
- Nova format: `chunk["contentBlockDelta"]["delta"]["text"]`

**Fix**: Updated response parsing
```python
# OLD (Anthropic format)
if "delta" in chunk_json and "text" in chunk_json["delta"]:
    text += chunk_json["delta"]["text"]

# NEW (Nova format)
if "contentBlockDelta" in chunk_json:
    delta = chunk_json["contentBlockDelta"].get("delta", {})
    if "text" in delta:
        text += delta["text"]
```

### Issue #4: Wrong Message Format ❌ → ✅
**Problem**: Messages had `content` as string, but Nova expects list of objects
- OLD: `{"role": "user", "content": "Hello"}`
- NEW: `{"role": "user", "content": [{"text": "Hello"}]}`

**Fix**: Updated `_build_messages_for_llm()`
```python
messages.append({
    "role": role,
    "content": [{"text": turn.content}]  # ← List of objects
})
```

### Issue #5: Wrong System Prompt Format ❌ → ✅
**Problem**: System prompt had `type` and `cache_control` fields not supported by Nova
- OLD: `[{"type": "text", "text": "...", "cache_control": {...}}]`
- NEW: `[{"text": "..."}]`

**Fix**: Updated `_build_llm_system_prompt()`
```python
# Nova format: simple list of text objects
return [
    {"text": static_prefix},
    {"text": dynamic_suffix}
]
```

---

## ✅ Verification

### AWS CLI Test
```bash
$ aws sts get-caller-identity
Account: 826229823693
User: NgocTin
```

### Bedrock Model Availability
```bash
$ aws bedrock list-foundation-models --region us-east-1 | grep nova-micro
✅ amazon.nova-micro-v1:0 available
```

### Direct Bedrock Test (Production Format)
```bash
$ python3 scripts/test_bedrock_nova_format.py
✅ Successfully called Bedrock streaming API
✅ Full response: "Hello! I'm doing well, thank you for asking. How are you today? It looks like you might be preparing for a business meeting; is that correct? If you need any help with your meeting or have any specific questions about business English, feel free to ask..."
✅ Bedrock is working correctly!
```

---

## 📋 Files Changed

1. **template.yaml**
   - Added `bedrock:InvokeModelWithResponseStream` to SpeakingSessionFunction
   - Added `bedrock:InvokeModelWithResponseStream` to SpeakingWebSocketFunction

2. **src/infrastructure/services/speaking_pipeline_services.py**
   - Fixed request format: Anthropic → Nova
   - Fixed response parsing: `content_block_delta` → `contentBlockDelta`
   - Fixed message format: string → list of objects
   - Fixed system prompt format: removed unsupported fields

3. **scripts/test_bedrock_direct.py** (new)
   - Direct Bedrock streaming test script
   - Verifies credentials and permissions work

4. **scripts/test_bedrock_nova_format.py** (new)
   - Test with exact Nova format from production code
   - Verifies complete flow works

---

## 🚀 Next Steps

1. **Deploy**: `sam deploy --guided` (or use existing deployment pipeline)
2. **Test**: Call `/sessions/{id}/turns` endpoint and verify real Bedrock response
3. **Monitor**: Check CloudWatch logs for any remaining issues

---

## 📚 References

- [Amazon Nova Model Parameters](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-nova.html)
- [Nova Complete Request Schema](https://docs.aws.amazon.com/nova/latest/userguide/complete-request-schema.html)
- [Bedrock InvokeModelWithResponseStream](https://docs.aws.amazon.com/boto3/latest/reference/services/bedrock-runtime/client/invoke_model_with_response_stream.html)
