# Turn-by-Turn Analysis Feature

## Overview

Formative assessment feature that provides on-demand feedback for learner's conversation turns.

## Key Features

### 1. On-Demand Analysis
- User clicks "Analyze" button after speaking
- Not automatic (user controls when to get feedback)
- Complements existing end-of-session scoring

### 2. Comprehensive Feedback
- **✅ Strengths**: What learner did well
- **⚠️ Mistakes**: Grammar, vocabulary, usage errors
- **💡 Improvements**: Suggestions for better expression
- **🎯 Overall Assessment**: Summary and encouragement

### 3. Level-Adaptive
- A1/A2: Focus on basic vocabulary and simple structures
- B1/B2: Focus on clarity and natural expressions
- C1/C2: Focus on precision, style, and native-like usage

### 4. Bilingual Output
- Vietnamese markdown for native speakers
- English markdown for practice
- Frontend renders with any markdown library

### 5. Long-Term Memory
- Stores mistakes in AgentCore Memory
- AI remembers patterns across sessions
- Personalized guidance based on history
- 365-day retention

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    User Interface                         │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │   Speak    │  │    Hint    │  │  Analyze   │ ← NEW  │
│  └────────────┘  └────────────┘  └────────────┘        │
└──────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────┐
│  POST /sessions/{id}/turns/{index}/analyze               │
│  ┌────────────────────────────────────────────────────┐ │
│  │  analyze_turn_handler.py                           │ │
│  │  ├─ Verify session ownership                       │ │
│  │  ├─ Get learner turn + AI response                 │ │
│  │  └─ Call ConversationAnalyzer                      │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│  ConversationAnalyzer (domain/services)                  │
│  ┌────────────────────────────────────────────────────┐ │
│  │  ├─ Build analysis prompt (level-adaptive)         │ │
│  │  ├─ Call Bedrock Nova Micro                        │ │
│  │  ├─ Parse JSON response                            │ │
│  │  └─ Format as bilingual markdown                   │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│  LearnerMemoryClient (infrastructure/services)           │
│  ┌────────────────────────────────────────────────────┐ │
│  │  store_turn_analysis()                             │ │
│  │  ├─ Create event with mistakes + improvements      │ │
│  │  └─ Store in AgentCore Memory                      │ │
│  │                                                     │ │
│  │  get_learner_context()                             │ │
│  │  ├─ Search long-term memories                      │ │
│  │  └─ Return formatted context for prompt            │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│  AWS Bedrock AgentCore Memory                            │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Short-term: Raw events (conversation turns)       │ │
│  │  Long-term: Extracted patterns (semantic)          │ │
│  │  Retention: 365 days                               │ │
│  │  Scope: Per user (actor_id = user_id)             │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

## Integration with Conversation Flow

```
┌──────────────────────────────────────────────────────────┐
│  ConversationOrchestrator.generate_response()            │
│  ┌────────────────────────────────────────────────────┐ │
│  │  1. Route to model                                 │ │
│  │  2. Build base prompt                              │ │
│  │  3. Retrieve learner context from Memory ← NEW    │ │
│  │  4. Append context to system prompt                │ │
│  │  5. Generate response with streaming               │ │
│  │  6. Validate response                              │ │
│  │  7. Log metrics                                    │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

## Example Flow

### 1. User speaks (Turn 5)
```
User: "I go to school yesterday"
AI: "That's great! What did you do at school?"
```

### 2. User clicks "Analyze"
```
POST /sessions/abc123/turns/5/analyze
```

### 3. Response (Vietnamese)
```markdown
## ✅ Điểm mạnh
- Bạn đã dùng cấu trúc câu đơn giản và rõ ràng
- Từ vựng phù hợp với ngữ cảnh

## ⚠️ Lỗi cần sửa
- Sai thì quá khứ: "go" → "went"
- "Yesterday" cần dùng thì quá khứ đơn

## 💡 Cải thiện
- Câu đúng: "I went to school yesterday"
- Ghi nhớ: go (hiện tại) → went (quá khứ)

## 🎯 Đánh giá tổng thể
Bạn đã thể hiện ý tưởng rõ ràng! Chỉ cần chú ý thì của động từ khi nói về quá khứ. Hãy thử nói lại câu với "went" nhé!
```

### 4. Memory stores pattern
```json
{
  "user_id": "user123",
  "session_id": "abc123",
  "turn_index": 5,
  "mistakes": ["Incorrect past tense: 'go' should be 'went'"],
  "improvements": ["Use 'went' for past tense"]
}
```

### 5. Next session - AI remembers
```
System prompt: "...

## Learner History (from previous sessions)
The learner has shown these patterns in past conversations:
- Frequently confuses present and past tense (go/went)
- Needs practice with irregular past tense verbs

Use this information to provide more personalized guidance."
```

## API Endpoint

### Request
```http
POST /sessions/{session_id}/turns/{turn_index}/analyze
Authorization: Bearer <cognito-token>
```

### Response (200 OK)
```json
{
  "markdown": {
    "vi": "## ✅ Điểm mạnh\n...",
    "en": "## ✅ Strengths\n..."
  }
}
```

### Error Responses
- **401 Unauthorized**: Missing or invalid token
- **403 Forbidden**: Session doesn't belong to user
- **404 Not Found**: Session or turn not found
- **500 Internal Server Error**: Analysis failed

## Files Created

### Core Services
- `src/domain/services/conversation_analyzer.py` - LLM-based turn analysis
- `src/infrastructure/services/memory_client.py` - AgentCore Memory wrapper

### Handler
- `src/infrastructure/handlers/speaking/analyze_turn_handler.py` - API endpoint

### Documentation
- `docs/AGENTCORE_MEMORY_SETUP.md` - Memory setup guide
- `docs/TURN_ANALYSIS_FEATURE.md` - This file

### Updated Files
- `src/domain/services/conversation_orchestrator.py` - Memory integration
- `src/infrastructure/handlers/session_handler.py` - Inject memory client
- `src/infrastructure/handlers/speaking/session_handler.py` - Inject memory client
- `API_DOCUMENTATION.md` - New endpoint documentation

## Deployment Checklist

### 1. Create AgentCore Memory
```bash
# See docs/AGENTCORE_MEMORY_SETUP.md for detailed steps
python scripts/create_memory.py
```

### 2. Update SAM Template
```yaml
# template.yaml
AnalyzeTurnFunction:
  Type: AWS::Serverless::Function
  Properties:
    Handler: src.infrastructure.handlers.speaking.analyze_turn_handler.lambda_handler
    Environment:
      Variables:
        AGENTCORE_MEMORY_ID: !Ref LexiLearnerMemory
    Events:
      AnalyzeTurn:
        Type: Api
        Properties:
          Path: /sessions/{session_id}/turns/{turn_index}/analyze
          Method: POST
          Auth:
            Authorizer: CognitoAuthorizer
```

### 3. Add IAM Permissions
```yaml
# template.yaml - Add to Lambda execution role
- Effect: Allow
  Action:
    - bedrock-agentcore:CreateEvent
    - bedrock-agentcore:GetEvent
    - bedrock-agentcore:SearchLongTermMemories
    - bedrock-agentcore:ListSessions
  Resource: !Sub "arn:aws:bedrock-agentcore:${AWS::Region}:${AWS::AccountId}:memory/*"
```

### 4. Deploy
```bash
sam build
sam deploy --guided
```

### 5. Test
```bash
# Get session and turn
SESSION_ID="your-session-id"
TURN_INDEX=1
TOKEN="your-cognito-token"

# Analyze turn
curl -X POST \
  "https://your-api.execute-api.ap-southeast-1.amazonaws.com/Prod/sessions/$SESSION_ID/turns/$TURN_INDEX/analyze" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

## Testing Strategy

### Unit Tests
```python
# tests/unit/test_conversation_analyzer.py
def test_analyze_turn_returns_markdown():
    analyzer = ConversationAnalyzer(bedrock_client=mock_client)
    result = analyzer.analyze_turn(
        learner_message="I go to school yesterday",
        ai_response="That's great!",
        level="A2",
        scenario_context="Daily routine",
    )
    assert "✅" in result.markdown_vi
    assert "Strengths" in result.markdown_en
```

### Integration Tests
```python
# tests/integration/test_analyze_turn_handler.py
def test_analyze_turn_endpoint():
    event = {
        "pathParameters": {"session_id": "abc", "turn_index": "1"},
        "requestContext": {"authorizer": {"claims": {"sub": "user123"}}},
    }
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "markdown" in body
    assert "vi" in body["markdown"]
    assert "en" in body["markdown"]
```

## Monitoring

### CloudWatch Metrics
- `AnalyzeTurnInvocations`: Number of analysis requests
- `AnalyzeTurnLatency`: Time to analyze turn
- `MemoryStorageSuccess`: Successful memory writes
- `MemoryRetrievalLatency`: Time to retrieve learner context

### Alarms
- Analysis latency > 5 seconds
- Memory storage failure rate > 5%
- Analysis error rate > 1%

## Cost Estimate

### Per Analysis Request
- Bedrock Nova Micro: ~$0.0001 (500 tokens)
- Memory write: ~$0.00001
- Lambda execution: ~$0.00001
- **Total: ~$0.00012 per analysis**

### Monthly (1000 users, 10 analyses/user)
- 10,000 analyses × $0.00012 = **$1.20/month**
- Memory storage: **$0.40/month**
- **Total: ~$1.60/month**

## Future Enhancements

1. **Batch Analysis**: Analyze multiple turns at once
2. **Progress Tracking**: Show improvement over time
3. **Custom Strategies**: Add episodic memory for specific learning goals
4. **Voice Feedback**: TTS for analysis (Polly integration)
5. **Gamification**: Badges for consistent improvement

## References

- [Formative Assessment in Language Learning](https://www.cambridge.org/elt/blog/2019/09/16/formative-assessment/)
- [AWS Bedrock AgentCore Memory](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory.html)
- [CEFR Levels](https://www.coe.int/en/web/common-european-framework-reference-languages/level-descriptions)
