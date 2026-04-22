# Requirements Document — Admin Management

**Version:** 1.0  
**Status:** Confirmed  
**Ngày chốt:** 2026-04-22

---

## Glossary

| Thuật ngữ | Định nghĩa |
|---|---|
| `Admin` | User có `role = ADMIN`, có quyền quản trị nội dung và người dùng |
| `Learner` | User có `role = LEARNER`, người học tiếng Anh |
| `Scenario` | Tình huống hội thoại do Admin tạo và quản lý |
| `is_active` | Flag Boolean trên Scenario. `true` = đang mở, `false` = đang ẩn |
| `is_new_user` | Flag Boolean trên UserProfile. `true` = chưa onboarding |
| `StaticScenarioRepository` | Repo hiện tại dùng hardcode in-memory — cần migrate sang DynamoDB |

---

## Phạm vi

Feature này gồm **2 nhóm**:

### Nhóm 1: Admin User Management (§5.3 business spec)
- Xem danh sách learner
- Cập nhật thông tin quản trị của user (status, level, notes)

### Nhóm 2: Admin Scenario Management (§5.4, §5.5 business spec)
- Xem danh sách tất cả scenario (kể cả inactive)
- Tạo scenario mới
- Cập nhật scenario
- Bật/ẩn scenario

**Kỹ thuật nợ đi kèm:** Migrate `StaticScenarioRepository` → `DynamoScenarioRepository` để Admin có thể thực sự quản lý scenario.

---

## Requirements

### Requirement 1: Xác thực quyền Admin

**User Story:** Là hệ thống, tôi muốn chỉ cho phép user có role ADMIN gọi các endpoint admin.

#### Acceptance Criteria

1. WHEN một request đến endpoint `/admin/*`, THE System SHALL kiểm tra JWT claims
2. IF `role` trong JWT claims không phải `ADMIN`, THEN THE System SHALL trả về 403 Forbidden
3. IF JWT không hợp lệ hoặc thiếu, THEN THE System SHALL trả về 401 Unauthorized
4. THE System SHALL lấy `user_id` từ JWT claims `sub`, không nhận từ request body

---

### Requirement 2: Liệt kê danh sách Learner

**User Story:** Là Admin, tôi muốn xem danh sách tất cả learner để theo dõi và quản lý.

#### Acceptance Criteria

1. THE System SHALL cung cấp endpoint `GET /admin/users`
2. THE System SHALL trả về danh sách user có `role = LEARNER`
3. THE System SHALL hỗ trợ phân trang với `limit` (default 20, max 100) và `last_key` cursor
4. Mỗi item trong danh sách SHALL chứa: `user_id`, `email`, `display_name`, `avatar_url`, `current_level`, `target_level`, `is_active`, `is_new_user`, `current_streak`, `total_words_learned`, `joined_at`
5. THE System SHALL sắp xếp theo `joined_at` giảm dần (mới nhất trước)

---

### Requirement 3: Cập nhật thông tin quản trị của User

**User Story:** Là Admin, tôi muốn cập nhật trạng thái và level của learner khi cần.

#### Acceptance Criteria

1. THE System SHALL cung cấp endpoint `PATCH /admin/users/{user_id}`
2. Admin SHALL có thể cập nhật các field: `is_active`, `current_level`, `target_level`
3. Admin SHALL KHÔNG được cập nhật: `email`, `user_id`, `role`, dữ liệu học (`current_streak`, `total_words_learned`)
4. WHEN `current_level` hoặc `target_level` được cung cấp, THE System SHALL validate là CEFR hợp lệ (A1/A2/B1/B2/C1/C2)
5. IF user không tồn tại, THEN THE System SHALL trả về 404
6. WHEN cập nhật thành công, THE System SHALL trả về profile đã cập nhật

---

### Requirement 4: Liệt kê tất cả Scenario (Admin view)

**User Story:** Là Admin, tôi muốn xem tất cả scenario kể cả đang ẩn để quản lý nội dung.

#### Acceptance Criteria

1. THE System SHALL cung cấp endpoint `GET /admin/scenarios`
2. THE System SHALL trả về **tất cả** scenario, bao gồm cả `is_active = false`
3. Mỗi item SHALL chứa: `scenario_id`, `scenario_title`, `context`, `roles[]`, `goals[]`, `is_active`, `usage_count`, `order`, `difficulty_level`, `notes`
4. THE System SHALL sắp xếp theo `order` tăng dần
5. Endpoint `GET /scenarios` (public) chỉ trả về scenario `is_active = true` — không thay đổi

---

### Requirement 5: Tạo Scenario mới

**User Story:** Là Admin, tôi muốn tạo scenario mới để mở rộng kho nội dung học.

#### Acceptance Criteria

1. THE System SHALL cung cấp endpoint `POST /admin/scenarios`
2. Request body SHALL chứa các field bắt buộc: `scenario_title`, `context`, `roles[]` (đúng 2 phần tử), `goals[]` (ít nhất 1)
3. Request body SHALL chứa các field tùy chọn: `difficulty_level`, `order`, `notes`, `is_active` (default `true`)
4. THE System SHALL validate `roles` có đúng 2 phần tử (MVP rule)
5. THE System SHALL validate `goals` có ít nhất 1 phần tử
6. THE System SHALL tự sinh `scenario_id` (ULID)
7. THE System SHALL set `usage_count = 0` khi tạo mới
8. WHEN tạo thành công, THE System SHALL trả về 201 với scenario đã tạo

---

### Requirement 6: Cập nhật Scenario

**User Story:** Là Admin, tôi muốn sửa nội dung scenario mà không ảnh hưởng đến session cũ.

#### Acceptance Criteria

1. THE System SHALL cung cấp endpoint `PATCH /admin/scenarios/{scenario_id}`
2. Admin SHALL có thể cập nhật: `scenario_title`, `context`, `roles[]`, `goals[]`, `difficulty_level`, `order`, `notes`, `is_active`
3. THE System SHALL KHÔNG cập nhật `usage_count` qua endpoint này
4. IF scenario không tồn tại, THEN THE System SHALL trả về 404
5. WHEN `roles` được cập nhật, THE System SHALL validate có đúng 2 phần tử
6. WHEN `goals` được cập nhật, THE System SHALL validate có ít nhất 1 phần tử
7. Session cũ đã tạo từ scenario này SHALL KHÔNG bị ảnh hưởng (prompt_snapshot đã được lưu trong session)

---

### Requirement 7: Bật/Ẩn Scenario

**User Story:** Là Admin, tôi muốn bật hoặc ẩn scenario để kiểm soát nội dung hiển thị cho learner.

#### Acceptance Criteria

1. THE System SHALL hỗ trợ toggle `is_active` qua `PATCH /admin/scenarios/{scenario_id}` với body `{"is_active": true/false}`
2. WHEN `is_active = false`, THE System SHALL không trả scenario này trong `GET /scenarios` (public endpoint)
3. WHEN `is_active = false`, THE System SHALL không cho phép tạo session mới từ scenario này
4. Session cũ đã tạo từ scenario bị ẩn SHALL vẫn hoạt động bình thường

---

### Requirement 8: Migrate Scenario sang DynamoDB

**User Story:** Là hệ thống, tôi cần lưu scenario trong DynamoDB thay vì hardcode để Admin có thể quản lý.

#### Acceptance Criteria

1. THE System SHALL có `DynamoScenarioRepository` implement `ScenarioRepository` interface
2. `DynamoScenarioRepository` SHALL implement: `list_active()`, `get_by_id()`, `save()`
3. `DynamoScenarioRepository` SHALL thêm: `list_all()`, `create()`, `update()`
4. DynamoDB item pattern: `PK = SCENARIO#{scenario_id}`, `SK = METADATA`
5. THE System SHALL seed 14 scenario hiện có từ `StaticScenarioRepository` vào DynamoDB khi deploy
6. `GET /scenarios` (public) và session creation SHALL dùng `DynamoScenarioRepository` thay vì `StaticScenarioRepository`
