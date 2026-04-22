# Implementation Tasks — Admin Management

**Version:** 1.0  
**Status:** Ready to implement

---

## Phase 0: Bootstrap Admin

### Task 0: Tạo Admin đầu tiên (thủ công, chạy một lần)

**Status:** pending  
**Không cần code** — thực hiện thủ công sau khi deploy

**Bước 1:** Admin đăng ký tài khoản bình thường qua app

**Bước 2:** Lấy `user_id` từ Cognito:
```bash
aws cognito-idp list-users \
  --user-pool-id <USER_POOL_ID> \
  --filter "email = \"admin@example.com\"" \
  --query "Users[0].Username" \
  --output text
```

**Bước 3:** Promote role trong DynamoDB:
```bash
aws dynamodb update-item \
  --table-name LexiApp \
  --key '{"PK":{"S":"USER#<user_id>"},"SK":{"S":"PROFILE"}}' \
  --update-expression "SET #r = :admin, is_new_user = :false" \
  --expression-attribute-names '{"#r":"role"}' \
  --expression-attribute-values '{":admin":{"S":"ADMIN"},":false":{"BOOL":false}}'
```

**Bước 4:** Verify:
```bash
aws dynamodb get-item \
  --table-name LexiApp \
  --key '{"PK":{"S":"USER#<user_id>"},"SK":{"S":"PROFILE"}}' \
  --query 'Item.role'
# Expect: {"S": "ADMIN"}
```

**Done khi:** User có `role = ADMIN` trong DynamoDB và có thể gọi `/admin/*` endpoints.

---

## Phase 1: Domain & Repository Layer

### Task 1: Cập nhật Scenario entity

**Status:** pending  
**File:** `src/domain/entities/scenario.py`

**Xóa các field bất nhất với business spec §4.5 và §7.3:**
- `my_character`
- `ai_character`
- `user_roles`
- `ai_roles`

Xóa luôn logic trong `__post_init__` đang set các field này.

**Thêm fields mới:**
```python
difficulty_level: str = ""
order: int = 0
notes: str = ""
created_at: str = ""
updated_at: str = ""
```

**Thêm methods:**
```python
def activate(self):
    self.is_active = True

def update_info(self, scenario_title=None, context=None, roles=None,
                goals=None, difficulty_level=None, order=None,
                notes=None, is_active=None):
    if scenario_title is not None: self.scenario_title = scenario_title
    if context is not None: self.context = context
    if roles is not None: self.roles = list(roles)
    if goals is not None: self.goals = list(goals)
    if difficulty_level is not None: self.difficulty_level = difficulty_level
    if order is not None: self.order = order
    if notes is not None: self.notes = notes
    if is_active is not None: self.is_active = is_active
```

**Kiểm tra trước khi xóa:** Grep toàn bộ codebase cho `my_character`, `ai_character`, `user_roles`, `ai_roles` để đảm bảo không có code nào đang đọc các field này ngoài `__post_init__`.

**Done khi:** Entity không còn 4 field cũ, có đủ fields mới, không break code hiện tại.

---

### Task 2: Cập nhật ScenarioRepository interface

**Status:** pending  
**File:** `src/application/repositories/scenario_repository.py`

**Thêm 3 abstract methods:**
- `list_all() -> List[Scenario]`
- `create(scenario: Scenario) -> None`
- `update(scenario: Scenario) -> None`

**Cập nhật StaticScenarioRepository** để implement 3 methods mới (tránh break):
- `list_all()`: trả về tất cả (kể cả inactive)
- `create()`: thêm vào dict
- `update()`: ghi đè trong dict

**Done khi:** `StaticScenarioRepository` không raise `NotImplementedError`.

---

### Task 3: Cập nhật UserProfileRepository interface

**Status:** pending  
**File:** `src/application/repositories/user_profile_repository.py`

**Thêm:**
```python
@abstractmethod
def list_learners(self, limit: int, last_key: Optional[dict]) -> tuple[List[UserProfile], Optional[dict]]:
    ...
```

**Done khi:** Interface có method mới.

---

### Task 4: Tạo DynamoScenarioRepository

**Status:** pending  
**File:** `src/infrastructure/persistence/dynamo_scenario_repo.py`

**Implement đầy đủ 6 methods:**
- `list_active()` — query GSI3 + filter `is_active=true`
- `list_all()` — query GSI3 không filter
- `get_by_id(scenario_id)` — get_item PK/SK
- `create(scenario)` — put_item với condition
- `save(scenario)` — put_item (upsert, dùng cho `increment_usage`)
- `update(scenario)` — update_item chỉ các field thay đổi

**DynamoDB key pattern:**
```
PK = SCENARIO#{scenario_id}
SK = METADATA
GSI3PK = SCENARIO
GSI3SK = created_at
```

**Done khi:** Syntax valid, pattern đúng với database.yaml.

---

### Task 5: Thêm list_learners vào DynamoDBUserRepo

**Status:** pending  
**File:** `src/infrastructure/persistence/dynamo_user_repo.py`

**Implement:**
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
    return profiles, response.get("LastEvaluatedKey")
```

**Thêm helper `_to_entity(item)`** nếu chưa có (extract từ `get_by_user_id`).

**Done khi:** Method tồn tại và syntax valid.

---

## Phase 2: Application Layer (Use Cases)

### Task 6: Tạo ListAdminUsersUseCase

**Status:** pending  
**Files:**
- `src/application/use_cases/admin/__init__.py`
- `src/application/use_cases/admin/list_admin_users_uc.py`

**Logic:**
1. `repo.list_learners(limit, last_key)`
2. Map mỗi profile sang dict (chỉ các field được phép trả về)
3. Trả về `Result.success({"users": [...], "next_key": ...})`

**Done khi:** Use case trả đúng structure.

---

### Task 7: Tạo UpdateAdminUserUseCase

**Status:** pending  
**File:** `src/application/use_cases/admin/update_admin_user_uc.py`

**Logic:**
1. `repo.get_by_user_id(target_user_id)` → failure nếu None
2. Validate `current_level`, `target_level` nếu có (dùng `ProficiencyLevel` enum)
3. Chỉ update: `is_active`, `current_level`, `target_level`
4. `repo.update(profile)`
5. Trả về profile dict

**Done khi:** Chỉ update đúng 3 fields, không touch email/role/streak.

---

### Task 8: Tạo ListAdminScenariosUseCase

**Status:** pending  
**File:** `src/application/use_cases/admin/list_admin_scenarios_uc.py`

**Logic:**
1. `scenario_repo.list_all()`
2. Sort theo `order` tăng dần
3. Map sang dict
4. Trả về `Result.success({"scenarios": [...]})`

**Done khi:** Trả về tất cả scenario kể cả inactive.

---

### Task 9: Tạo CreateAdminScenarioUseCase

**Status:** pending  
**File:** `src/application/use_cases/admin/create_admin_scenario_uc.py`

**Validation:**
- `scenario_title`: required, 1-100 chars
- `context`: required, 1-100 chars
- `roles`: required, đúng 2 phần tử
- `goals`: required, ít nhất 1 phần tử
- `difficulty_level`: optional, nếu có phải là A1/A2/B1/B2/C1/C2

**Logic:**
1. Validate
2. Tạo `Scenario` với `scenario_id = new_ulid()`, `usage_count = 0`
3. `scenario_repo.create(scenario)`
4. Trả về scenario dict

**Done khi:** Validation đúng, scenario được tạo với ULID.

---

### Task 10: Tạo UpdateAdminScenarioUseCase

**Status:** pending  
**File:** `src/application/use_cases/admin/update_admin_scenario_uc.py`

**Logic:**
1. `scenario_repo.get_by_id(scenario_id)` → failure nếu None
2. Validate các field nếu có (roles=2, goals≥1, difficulty_level valid)
3. `scenario.update_info(**provided_fields)`
4. `scenario_repo.update(scenario)`
5. Trả về scenario dict

**Done khi:** Chỉ update fields được cung cấp, không reset fields khác.

---

## Phase 3: Infrastructure Layer (Handlers)

### Task 11: Tạo list_admin_users_handler

**Status:** pending  
**File:** `src/infrastructure/handlers/admin/list_admin_users_handler.py`

**Pattern:**
```python
def handler(event, context):
    user_id, err = _check_admin(event, user_repo)
    if err: return err
    
    query = event.get("queryStringParameters") or {}
    limit = min(int(query.get("limit", 20)), 100)
    last_key = _decode_cursor(query.get("last_key"))
    
    result = list_admin_users_uc.execute(limit, last_key)
    ...
```

**Done khi:** 401/403 đúng, response đúng format.

---

### Task 12: Tạo update_admin_user_handler

**Status:** pending  
**File:** `src/infrastructure/handlers/admin/update_admin_user_handler.py`

**Done khi:** Lấy `user_id` từ path params, parse body, trả 404 nếu không tìm thấy.

---

### Task 13: Tạo list_admin_scenarios_handler

**Status:** pending  
**File:** `src/infrastructure/handlers/admin/list_admin_scenarios_handler.py`

**Done khi:** Trả tất cả scenarios kể cả inactive.

---

### Task 14: Tạo create_admin_scenario_handler

**Status:** pending  
**File:** `src/infrastructure/handlers/admin/create_admin_scenario_handler.py`

**Done khi:** Trả 201 khi tạo thành công, 400 khi validation fail.

---

### Task 15: Tạo update_admin_scenario_handler

**Status:** pending  
**File:** `src/infrastructure/handlers/admin/update_admin_scenario_handler.py`

**Done khi:** Lấy `scenario_id` từ path params, trả 404 nếu không tìm thấy.

---

## Phase 4: Infrastructure as Code

### Task 16: Fix database.yaml — GSI3 projection

**Status:** pending  
**File:** `config/database.yaml`

**Thay đổi trong GSI3 NonKeyAttributes:**
```yaml
# Trước (sai)
- is_onboarded

# Sau (đúng)
- is_new_user
```

**Lưu ý:** Thay đổi GSI projection cần deploy cẩn thận. Với bảng đang có data, AWS sẽ backfill GSI tự động.

**Done khi:** `sam validate` pass.

---

### Task 17: Cập nhật SAM template — 5 Lambda functions

**Status:** pending  
**File:** `template.yaml`

**Thêm 5 functions:**
```yaml
ListAdminUsersFunction:       GET  /admin/users
UpdateAdminUserFunction:      PATCH /admin/users/{user_id}
ListAdminScenariosFunction:   GET  /admin/scenarios
CreateAdminScenarioFunction:  POST /admin/scenarios
UpdateAdminScenarioFunction:  PATCH /admin/scenarios/{scenario_id}
```

Tất cả cần `LEXI_TABLE_NAME` env var và `DynamoDBCrudPolicy`.

**Done khi:** `sam validate` pass.

---

## Phase 5: Migration & Integration

### Task 18: Migrate scenarios_handler sang DynamoScenarioRepository

**Status:** pending  
**File:** `src/infrastructure/handlers/scenarios_handler.py`

**Thay:**
```python
# Trước
repository = StaticScenarioRepository()

# Sau
repository = DynamoScenarioRepository()
```

**Xóa** `SCENARIO_METADATA` dict (đã được lưu trong DynamoDB).

**Done khi:** Handler dùng DynamoDB, không còn hardcode.

---

### Task 19: Migrate session_handler sang DynamoScenarioRepository

**Status:** pending  
**File:** `src/infrastructure/handlers/session_handler.py`

**Thay `StaticScenarioRepository()` → `DynamoScenarioRepository()`** trong `build_session_controller()`.

**Done khi:** Session creation dùng DynamoDB scenarios.

---

### Task 20: Seed 14 scenarios vào DynamoDB

**Status:** pending  
**File:** `src/infrastructure/handlers/admin/seed_scenarios_handler.py` (Lambda chạy một lần)

**Logic:**
1. Lấy 14 scenarios từ `StaticScenarioRepository`
2. Map thêm `difficulty_level` và `order` từ `SCENARIO_METADATA`
3. Gọi `DynamoScenarioRepository.create()` cho từng scenario
4. Skip nếu đã tồn tại (condition expression)

**Done khi:** 14 scenarios có trong DynamoDB.

---

## Phase 6: Testing

### Task 21: Manual testing — Admin User Management

**Status:** pending

```bash
# Lấy JWT của admin user

# TC1: List users
curl -X GET https://<api>/admin/users \
  -H "Authorization: Bearer <admin_token>"
# Expect: 200, danh sách learners

# TC2: List users với limit
curl -X GET "https://<api>/admin/users?limit=5" \
  -H "Authorization: Bearer <admin_token>"
# Expect: 200, 5 users, next_key nếu có thêm

# TC3: Update user
curl -X PATCH https://<api>/admin/users/<user_id> \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false, "current_level": "B1"}'
# Expect: 200, profile đã cập nhật

# TC4: Learner token gọi admin endpoint
curl -X GET https://<api>/admin/users \
  -H "Authorization: Bearer <learner_token>"
# Expect: 403

# TC5: Update user không tồn tại
curl -X PATCH https://<api>/admin/users/nonexistent \
  -H "Authorization: Bearer <admin_token>" \
  -d '{}'
# Expect: 404
```

---

### Task 22: Manual testing — Admin Scenario Management

**Status:** pending

```bash
# TC1: List all scenarios (kể cả inactive)
curl -X GET https://<api>/admin/scenarios \
  -H "Authorization: Bearer <admin_token>"
# Expect: 200, tất cả 14 scenarios

# TC2: Create scenario
curl -X POST https://<api>/admin/scenarios \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"scenario_title":"Test","context":"Test context","roles":["Role A","Role B"],"goals":["Goal 1"]}'
# Expect: 201, scenario mới với ULID

# TC3: Update scenario
curl -X PATCH https://<api>/admin/scenarios/<id> \
  -H "Authorization: Bearer <admin_token>" \
  -d '{"is_active": false}'
# Expect: 200, is_active=false

# TC4: Verify public endpoint không trả scenario inactive
curl -X GET https://<api>/scenarios
# Expect: không có scenario vừa ẩn

# TC5: Create với roles != 2 phần tử
curl -X POST https://<api>/admin/scenarios \
  -H "Authorization: Bearer <admin_token>" \
  -d '{"scenario_title":"T","context":"C","roles":["Only One"],"goals":["G"]}'
# Expect: 400
```

---

## Thứ tự thực hiện

```
Phase 1: Task 1 → 2 → 3 → 4 → 5
Phase 2: Task 6 → 7 → 8 → 9 → 10
Phase 3: Task 11 → 12 → 13 → 14 → 15
Phase 4: Task 16 → 17
Phase 5: Task 18 → 19 → 20  (migration — làm sau cùng)
Phase 6: Task 21 → 22
```

**Quan trọng:** Task 18, 19, 20 (migration) phải làm sau khi DynamoScenarioRepository đã được test. Không nên migrate trước khi repo hoạt động đúng.
