# 🔍 GET Profile Flow - Issues Found

## ⚠️ CRITICAL ISSUE: Handler Bug

### Location
`src/infrastructure/handlers/profile/get_profile_handler.py` - Line 56

### The Problem
```python
# ❌ WRONG - Line 56
result = controller.get_profile(user_id)

if result.is_success:
    return presenter.present_success(result.value)  # ✅ Correct
else:
    error = result.error
    return presenter._format_response(400, {
        "error": error.message,
        "code": error.code or "ERROR"
    })
```

**Issue:** The handler is calling `presenter.present_success(result.value)` but:
- `result.value` is a `UserProfileViewModel` (dataclass)
- `presenter.present_success()` expects to convert it to dict using `asdict()`
- This should work, but the error handling path is inconsistent

### The Real Problem: Inconsistent Error Handling

The error path tries to access `result.error.message` and `result.error.code`, but:
1. The `Result` class might not have an `error` attribute with those properties
2. The success path uses `result.value` but error path uses `result.error`

---

## 📋 Complete Flow Analysis

### 1. Handler Layer (`get_profile_handler.py`)
```
Lambda Event
    ↓
Extract user_id from Cognito claims
    ↓
Build ProfileController (singleton)
    ↓
Call controller.get_profile(user_id)
    ↓
Return HTTP response
```

**Status:** ✅ Mostly OK, but error handling needs review

---

### 2. Controller Layer (`profile_controller.py`)
```
get_profile(user_id: str)
    ↓
Call use_case.execute(user_id)
    ↓
Check result.is_success
    ↓
Map Response DTO → UserProfileViewModel
    ↓
Return OperationResult[UserProfileViewModel]
```

**Status:** ✅ Good - proper mapping and error handling

---

### 3. Use Case Layer (`user_profile_use_cases.py`)
```
GetProfileUseCase.execute(user_id)
    ↓
Query repository.get_by_user_id(user_id)
    ↓
If not found: return Result.failure()
    ↓
Map Entity → GetProfileResponse DTO
    ↓
Return Result.success(response)
```

**Status:** ✅ Good - proper error handling

---

### 4. Presenter Layer (`http_presenter.py`)
```
present_success(data: UserProfileViewModel)
    ↓
Convert dataclass to dict using asdict()
    ↓
Format as HTTP response with status 200
    ↓
Return {"statusCode": 200, "headers": {...}, "body": JSON}
```

**Status:** ✅ Good - proper serialization

---

## 🐛 Issues Found

### Issue 1: Handler Error Path Bug
**Severity:** HIGH

The error handling in handler assumes `result.error` has `.message` and `.code` attributes:
```python
error = result.error
return presenter._format_response(400, {
    "error": error.message,  # ❌ May not exist
    "code": error.code or "ERROR"  # ❌ May not exist
})
```

**Fix:** Check what `Result` class actually returns for errors.

---

### Issue 2: Inconsistent Result Handling
**Severity:** MEDIUM

Handler uses `result.value` for success but `result.error` for failure. Need to verify `Result` class structure:
- Does it have `.value` and `.error` attributes?
- Are they mutually exclusive?
- What's the actual structure?

---

### Issue 3: Missing Null Checks
**Severity:** MEDIUM

In `profile_controller.py`, the mapping assumes all fields exist:
```python
view_model = UserProfileViewModel(
    user_id=response.user_id,  # What if response is None?
    email=response.email,
    # ... more fields
)
```

---

## ✅ What Works Well

1. **Proper Dependency Injection** - Controller receives use cases
2. **Proper DTO Mapping** - Response DTO → View Model
3. **Proper Error Handling in Use Case** - Returns Result with failure message
4. **Proper Serialization** - Dataclass to dict conversion
5. **Singleton Pattern** - Lambda container reuse optimization

---

## 🧪 Test Script

Use the provided `test_get_profile.sh`:

```bash
# 1. Make it executable
chmod +x test_get_profile.sh

# 2. Update API_ENDPOINT in the script
# 3. Run it
./test_get_profile.sh
```

---

## 🔧 Recommended Fixes

### Fix 1: Verify Result Class Structure
```bash
grep -r "class Result" src/
```

### Fix 2: Update Handler Error Handling
```python
# After verifying Result structure, update:
if result.is_success:
    return presenter.present_success(result.value)
else:
    # Use proper error handling based on Result class
    return presenter.present_bad_request(str(result.error))
```

### Fix 3: Add Null Checks
```python
if not response:
    return OperationResult.fail("Invalid response from use case", "INTERNAL_ERROR")
```

---

## 📊 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ Lambda Handler (get_profile_handler.py)                     │
│ - Extract user_id from Cognito claims                       │
│ - Build ProfileController (singleton)                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ ProfileController (profile_controller.py)                   │
│ - Call GetProfileUseCase.execute(user_id)                   │
│ - Map Response DTO → UserProfileViewModel                   │
│ - Return OperationResult[UserProfileViewModel]              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ GetProfileUseCase (user_profile_use_cases.py)               │
│ - Query repository.get_by_user_id(user_id)                  │
│ - Map Entity → GetProfileResponse DTO                       │
│ - Return Result.success(response)                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ UserProfileRepository (DynamoDB)                            │
│ - Query user profile by user_id                             │
│ - Return UserProfile entity or None                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Next Steps

1. **Verify Result class structure** - Check `shared/result.py`
2. **Fix handler error handling** - Update error path
3. **Add null checks** - Defensive programming
4. **Test with curl** - Use the test script
5. **Check CloudWatch logs** - Monitor for errors
