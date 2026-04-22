# Design Spec — AI Conversation Pipeline

**Version:** 1.0  
**Status:** Research-based, ready for implementation  
**Ngày:** 2026-04-22

---

## 1. Tổng quan vấn đề

### 1.1 Hiện trạng (Baseline)

Luồng hội thoại hiện tại dùng:
- **STT:** Upload audio → S3 → (chưa có STT thực, chỉ nhận text từ frontend)
- **LLM:** `RuleBasedConversationGenerationService` — hardcode template, không có AI thực
- **TTS:** Amazon Polly (neural voice Joanna/Matthew) → S3 presigned URL
- **Scoring:** Rule-based heuristic (đếm từ, câu, hint count)
- **Hint:** Hardcode string từ `selected_goals[0]`
- **Off-topic handling:** Không có

### 1.2 Vấn đề cần giải quyết

| Vấn đề | Mức độ | Mô tả |
|---|---|---|
| Không có LLM thực | Critical | AI trả lời cứng nhắc, không tự nhiên |
| Không xử lý off-topic | Critical | User nói tầm bậy → AI vẫn trả lời bình thường |
| STT chưa hoạt động | High | `audio_uploaded` chỉ trả `STT_LOW_CONFIDENCE` giả |
| Hint quá đơn giản | Medium | Không có ngữ cảnh, không hữu ích |
| Scoring không chính xác | Medium | Chỉ đếm từ, không đánh giá chất lượng thực |

---

## 2. Kiến trúc đề xuất

### 2.1 Pipeline tổng thể

```
User Input (Text hoặc Audio)
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│                    LAYER 1: INPUT                        │
│  Text path: text → validate → proceed                   │
│  Audio path: S3 key → Amazon Transcribe → text          │
└─────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│                 LAYER 2: INTENT GUARD                    │
│  Amazon Comprehend: detect language, sentiment          │
│  Off-topic check: so sánh với scenario context          │
│  → ON-TOPIC: tiếp tục pipeline                         │
│  → OFF-TOPIC: redirect response (không block cứng)      │
└─────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│              LAYER 3: LLM GENERATION                     │
│  Amazon Bedrock (Claude 3 Haiku/Sonnet)                 │
│  System prompt: scenario + role + goals + level         │
│  Message history: last N turns (sliding window)         │
│  → AI response text                                     │
└─────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│                 LAYER 4: TTS OUTPUT                      │
│  Amazon Polly Neural TTS                                │
│  → MP3 → S3 → presigned URL                            │
└─────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│              LAYER 5: SCORING (async)                    │
│  Chạy sau khi session kết thúc                          │
│  LLM-based scoring: fluency, grammar, vocabulary        │
│  Comprehend: key phrases, sentiment                     │
└─────────────────────────────────────────────────────────┘
```

### 2.2 WebSocket Event Flow

```
Client                          Server (Lambda WS)
  │                                    │
  │── $connect (token, session_id) ──► │ Verify JWT, save connection_id
  │                                    │
  │── START_SESSION ──────────────────► │ Generate presigned S3 URL
  │◄── SESSION_READY (upload_url) ─────│
  │                                    │
  │── SEND_MESSAGE (text) ────────────► │ Layer 2 → Layer 3 → Layer 4
  │◄── TURN_SAVED (turn_index) ────────│ (ngay sau khi lưu user turn)
  │◄── AI_TEXT_CHUNK (text, done) ─────│ (streaming từng chunk)
  │◄── AI_AUDIO_URL (url) ─────────────│ (sau khi Polly xong)
  │                                    │
  │── AUDIO_UPLOADED (s3_key) ────────► │ Transcribe → text → pipeline
  │◄── STT_RESULT (text, confidence) ──│
  │◄── TURN_SAVED ─────────────────────│
  │◄── AI_TEXT_CHUNK ──────────────────│
  │◄── AI_AUDIO_URL ───────────────────│
  │                                    │
  │── USE_HINT ───────────────────────► │ LLM generate contextual hint
  │◄── HINT_TEXT (hint) ───────────────│
  │                                    │
  │── END_SESSION ────────────────────► │ Trigger scoring pipeline
  │◄── SCORING_COMPLETE ───────────────│
```

---

## 3. Layer 1: Input Processing

### 3.1 Text Input

Đơn giản — nhận text từ `SEND_MESSAGE`, validate không rỗng, tiếp tục.

### 3.2 Audio Input (STT)

**Vấn đề hiện tại:** `audio_uploaded` handler chỉ trả `STT_LOW_CONFIDENCE` giả.

**Giải pháp:** Amazon Transcribe batch job (không phải streaming) vì:
- Audio đã upload lên S3 trước khi gọi `AUDIO_UPLOADED`
- Batch job đơn giản hơn streaming, phù hợp với kiến trúc Lambda
- Latency chấp nhận được (~2-5s cho audio ngắn)

**Flow:**
```python
# Khi nhận AUDIO_UPLOADED với s3_key
1. Gọi transcribe_client.start_transcription_job(
       TranscriptionJobName=unique_id,
       Media={"MediaFileUri": f"s3://{bucket}/{s3_key}"},
       MediaFormat="webm",
       LanguageCode="en-US",
       Settings={"ShowAlternatives": False}
   )
2. Poll kết quả (max 30s, interval 2s)
3. Lấy transcript text
4. Gửi STT_RESULT về client
5. Tiếp tục pipeline với text đó
```

**AWS Transcribe best practices (từ docs):**
- PCM audio: chunk 50-200ms
- Sample rate 16,000 Hz tối ưu
- Gửi silence khi không có speech

**Fallback:** Nếu Transcribe timeout → gửi `STT_LOW_CONFIDENCE` → user nhập text thủ công.

---

## 4. Layer 2: Intent Guard (Off-topic Detection)

### 4.1 Vấn đề

User có thể:
- Nói chuyện không liên quan đến scenario ("Tell me a joke")
- Nói tục, nói bậy
- Cố tình phá vỡ roleplay ("You are not an AI, you are...")
- Hỏi về chủ đề nhạy cảm

### 4.2 Giải pháp: Prompt-based Intent Guard trong System Prompt

**Không dùng Bedrock Guardrails** cho off-topic vì:
- Guardrails block cứng → trải nghiệm xấu (user thấy error message)
- Với language learning, off-topic cần được *redirect* nhẹ nhàng, không block
- Guardrails phù hợp hơn cho harmful content (tục tĩu, bạo lực)

**Giải pháp đúng: Encode off-topic handling vào System Prompt của LLM**

```
SYSTEM PROMPT STRUCTURE:
1. Role definition (AI đóng vai gì)
2. Scenario context (tình huống, goals)
3. Level constraint (A1/A2/B1/B2/C1/C2)
4. OFF-TOPIC REDIRECT RULE (quan trọng nhất)
5. Response format rules
```

**Off-topic redirect rule trong system prompt:**
```
If the learner says something unrelated to the scenario 
(e.g., jokes, personal questions, off-topic requests), 
do NOT engage with the off-topic content.
Instead, gently redirect them back to the scenario with a 
natural transition phrase like:
- "That's interesting! But let's get back to [scenario context]..."
- "Ha, good one! Now, about [current goal]..."
- "I'd love to chat about that later! For now, [redirect to task]..."

If the learner uses inappropriate language, respond with:
"Let's keep our conversation professional. [redirect to scenario]"

NEVER break character. NEVER acknowledge you are an AI unless directly asked.
```

### 4.3 Amazon Comprehend: Sentiment + Language Detection

Dùng Comprehend để:
1. **Detect language** — nếu user nói tiếng Việt hoàn toàn → nhắc nhở bằng tiếng Anh
2. **Sentiment analysis** — nếu sentiment rất negative → AI phản hồi nhẹ nhàng hơn

```python
# Trước khi gọi LLM
comprehend_result = comprehend.detect_sentiment(Text=user_text, LanguageCode="en")
language_result = comprehend.detect_dominant_language(Text=user_text)

# Nếu ngôn ngữ không phải English
if language_result["Languages"][0]["LanguageCode"] != "en":
    # Thêm instruction vào message: "The learner wrote in [lang], gently remind them to use English"
    
# Nếu sentiment = NEGATIVE với confidence cao
if comprehend_result["Sentiment"] == "NEGATIVE" and comprehend_result["SentimentScore"]["Negative"] > 0.8:
    # Thêm instruction: "The learner seems frustrated, be extra encouraging"
```

### 4.4 Bedrock Guardrails: Chỉ cho Harmful Content

Dùng Bedrock Guardrails với `inputAction: NONE` (detect nhưng không block) cho:
- Hate speech
- Sexual content
- Violence

Khi detect → AI redirect với tone nhẹ nhàng, không block cứng.

---

## 5. Layer 3: LLM Generation (Amazon Bedrock)

### 5.1 Model Selection

| Model | Latency | Cost | Quality | Recommendation |
|---|---|---|---|---|
| Claude 3 Haiku | ~1s | Thấp nhất | Tốt | ✅ **MVP** |
| Claude 3 Sonnet | ~2-3s | Trung bình | Rất tốt | Phase 2 |
| Claude 3.5 Sonnet | ~2-4s | Cao | Tốt nhất | Phase 3 |

**Chọn Claude 3 Haiku cho MVP** — latency thấp, đủ chất lượng cho A1-B2.

### 5.2 System Prompt Design

```python
def build_llm_system_prompt(session: Session, scenario: Scenario) -> str:
    level_instructions = {
        "A1": "Use very simple words. Max 1-2 short sentences. Speak slowly and clearly.",
        "A2": "Use simple vocabulary. Max 2 sentences. Ask one simple question.",
        "B1": "Use everyday vocabulary. 2-3 sentences. Ask follow-up questions.",
        "B2": "Use varied vocabulary. 2-4 sentences. Discuss ideas naturally.",
        "C1": "Use sophisticated language. 3-5 sentences. Engage deeply.",
        "C2": "Use native-level language. Natural conversation flow.",
    }
    
    return f"""You are playing the role of {session.ai_role_id} in a roleplay conversation.

SCENARIO: {scenario.scenario_title}
CONTEXT: {scenario.context}
YOUR ROLE: {session.ai_role_id}
LEARNER'S ROLE: {session.learner_role_id}
LEARNING GOALS: {", ".join(session.selected_goals)}

LANGUAGE LEVEL: {session.level.value}
{level_instructions.get(session.level.value, "")}

CONVERSATION RULES:
1. Stay in character as {session.ai_role_id} at all times.
2. Keep responses SHORT and NATURAL (match the level above).
3. Always move the conversation forward — ask a question or prompt the next action.
4. Do NOT correct grammar during conversation. Evaluation happens after.
5. If the learner goes off-topic, gently redirect: "That's interesting! But let's focus on {scenario.scenario_title}..."
6. If the learner uses inappropriate language: "Let's keep it professional. Now, {session.selected_goals[0] if session.selected_goals else 'let us continue'}..."
7. If the learner writes in Vietnamese, respond: "Please try in English! I'll help you. [simple prompt in English]"
8. NEVER say you are an AI unless directly asked.

CURRENT GOALS TO ACHIEVE: {", ".join(session.selected_goals)}"""
```

### 5.3 Message History (Sliding Window)

**Vấn đề:** Lambda stateless, mỗi lần gọi phải load lại history từ DynamoDB.

**Giải pháp:** Sliding window — chỉ gửi N turns gần nhất vào LLM context.

```python
MAX_HISTORY_TURNS = 10  # 5 user + 5 AI turns

def build_messages_for_llm(turns: List[Turn]) -> List[dict]:
    # Lấy N turns gần nhất
    recent_turns = sorted(turns, key=lambda t: t.turn_index)[-MAX_HISTORY_TURNS:]
    
    messages = []
    for turn in recent_turns:
        role = "user" if turn.speaker == Speaker.USER else "assistant"
        messages.append({"role": role, "content": turn.content})
    
    return messages
```

**Prompt caching:** Dùng Bedrock prompt caching cho system prompt (không đổi trong session) → giảm latency và cost.

### 5.4 Bedrock API Call

```python
import boto3
import json

bedrock = boto3.client("bedrock-runtime")

def generate_ai_reply(system_prompt: str, messages: List[dict]) -> str:
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 150,  # Giới hạn ngắn để response nhanh
        "system": system_prompt,
        "messages": messages,
        "temperature": 0.7,  # Đủ creative nhưng không quá random
    }
    
    response = bedrock.invoke_model(
        modelId="anthropic.claude-3-haiku-20240307-v1:0",
        body=json.dumps(body),
    )
    
    result = json.loads(response["body"].read())
    return result["content"][0]["text"].strip()
```

### 5.5 Streaming Response (Phase 2)

Dùng `InvokeModelWithResponseStream` để stream từng chunk về client qua WebSocket:

```python
# Gửi từng chunk qua WS event AI_TEXT_CHUNK
response = bedrock.invoke_model_with_response_stream(...)
for event in response["body"]:
    chunk = json.loads(event["chunk"]["bytes"])
    if chunk["type"] == "content_block_delta":
        text_chunk = chunk["delta"]["text"]
        send_ws_message({"event": "AI_TEXT_CHUNK", "chunk": text_chunk, "done": False})

send_ws_message({"event": "AI_TEXT_CHUNK", "chunk": "", "done": True})
```

---

## 6. Layer 4: TTS Output (Amazon Polly)

### 6.1 Hiện trạng

Polly đang hoạt động đúng với neural voices (Joanna/Matthew). Cần cải thiện:

### 6.2 SSML Enhancement

Dùng SSML để tăng tính tự nhiên:

```python
def wrap_with_ssml(text: str, level: str) -> str:
    # Thêm pause sau câu hỏi, điều chỉnh tốc độ theo level
    rate = {
        "A1": "slow", "A2": "slow",
        "B1": "medium", "B2": "medium",
        "C1": "fast", "C2": "fast"
    }.get(level, "medium")
    
    return f'<speak><prosody rate="{rate}">{text}</prosody></speak>'
```

### 6.3 Voice Selection

```python
VOICE_MAP = {
    "female": "Joanna",   # Neural, US English
    "male": "Matthew",    # Neural, US English
}
# Phase 2: thêm British English (Amy/Brian), Australian (Olivia/Russell)
```

### 6.4 Caching TTS

Nếu AI trả lời giống nhau (ví dụ: greeting cố định) → cache audio URL để tránh gọi Polly lại.

```python
import hashlib

def get_audio_cache_key(text: str, voice_id: str) -> str:
    return f"tts-cache/{hashlib.sha256(f'{voice_id}:{text}'.encode()).hexdigest()}.mp3"
```

---

## 7. Hint System

### 7.1 Hiện trạng

Hint hiện tại: `f"Hãy thử nói ngắn gọn về: {session.selected_goals[0]}"` — quá đơn giản.

### 7.2 Contextual Hint với LLM

Khi user gọi `USE_HINT`, gọi LLM với prompt đặc biệt:

```python
def generate_hint(session: Session, turns: List[Turn]) -> str:
    last_ai_turn = next((t for t in reversed(turns) if t.speaker == Speaker.AI), None)
    
    hint_prompt = f"""The learner is stuck in this conversation.
    
Last AI message: "{last_ai_turn.content if last_ai_turn else 'Start of conversation'}"
Current goal: {session.selected_goals[0] if session.selected_goals else 'general conversation'}
Learner level: {session.level.value}

Generate a SHORT hint (1 sentence) that:
1. Suggests what the learner could say next
2. Uses vocabulary appropriate for {session.level.value} level
3. Is in the format: "You could say: '[example phrase]'"
4. Relates to the current goal

Hint:"""
    
    # Gọi LLM với max_tokens=50
    return generate_ai_reply(system_prompt="", messages=[{"role": "user", "content": hint_prompt}])
```

---

## 8. Scoring System

### 8.1 Hiện trạng

Scoring hiện tại dùng heuristic đơn giản (đếm từ, câu). Không chính xác.

### 8.2 LLM-based Scoring (Post-session)

Sau khi session kết thúc, gọi LLM để chấm điểm toàn bộ transcript:

```python
SCORING_PROMPT = """You are an English language examiner. Evaluate this conversation transcript.

SCENARIO: {scenario_title}
LEARNER ROLE: {learner_role}
LEVEL: {level}
GOALS: {goals}

TRANSCRIPT (learner's turns only):
{learner_transcript}

Score each dimension from 0-100:
1. FLUENCY: Natural flow, appropriate pace, minimal hesitation
2. GRAMMAR: Correct sentence structure, verb tenses, articles
3. VOCABULARY: Appropriate word choice, variety, level-appropriate
4. TASK_COMPLETION: Did the learner achieve the conversation goals?

Also provide:
- FEEDBACK: 2-3 sentences of constructive feedback in Vietnamese
- STRENGTHS: What the learner did well (1 sentence)
- IMPROVEMENT: One specific thing to improve (1 sentence)

Respond in JSON format:
{{
  "fluency": <0-100>,
  "grammar": <0-100>,
  "vocabulary": <0-100>,
  "task_completion": <0-100>,
  "overall": <average>,
  "feedback": "<Vietnamese feedback>",
  "strengths": "<Vietnamese>",
  "improvement": "<Vietnamese>"
}}"""
```

### 8.3 Comprehend-assisted Scoring

Kết hợp Comprehend để bổ sung:
- `detect_key_phrases` → vocabulary richness
- `detect_syntax` → grammar complexity
- `detect_sentiment` → engagement level

---

## 9. Thay đổi cần implement

### 9.1 Thay thế `RuleBasedConversationGenerationService`

**File:** `src/infrastructure/services/speaking_pipeline_services.py`

```python
class BedrockConversationGenerationService(ConversationGenerationService):
    def __init__(self, bedrock_client=None):
        self._bedrock = bedrock_client or boto3.client("bedrock-runtime")
    
    def generate_reply(self, session, user_turn, analysis, turn_history) -> str:
        system_prompt = build_llm_system_prompt(session)
        messages = build_messages_for_llm(turn_history + [user_turn])
        return generate_ai_reply(self._bedrock, system_prompt, messages)
```

### 9.2 Implement STT thực

**File:** `src/infrastructure/services/speaking_pipeline_services.py`

```python
class TranscribeSTTService:
    def transcribe(self, s3_bucket: str, s3_key: str) -> tuple[str, float]:
        """Returns (transcript_text, confidence)"""
        # Start job → poll → return result
```

### 9.3 Cập nhật `websocket_handler.py`

- `audio_uploaded`: Gọi `TranscribeSTTService` thay vì trả `STT_LOW_CONFIDENCE` giả
- `use_hint`: Gọi LLM hint thay vì hardcode string

### 9.4 Cập nhật `CompleteSpeakingSessionUseCase`

- `_build_scoring`: Gọi LLM scoring thay vì heuristic

### 9.5 Cập nhật `prompt_builder.py`

- `build_session_prompt`: Thêm off-topic redirect rules, level-specific instructions

### 9.6 Cập nhật `template.yaml`

Thêm permissions:
```yaml
Policies:
  - Statement:
      - Effect: Allow
        Action:
          - bedrock:InvokeModel
          - bedrock:InvokeModelWithResponseStream
          - transcribe:StartTranscriptionJob
          - transcribe:GetTranscriptionJob
        Resource: "*"
```

---

## 10. Thứ tự implement (MVP → Phase 2)

### MVP (Ưu tiên cao nhất)

1. **Thay `RuleBasedConversationGenerationService` bằng Bedrock Claude 3 Haiku**
   - Đây là thay đổi có impact lớn nhất
   - Giải quyết cả off-topic (qua system prompt) và chất lượng hội thoại

2. **Cải thiện `build_session_prompt`**
   - Thêm off-topic redirect rules
   - Thêm level-specific instructions

3. **Cải thiện Hint với LLM**
   - Thay hardcode string bằng LLM-generated contextual hint

### Phase 2

4. **Implement STT thực với Amazon Transcribe**
5. **LLM-based scoring sau session**
6. **Streaming response (AI_TEXT_CHUNK từng chunk)**

### Phase 3

7. **Bedrock Guardrails cho harmful content**
8. **Prompt caching để giảm latency**
9. **SSML enhancement cho Polly**

---

## 11. Tóm tắt kỹ thuật

| Component | Hiện tại | Đề xuất |
|---|---|---|
| STT | Không có (giả) | Amazon Transcribe batch |
| LLM | Rule-based hardcode | Amazon Bedrock Claude 3 Haiku |
| Off-topic | Không xử lý | System prompt redirect rules |
| Harmful content | Không xử lý | Bedrock Guardrails (Phase 3) |
| TTS | Polly Neural ✅ | Polly Neural + SSML (Phase 2) |
| Hint | Hardcode string | LLM contextual hint |
| Scoring | Heuristic đếm từ | LLM-based scoring (Phase 2) |
| Comprehend | Có nhưng chỉ lấy key phrases | Thêm sentiment + language detection |

---

## 12. Chi phí ước tính (per session ~10 turns)

| Service | Usage | Cost estimate |
|---|---|---|
| Bedrock Claude 3 Haiku | ~2000 tokens/turn × 10 | ~$0.005/session |
| Amazon Polly Neural | ~100 chars/turn × 10 | ~$0.001/session |
| Amazon Transcribe | ~30s audio | ~$0.006/session |
| Amazon Comprehend | 10 calls | ~$0.001/session |
| **Total** | | **~$0.013/session** |

Rất hợp lý cho MVP.
