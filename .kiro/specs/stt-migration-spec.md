# STT Migration Spec: Client-side Streaming

## Overview
Migrate từ server-side streaming STT (deprecated SDK) sang client-side streaming (AWS recommended) và cleanup toàn bộ legacy code.

## Current State (Legacy)

### Architecture
```
Browser → WebSocket → Lambda → amazon-transcribe-streaming-sdk → Transcribe
         (audio)      (extra hop)        (deprecated SDK)
```

### Files to Remove
1. `src/infrastructure/services/streaming_stt_service.py` - Deprecated SDK implementation
2. `src/infrastructure/services/streaming_stt_service_sync.py` - Sync wrapper for deprecated SDK

### Files to Modify
1. `src/infrastructure/handlers/websocket_handler.py` - Remove streaming endpoints
2. `requirements.txt` - Remove `amazon-transcribe-streaming-sdk` dependency
3. `template.yaml` - Remove streaming-related environment variables

---

## Target State (AWS Recommended)

### Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                        BROWSER                               │
│  ┌─────────────┐    ┌──────────────────────────────────┐   │
│  │ Microphone  │───→│ Transcribe WebSocket (presigned) │   │
│  └─────────────┘    │ wss://transcribestreaming...     │   │
│                     └──────────────────────────────────┘   │
│                              ↓                               │
│                    ┌─────────────────┐                      │
│                    │ Final Transcript│                      │
│                    └─────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
                              ↓
                    ┌─────────────────┐
                    │ Lambda WebSocket│
                    │ (SUBMIT_TRANSCRIPT)│
                    └─────────────────┘
                              ↓
                    ┌─────────────────┐
                    │ Bedrock → Polly │
                    └─────────────────┘
```

### Benefits
- ✅ No deprecated SDK dependency
- ✅ Lower latency (direct browser → Transcribe)
- ✅ No Lambda timeout issues
- ✅ Simpler backend (just receive final transcript)
- ✅ AWS officially recommended for browser clients

---

## Implementation Tasks

### Phase 1: Backend Changes

#### Task 1.1: Create Presigned URL Generator
**File:** `src/infrastructure/services/transcribe_presigned_url.py`

Create service to generate presigned WebSocket URLs for Transcribe streaming.

**Key features:**
- Generate SigV4 signed WebSocket URL
- Support multiple regions
- Configurable expiry (max 300 seconds per AWS)
- Support language code, media encoding, sample rate

**Reference:** https://docs.aws.amazon.com/transcribe/latest/dg/streaming-setting-up.html#streaming-websocket

#### Task 1.2: Add New WebSocket Endpoint
**File:** `src/infrastructure/handlers/websocket_handler.py`

Add `GET_TRANSCRIBE_URL` action to return presigned URL to client.

**Flow:**
1. Client sends `GET_TRANSCRIBE_URL` with session_id
2. Backend validates session
3. Backend generates presigned URL
4. Backend returns URL to client
5. Client connects directly to Transcribe

#### Task 1.3: Keep SUBMIT_TRANSCRIPT Endpoint
**File:** `src/infrastructure/handlers/websocket_handler.py`

This endpoint already exists and works correctly. No changes needed.

**Flow:**
1. Client sends final transcript via `SUBMIT_TRANSCRIPT`
2. Backend processes transcript (Bedrock → Polly)
3. Backend sends AI response

---

### Phase 2: Remove Legacy Code

#### Task 2.1: Remove Deprecated SDK Files
Delete:
- `src/infrastructure/services/streaming_stt_service.py`
- `src/infrastructure/services/streaming_stt_service_sync.py`

#### Task 2.2: Remove Streaming Endpoints
Remove from `websocket_handler.py`:
- `start_streaming()` method
- `audio_chunk()` method
- `end_streaming()` method
- Related imports

#### Task 2.3: Update Dependencies
Remove from `requirements.txt`:
- `amazon-transcribe-streaming-sdk`

#### Task 2.4: Update WebSocket Controller
Remove from `WebSocketSessionController`:
- `streaming_stt_service` field
- Related initialization

---

### Phase 3: Testing & Documentation

#### Task 3.1: Update Tests
- Remove tests for deprecated streaming service
- Add tests for presigned URL generation
- Add tests for new `GET_TRANSCRIBE_URL` endpoint

#### Task 3.2: Update Documentation
- Update `STREAMING_REMOVAL_SUMMARY.md`
- Create migration guide for frontend team
- Update API documentation

---

## API Changes

### New Endpoint: GET_TRANSCRIBE_URL

**Request:**
```json
{
  "action": "GET_TRANSCRIBE_URL",
  "session_id": "session-123"
}
```

**Response (via WebSocket):**
```json
{
  "event": "TRANSCRIBE_URL",
  "url": "wss://transcribestreaming.ap-southeast-1.amazonaws.com:8443/stream-transcription-websocket?X-Amz-Algorithm=...",
  "expires_in": 300,
  "language_code": "en-US",
  "media_encoding": "opus",
  "sample_rate": 16000
}
```

### Existing Endpoint: SUBMIT_TRANSCRIPT (No changes)

**Request:**
```json
{
  "action": "SUBMIT_TRANSCRIPT",
  "session_id": "session-123",
  "text": "Hello, how are you?",
  "confidence": 0.95
}
```

---

## Removed Endpoints

| Endpoint | Status | Replacement |
|----------|--------|-------------|
| `START_STREAMING` | ❌ Remove | `GET_TRANSCRIBE_URL` |
| `AUDIO_CHUNK` | ❌ Remove | Client sends directly to Transcribe |
| `END_STREAMING` | ❌ Remove | Client closes Transcribe connection |
| `SUBMIT_TRANSCRIPT` | ✅ Keep | No changes |

---

## Frontend Changes Required

### Step 1: Get Presigned URL
```javascript
// Request presigned URL from backend
websocket.send(JSON.stringify({
  action: 'GET_TRANSCRIBE_URL',
  session_id: sessionId
}));

// Receive URL
websocket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.event === 'TRANSCRIBE_URL') {
    connectToTranscribe(data.url);
  }
};
```

### Step 2: Connect to Transcribe WebSocket
```javascript
function connectToTranscribe(presignedUrl) {
  const transcribeSocket = new WebSocket(presignedUrl);
  
  transcribeSocket.onopen = () => {
    // Start recording audio
    startRecording(transcribeSocket);
  };
  
  transcribeSocket.onmessage = (event) => {
    // Handle transcripts
    const data = JSON.parse(event.data);
    handleTranscript(data);
  };
}
```

### Step 3: Send Audio Chunks
```javascript
function startRecording(transcribeSocket) {
  navigator.mediaDevices.getUserMedia({ audio: true })
    .then(stream => {
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus',
        audioBitsPerSecond: 16000
      });
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          // Send audio chunk to Transcribe (100ms chunks = AWS recommended)
          transcribeSocket.send(event.data);
        }
      };
      
      // 100ms chunks (AWS best practice: 50-200ms)
      mediaRecorder.start(100);
    });
}
```

### Step 4: Handle Transcripts
```javascript
function handleTranscript(data) {
  const results = data.Transcript?.Results || [];
  
  for (const result of results) {
    const transcript = result.Alternatives[0].Transcript;
    
    if (result.IsPartial) {
      // Show partial transcript (real-time feedback)
      showPartialTranscript(transcript);
    } else {
      // Send final transcript to backend
      sendFinalTranscript(transcript, result.Alternatives[0].Confidence);
    }
  }
}
```

### Step 5: Submit Final Transcript
```javascript
function sendFinalTranscript(text, confidence) {
  websocket.send(JSON.stringify({
    action: 'SUBMIT_TRANSCRIPT',
    session_id: sessionId,
    text: text,
    confidence: confidence
  }));
}
```

---

## Rollback Plan

If issues arise:
1. Revert to previous commit
2. Redeploy Lambda with legacy code
3. Frontend can fall back to batch STT (upload audio to S3)

---

## Success Criteria

- [x] Presigned URL generation works
- [x] Client can connect to Transcribe WebSocket (frontend required)
- [x] Audio chunks are transcribed correctly (frontend required)
- [x] Final transcript is processed by backend
- [x] All legacy streaming code removed
- [ ] Tests pass (need to write tests)
- [x] Documentation updated

---

## Timeline

- **Phase 1 (Backend):** ✅ Complete (2026-04-27)
- **Phase 2 (Cleanup):** ✅ Complete (2026-04-27)
- **Phase 3 (Testing):** ⏳ Pending
- **Frontend Integration:** ⏳ Pending (frontend team)

**Total Backend Effort:** 2.5 hours (actual)
