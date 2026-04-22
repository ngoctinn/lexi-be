# Implementation Tasks — User Onboarding Flow

**Version:** 1.1  
**Status:** Ready to implement

---

## Task 1: Fix bug `update_profile_info()` trong UserProfile entity

**Status:** pending  
**Priority:** HIGH — bug ảnh hưởng cả profile update lẫn onboarding

**File:** `src/domain/entities/user_profile.py`

**Vấn đề:** `if avatar_url:` → nếu user gửi `""` để xóa avatar, điều kiện False → không lưu được.

**Thay đổi:**
```python
# Trước (sai)
if avatar_url:
    self.avatar_url = avatar_url

# Sau (đúng)
if avatar_url is not None:
    self.avatar_url = avatar_url
```

**Done khi:** Gọi `update_profile_info(avatar_url="")` → `self.avatar_url` được set thành `""`.

---

## Task 2: Fix bug fallback `learning_goal` trong DynamoDBUserRepo

**Status:** pending  
**Priority:** HIGH — field `learning_goal` không còn tồn tại

**File:** `src/infrastructure/persistence/dynamo_user_repo.py`

**Vấn đề:** `get_by_user_id()` đang fallback sang field cũ không tồn tại.

**Thay đổi:**
```python
# Trước (sai)
target_level=ProficiencyLevel(item.get("target_level") or item.get("learning_goal", "B2")),

# Sau (đúng)
target_level=ProficiencyLevel(item.get("target_level", "B2")),
```

**Done khi:** `get_by_user_id()` không còn reference đến `learning_goal`.

---

## Task 3: Tạo CompleteOnboardingCommand DTO

**Status:** pending

**Files:**
- `src/application/dtos/onboarding/__init__.py` (rỗng)
- `src/application/dtos/onboarding/complete_onboarding_command.py`

**Nội dung:**
```python
from dataclasses import dataclass

@dataclass
class CompleteOnboardingCommand:
    user_id: str
    display_name: str
    current_level: str
    target_level: str
    avatar_url: str = ""
```

**Done khi:** Import được từ module khác.

---

## Task 4: Tạo CompleteOnboardingResponse DTO

**Status:** pending

**File:** `src/application/dtos/onboarding/complete_onboarding_response.py`

**Nội dung:**
```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class CompleteOnboardingResponse:
    is_success: bool
    message: str
    profile: Optional[dict] = None
```

**Done khi:** Import được từ module khác.

---

## Task 5: Tạo validation functions

**Status:** pending

**Files:**
- `src/application/validators/__init__.py` (rỗng)
- `src/application/validators/onboarding_validators.py`

**Nội dung:** 3 functions theo design section 5:
- `validate_display_name(v: str) -> tuple[bool, str]`
- `validate_cefr_level(v: str, field_name: str) -> tuple[bool, str]`
- `validate_avatar_url(v: str) -> tuple[bool, str]`

**Done khi:**
- `validate_display_name("")` → `(False, "...trống...")`
- `validate_display_name("a" * 51)` → `(False, "...50 ký tự...")`
- `validate_cefr_level("X9")` → `(False, "...không hợp lệ...")`
- `validate_cefr_level("B2")` → `(True, "")`
- `validate_avatar_url("http://...")` → `(False, "...HTTPS...")`
- `validate_avatar_url("")` → `(True, "")`

---

## Task 6: Implement CompleteOnboardingUseCase

**Status:** pending

**Files:**
- `src/application/use_cases/onboarding/__init__.py` (rỗng)
- `src/application/use_cases/onboarding/complete_onboarding_uc.py`

**Logic theo thứ tự (xem design section 4):**
1. `repo.get_by_user_id(user_id)` → 404 nếu None
2. Validate `display_name`
3. Validate `current_level` → convert sang `ProficiencyLevel`
4. Validate `target_level` → convert sang `ProficiencyLevel`
5. Validate `avatar_url`
6. `profile.update_profile_info(display_name=..., avatar_url=..., current_level=..., target_level=..., is_new_user=False)`
7. `repo.update(profile)`
8. Trả về `Result.success(CompleteOnboardingResponse(...))`

**Profile dict trong response** phải chứa: `user_id`, `display_name`, `current_level`, `target_level`, `avatar_url`, `is_new_user`, `role`, `is_active`, `current_streak`, `total_words_learned`.

**Done khi:**
- Happy path: trả về `Result.success` với `is_new_user=False`
- `display_name=""` → `Result.failure("...trống...")`
- `current_level="X9"` → `Result.failure("...không hợp lệ...")`
- Profile không tồn tại → `Result.failure("Hồ sơ không tồn tại")`

---

## Task 7: Tạo complete_onboarding_handler

**Status:** pending

**Files:**
- `src/infrastructure/handlers/onboarding/__init__.py` (rỗng)
- `src/infrastructure/handlers/onboarding/complete_onboarding_handler.py`

**Pattern:** Theo design section 7 — giống các handler hiện có.

**HTTP mapping:**
- Use case success → 200
- `"không tồn tại"` trong error → 404
- Các lỗi validation khác → 400
- KeyError khi lấy JWT → 401
- JSONDecodeError → 400

**Done khi:** Handler trả đúng status code cho từng case.

---

## Task 8: Cập nhật SAM template

**Status:** pending

**File:** `template.yaml`

**Thêm:** `CompleteOnboardingFunction` theo design section 8.

**Kiểm tra:** `sam validate` không có lỗi.

**Done khi:** `sam validate` pass.

---

## Task 9: Verify `create_user_profile.py` set `is_new_user=True`

**Status:** pending

**File:** `src/application/use_cases/auth/create_user_profile.py`

**Kiểm tra:** `UserProfile(...)` được tạo với `is_new_user=True` (default của entity là `True` nên thường đã đúng).

**Done khi:** Xác nhận profile mới luôn có `is_new_user=True`. Nếu đã đúng → task này chỉ cần verify, không cần sửa.

---

## Task 10: Manual testing

**Status:** pending

**Test cases:**

```bash
# Setup: lấy JWT token của user mới (is_new_user=true)

# TC1: Happy path đầy đủ
curl -X POST https://<api>/onboarding/complete \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"display_name":"Minh Tú","current_level":"A2","target_level":"B2","avatar_url":"https://api.dicebear.com/7.x/avataaars/svg?seed=test"}'
# Expect: 200, is_new_user=false

# TC2: Không có avatar_url
curl ... -d '{"display_name":"Minh Tú","current_level":"A2","target_level":"B2"}'
# Expect: 200, avatar_url=""

# TC3: display_name rỗng
curl ... -d '{"display_name":"","current_level":"A2","target_level":"B2"}'
# Expect: 400

# TC4: display_name > 50 ký tự
curl ... -d '{"display_name":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","current_level":"A2","target_level":"B2"}'
# Expect: 400

# TC5: current_level không hợp lệ
curl ... -d '{"display_name":"Test","current_level":"X9","target_level":"B2"}'
# Expect: 400

# TC6: avatar_url dùng http (không phải https)
curl ... -d '{"display_name":"Test","current_level":"A2","target_level":"B2","avatar_url":"http://example.com/img.png"}'
# Expect: 400

# TC7: Verify DynamoDB sau TC1
aws dynamodb get-item \
  --table-name LexiApp \
  --key '{"PK":{"S":"USER#<user_id>"},"SK":{"S":"PROFILE"}}' \
  --query 'Item.{is_new_user:is_new_user,display_name:display_name,current_level:current_level}'
# Expect: is_new_user=false, display_name="Minh Tú", current_level="A2"
```

**Done khi:** Tất cả 7 test case pass.

---

## Thứ tự thực hiện

```
Task 1 (fix entity bug)
Task 2 (fix repo bug)
Task 3, 4 (DTOs)
Task 5 (validators)
Task 6 (use case)
Task 7 (handler)
Task 8 (SAM template)
Task 9 (verify auth)
Task 10 (manual test)
```

Task 1 và 2 là **bug fix** — nên làm trước vì ảnh hưởng đến code hiện tại, không chỉ onboarding.
