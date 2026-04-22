# Design Document — Admin Management

**Version:** 1.0  
**Status:** Confirmed  
**Ngày chốt:** 2026-04-22

---

## 1. Nguồn sự thật (Single Source of Truth)

### 1.1 Admin Authorization

Admin được xác định bằng `role = ADMIN` trong UserProfile. JWT claims từ Cognito chứa `custom:role` hoặc được lấy từ DynamoDB profile.

**Cách implement đơn giản nhất cho MVP:** Handler tự query profile theo `user_id` từ JWT, kiểm tra `role == "ADMIN"`.

### 1.1.1 Cách tạo Admin — Bootstrap Problem

**Vấn đề:** Không có endpoint nào tạo admin, vì ai gọi endpoint đó đầu tiên?

**Giải pháp cho MVP: Promote thủ công qua AWS CLI**

Admin đăng ký tài khoản bình thường qua app (role mặc định = LEARNER), sau đó người có AWS access chạy lệnh CLI để promote:

```bash
# Bước 1: Lấy user_id (sub) từ Cognito sau khi đăng ký
aws cognito-idp list-users \
  --user-pool-id <USER_POOL_ID> \
  --filter "email = \"admin@example.com\"" \
  --query "Users[0].Username" \
  --output text

# Bước 2: Promote role trong DynamoDB
aws dynamodb update-item \
  --table-name LexiApp \
  --key '{"PK":{"S":"USER#<user_id>"},"SK":{"S":"PROFILE"}}' \
  --update-expression "SET #r = :admin, is_new_user = :false" \
  --expression-attribute-names '{"#r":"role"}' \
  --expression-attribute-values '{":admin":{"S":"ADMIN"},":false":{"BOOL":false}}'
```

**Lý do chọn cách này:**
- Không cần code thêm gì
- Admin là role đặc biệt, số lượng rất ít (1-2 người)
- Người setup hệ thống đã có AWS access
- Tránh bootstrap problem (ai tạo admin đầu tiên?)
- Phù hợp với nguyên tắc Simplicity First

**Không làm:**
- Endpoint `POST /admin/promote` — cần ai đó có quyền gọi trước, circular dependency
- Cognito custom attribute `custom:role` — thêm complexity không cần thiết cho MVP

### 1.2 Icon Scenario — Quyết định thiết kế (dựa trên Lucide docs chính thức)

**Icon KHÔNG được lưu trong database.**

Lucide docs chính thức ([Dynamic Icon Component](https://github.com/lucide-icons/lucide/blob/main/docs/guide/react/advanced/dynamic-icon-component.md)) phân biệt rõ 2 use case:

| Use case | Cách làm | Khuyến nghị |
|---|---|---|
| Icon name biết trước (static) | Import trực tiếp hoặc static map | ✅ **Recommended** |
| Icon name từ DB/runtime | `DynamicIcon` từ `lucide-react/dynamic` | ⚠️ Có caveats: import ALL icons, tăng bundle size, flashing |

**Frontend hiện tại đang dùng đúng pattern được khuyến nghị:**
```ts
// scenario-contexts.ts — static map, tree-shakeable
const SCENARIO_CONTEXT_ICON_MAP: Record<string, LucideIcon> = {
  "Tại quán cà phê": Coffee,
  "Du lịch & Khách sạn": Plane,
  // ...
}

// scenario-picker.tsx — lookup bằng context string
const Icon = SCENARIO_CONTEXT_ICON_MAP[scenario.context] ?? BookOpen;
```

**Flow đúng:**
```
Admin chọn context từ dropdown (14 options cố định)
→ Backend lưu context string (e.g. "Tại quán cà phê")
→ Frontend tra SCENARIO_CONTEXT_ICON_MAP → render Coffee icon
→ Fallback: BookOpen nếu context không có trong map
```

**Kết luận:** Không cần thêm field `icon` vào Scenario entity hay database. `context` string là đủ. Nếu cần thêm context mới, chỉ cần cập nhật `SCENARIO_CONTEXT_OPTIONS` ở frontend.

### 1.3 DynamoDB GSI3 — Admin list query (dựa trên AWS docs chính thức)

```python
@dataclass
class Scenario:
    scenario_id: str          # ULID string
    scenario_title: str       # Bắt buộc
    context: str              # Bắt buộc — dùng làm icon lookup key ở frontend
    roles: List[str]          # Đúng 2 phần tử (MVP) — source of truth duy nhất
    goals: List[str]          # Ít nhất 1 phần tử
    is_active: bool = True
    usage_count: int = 0
    difficulty_level: str = ""  # A1/A2/B1/B2/C1/C2 — THÊM MỚI
    order: int = 0              # Thứ tự hiển thị — THÊM MỚI
    notes: str = ""             # Ghi chú nội bộ — THÊM MỚI
    created_at: str = ""
    updated_at: str = ""
```

**Các field cần XÓA khỏi entity** (bất nhất với business spec §4.5 và §7.3):
- `my_character` — không dùng, roles[] là source of truth
- `ai_character` — không dùng, roles[] là source of truth
- `user_roles` — business spec §7.3 nói không dùng 2 mảng này
- `ai_roles` — business spec §7.3 nói không dùng 2 mảng này

**Lưu ý migration:** `__post_init__` hiện tại đang set `user_roles = list(roles)` và `ai_roles = list(roles)` để backward compatibility. Sau khi xóa, cần kiểm tra không có code nào đang đọc 4 field này.

### 1.4 AdminUser — Mapping với UserProfile

Frontend `AdminUser` type có một số field không tồn tại trong backend `UserProfile`. Cần làm rõ:

| Frontend field | Backend field | Ghi chú |
|---|---|---|
| `id` | `user_id` | Rename khi serialize |
| `display_name` | `display_name` | ✅ Khớp |
| `email` | `email` | ✅ Khớp |
| `current_level` | `current_level` | ✅ Khớp |
| `target_level` | `target_level` | ✅ Khớp |
| `learning_goal_text` | ❌ Không có | Field đã bị loại bỏ — frontend cần xóa |
| `status` | ❌ Không có | Backend chỉ có `is_active` (bool). Frontend cần map: `is_active=true` → `"active"`, `is_active=false` → `"paused"` |
| `sessions_completed` | ❌ Không có | Không có trong UserProfile — bỏ hoặc tính từ session count |
| `streak` | `current_streak` | Rename khi serialize |
| `last_active_at` | `last_completed_at` | Rename khi serialize |
| `notes` | ❌ Không có | Field admin-only — cần thêm vào UserProfile hoặc lưu riêng |
| `avatar_url` | `avatar_url` | ✅ Khớp |

**Quyết định cho MVP:**
- `status`: Backend trả `is_active` (bool), frontend tự map sang status string
- `sessions_completed`: Bỏ khỏi list response (không có trong UserProfile)
- `notes`: Thêm field `admin_notes: str = ""` vào UserProfile entity
- `learning_goal_text`: Frontend cần xóa field này

### 1.5 DynamoDB Item Pattern — Scenario

```
PK = SCENARIO#{scenario_id}
SK = METADATA
GSI3PK = SCENARIO          ← dùng GSI3 để list all
GSI3SK = created_at        ← sort theo thời gian tạo
EntityType = SCENARIO
```

**Attributes lưu trong item:**
`scenario_id`, `scenario_title`, `context`, `roles`, `goals`, `is_active`, `usage_count`, `difficulty_level`, `order`, `notes`, `created_at`, `updated_at`

### 1.4 DynamoDB Item Pattern — UserProfile (đã có, không thay đổi)

```
PK = USER#{user_id}
SK = PROFILE
GSI3PK = USER_PROFILE      ← dùng GSI3 để list all users
GSI3SK = joined_at
EntityType = USER_PROFILE
```

---

## 2. Architecture

```
Admin Frontend
  ├── GET  /admin/users                    → ListAdminUsersFunction
  ├── PATCH /admin/users/{user_id}         → UpdateAdminUserFunction
  ├── GET  /admin/scenarios                → ListAdminScenariosFunction
  ├── POST /admin/scenarios                → CreateAdminScenarioFunction
  └── PATCH /admin/scenarios/{scenario_id} → UpdateAdminScenarioFunction

Shared:
  └── AdminAuthGuard (inline trong mỗi handler)
        └── DynamoDBUserRepo.get_by_user_id() → check role == ADMIN
```

---

## 3. API Contracts

### 3.1 GET /admin/users

**Auth:** Cognito JWT + role ADMIN

**Query params:**
- `limit`: int, default 20, max 100
- `last_key`: string (base64 encoded cursor, optional)

**Response 200:**
```json
{
  "users": [
    {
      "user_id": "abc123",
      "email": "user@example.com",
      "display_name": "Minh Tú",
      "avatar_url": "https://...",
      "current_level": "A2",
      "target_level": "B2",
      "is_active": true,
      "is_new_user": false,
      "current_streak": 5,
      "total_words_learned": 42,
      "joined_at": "2026-04-01T10:00:00Z"
    }
  ],
  "next_key": "eyJQSyI6..."
}
```

---

### 3.2 PATCH /admin/users/{user_id}

**Auth:** Cognito JWT + role ADMIN

**Request Body (tất cả optional):**
```json
{
  "is_active": false,
  "current_level": "B1",
  "target_level": "B2"
}
```

**Validation:**
- `current_level`, `target_level`: nếu có phải là A1/A2/B1/B2/C1/C2
- Các field khác bị ignore (không update email, role, streak, v.v.)

**Response 200:**
```json
{
  "success": true,
  "user": { ...updated profile fields... }
}
```

---

### 3.3 GET /admin/scenarios

**Auth:** Cognito JWT + role ADMIN

**Response 200:**
```json
{
  "scenarios": [
    {
      "scenario_id": "s1",
      "scenario_title": "Gọi cà phê",
      "context": "Tại quán cà phê",
      "roles": ["Khách hàng", "Barista"],
      "goals": ["Chọn đồ uống", "Hỏi về giá"],
      "is_active": true,
      "usage_count": 150,
      "difficulty_level": "A1",
      "order": 1,
      "notes": ""
    }
  ]
}
```

---

### 3.4 POST /admin/scenarios

**Auth:** Cognito JWT + role ADMIN

**Request Body:**
```json
{
  "scenario_title": "Đặt phòng khách sạn",
  "context": "Du lịch & Khách sạn",
  "roles": ["Khách du lịch", "Lễ tân"],
  "goals": ["Hỏi phòng trống", "Xác nhận giá"],
  "difficulty_level": "A2",
  "order": 15,
  "notes": "Scenario mới cho A2",
  "is_active": true
}
```

**Validation:**
- `scenario_title`: required, 1-100 chars
- `context`: required, 1-100 chars
- `roles`: required, đúng 2 phần tử
- `goals`: required, ít nhất 1 phần tử
- `difficulty_level`: optional, nếu có phải là A1/A2/B1/B2/C1/C2

**Response 201:**
```json
{
  "success": true,
  "scenario": { ...created scenario... }
}
```

---

### 3.5 PATCH /admin/scenarios/{scenario_id}

**Auth:** Cognito JWT + role ADMIN

**Request Body (tất cả optional):**
```json
{
  "scenario_title": "...",
  "context": "...",
  "roles": ["...", "..."],
  "goals": ["..."],
  "difficulty_level": "B1",
  "order": 5,
  "notes": "...",
  "is_active": false
}
```

**Validation:** Giống POST nhưng tất cả optional.

**Response 200:**
```json
{
  "success": true,
  "scenario": { ...updated scenario... }
}
```

---

## 4. Domain Entity Changes

### 4.1 Scenario entity — Thêm fields mới

**File:** `src/domain/entities/scenario.py`

Thêm vào dataclass:
```python
difficulty_level: str = ""   # CEFR level khuyến nghị
order: int = 0               # Thứ tự hiển thị
notes: str = ""              # Ghi chú nội bộ của Admin
created_at: str = ""
updated_at: str = ""
```

Thêm method:
```python
def activate(self):
    self.is_active = True

def update_info(self, **kwargs):
    """Cập nhật các field được phép."""
    allowed = {"scenario_title", "context", "roles", "goals",
               "difficulty_level", "order", "notes", "is_active"}
    for key, value in kwargs.items():
        if key in allowed and value is not None:
            setattr(self, key, value)
```

### 4.2 ScenarioRepository interface — Thêm methods

**File:** `src/application/repositories/scenario_repository.py`

Thêm:
```python
@abstractmethod
def list_all(self) -> List[Scenario]:
    """Lấy tất cả scenario (kể cả inactive) — dùng cho Admin."""
    ...

@abstractmethod
def create(self, scenario: Scenario) -> None:
    """Tạo scenario mới."""
    ...

@abstractmethod
def update(self, scenario: Scenario) -> None:
    """Cập nhật scenario đã tồn tại."""
    ...
```

### 4.3 UserProfileRepository interface — Thêm method

**File:** `src/application/repositories/user_profile_repository.py`

Thêm:
```python
@abstractmethod
def list_learners(self, limit: int, last_key: Optional[dict]) -> tuple[List[UserProfile], Optional[dict]]:
    """Liệt kê tất cả learner — dùng cho Admin."""
    ...
```

---

## 5. New Repository: DynamoScenarioRepository

**File:** `src/infrastructure/persistence/dynamo_scenario_repo.py`

### DynamoDB operations:

**`create(scenario)`** — `put_item` với `ConditionExpression="attribute_not_exists(PK)"`

**`save(scenario)` / `update(scenario)`** — `update_item` với UpdateExpression

**`get_by_id(scenario_id)`** — `get_item` với `PK=SCENARIO#{id}`, `SK=METADATA`

**`list_active()`** — Query GSI3 với `EntityType=SCENARIO` + filter `is_active=true`

**`list_all()`** — Query GSI3 với `EntityType=SCENARIO` (không filter)

### Item structure:
```python
{
    "PK": f"SCENARIO#{scenario.scenario_id}",
    "SK": "METADATA",
    "GSI3PK": "SCENARIO",
    "GSI3SK": scenario.created_at,
    "EntityType": "SCENARIO",
    "scenario_id": scenario.scenario_id,
    "scenario_title": scenario.scenario_title,
    "context": scenario.context,
    "roles": scenario.roles,          # List[str]
    "goals": scenario.goals,          # List[str]
    "is_active": scenario.is_active,
    "usage_count": scenario.usage_count,
    "difficulty_level": scenario.difficulty_level,
    "order": scenario.order,
    "notes": scenario.notes,
    "created_at": scenario.created_at,
    "updated_at": scenario.updated_at,
}
```

---

## 6. UserProfileRepository — Thêm list_learners

**File:** `src/infrastructure/persistence/dynamo_user_repo.py`

```python
def list_learners(self, limit: int = 20, last_key: Optional[dict] = None):
    kwargs = {
        "IndexName": "GSI3-Admin-EntityList",
        "KeyConditionExpression": Key("EntityType").eq("USER_PROFILE"),
        "ScanIndexForward": False,
        "Limit": limit,
    }
    if last_key:
        kwargs["ExclusiveStartKey"] = last_key
    
    response = self._table.query(**kwargs)
    profiles = [self._to_entity(item) for item in response.get("Items", [])]
    next_key = response.get("LastEvaluatedKey")
    return profiles, next_key
```

**Lưu ý:** GSI3 projection hiện tại có `is_onboarded` (sai) thay vì `is_new_user`. Cần thêm `is_new_user` vào GSI3 projection trong `database.yaml`.

---

## 7. Use Cases

### 7.1 ListAdminUsersUseCase

**File:** `src/application/use_cases/admin/list_admin_users_uc.py`

Logic:
1. Query `repo.list_learners(limit, last_key)`
2. Filter chỉ giữ `role == LEARNER` (GSI3 trả về tất cả USER_PROFILE)
3. Map sang response dict
4. Trả về `Result.success({users, next_key})`

### 7.2 UpdateAdminUserUseCase

**File:** `src/application/use_cases/admin/update_admin_user_uc.py`

Logic:
1. `repo.get_by_user_id(target_user_id)` → 404 nếu không có
2. Validate `current_level`, `target_level` nếu có
3. Chỉ update các field được phép: `is_active`, `current_level`, `target_level`
4. `repo.update(profile)`
5. Trả về profile đã cập nhật

### 7.3 ListAdminScenariosUseCase

**File:** `src/application/use_cases/admin/list_admin_scenarios_uc.py`

Logic:
1. `scenario_repo.list_all()`
2. Sort theo `order` tăng dần
3. Trả về list

### 7.4 CreateAdminScenarioUseCase

**File:** `src/application/use_cases/admin/create_admin_scenario_uc.py`

Logic:
1. Validate `scenario_title`, `context`, `roles` (2 phần tử), `goals` (≥1)
2. Validate `difficulty_level` nếu có
3. Tạo `Scenario` entity với `scenario_id = new_ulid()`
4. `scenario_repo.create(scenario)`
5. Trả về scenario đã tạo

### 7.5 UpdateAdminScenarioUseCase

**File:** `src/application/use_cases/admin/update_admin_scenario_uc.py`

Logic:
1. `scenario_repo.get_by_id(scenario_id)` → 404 nếu không có
2. Validate các field nếu có
3. `scenario.update_info(**kwargs)`
4. `scenario_repo.update(scenario)`
5. Trả về scenario đã cập nhật

---

## 8. Lambda Handlers

Tất cả handlers đều có pattern giống nhau:

```python
def _check_admin(event, user_repo) -> tuple[str | None, dict | None]:
    """Trả về (user_id, None) nếu là admin, hoặc (None, error_response)."""
    try:
        user_id = event["requestContext"]["authorizer"]["claims"]["sub"]
    except KeyError:
        return None, _response(401, {"error": "Unauthorized"})
    
    profile = user_repo.get_by_user_id(user_id)
    if not profile or profile.role.value != "ADMIN":
        return None, _response(403, {"error": "Forbidden"})
    
    return user_id, None
```

**Files:**
- `src/infrastructure/handlers/admin/list_admin_users_handler.py`
- `src/infrastructure/handlers/admin/update_admin_user_handler.py`
- `src/infrastructure/handlers/admin/list_admin_scenarios_handler.py`
- `src/infrastructure/handlers/admin/create_admin_scenario_handler.py`
- `src/infrastructure/handlers/admin/update_admin_scenario_handler.py`

---

## 9. SAM Template — Thêm 5 Lambda Functions

```yaml
# Admin User Management
ListAdminUsersFunction:
  Path: /admin/users, Method: GET

UpdateAdminUserFunction:
  Path: /admin/users/{user_id}, Method: PATCH

# Admin Scenario Management
ListAdminScenariosFunction:
  Path: /admin/scenarios, Method: GET

CreateAdminScenarioFunction:
  Path: /admin/scenarios, Method: POST

UpdateAdminScenarioFunction:
  Path: /admin/scenarios/{scenario_id}, Method: PATCH
```

Tất cả đều cần:
- `LEXI_TABLE_NAME` env var
- `DynamoDBCrudPolicy` cho `LexiAppTable`
- Cognito authorizer

---

## 10. Database.yaml — Cần fix GSI3 projection

**Vấn đề:** GSI3 projection hiện có `is_onboarded` (sai) — field thực tế là `is_new_user`.

**Fix:** Thay `is_onboarded` → `is_new_user` trong `NonKeyAttributes` của GSI3.

**Lưu ý:** Thay đổi GSI projection yêu cầu xóa và tạo lại GSI (hoặc dùng `UpdateTable`). Với DeletionPolicy: Retain, cần deploy cẩn thận.

---

## 11. Seed Data — 14 Scenarios

Khi migrate sang DynamoDB, cần seed 14 scenario từ `StaticScenarioRepository`. Cách đơn giản nhất: tạo một script seed hoặc Lambda function chạy một lần.

**Mapping difficulty_level từ SCENARIO_METADATA trong scenarios_handler.py:**
```
s1, s1_2, ..., s1_7 → A1
s2, s3 → A2
s4, s5 → B1
s6 → B2
s7 → C1
s8 → C2
```

---

## 12. Tóm tắt thay đổi cần thực hiện

| File | Loại | Mô tả |
|---|---|---|
| `domain/entities/scenario.py` | **Cập nhật** | Xóa `my_character`, `ai_character`, `user_roles`, `ai_roles`. Thêm `difficulty_level`, `order`, `notes`, `created_at`, `updated_at`, method `update_info()`, `activate()` |
| `domain/entities/user_profile.py` | **Cập nhật** | Thêm `admin_notes: str = ""` |
| `application/repositories/scenario_repository.py` | **Cập nhật** | Thêm `list_all()`, `create()`, `update()` |
| `application/repositories/user_profile_repository.py` | **Cập nhật** | Thêm `list_learners()` |
| `infrastructure/persistence/dynamo_scenario_repo.py` | **Tạo mới** | DynamoDB implementation đầy đủ |
| `infrastructure/persistence/dynamo_user_repo.py` | **Cập nhật** | Thêm `list_learners()`, thêm `admin_notes` vào create/get/update |
| `application/use_cases/admin/*.py` | **Tạo mới** | 5 use cases |
| `infrastructure/handlers/admin/*.py` | **Tạo mới** | 5 handlers |
| `template.yaml` | **Cập nhật** | Thêm 5 Lambda functions |
| `config/database.yaml` | **Cập nhật** | Fix GSI3 projection: `is_onboarded` → `is_new_user` |
| `infrastructure/handlers/scenarios_handler.py` | **Cập nhật** | Dùng `DynamoScenarioRepository` thay `StaticScenarioRepository` |
| `infrastructure/handlers/session_handler.py` | **Cập nhật** | Dùng `DynamoScenarioRepository` thay `StaticScenarioRepository` |
| `infrastructure/handlers/websocket_handler.py` | **Không đổi** | Không dùng scenario repo trực tiếp |

### Các bất nhất cần fix ở Frontend (ngoài scope backend)

| File | Vấn đề | Fix |
|---|---|---|
| `features/admin/types/index.ts` | `AdminUser.learning_goal_text` không có trong backend | Xóa field |
| `features/admin/types/index.ts` | `AdminUser.status` không có trong backend | Map từ `is_active`: `true→"active"`, `false→"paused"` |
| `features/admin/types/index.ts` | `AdminUser.sessions_completed` không có trong backend | Xóa hoặc tính riêng |
| `features/admin/types/index.ts` | `AdminUser.streak` → backend là `current_streak` | Rename |
| `features/admin/types/index.ts` | `AdminUser.last_active_at` → backend là `last_completed_at` | Rename |
