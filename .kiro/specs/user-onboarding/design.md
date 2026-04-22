# Design Document — User Onboarding Flow

**Version:** 1.1  
**Status:** Confirmed  
**Ngày chốt:** 2026-04-22

---

## 1. Nguồn sự thật (Single Source of Truth)

### 1.1 Field onboarding flag

**Tên field duy nhất:** `is_new_user` (Boolean)

| Giá trị | Ý nghĩa |
|---|---|
| `true` | User chưa hoàn tất onboarding |
| `false` | User đã hoàn tất onboarding |

> ⚠️ `database.yaml` GSI3 projection đang dùng `is_onboarded` — đây là **lỗi cũ trong config**, không phản ánh code thực tế. Field trong DynamoDB item thực tế là `is_new_user`. Không cần sửa GSI3 vì onboarding không query qua GSI3.

### 1.2 Fields thu thập trong Onboarding

| Field | Type | Bắt buộc | Validation | DynamoDB attribute |
|---|---|---|---|---|
| `display_name` | string | ✅ | 1–50 ký tự, không rỗng | `display_name` |
| `current_level` | string | ✅ | Enum: A1/A2/B1/B2/C1/C2 | `current_level` |
| `target_level` | string | ✅ | Enum: A1/A2/B1/B2/C1/C2 | `target_level` |
| `avatar_url` | string | ❌ | HTTPS URL hoặc `""` | `avatar_url` |

**Không có field `learning_goal_text`** — đã loại bỏ.

### 1.3 UserProfile Entity — Trạng thái hiện tại (không thay đổi)

```python
@dataclass
class UserProfile:
    user_id: str = ""
    email: str = ""
    display_name: str = ""
    avatar_url: str = ""
    current_level: ProficiencyLevel = ProficiencyLevel.A1
    target_level: ProficiencyLevel = ProficiencyLevel.B2
    role: Role = Role.LEARNER
    is_active: bool = True
    is_new_user: bool = True      # ← flag onboarding
    current_streak: int = 0
    last_completed_at: str = ""
    total_words_learned: int = 0
```

Entity **không cần thêm field mới** cho onboarding.

### 1.4 DynamoDB Item Pattern

```
PK = USER#{user_id}
SK = PROFILE
```

Các attribute liên quan onboarding được lưu trực tiếp trong item này.

---

## 2. Architecture

```
Frontend (Next.js)
  ├── GET /profile          → kiểm tra is_new_user
  ├── Redirect /onboarding  → nếu is_new_user = true
  └── POST /onboarding/complete
        └── CompleteOnboardingFunction (Lambda)
              └── CompleteOnboardingUseCase
                    └── DynamoDBUserRepo.update()
                          └── DynamoDB: PK=USER#{id}, SK=PROFILE
```

**Avatar:** Frontend dùng thư viện ngoài (DiceBear, v.v.) → user chọn → URL gửi kèm request. Không có endpoint upload.

---

## 3. API Contract

### POST /onboarding/complete

**Authentication:** Cognito JWT (bắt buộc)  
**user_id:** lấy từ JWT claims `sub`, không nhận từ body

**Request Body:**
```json
{
  "display_name": "Minh Tú",
  "current_level": "A2",
  "target_level": "B2",
  "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=abc123"
}
```

**Validation rules:**

| Field | Rule | Error khi sai |
|---|---|---|
| `display_name` | Required, 1–50 chars, không chỉ whitespace | 400 |
| `current_level` | Required, phải là A1/A2/B1/B2/C1/C2 | 400 |
| `target_level` | Required, phải là A1/A2/B1/B2/C1/C2 | 400 |
| `avatar_url` | Optional; nếu có phải bắt đầu `https://` | 400 |

**Success Response (200):**
```json
{
  "success": true,
  "message": "Onboarding hoàn tất",
  "profile": {
    "user_id": "abc123",
    "display_name": "Minh Tú",
    "current_level": "A2",
    "target_level": "B2",
    "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=abc123",
    "is_new_user": false,
    "role": "LEARNER",
    "is_active": true,
    "current_streak": 0,
    "total_words_learned": 0
  }
}
```

**Error Responses:**

| Status | Khi nào |
|---|---|
| 400 | Validation thất bại — body kèm `"error": "<message>"` |
| 401 | Thiếu hoặc sai JWT |
| 404 | Profile không tồn tại trong DB |
| 500 | Lỗi DynamoDB hoặc hệ thống |

---

## 4. Use Case Design

### CompleteOnboardingUseCase

**File:** `src/application/use_cases/onboarding/complete_onboarding_uc.py`

**Input DTO:**
```python
@dataclass
class CompleteOnboardingCommand:
    user_id: str
    display_name: str
    current_level: str
    target_level: str
    avatar_url: str = ""
```

**Output:** `Result[CompleteOnboardingResponse, str]`

```python
@dataclass
class CompleteOnboardingResponse:
    is_success: bool
    message: str
    profile: dict | None = None   # serialized profile fields
```

**Logic (theo thứ tự):**
1. Lấy profile từ repo theo `user_id` → nếu không có: `Result.failure("Hồ sơ không tồn tại")` → 404
2. Validate `display_name`: không rỗng, 1–50 chars → 400 nếu sai
3. Validate `current_level`: `ProficiencyLevel(value)` → 400 nếu ValueError
4. Validate `target_level`: `ProficiencyLevel(value)` → 400 nếu ValueError
5. Validate `avatar_url`: nếu có, phải bắt đầu `https://` → 400 nếu sai
6. Gọi `profile.update_profile_info(display_name=..., avatar_url=..., current_level=..., target_level=..., is_new_user=False)`
7. Gọi `repo.update(profile)`
8. Trả về `Result.success(CompleteOnboardingResponse(...))`

---

## 5. Validation Functions

**File:** `src/application/validators/onboarding_validators.py`

```python
from domain.value_objects.enums import ProficiencyLevel

def validate_display_name(v: str) -> tuple[bool, str]:
    if not v or not v.strip():
        return False, "Tên hiển thị không được để trống"
    if len(v.strip()) > 50:
        return False, "Tên hiển thị không được vượt quá 50 ký tự"
    return True, ""

def validate_cefr_level(v: str, field_name: str = "Trình độ") -> tuple[bool, str]:
    try:
        ProficiencyLevel(v)
        return True, ""
    except ValueError:
        return False, f"{field_name} '{v}' không hợp lệ. Chỉ chấp nhận: A1, A2, B1, B2, C1, C2"

def validate_avatar_url(v: str) -> tuple[bool, str]:
    if not v:
        return True, ""  # optional
    if not v.startswith("https://"):
        return False, "URL ảnh đại diện phải dùng HTTPS"
    return True, ""
```

---

## 6. Repository — Các thay đổi cần thiết

### 6.1 Bug cần fix trong `get_by_user_id()`

**Hiện tại (sai):**
```python
target_level=ProficiencyLevel(item.get("target_level") or item.get("learning_goal", "B2")),
```

**Sau khi fix:**
```python
target_level=ProficiencyLevel(item.get("target_level", "B2")),
```

`learning_goal` là field cũ không còn tồn tại, cần xóa fallback này.

### 6.2 Bug cần fix trong `update_profile_info()` của entity

**Hiện tại (sai):**
```python
if avatar_url:
    self.avatar_url = avatar_url
```

Nếu user muốn xóa avatar (gửi `""`), điều kiện `if avatar_url` sẽ là `False` → không lưu được.

**Sau khi fix:**
```python
if avatar_url is not None:
    self.avatar_url = avatar_url
```

### 6.3 `update()` method — không cần thay đổi

Method hiện tại đã update đúng tất cả fields cần thiết cho onboarding.

---

## 7. Lambda Handler

**File:** `src/infrastructure/handlers/onboarding/complete_onboarding_handler.py`

Pattern giống các handler hiện có:

```python
import json
from infrastructure.persistence.dynamo_user_repo import DynamoDBUserRepo
from application.use_cases.onboarding.complete_onboarding_uc import CompleteOnboardingUseCase
from application.dtos.onboarding.complete_onboarding_command import CompleteOnboardingCommand

user_repo = DynamoDBUserRepo()
complete_onboarding_uc = CompleteOnboardingUseCase(user_repo)

def _response(status: int, body: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body),
    }

def handler(event, context):
    try:
        user_id = event["requestContext"]["authorizer"]["claims"]["sub"]
    except KeyError:
        return _response(401, {"error": "Unauthorized"})

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _response(400, {"error": "JSON không hợp lệ"})

    command = CompleteOnboardingCommand(
        user_id=user_id,
        display_name=body.get("display_name", ""),
        current_level=body.get("current_level", ""),
        target_level=body.get("target_level", ""),
        avatar_url=body.get("avatar_url", ""),
    )

    result = complete_onboarding_uc.execute(command)

    if result.is_success:
        return _response(200, {"success": True, "message": result.value.message, "profile": result.value.profile})

    error = result.error
    if "không tồn tại" in error:
        return _response(404, {"error": error})
    return _response(400, {"error": error})
```

---

## 8. SAM Template

Thêm **1 Lambda function** duy nhất:

```yaml
CompleteOnboardingFunction:
  Type: AWS::Serverless::Function
  Properties:
    CodeUri: src/
    Handler: infrastructure.handlers.onboarding.complete_onboarding_handler.handler
    Runtime: python3.12
    Environment:
      Variables:
        LEXI_TABLE_NAME: !Ref LexiAppTable
    Policies:
      - DynamoDBCrudPolicy:
          TableName: !Ref LexiAppTable
    Events:
      CompleteOnboarding:
        Type: Api
        Properties:
          Path: /onboarding/complete
          Method: POST
          RestApiId: !Ref LexiApi
          Auth:
            Authorizer: CognitoAuthorizer
```

**Không cần:** S3 bucket, presigned URL endpoint, avatar upload service.

---

## 9. Access Control

**MVP:** Frontend guard duy nhất.

```typescript
// Pseudo-code
function OnboardingGuard({ children }) {
  const profile = useProfile(); // từ GET /profile
  if (profile.is_new_user) redirect("/onboarding");
  return children;
}
```

Protected routes: `/dashboard`, `/scenarios`, `/sessions/*`, `/flashcards`, `/profile`  
Unprotected routes: `/login`, `/signup`, `/onboarding`

Backend **không** enforce guard trong MVP.

---

## 10. Tóm tắt thay đổi cần thực hiện

| File | Loại thay đổi | Mô tả |
|---|---|---|
| `domain/entities/user_profile.py` | **Fix bug** | `update_profile_info()`: đổi `if avatar_url:` → `if avatar_url is not None:` |
| `infrastructure/persistence/dynamo_user_repo.py` | **Fix bug** | `get_by_user_id()`: xóa fallback `or item.get("learning_goal", "B2")` |
| `application/dtos/onboarding/complete_onboarding_command.py` | **Tạo mới** | DTO command |
| `application/dtos/onboarding/complete_onboarding_response.py` | **Tạo mới** | DTO response |
| `application/validators/onboarding_validators.py` | **Tạo mới** | 3 validation functions |
| `application/use_cases/onboarding/complete_onboarding_uc.py` | **Tạo mới** | Use case |
| `infrastructure/handlers/onboarding/complete_onboarding_handler.py` | **Tạo mới** | Lambda handler |
| `template.yaml` | **Cập nhật** | Thêm CompleteOnboardingFunction |
