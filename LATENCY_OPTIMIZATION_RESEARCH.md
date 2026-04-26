# Latency Optimization Research - AWS Best Practices

## 🎯 Problem Statement
Hint generation and conversation analysis take 1-3 seconds, blocking WebSocket responses and degrading UX.

## 📚 AWS Best Practices Research

### 1. **Bedrock Latency Optimization** ✅
**Source**: https://docs.aws.amazon.com/bedrock/latest/userguide/latency-optimized-inference.html

**Key Finding**: Bedrock offers **latency-optimized inference** for select models
- **Feature**: Set `performanceConfig.latency = "optimized"` in API calls
- **Supported Models**: 
  - Amazon Nova Pro (us-east-1, us-east-2, us-west-2)
  - Claude 3.5 Haiku (us-east-2, us-west-2)
  - Llama 3.1 70B/405B (us-east-2, us-west-2)
- **Benefit**: Significantly reduced latency without accuracy loss
- **Fallback**: If quota exceeded, falls back to standard latency (charged at standard rate)
- **Limitation**: Llama 3.1 405B limited to 11K total tokens

**Action**: Add `performanceConfig` to `converse_stream()` calls

```python
response = self._bedrock.converse_stream(
    modelId="apac.amazon.nova-lite-v1:0",
    performanceConfig={"latency": "optimized"},  # NEW
    messages=[...],
    ...
)
```

---

### 2. **Prompt Caching** ✅
**Source**: https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html

**Key Finding**: Cache static prompt components to reduce latency + costs
- **How it works**: Define cache checkpoints for static content (system prompts, few-shot examples)
- **Supported Models**: Claude 3.7 Sonnet, Claude Opus 4, Amazon Nova (automatic)
- **Benefits**:
  - Reduced latency (skip recomputation)
  - Reduced token costs (cached tokens charged at lower rate)
  - 5-minute TTL (resets on cache hit)
- **Minimum tokens**: Claude requires 1,024 tokens per checkpoint
- **Amazon Nova**: Automatic prompt caching for all text prompts (no config needed)

**For Nova Lite (our model)**:
- Automatic caching enabled by default
- No explicit configuration required
- Cache hits when prompts start with repetitive parts

**Action**: Structure prompts to maximize cache hits
- System prompt (static) → cached automatically
- Few-shot examples (static) → cached automatically
- User input (dynamic) → not cached

---

### 3. **Lambda Async Processing** ✅
**Source**: https://docs.aws.amazon.com/lambda/latest/dg/lambda-concurrency.html

**Key Finding**: Use async invocation for non-blocking operations
- **Pattern**: Invoke Lambda asynchronously via SQS/EventBridge
- **Benefit**: Return immediately to client, process in background
- **Concurrency**: Default 1,000 concurrent executions per account
- **Scaling**: 1,000 new environments per 10 seconds

**For WebSocket use case**:
- Send hint/analyzer request to SQS
- Return "Generating..." immediately to client
- Lambda processes from queue, sends result via WebSocket callback
- Client receives result when ready (no blocking)

---

### 4. **WebSocket Streaming** ✅
**Source**: AWS Lambda + API Gateway WebSocket documentation

**Key Finding**: Stream responses to client in real-time
- **Pattern**: Send partial results as they arrive
- **Benefit**: Perceived latency reduction (user sees progress)
- **Implementation**: Send multiple WebSocket messages instead of one

**For hint/analyzer**:
- Send "Generating hint..." immediately
- Stream hint chunks as Bedrock returns them
- Send "Done" when complete

---

### 5. **Bedrock Streaming Best Practices** ✅
**Source**: https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-runtime_example_bedrock-runtime_ConverseStream_MetaLlama_section.html

**Key Finding**: Use `converse_stream()` for real-time response processing
- **API**: `converse_stream()` returns iterator of events
- **Pattern**: Process events as they arrive (don't buffer entire response)
- **Benefit**: Lower latency perception + memory efficiency

**Current Implementation**: Already using streaming ✅
- Collects streamed response in loop
- Extracts tool use data incrementally

**Optimization**: Stream to client instead of buffering

---

## 🔍 Current Bottlenecks vs AWS Best Practices

| Bottleneck | Current | AWS Best Practice | Gap |
|-----------|---------|-------------------|-----|
| **Latency Optimization** | Not enabled | Use `performanceConfig.latency="optimized"` | ❌ Missing |
| **Prompt Caching** | No caching | Automatic for Nova | ✅ Already enabled |
| **Async Processing** | Synchronous (blocking) | Use SQS + Lambda async | ❌ Missing |
| **Streaming to Client** | Buffered response | Stream chunks in real-time | ❌ Missing |
| **Concurrency** | Single thread | Use Lambda concurrency | ❌ Missing |
| **Temperature** | 0 (greedy) | 0 for structured output | ✅ Correct |
| **Token Optimization** | Few-shot examples | Prompt caching | ✅ Automatic |

---

## 💡 Optimization Strategy (Priority Order)

### **Phase 1: Quick Wins (1-2 hours)**
1. **Enable Bedrock Latency Optimization** (30 min)
   - Add `performanceConfig` to `converse_stream()` calls
   - Expected improvement: 20-30% latency reduction
   - Risk: Low (fallback to standard if quota exceeded)

2. **Stream Responses to Client** (1 hour)
   - Send partial hints/analysis as they arrive
   - Expected improvement: Perceived latency 50%+ (user sees progress)
   - Risk: Low (requires WebSocket message batching)

### **Phase 2: Medium Effort (2-4 hours)**
3. **Async Hint/Analyzer via SQS** (2-3 hours)
   - Move hint/analyzer to background Lambda
   - Return immediately to client
   - Send result via WebSocket callback
   - Expected improvement: 1-3s latency elimination
   - Risk: Medium (requires SQS + callback pattern)

### **Phase 3: Advanced (4+ hours)**
4. **Prompt Caching Optimization** (1-2 hours)
   - Explicit cache checkpoints for system prompts
   - Monitor cache hit rates
   - Expected improvement: 10-20% latency + cost reduction
   - Risk: Low (Nova has automatic caching)

5. **Lambda Provisioned Concurrency** (1-2 hours)
   - Pre-warm Lambda environments
   - Expected improvement: Cold start elimination
   - Risk: Medium (additional cost)

---

## 📊 Expected Latency Improvements

### Current State
- Hint generation: 1-3s (Bedrock API + streaming)
- Analysis: 1-3s (Bedrock API + streaming)
- Total blocking time: 2-6s

### After Phase 1 (Latency Optimization + Streaming)
- Bedrock latency: 0.7-2s (20-30% reduction)
- Perceived latency: 0.2-0.5s (streaming shows progress)
- **Total improvement: 60-70%**

### After Phase 2 (Async Processing)
- Blocking time: 0s (returns immediately)
- Background processing: 1-3s (non-blocking)
- **Total improvement: 100% (no blocking)**

### After Phase 3 (Full Optimization)
- Bedrock latency: 0.5-1.5s (prompt caching + latency optimization)
- Perceived latency: 0.1-0.3s (streaming)
- Background processing: 0.5-1.5s (provisioned concurrency)
- **Total improvement: 80-90% latency reduction**

---

## 🛠 Implementation Plan

### Phase 1: Latency Optimization + Streaming

**File 1: `structured_hint_generator.py`**
```python
# Add performanceConfig
response = self._bedrock.converse_stream(
    modelId="apac.amazon.nova-lite-v1:0",
    performanceConfig={"latency": "optimized"},  # NEW
    system=[{"text": system_prompt}],
    messages=[{"role": "user", "content": [{"text": user_prompt}]}],
    toolConfig=tool_config,
    inferenceConfig={
        "maxTokens": 500,
        "temperature": 0,
    },
)
```

**File 2: `conversation_analyzer.py`**
```python
# Same change as above
response = self.bedrock_client.converse_stream(
    modelId=self._model_id,
    performanceConfig={"latency": "optimized"},  # NEW
    system=[{"text": system_prompt}],
    messages=[{"role": "user", "content": [{"text": user_prompt}]}],
    toolConfig=tool_config,
    inferenceConfig={
        "maxTokens": 500,
        "temperature": 0,
    },
)
```

**File 3: `websocket_handler.py`**
```python
# Stream hint chunks to client instead of buffering
def use_hint(self, session_id: str, connection_id: str) -> dict[str, Any]:
    # ... existing code ...
    
    # Send "Generating..." immediately
    self.send_message({
        "event": "HINT_TEXT",
        "hint": {"markdown": {"vi": "💡 Đang tạo gợi ý...", "en": "💡 Generating hint..."}},
        "isStreaming": True,
        "isDone": False
    })
    
    # Generate hint (streaming)
    hint = generator.generate(session, last_ai_turn, turn_history)
    
    # Send complete hint
    self.send_message({
        "event": "HINT_TEXT",
        "hint": hint.to_dict(),
        "isStreaming": False,
        "isDone": True
    })
```

---

## 📋 Checklist

- [ ] Phase 1: Add `performanceConfig` to hint generator
- [ ] Phase 1: Add `performanceConfig` to analyzer
- [ ] Phase 1: Implement streaming to WebSocket client
- [ ] Phase 1: Test latency improvements
- [ ] Phase 2: Design async SQS pattern
- [ ] Phase 2: Implement background Lambda for hint/analyzer
- [ ] Phase 2: Add WebSocket callback mechanism
- [ ] Phase 2: Test end-to-end async flow
- [ ] Phase 3: Monitor prompt caching metrics
- [ ] Phase 3: Configure provisioned concurrency

---

## 🔗 References

1. **Bedrock Latency Optimization**: https://docs.aws.amazon.com/bedrock/latest/userguide/latency-optimized-inference.html
2. **Prompt Caching**: https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html
3. **Lambda Concurrency**: https://docs.aws.amazon.com/lambda/latest/dg/lambda-concurrency.html
4. **Bedrock Streaming**: https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-runtime_example_bedrock-runtime_ConverseStream_MetaLlama_section.html
5. **Cost Optimization**: https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/gencost03-bp03.html
