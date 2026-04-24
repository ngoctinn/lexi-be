# WebSocket & Connection Fixes Summary

## Issues Fixed

### 1. ✅ WebSocket Connection Reconnect Loop (Code 1005)
**Problem**: Client reconnected infinitely with code 1005 (Going Away)
**Root Cause**: Client-side code treated code 1005 as error and reconnected
**Fix**: Updated `use-websocket.ts` to treat code 1005 as normal close (don't reconnect)

**File**: `lexi-fe/features/session/hooks/use-websocket.ts`
```typescript
// Before: Only ignored 1000/1001
if (ev.code === 1000 || ev.code === 1001) return;

// After: Also ignore 1005 (client-side close)
if (ev.code === 1000 || ev.code === 1001 || ev.code === 1005) return;
```

### 2. ✅ CloudWatch PutMetricData Permission Denied
**Problem**: Lambda couldn't write metrics to CloudWatch
**Root Cause**: Missing `cloudwatch:PutMetricData` permission in IAM policy
**Fix**: Added permission to `SpeakingWebSocketFunction` in SAM template

**File**: `lexi-be/template.yaml`
```yaml
- Effect: Allow
  Action:
    - cloudwatch:PutMetricData  # ← Added this
  Resource: "*"
```

### 3. ✅ Backend WebSocket Handler Improvements
**Problem**: Message send failures weren't logged, connection issues hard to debug
**Root Cause**: Missing error handling and logging in `_make_sender`
**Fix**: Enhanced error handling with proper logging (already implemented in previous commit)

**File**: `lexi-be/src/infrastructure/handlers/websocket_handler.py`
- Added logging for all send operations
- Proper GoneException handling
- Exception handling in all message-sending methods

---

## Testing Checklist

- [ ] Deploy changes: `sam build && sam deploy`
- [ ] Test WebSocket connection - should NOT reconnect infinitely
- [ ] Send message - should receive AI response
- [ ] Check CloudWatch logs for `[ws]` messages
- [ ] Verify metrics are written to CloudWatch

---

## Expected Behavior After Fixes

1. **Connection**: Client connects once and stays connected
2. **Messages**: Client sends message → AI responds → Client receives response
3. **Logging**: CloudWatch logs show clear flow:
   ```
   [ws] Connected successfully
   [ws] Sending message to ...: SEND_MESSAGE
   [ws] Message sent successfully
   [ws] Sending message to ...: AI_TEXT_CHUNK
   [ws] Message sent successfully
   ```
4. **Metrics**: CloudWatch metrics are written without errors

---

## Deployment Steps

```bash
cd lexi-be
sam build
sam deploy
```

Then test in browser:
1. Open session
2. Send message
3. Check browser console for `[ws] Connected` (no reconnects)
4. Verify AI response is received
