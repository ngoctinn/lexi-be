# Frontend Quick Start Guide - Speaking Session

**Mục đích**: Hướng dẫn nhanh cho Frontend team implement speaking session feature

---

## 🎯 Workflow Chính (5 Bước)

### 1️⃣ Load Scenarios

```typescript
// Lấy danh sách kịch bản
const response = await fetch('/scenarios', {
  headers: { 'Authorization': `Bearer ${token}` }
});

const scenarios = await response.json();
// [
//   {
//     scenario_id: "s1",
//     scenario_title: "Restaurant Ordering",
//     context: "restaurant",
//     roles: ["customer", "waiter"],
//     goals: ["order_food", "ask_questions"],
//     difficulty_level: "B1"
//   },
//   ...
// ]
```

---

### 2️⃣ Create Session

```typescript
const createSession = async (scenarioId, learnerRole, aiRole) => {
  const response = await fetch('/sessions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      scenario_id: scenarioId,
      learner_role_id: learnerRole,      // e.g., "customer"
      ai_role_id: aiRole,                // e.g., "waiter"
      ai_gender: 'female',               // or 'male'
      level: 'B1',                       // A1, A2, B1, B2, C1, C2
      selected_goals: ['order_food']     // User selected goals
    })
  });

  const data = await response.json();
  return data.session_id;  // Save this!
};
```

**Response**:
```json
{
  "success": true,
  "session_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
  "session": {
    "session_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
    "status": "ACTIVE",
    "total_turns": 0,
    "created_at": "2026-04-25T11:00:00Z"
  }
}
```

---

### 3️⃣ Main Loop: Submit Turn

```typescript
const submitTurn = async (sessionId, userText, audioUrl = null) => {
  const response = await fetch(`/sessions/${sessionId}/turns`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      text: userText,                    // User's spoken text
      audio_url: audioUrl,               // Optional: S3 URL of audio
      is_hint_used: false                // Did user use hint?
    })
  });

  const data = await response.json();
  return {
    userTurn: data.user_turn,
    aiTurn: data.ai_turn,
    session: data.session,
    keywords: data.analysis_keywords
  };
};
```

**Response**:
```json
{
  "success": true,
  "user_turn": {
    "turn_index": 0,
    "speaker": "USER",
    "content": "I'd like to order a coffee",
    "audio_url": "s3://..."
  },
  "ai_turn": {
    "turn_index": 1,
    "speaker": "AI",
    "content": "Of course! Hot or iced?",
    "audio_url": "s3://...",
    "ttft_ms": "245.5",
    "latency_ms": "1250.3",
    "output_tokens": 42,
    "cost_usd": "0.00015"
  },
  "session": {
    "total_turns": 2,
    "user_turns": 1,
    "avg_ttft_ms": "245.5",
    "avg_latency_ms": "1250.3",
    "total_cost_usd": "0.00015"
  },
  "analysis_keywords": ["coffee", "order"]
}
```

---

### 4️⃣ Display Turns

```typescript
// Render conversation history
const renderConversation = (turns) => {
  return turns.map(turn => (
    <div key={turn.turn_index} className={`turn turn-${turn.speaker.toLowerCase()}`}>
      <div className="speaker">{turn.speaker}</div>
      <div className="content">{turn.content}</div>
      
      {turn.audio_url && (
        <audio controls>
          <source src={turn.audio_url} type="audio/mpeg" />
        </audio>
      )}
      
      {turn.speaker === 'AI' && (
        <div className="metrics">
          <span>TTFT: {turn.ttft_ms}ms</span>
          <span>Latency: {turn.latency_ms}ms</span>
          <span>Tokens: {turn.output_tokens}</span>
          <span>Cost: ${turn.cost_usd}</span>
        </div>
      )}
    </div>
  ));
};
```

---

### 5️⃣ Complete Session

```typescript
const completeSession = async (sessionId) => {
  const response = await fetch(`/sessions/${sessionId}/complete`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  const data = await response.json();
  return data.scoring;  // Show results to user
};
```

**Response**:
```json
{
  "success": true,
  "scoring": {
    "fluency": 78,
    "pronunciation": 82,
    "grammar": 75,
    "vocabulary": 80,
    "overall": 79,
    "feedback": "Great job! Your pronunciation is excellent."
  }
}
```

---

## 🎨 UI Components Needed

### 1. Scenario Selector
- Display list of scenarios
- Show difficulty level
- Show roles and goals
- Allow user to select

### 2. Session Setup
- Choose learner role
- Choose AI gender
- Choose proficiency level
- Select learning goals

### 3. Conversation Display
- Show user turns (left side)
- Show AI turns (right side)
- Audio player for each turn
- Show metrics (optional)

### 4. Input Area
- Text input for user response
- Audio recording button (optional)
- Submit button
- Loading indicator while waiting for AI

### 5. Results Screen
- Show scoring (fluency, pronunciation, etc.)
- Show feedback
- Show session statistics
- Option to start new session

---

## 🔊 Audio Handling

### Recording User Audio (Optional)

```typescript
const recordAudio = async () => {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const mediaRecorder = new MediaRecorder(stream);
  const chunks = [];

  mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
  mediaRecorder.onstop = async () => {
    const blob = new Blob(chunks, { type: 'audio/webm' });
    const audioUrl = await uploadToS3(blob);  // Your S3 upload logic
    return audioUrl;
  };

  mediaRecorder.start();
  return mediaRecorder;
};
```

### Playing AI Audio

```typescript
const playAIAudio = (audioUrl) => {
  const audio = new Audio(audioUrl);
  audio.play();
};
```

---

## ⚠️ Error Handling

```typescript
const submitTurnWithErrorHandling = async (sessionId, text) => {
  try {
    const result = await submitTurn(sessionId, text);
    return result;
  } catch (error) {
    if (error.response?.status === 401) {
      // Redirect to login
      window.location.href = '/login';
    } else if (error.response?.status === 404) {
      // Session not found
      showError('Session expired. Start a new one.');
    } else if (error.response?.status === 500) {
      // Server error - show fallback response
      showError('Server error. Using fallback response.');
      // Backend will return: "Thanks. Could you say a bit more about that?"
    } else {
      showError('Network error. Please try again.');
    }
  }
};
```

---

## 📊 Displaying Metrics

```typescript
const MetricsDisplay = ({ aiTurn, session }) => {
  return (
    <div className="metrics">
      <h3>Performance Metrics</h3>
      
      <div className="metric">
        <label>Time to First Token (TTFT)</label>
        <value>{aiTurn.ttft_ms}ms</value>
        <bar width={Math.min(aiTurn.ttft_ms / 5, 100)} />
      </div>
      
      <div className="metric">
        <label>Total Latency</label>
        <value>{aiTurn.latency_ms}ms</value>
        <bar width={Math.min(aiTurn.latency_ms / 20, 100)} />
      </div>
      
      <div className="metric">
        <label>Output Tokens</label>
        <value>{aiTurn.output_tokens}</value>
      </div>
      
      <div className="metric">
        <label>Cost</label>
        <value>${aiTurn.cost_usd}</value>
      </div>
      
      <div className="session-stats">
        <h4>Session Average</h4>
        <p>Avg TTFT: {session.avg_ttft_ms}ms</p>
        <p>Avg Latency: {session.avg_latency_ms}ms</p>
        <p>Total Cost: ${session.total_cost_usd}</p>
      </div>
    </div>
  );
};
```

---

## 🔄 State Management (React Example)

```typescript
const useSpeakingSession = () => {
  const [session, setSession] = useState(null);
  const [turns, setTurns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const createSession = async (scenarioId, roles) => {
    setLoading(true);
    try {
      const response = await fetch('/sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          scenario_id: scenarioId,
          learner_role_id: roles.learner,
          ai_role_id: roles.ai,
          ai_gender: 'female',
          level: 'B1',
          selected_goals: []
        })
      });
      
      const data = await response.json();
      setSession(data.session);
      setTurns([]);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const submitTurn = async (text) => {
    setLoading(true);
    try {
      const response = await fetch(`/sessions/${session.session_id}/turns`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ text, is_hint_used: false })
      });
      
      const data = await response.json();
      setTurns(data.session.turns);
      setSession(data.session);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return { session, turns, loading, error, createSession, submitTurn };
};
```

---

## 📋 Checklist

- [ ] Load scenarios on app start
- [ ] Implement scenario selector UI
- [ ] Implement session creation
- [ ] Implement turn submission loop
- [ ] Display conversation history
- [ ] Play AI audio
- [ ] Record user audio (optional)
- [ ] Show metrics
- [ ] Handle errors
- [ ] Implement session completion
- [ ] Show scoring results
- [ ] Test with real backend

---

## 🚀 Testing Locally

```bash
# Start backend
sam local start-api --port 3001

# Test create session
curl -X POST http://localhost:3001/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_id": "test",
    "learner_role_id": "customer",
    "ai_role_id": "waiter",
    "ai_gender": "female",
    "level": "B1",
    "selected_goals": []
  }'

# Test submit turn
curl -X POST http://localhost:3001/sessions/{session_id}/turns \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, I would like to order",
    "is_hint_used": false
  }'
```

---

**Tài liệu chi tiết**: Xem `CONVERSATION_ARCHITECTURE.md`  
**API Reference**: Xem `API_RESPONSE_FORMAT.md`  
**Liên hệ**: Backend Team
