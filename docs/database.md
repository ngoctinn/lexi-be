# Database Specification (LexiLearn)

Tài liệu này đặc tả toàn bộ cấu trúc dữ liệu và mô hình truy cập trên Amazon DynamoDB cho nền tảng LexiLearn, đã được đồng bộ hóa với định nghĩa các Domain Entities.

---

## 1. Tổng quan các bảng (Table List)

| Table Name | Billing Mode | Partition Key (PK) | Sort Key (SK) | Mô tả |
|------------|--------------|-------------------|---------------|-------|
| `LexiApp` | PAY_PER_REQUEST | String (S) | String (S) | Bảng chính (Single-Table Design) chứa dữ liệu nghiệp vụ: Profile, Scenario, Session, Turn, Scoring, Flashcards. |
| `WordCache` | PAY_PER_REQUEST | String (S) | String (S) | Bảng cache từ vựng (Vocabulary) chung cho tất cả người dùng. |

---

## 2. Đặc tả bảng LexiApp (Single-Table Design)

Bảng `LexiApp` được thiết kế để gom nhiều loại thực thể vào một bảng duy nhất nhằm tối ưu hóa hiệu năng truy vấn liên quan.

### 2.1 Các Loại Thực Thể (Entity Types)

| Thực thể | PK | SK | Entity ID Field |
|----------|----|----|-----------------|
| **USER_PROFILE** | `USER#<user_id>` | `PROFILE` | `user_id` |
| **SCENARIO** | `SYSTEM#SCENARIOS` | `SCENARIO#<scenario_id>` | `scenario_id` |
| **SESSION** | `SESSION#<session_id>` | `METADATA` | `session_id` |
| **TURN** | `SESSION#<session_id>` | `TURN#<turn_index>` | `turn_id` |
| **SCORING** | `SESSION#<session_id>` | `SCORING` | `scoring_id` |
| **FLASHCARD** | `USER#<user_id>` | `FLASHCARD#<flashcard_id>` | `flashcard_id` |

### 2.2 Các Chỉ Mục Phụ (GSIs)

*   **GSI1: `GSI1-UserEntity-Time`**
    *   **GSI1PK**: `<USER#id>#<ENTITY_TYPE>` (Để lọc theo từng loại: `USER#123#SESSION`)
    *   **GSI1SK**: `ID (ULID)` hoặc `ISO8601 Timestamp` (Để sắp xếp theo thời gian. Lưu ý: UserProfile dùng Timestamp ẩn tại tầng Infra).
*   **GSI2: `GSI2-SRS-ReviewQueue`**
    *   **GSI2PK**: `USER#<user_id>`
    *   **GSI2SK**: `next_review_at` (Sắp xếp theo hạn ôn tập)
*   **GSI3: `GSI3-Admin-EntityList`**
    *   **GSI3PK**: `EntityType` (Ví dụ: `USER_PROFILE`)
    *   **GSI3SK**: `joined_at` (Technical Metadata - Timestamp khi tham gia hệ thống)

---

## 3. Đặc tả bảng WordCache (Vocabulary Entity)

Bảng này hoạt động như một tầng cache dùng chung để lưu định nghĩa và thông tin từ điển.

*   **PK**: `WORD#<word_normalized>` (từ đã viết thường)
*   **SK**: `METADATA`
*   **TTL**: Tự động xóa sau 60 ngày nếu không có cập nhật mới (`ttl` attribute).

---

## 4. Mô hình truy cập (Access Patterns)

| # | Use Case (Nghiệp vụ) | Operation | Index | Key Pattern |
|---|-----------------------|-----------|-------|-------------|
| 1 | Lấy profile người dùng | `GetItem` | Base | `PK=USER#id, SK=PROFILE` |
| 2 | Lấy danh sách Scenarios | `Query` | Base | `PK=SYSTEM#SCENARIOS, SK begins_with(SCENARIO#)` |
| 3 | Tạo session mới | `PutItem` | Base | `PK=SESSION#[id], SK=METADATA` |
| 4 | Lấy danh sách session | `Query` | GSI1 | `GSI1PK=USER#id#SESSION, GSI1SK desc` |
| 5 | Lấy hội thoại session | `Query` | Base | `PK=SESSION#id, SK begins_with(TURN#)` |
| 6 | Lưu lượt nói & bản dịch | `PutItem` | Base | `PK=SESSION#id, SK=TURN#index` |
| 7 | Ghi chấm điểm session | `PutItem` | Base | `PK=SESSION#id, SK=SCORING` |
| 8 | Flashcards theo User | `Query` | GSI1 | `GSI1PK=USER#id#FLASHCARD, GSI1SK desc` |
| 9 | Flashcards cần ôn (SRS)| `Query` | GSI2 | `GSI2PK=USER#id, GSI2SK <= today` |
| 10 | Tra cứu từ điển cache | `GetItem` | WordCache| `PK=WORD#word, SK=METADATA` |

---

## 5. Đặc tả chi tiết thuộc tính (Attribute Reference)

### 5.1 Bảng LexiApp

#### Thực thể USER_PROFILE
| Thuộc tính | Kiểu | Mô tả |
|------------|------|-------|
| `user_id` | S | ID định danh hệ thống (Trùng khớp auth id). |
| `email` | S | Địa chỉ email của người dùng. |
| `display_name` | S | Tên hiển thị của người dùng. |
| `current_level` | S | Trình độ CEFR hiện tại (A1-C2). |
| `learning_goal` | S | Mục tiêu học tập. |
| `role` | S | Quyền truy cập: `LEARNER` hoặc `ADMIN`. |
| `is_active` | BOOL | Trạng thái hoạt động của tài khoản. |
| `current_streak` | N | Số ngày học liên tục hiện tại (Streak). |
| `last_completed_at` | S | Lần cuối hoàn thành bài học (ISO8601). |
| `total_words_learned` | N | Tổng số từ vựng đã học được. |

#### Thực thể SCENARIO
| Thuộc tính | Kiểu | Mô tả |
|------------|------|-------|
| `scenario_id` | S | ULID định danh kịch bản. |
| `scenario_title` | S | Tiêu đề kịch bản. |
| `scenario_prompt` | S | Lệnh điều hướng (Prompt) cho AI. |
| `my_character` | S | Nhân vật người dùng sẽ đóng vai. |
| `ai_character` | S | Nhân vật AI sẽ đóng vai. |
| `is_active` | BOOL | Trạng thái kích hoạt. |
| `usage_count` | N | Số lượt session đã dùng kịch bản này. |

#### Thực thể SESSION
| Thuộc tính | Kiểu | Mô tả |
|------------|------|-------|
| `session_id` | S | ULID định danh phiên học. |
| `user_id` | S | ID người dùng tham gia. |
| `scenario_id` | S | ID kịch bản đang học. |
| `ai_gender` | S | Giới tính nhân vật AI (`MALE`/`FEMALE`). |
| `level` | S | Trình độ ngoại ngữ chọn cho phiên này (`A1`-`C2`). |
| `total_turns` | N | Tổng số lượt thoại. |
| `user_turns` | N | Số lượt thoại của người dùng. |
| `hint_used_count` | N | Số lần đã sử dụng gợi ý (hint). |

#### Thực thể TURN
| Thuộc tính | Kiểu | Mô tả |
|------------|------|-------|
| `turn_id` | S | ULID định danh lượt thoại. |
| `session_id` | S | ID của session chứa lượt thoại. |
| `turn_index` | N | Thứ tự lượt nói trong session (0, 1, 2...). |
| `speaker` | S | Người nói: `AI` hoặc `USER`. |
| `content` | S | Nội dung văn bản tiếng Anh. |
| `audio_url` | S | Đường dẫn file âm thanh. |
| `translated_content` | S | Bản dịch tiếng Việt. |
| `is_hint_used` | BOOL | Lượt này có dùng gợi ý không. |

#### Thực thể SCORING (Chấm điểm)
| Thuộc tính | Kiểu | Mô tả |
|------------|------|-------|
| `scoring_id` | S | ULID định danh bản ghi chấm điểm. |
| `session_id` | S | ID của session tương ứng. |
| `grammar_score` | N | Điểm ngữ pháp (0-100). |
| `vocabulary_score` | N | Điểm phong phú từ vựng (0-100). |
| `fluency_score` | N | Điểm độ trôi chảy (0-100). |
| `coherence_score` | N | Điểm tính mạch lạc (0-100). |
| `overall_score` | N | Điểm trung bình tổng kết. |
| `feedback_fluency` | S | Nhận xét chi tiết từ AI. |

#### Thực thể FLASHCARD
| Thuộc tính | Kiểu | Mô tả |
|------------|------|-------|
| `flashcard_id` | S | ULID định danh thẻ. |
| `user_id` | S | ID của người sở hữu. |
| `word` | S | Từ vựng liên kết (ID của Vocabulary). |
| `review_count` | N | Số lần đã ôn tập. |
| `interval_days` | N | Khoảng cách ngày ôn tiếp theo. |
| `difficulty` | N | Mức độ khó (0-5). |
| `last_reviewed_at` | S | Thời điểm ôn tập gần nhất. |
| `next_review_at` | S | Thời điểm đến hạn ôn tập tiếp theo. |

---

### 5.2 Bảng VOCABULARY

| Thuộc tính | Kiểu | Mô tả |
|------------|------|-------|
| `word` | S | Từ vựng (viết thường) - Đóng vai trò là ID định danh. |
| `word_type` | S | Loại từ (n, v, adj...). |
| `definition_vi` | S | Định nghĩa tiếng Việt. |
| `phonetic` | S | Phiên âm IPA. |
| `audio_url` | S | Đường dẫn file phát âm. |
| `example_sentence` | S | Câu ví dụ mẫu. |
| `source_api` | S | Nguồn API cung cấp dữ liệu. |
