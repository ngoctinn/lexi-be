# Requirements Document — User Onboarding Flow

**Version:** 1.1  
**Status:** Confirmed  
**Ngày chốt:** 2026-04-22

---

## Glossary

| Thuật ngữ | Định nghĩa |
|---|---|
| `is_new_user` | Flag Boolean trong UserProfile. `true` = chưa hoàn tất onboarding. `false` = đã xong. **Đây là tên field duy nhất được dùng trong toàn hệ thống.** |
| New_User | User có `is_new_user = true` |
| Onboarding | Luồng thu thập thông tin ban đầu bắt buộc cho New_User |
| CEFR_Level | Trình độ tiếng Anh: A1, A2, B1, B2, C1, C2 |
| Avatar_URL | URL HTTPS trỏ đến ảnh đại diện từ thư viện ngoài (DiceBear, v.v.) |

---

## Phạm vi

Onboarding thu thập **3 trường bắt buộc** và **1 trường tùy chọn**:

| Field | Bắt buộc | Mô tả |
|---|---|---|
| `display_name` | ✅ | Tên hiển thị, 1–50 ký tự |
| `current_level` | ✅ | Trình độ hiện tại (CEFR) |
| `target_level` | ✅ | Trình độ mục tiêu (CEFR) |
| `avatar_url` | ❌ | URL ảnh đại diện từ thư viện ngoài |

**Không có field `learning_goal_text`** — đã loại bỏ khỏi scope.

---

## Requirements

### Requirement 1: Phát hiện New User

**User Story:** Là user mới, tôi muốn hệ thống nhận ra tôi chưa onboarding để dẫn tôi vào luồng setup trước khi học.

#### Acceptance Criteria

1. WHEN user đăng nhập thành công, THE Profile_System SHALL trả về profile kèm field `is_new_user`
2. IF `is_new_user = true`, THEN Frontend SHALL redirect user đến trang `/onboarding`
3. IF `is_new_user = false`, THEN Frontend SHALL cho phép user vào Dashboard
4. WHEN Auth_System tạo profile mới qua post-confirmation trigger, THE System SHALL set `is_new_user = true`

---

### Requirement 2: Thu thập Display Name

**User Story:** Là user mới, tôi muốn đặt tên hiển thị để hệ thống gọi tôi đúng tên.

#### Acceptance Criteria

1. THE Onboarding_System SHALL hiển thị input field cho `display_name`
2. WHEN user submit form, THE System SHALL validate `display_name` không rỗng và không chỉ có khoảng trắng
3. WHEN user submit form, THE System SHALL validate độ dài `display_name` từ 1 đến 50 ký tự
4. IF validation thất bại, THEN THE System SHALL trả về lỗi 400 với message cụ thể
5. WHEN `display_name` hợp lệ, THE System SHALL lưu vào UserProfile

---

### Requirement 3: Thu thập Current Level

**User Story:** Là user mới, tôi muốn chọn trình độ hiện tại để hệ thống gợi ý nội dung phù hợp.

#### Acceptance Criteria

1. THE Onboarding_System SHALL hiển thị 6 lựa chọn CEFR: A1, A2, B1, B2, C1, C2
2. WHEN user submit form, THE System SHALL validate `current_level` không rỗng
3. THE System SHALL chỉ chấp nhận các giá trị: `A1`, `A2`, `B1`, `B2`, `C1`, `C2`
4. IF `current_level` không hợp lệ, THEN THE System SHALL trả về lỗi 400
5. WHEN `current_level` hợp lệ, THE System SHALL lưu vào UserProfile

---

### Requirement 4: Thu thập Target Level

**User Story:** Là user mới, tôi muốn đặt trình độ mục tiêu để hệ thống biết tôi muốn đạt đến đâu.

#### Acceptance Criteria

1. THE Onboarding_System SHALL hiển thị 6 lựa chọn CEFR: A1, A2, B1, B2, C1, C2
2. WHEN user submit form, THE System SHALL validate `target_level` không rỗng
3. THE System SHALL chỉ chấp nhận các giá trị: `A1`, `A2`, `B1`, `B2`, `C1`, `C2`
4. IF `target_level` không hợp lệ, THEN THE System SHALL trả về lỗi 400
5. WHEN `target_level` hợp lệ, THE System SHALL lưu vào UserProfile

---

### Requirement 5: Chọn Avatar (Tùy chọn)

**User Story:** Là user mới, tôi muốn chọn ảnh đại diện từ thư viện có sẵn để cá nhân hóa tài khoản.

#### Acceptance Criteria

1. THE Onboarding_System SHALL hiển thị control chọn avatar từ thư viện ngoài (DiceBear hoặc tương đương)
2. THE System SHALL cho phép user bỏ qua bước này mà không ảnh hưởng đến việc hoàn tất onboarding
3. IF `avatar_url` được cung cấp, THEN THE System SHALL validate URL bắt đầu bằng `https://`
4. IF `avatar_url` không hợp lệ, THEN THE System SHALL trả về lỗi 400
5. WHEN `avatar_url` hợp lệ, THE System SHALL lưu vào UserProfile
6. WHEN không có `avatar_url`, THE System SHALL lưu `avatar_url = ""`

---

### Requirement 6: Hoàn tất Onboarding

**User Story:** Là user mới, tôi muốn hệ thống đánh dấu tôi đã onboarding xong để không bị redirect lại.

#### Acceptance Criteria

1. WHEN tất cả field bắt buộc hợp lệ và user submit, THE System SHALL cập nhật UserProfile với dữ liệu đã thu thập
2. WHEN cập nhật thành công, THE System SHALL set `is_new_user = false`
3. WHEN `is_new_user = false`, THE System SHALL trả về profile đã cập nhật trong response
4. IF cập nhật thất bại, THEN THE System SHALL trả về lỗi 500 và không thay đổi `is_new_user`
5. THE System SHALL persist tất cả thay đổi vào DynamoDB trong một lần gọi

---

### Requirement 7: Kiểm soát truy cập (Frontend Guard)

**User Story:** Là product owner, tôi muốn user mới phải hoàn tất onboarding trước khi vào học.

#### Acceptance Criteria

1. WHEN Frontend nhận profile với `is_new_user = true`, Frontend SHALL redirect đến `/onboarding`
2. THE Frontend SHALL bảo vệ các route: `/dashboard`, `/scenarios`, `/sessions/*`, `/flashcards`, `/profile`
3. THE Frontend SHALL không bảo vệ các route: `/login`, `/signup`, `/onboarding`
4. WHEN `is_new_user = false`, Frontend SHALL cho phép truy cập tất cả route

**Ghi chú:** Backend không enforce guard này trong MVP. Chỉ Frontend guard.

---

### Requirement 8: Dữ liệu Onboarding là Profile chính thức

**User Story:** Là system admin, tôi muốn dữ liệu onboarding trở thành profile chính thức, không có bản ghi trùng lặp.

#### Acceptance Criteria

1. WHEN onboarding hoàn tất, THE System SHALL lưu dữ liệu trực tiếp vào UserProfile entity hiện có
2. THE System SHALL KHÔNG tạo bản ghi profile mới hay bản ghi tạm thời
3. WHEN user cập nhật profile sau onboarding, THE System SHALL sửa đúng các field đã set trong onboarding
4. Dữ liệu onboarding và dữ liệu profile dùng chung một DynamoDB item: `PK=USER#{user_id}`, `SK=PROFILE`
