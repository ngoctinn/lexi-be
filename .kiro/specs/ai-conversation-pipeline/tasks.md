# Implementation Tasks — AI Conversation Pipeline

**Version:** 1.0  
**Dựa trên:** design.md + AWS docs (Bedrock, Transcribe, Polly, Comprehend)

---

## Phase 1: LLM Integration (Impact cao nhất — làm trước)

### Task 1: Tạo BedrockConversationGenerationService

**Status:** pending  
**File:** `src/infrastructure/services/speaking_pipeline_services.py`

**Thay thế `RuleBasedConversationGenerationService` bằng Bedrock Claude 3 Haiku.**

Model ID chính xác (từ AWS docs): `anthropic.claude-3-haiku-20240307-v1:0`

**Implementation:**
```python
class BedrockConversationGenerationService(ConversationGenerationService):
    def __init__(self, bedrock_client=None):
        self._bedrock = bedrock_client or boto3.client("bedrock-runtime")

    def generate_reply(
        self,
        session: Session,
        user_turn: Turn,
        analysis: SpeakingAnalysis,
        turn_history: List[Turn],
    ) -> str:
        system_prompt = _build_llm_system_prompt(session)
        messages = _build_messages_for_llm(turn_history + [user_turn])
        
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 150,
            "system": system_prompt,
            "messages": messages,
            "temperature": 0.7,
        })
        
        try:
            response = self._bedrock.invoke_model(
                modelId="anthropic.claude-3-haiku-20240307-v1:0",
                body=body,
            )
            result = json.loads(response["body"].read())
            return result["content"][0]["text"].strip()
        except Exception:
            logger.exception("Bedrock generation failed")
            return "I see. Could you tell me more about that?"
```

**Done khi:** AI trả lời tự nhiên, không còn hardcode template.

---

### Task 2: Cập nhật `build_session_prompt` với off-topic redirect rules

**Status:** pending  
**File:** `src/domain/services/prompt_builder.py`

**Thêm vào system prompt:**
1. Off-topic redirect rules
2. Level-specific language instructions
3. Vietnamese language detection rule

```python
_LEVEL_INSTRUCTIONS = {
    "A1": "Use very simple words. Max 1-2 short sentences. Speak slowly.",
    "A2": "Use simple vocabulary. Max 2 sentences. Ask one simple question.",
    "B1": "Use everyday vocabulary. 2-3 sentences. Ask follow-up questions.",
    "B2": "Use varied vocabulary. 2-4 sentences. Discuss ideas naturally.",
    "C1": "Use sophisticated language. 3-5 sentences. Engage deeply.",
    "C2": "Use native-level language. Natural conversation flow.",
}

def build_session_prompt(...) -> str:
    # Thêm vào cuối prompt hiện tại:
    off_topic_rules = """
OFF-TOPIC HANDLING:
- If the learner says something unrelated to the scenario, gently redirect:
  "That's interesting! But let's get back to [scenario context]..."
- If the learner uses inappropriate language:
  "Let's keep our conversation professional. Now, [redirect to goal]..."
- If the learner writes in Vietnamese, respond:
  "Please try in English! I'll help you. [simple English prompt]"
- NEVER break character. NEVER acknowledge you are an AI unless directly asked.
"""
```

**Done khi:** AI redirect off-topic thay vì trả lời bình thường.

---

### Task 3: Implement `_build_messages_for_llm` (sliding window)

**Status:** pending  
**File:** `src/infrastructure/services/speaking_pipeline_services.py`

```python
MAX_HISTORY_TURNS = 10  # 5 user + 5 AI turns

def _build_messages_for_llm(turns: List[Turn]) -> List[dict]:
    recent = sorted(turns, key=lambda t: t.turn_index)[-MAX_HISTORY_TURNS:]
    messages = []
    for turn in recent:
        role = "user" if _enum_value(turn.speaker) == Speaker.USER.value else "assistant"
        messages.append({"role": role, "content": turn.content})
    # Đảm bảo messages không rỗng và bắt đầu bằng user role
    if not messages or messages[0]["role"] != "user":
        messages = [{"role": "user", "content": "Hello"}] + messages
    return messages
```

**Done khi:** Messages được build đúng format cho Bedrock API.

---

### Task 4: Cập nhật `websocket_handler.py` dùng BedrockConversationGenerationService

**Status:** pending  
**File:** `src/infrastructure/handlers/websocket_handler.py`

**Thay trong `get_websocket_controller()`:**
```python
# Trước
RuleBasedConversationGenerationService()

# Sau
BedrockConversationGenerationService()
```

**Done khi:** WebSocket handler dùng Bedrock thay vì rule-based.

---

### Task 5: Cập nhật `template.yaml` — thêm Bedrock permissions

**Status:** pending  
**File:** `template.yaml`

**Thêm vào `SpeakingWebSocketFunction` Policies:**
```yaml
- Statement:
    - Effect: Allow
      Action:
        - bedrock:InvokeModel
      Resource: "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
```

**Done khi:** `sam validate` pass, Lambda có quyền gọi Bedrock.

---

## Phase 2: Contextual Hint với LLM

### Task 6: Implement LLM-based hint generation

**Status:** pending  
**File:** `src/infrastructure/handlers/websocket_handler.py`

**Thay `_build_hint()` trong `WebSocketSessionController`:**

```python
def use_hint(self, session_id: str, connection_id: str) -> dict[str, Any]:
    session = self._get_session(session_id)
    if not session:
        return _response(404, {"message": "Session không tồn tại."})

    self._sync_connection(session, connection_id)
    
    # Lấy turns để có context
    turns = self._turn_repo.list_by_session(session_id)
    hint = self._generate_contextual_hint(session, turns)
    self.send_message({"event": "HINT_TEXT", "hint": hint})
    return _response(200, {"message": "Hint sent"})

def _generate_contextual_hint(self, session: Session, turns: List[Turn]) -> str:
    last_ai = next((t for t in reversed(turns) if _enum_value(t.speaker) == "AI"), None)
    goal = session.selected_goals[0] if session.selected_goals else "continue the conversation"
    level = session.level.value if hasattr(session.level, "value") else str(session.level)
    
    hint_prompt = (
        f"The learner is stuck. Last AI message: '{last_ai.content if last_ai else 'Start'}'. "
        f"Goal: {goal}. Level: {level}. "
        f"Give a 1-sentence hint starting with 'You could say:' in simple English."
    )
    
    try:
        bedrock = boto3.client("bedrock-runtime")
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 60,
            "messages": [{"role": "user", "content": hint_prompt}],
        })
        response = bedrock.invoke_model(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            body=body,
        )
        result = json.loads(response["body"].read())
        return result["content"][0]["text"].strip()
    except Exception:
        return f"You could say something about: {goal}"
```

**Cần inject `turn_repo` vào `WebSocketSessionController`** — thêm field `turn_repo: DynamoTurnRepo`.

**Done khi:** Hint có ngữ cảnh thực tế, không còn hardcode.

---

## Phase 3: STT với Amazon Transcribe

### Task 7: Implement `TranscribeSTTService`

**Status:** pending  
**File:** `src/infrastructure/services/speaking_pipeline_services.py`

**Dựa trên AWS docs pattern (StartTranscriptionJob → poll GetTranscriptionJob):**

```python
import time
import urllib.request

class TranscribeSTTService:
    """
    Batch transcription: upload audio → S3 → Transcribe job → poll → text.
    Polling pattern từ AWS docs: max 15 lần, interval 2s = max 30s timeout.
    """
    MAX_POLL = 15
    POLL_INTERVAL = 2

    def __init__(self, transcribe_client=None):
        self._client = transcribe_client or boto3.client("transcribe")

    def transcribe(self, s3_bucket: str, s3_key: str) -> tuple[str, float]:
        """
        Returns (transcript_text, confidence).
        confidence = 1.0 nếu COMPLETED, 0.0 nếu FAILED/timeout.
        """
        job_name = f"lexi-{new_ulid()}"
        media_uri = f"s3://{s3_bucket}/{s3_key}"
        
        # Detect format từ extension
        media_format = "webm"
        if s3_key.endswith(".mp3"):
            media_format = "mp3"
        elif s3_key.endswith(".wav"):
            media_format = "wav"
        
        try:
            self._client.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={"MediaFileUri": media_uri},
                MediaFormat=media_format,
                LanguageCode="en-US",
            )
        except Exception:
            logger.exception("Failed to start transcription job")
            return "", 0.0

        # Poll kết quả
        for _ in range(self.MAX_POLL):
            time.sleep(self.POLL_INTERVAL)
            try:
                job = self._client.get_transcription_job(TranscriptionJobName=job_name)
                status = job["TranscriptionJob"]["TranscriptionJobStatus"]
                
                if status == "COMPLETED":
                    transcript_uri = job["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
                    with urllib.request.urlopen(transcript_uri) as resp:
                        data = json.loads(resp.read())
                    text = data["results"]["transcripts"][0]["transcript"]
                    # Cleanup job
                    try:
                        self._client.delete_transcription_job(TranscriptionJobName=job_name)
                    except Exception:
                        pass
                    return text, 1.0
                
                if status == "FAILED":
                    return "", 0.0
                    
            except Exception:
                logger.exception("Error polling transcription job")
                return "", 0.0
        
        # Timeout
        return "", 0.0
```

**Done khi:** Service trả về text từ audio file trong S3.

---

### Task 8: Cập nhật `audio_uploaded` handler dùng TranscribeSTTService

**Status:** pending  
**File:** `src/infrastructure/handlers/websocket_handler.py`

**Thay `audio_uploaded()` trong `WebSocketSessionController`:**

```python
def audio_uploaded(self, session_id: str, connection_id: str, body: dict[str, Any]) -> dict[str, Any]:
    session = self._get_session(session_id)
    if not session:
        return _response(404, {"message": "Session không tồn tại."})

    self._sync_connection(session, connection_id)
    
    s3_key = body.get("s3_key", "")
    bucket = os.environ.get("SPEAKING_AUDIO_BUCKET_NAME", "")
    
    if not s3_key or not bucket:
        self.send_message({"event": "STT_LOW_CONFIDENCE", "confidence": 0.0})
        return _response(400, {"message": "Thiếu s3_key hoặc bucket."})
    
    # Gọi Transcribe
    text, confidence = self.stt_service.transcribe(bucket, s3_key)
    
    if not text or confidence < 0.5:
        self.send_message({"event": "STT_LOW_CONFIDENCE", "confidence": confidence})
        return _response(200, {"message": "STT low confidence"})
    
    # Gửi kết quả STT về client
    self.send_message({"event": "STT_RESULT", "text": text, "confidence": confidence})
    
    # Tiếp tục pipeline với text
    result = self.submit_turn_use_case.execute(
        SubmitSpeakingTurnCommand(
            user_id=session.user_id,
            session_id=session_id,
            text=text,
            is_hint_used=False,
            audio_url=f"s3://{bucket}/{s3_key}",
        )
    )
    
    if not result.is_success or result.value is None:
        self.send_message({"event": "ERROR", "message": result.error or "Lỗi xử lý."})
        return _response(422, {"message": result.error})
    
    response = result.value
    self.send_message({"event": "TURN_SAVED", "turn_index": response.user_turn.turn_index})
    self.send_message({"event": "AI_TEXT_CHUNK", "chunk": response.ai_turn.content, "done": True})
    if response.ai_turn.audio_url:
        self.send_message({"event": "AI_AUDIO_URL", "url": response.ai_turn.audio_url, "text": response.ai_turn.content})
    
    return _response(200, {"message": "Audio processed"})
```

**Thêm `stt_service: TranscribeSTTService` vào `WebSocketSessionController` dataclass.**

**Done khi:** Audio upload → Transcribe → AI reply hoạt động end-to-end.

---

### Task 9: Cập nhật `template.yaml` — thêm Transcribe permissions

**Status:** pending  
**File:** `template.yaml`

**Thêm vào `SpeakingWebSocketFunction` Policies:**
```yaml
- Statement:
    - Effect: Allow
      Action:
        - transcribe:StartTranscriptionJob
        - transcribe:GetTranscriptionJob
        - transcribe:DeleteTranscriptionJob
      Resource: "*"
```

**Done khi:** `sam validate` pass.

---

## Phase 4: LLM-based Scoring

### Task 10: Implement LLM scoring trong `CompleteSpeakingSessionUseCase`

**Status:** pending  
**File:** `src/application/use_cases/speaking_session_use_cases.py`

**Thay `_build_scoring()` bằng LLM scoring:**

```python
def _build_scoring(self, session: Session, turns: List[Turn]) -> Scoring:
    user_turns = [t for t in turns if _is_user_turn(t)]
    learner_transcript = "\n".join(
        f"Turn {t.turn_index}: {t.content}" for t in user_turns
    )
    
    scoring_prompt = f"""You are an English language examiner. Evaluate this learner's performance.

SCENARIO: {session.prompt_snapshot.split('Scenario:')[1].split('\n')[0].strip() if 'Scenario:' in session.prompt_snapshot else 'English conversation'}
LEVEL: {session.level.value if hasattr(session.level, 'value') else str(session.level)}
GOALS: {', '.join(session.selected_goals)}

LEARNER'S TURNS:
{learner_transcript if learner_transcript else '(No turns recorded)'}

Score each from 0-100. Respond ONLY with valid JSON:
{{"fluency": <int>, "grammar": <int>, "vocabulary": <int>, "overall": <int>, "feedback": "<2 sentences in Vietnamese>"}}"""

    try:
        bedrock = boto3.client("bedrock-runtime")
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 200,
            "messages": [{"role": "user", "content": scoring_prompt}],
            "temperature": 0.3,
        })
        response = bedrock.invoke_model(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            body=body,
        )
        result = json.loads(response["body"].read())
        scores = json.loads(result["content"][0]["text"].strip())
        
        return Scoring(
            scoring_id=new_ulid(),
            session_id=session.session_id,
            user_id=session.user_id,
            fluency_score=_clamp(scores.get("fluency", 70)),
            pronunciation_score=_clamp(scores.get("fluency", 70)),  # Polly không đánh giá pronunciation
            grammar_score=_clamp(scores.get("grammar", 70)),
            vocabulary_score=_clamp(scores.get("vocabulary", 70)),
            overall_score=_clamp(scores.get("overall", 70)),
            feedback=scores.get("feedback", "Bạn đã hoàn thành phiên học."),
        )
    except Exception:
        logger.exception("LLM scoring failed, falling back to heuristic")
        return self._build_scoring_heuristic(session, turns)
```

**Giữ lại `_build_scoring_heuristic()` (đổi tên từ `_build_scoring` cũ) làm fallback.**

**Done khi:** Scoring dùng LLM, fallback về heuristic nếu Bedrock lỗi.

---

## Phase 5: Comprehend Enhancement

### Task 11: Cập nhật `ComprehendTranscriptAnalysisService` — thêm language detection

**Status:** pending  
**File:** `src/infrastructure/services/speaking_pipeline_services.py`

**Thêm language detection vào `analyze()`:**

```python
def analyze(self, text: str) -> SpeakingAnalysis:
    # ... existing code ...
    
    # Thêm: detect dominant language
    try:
        lang_response = client.detect_dominant_language(Text=cleaned_text)
        dominant_lang = lang_response["Languages"][0]["LanguageCode"] if lang_response["Languages"] else "en"
    except Exception:
        dominant_lang = "en"
    
    return SpeakingAnalysis(
        key_phrases=key_phrases[:5],
        word_count=...,
        unique_word_count=...,
        sentence_count=...,
        syntax_notes=syntax_notes,
        dominant_language=dominant_lang,  # Thêm field mới
    )
```

**Thêm `dominant_language: str = "en"` vào `SpeakingAnalysis` dataclass.**

**Done khi:** Analysis trả về ngôn ngữ chính của user input.

---

### Task 12: Dùng `dominant_language` trong conversation generation

**Status:** pending  
**File:** `src/infrastructure/services/speaking_pipeline_services.py`

**Trong `BedrockConversationGenerationService.generate_reply()`:**

```python
# Nếu user nói tiếng Việt, thêm instruction vào message cuối
if analysis.dominant_language != "en":
    messages[-1]["content"] += (
        f"\n[Note: The learner wrote in {analysis.dominant_language}. "
        "Gently remind them to use English and provide a simple English prompt.]"
    )
```

**Done khi:** AI nhắc user dùng tiếng Anh khi detect tiếng Việt.

---

## Phase 6: IAM & Validation

### Task 13: Validate toàn bộ SAM template

**Status:** pending  
**File:** `template.yaml`

**Chạy:** `sam validate --template template.yaml`

**Done khi:** Không có lỗi.

---

### Task 14: Validate Python syntax tất cả file đã sửa

**Status:** pending

**Chạy:**
```bash
python3 -c "import ast; [ast.parse(open(f).read()) for f in [
  'src/infrastructure/services/speaking_pipeline_services.py',
  'src/infrastructure/handlers/websocket_handler.py',
  'src/application/use_cases/speaking_session_use_cases.py',
  'src/domain/services/prompt_builder.py',
]]"
```

**Done khi:** Không có SyntaxError.

---

## Phase 7: Manual Testing

### Task 15: Test text conversation với LLM

**Status:** pending

```bash
# 1. Tạo session
curl -X POST https://<api>/sessions \
  -H "Authorization: Bearer <token>" \
  -d '{"scenario_id":"s1","learner_role_id":"Khách hàng","ai_role_id":"Barista","ai_gender":"female","level":"A2","selected_goals":["Chọn đồ uống"],"prompt_snapshot":""}'

# 2. Connect WebSocket
wscat -c "wss://<ws-api>?session_id=<id>" -H "Authorization: Bearer <token>"

# 3. Gửi START_SESSION
{"action":"START_SESSION","session_id":"<id>"}

# 4. Gửi SEND_MESSAGE — test normal
{"action":"SEND_MESSAGE","session_id":"<id>","text":"Hello, I'd like a coffee please"}
# Expect: AI_TEXT_CHUNK với response tự nhiên

# 5. Test off-topic
{"action":"SEND_MESSAGE","session_id":"<id>","text":"Tell me a joke about cats"}
# Expect: AI redirect về scenario

# 6. Test tiếng Việt
{"action":"SEND_MESSAGE","session_id":"<id>","text":"Tôi muốn uống cà phê"}
# Expect: AI nhắc dùng tiếng Anh

# 7. Test USE_HINT
{"action":"USE_HINT","session_id":"<id>"}
# Expect: HINT_TEXT với gợi ý có ngữ cảnh

# 8. Test END_SESSION
{"action":"END_SESSION","session_id":"<id>"}
# Expect: SCORING_COMPLETE với điểm từ LLM
```

---

### Task 16: Test audio flow với Transcribe

**Status:** pending

```bash
# 1. Lấy upload URL từ START_SESSION response
# 2. Upload audio file
curl -X PUT "<upload_url>" --data-binary @test_audio.webm

# 3. Gửi AUDIO_UPLOADED
{"action":"AUDIO_UPLOADED","session_id":"<id>","s3_key":"<key>"}
# Expect: STT_RESULT với text, sau đó AI_TEXT_CHUNK
```

---

## Thứ tự thực hiện

```
Phase 1: Task 1 → 2 → 3 → 4 → 5   (LLM — impact lớn nhất)
Phase 2: Task 6                      (Hint)
Phase 3: Task 7 → 8 → 9             (STT)
Phase 4: Task 10                     (Scoring)
Phase 5: Task 11 → 12               (Comprehend)
Phase 6: Task 13 → 14               (Validation)
Phase 7: Task 15 → 16               (Testing)
```

**Lưu ý quan trọng:**
- Task 1-5 (Phase 1) là MVP tối thiểu — làm trước, test trước
- Task 7-9 (STT) có thể làm song song với Phase 2
- Task 10 (Scoring) phụ thuộc vào Task 1 (Bedrock client đã setup)
- Không cần thêm dependency mới — `boto3` đã có sẵn
