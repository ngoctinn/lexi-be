# WebSocket Connection Debugging Guide

## Problem
Frontend gets `readyState=3` (connection closing) when trying to connect to WebSocket API.

## Root Causes to Check

### 1. **Token Not Being Passed**
- Frontend should send: `?token=<JWT>&session_id=<ID>`
- Check CloudWatch logs for: `[ws] Handler called: ... has_token=False`
- **Fix**: Ensure `getFreshIdToken()` succeeds in frontend

### 2. **Session Not Found**
- Session must exist before WebSocket connection
- Check CloudWatch logs for: `[ws] connect() failed: session not found`
- **Fix**: Create session via `/sessions` endpoint first

### 3. **Token Verification Failed**
- Token might be expired, invalid, or wrong format
- Check CloudWatch logs for: `[ws] Token verification failed:`
- **Fix**: Ensure token is fresh (frontend calls `forceRefresh: true`)

### 4. **User ID Mismatch**
- Session belongs to different user than token
- Check CloudWatch logs for: `[ws] Session user_id mismatch:`
- **Fix**: Ensure same user creates session and connects

### 5. **Lambda Exception**
- Unhandled exception in handler
- Check CloudWatch logs for: `[ws] Handler exception:`
- **Fix**: Check full traceback in logs

## How to Debug

### Step 1: Check CloudWatch Logs
```bash
# View WebSocket handler logs
aws logs tail /aws/lambda/lexi-be-SpeakingWebSocketFunction --follow
```

### Step 2: Look for These Log Patterns
```
[ws] Handler called: route_key=$connect ...
[ws] Processing $connect: session_id=...
[ws] connect() called: session_id=... token_len=...
[ws] Verifying token...
[ws] Token verified successfully: ...
[ws] Connected successfully: ...
```

### Step 3: Common Issues

| Log Pattern | Issue | Solution |
|---|---|---|
| `has_token=False` | Token not sent | Check frontend `buildWebSocketUrl()` |
| `session not found` | Session doesn't exist | Create session first via `/sessions` POST |
| `Token verification failed` | Invalid token | Check token expiration, format |
| `user_id mismatch` | Wrong user | Ensure same user creates session |
| `Handler exception` | Unhandled error | Check full traceback |

## Testing Locally

### 1. Create a Session
```bash
curl -X POST https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod/sessions \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"scenario_id": "test"}'
```

### 2. Get Fresh Token
```javascript
const session = await fetchAuthSession({ forceRefresh: true });
const token = session.tokens?.idToken?.toString();
console.log("Token:", token);
```

### 3. Connect to WebSocket
```javascript
const url = `wss://no8fa2u3qg.execute-api.ap-southeast-1.amazonaws.com/Prod?token=${token}&session_id=${sessionId}`;
const ws = new WebSocket(url);
ws.onopen = () => console.log("Connected!");
ws.onerror = (e) => console.error("Error:", e);
ws.onclose = (e) => console.log("Closed:", e.code, e.reason);
```

## Next Steps

After debugging, consider:
1. Add Lambda Authorizer for cleaner separation of concerns
2. Add request/response logging to API Gateway
3. Add CloudWatch alarms for connection failures
