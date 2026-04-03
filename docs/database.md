# Database Specification (LexiLearn)

Tài liệu này đặc tả toàn bộ cấu trúc dữ liệu và mô hình truy cập trên Amazon DynamoDB cho nền tảng LexiLearn.

---

## 1. Tổng quan các bảng (Table List)

| Table Name | Billing Mode | Partition Key (PK) | Sort Key (SK) | Mô tả |
|------------|--------------|-------------------|---------------|-------|
| `LexiApp` | PAY_PER_REQUEST | String (S) | String (S) | Bảng chính (Single-Table Design) chứa dữ liệu nghiệp vụ: Profile, Session, Turn, Scoring, Flashcards. |
| `WordCache` | PAY_PER_REQUEST | String (S) | String (S) | Bảng cache từ vựng chung cho tất cả người dùng (Định nghĩa, IPA, MP3). |

---

## 2. Đặc tả bảng LexiApp (Single-Table Design)

Bảng `LexiApp` được thiết kế để gom nhiều loại thực thể vào một bảng duy nhất nhằm tối ưu hóa hiệu năng truy vấn liên quan.

### 2.1 Các Loại Thực Thể (Entity Types)

| Thực thể | PK | SK | Mô tả |
|----------|----|----|-------|
| **USER_PROFILE** | `USER#<user_id>` | `PROFILE` | Thông tin cá nhân, trình độ, và quyền (role) của người học/admin. |
| **SCENARIO** | `SYSTEM#SCENARIOS` | `SCENARIO#<ulid>` | Kho kịch bản roleplay mẫu do Admin tạo ra để Users chọn. |
| **SESSION** | `SESSION#<ulid>` | `METADATA` | Cấu hình buổi luyện nói (scenario, my_character, ai_character, status). |
| **TURN** | `SESSION#<ulid>` | `TURN#<index>` | Chi tiết từng câu nói trong hội thoại, bao gồm cả nội dung dịch. |
| **SCORING** | `SESSION#<ulid>` | `SCORING` | Điểm số và nhận xét chi tiết sau khi kết thúc session. |
| **FLASHCARD** | `USER#<user_id>` | `FLASHCARD#<ulid>` | Thẻ từ vựng người dùng lưu lại để ôn tập theo thuật toán SRS. |

### 2.2 Các Chỉ Mục Phụ (GSIs)

*   **GSI1: `GSI1-UserEntity-Time`**
    *   **GSI1PK**: `<USER#id>#<ENTITY_TYPE>` (Để lọc theo từng loại: `USER#123#SESSION`)
    *   **GSI1SK**: `ISO8601 Timestamp` (Để sắp xếp theo thời gian)
*   **GSI2: `GSI2-SRS-ReviewQueue`**
    *   **GSI2PK**: `USER#<user_id>`
    *   **GSI2SK**: `next_review_at` (Sắp xếp theo hạn ôn tập)
*   **GSI3: `GSI3-Admin-EntityList`**
    *   **GSI3PK**: `EntityType` (Ví dụ: `USER_PROFILE`)
    *   **GSI3SK**: `created_at` (Hỗ trợ Admin query toàn bộ danh sách User/Scenario mới nhất)

---

## 3. Đặc tả bảng WordCache (Dictionary Cache)

Bảng này hoạt động như một tầng cache dùng chung để lưu định nghĩa tiếng Việt và giọng đọc MP3.

*   **PK**: `WORD#<word_normalized>` (từ đã viết thường)
*   **SK**: `METADATA`
*   **TTL**: Tự động xóa sau 60 ngày nếu không có cập nhật mới (`ttl` attribute).

---

## 4. Mô hình truy cập (Access Patterns)

| # | Use Case (Nghiệp vụ) | Operation | Index | Key Pattern |
|---|-----------------------|-----------|-------|-------------|
| 1 | Lấy profile người dùng | `GetItem` | Base | `PK=USER#id, SK=PROFILE` |
| 2 | Lấy danh sách Scenarios (Catalog) | `Query` | Base | `PK=SYSTEM#SCENARIOS, SK begins_with(SCENARIO#)` |
| 3 | **Tạo session mới** | `PutItem` | Base | `PK=SESSION#[ULID], SK=METADATA` |
| 4 | Lấy danh sách session | `Query` | GSI1 | `GSI1PK=USER#id#SESSION, GSI1SK desc` |
| 5 | Lấy hội thoại session | `Query` | Base | `PK=SESSION#id, SK begins_with(TURN#)` |
| 6 | Lưu lượt nói & bản dịch | `PutItem` | Base | `PK=SESSION#id, SK=TURN#index` |
| 7 | Ghi chấm điểm session | `PutItem` | Base | `PK=SESSION#id, SK=SCORING` |
| 8 | Flashcards theo User | `Query` | GSI1 | `GSI1PK=USER#id#FLASHCARD, GSI1SK desc` |
| 9 | Flashcards cần ôn (SRS)| `Query` | GSI2 | `GSI2PK=USER#id, GSI2SK <= today` |
| 10 | Tra cứu từ điển cache | `GetItem` | WordCache| `PK=WORD#word, SK=METADATA` |
| 11 | Cập nhật connectionId | `UpdateItem` | Base | `PK=SESSION#id, SK=METADATA` (khi WS `$connect`) |
| 12 | Admin xem danh sách User | `Query` | GSI3 | `GSI3PK=USER_PROFILE, GSI3SK desc` |

---

## 5. Đặc tả chi tiết thuộc tính (Attribute Reference)

Dưới đây là mô tả chi tiết cho toàn bộ các trường dữ liệu trong hệ thống.

### 5.1 Bảng LexiApp

#### Nhóm thuộc tính chung (Shared Attributes)
| Thuộc tính | Kiểu | Mô tả |
|------------|------|-------|
| `PK` | S | Partition Key của bảng chính (USER#id, SESSION#id). |
| `SK` | S | Sort Key (PROFILE, METADATA, TURN#..., FLASHCARD#...). |
| `EntityType` | S | Loại thực thể: USER_PROFILE, SESSION, TURN, SCORING, FLASHCARD. |
| `created_at` | S | Thời điểm tạo bản ghi (ISO8601). |
| `updated_at` | S | Thời điểm cập nhật cuối (ISO8601). |

#### Thực thể USER_PROFILE
| Thuộc tính | Kiểu | Mô tả |
|------------|------|-------|
| `user_id` | S | Id của người dùng. |
| `email` | S | Địa chỉ email của người dùng. |
| `display_name` | S | Tên hiển thị của người dùng. |
| `role` | S | Quyền truy cập: `LEARNER` hoặc `ADMIN`. |
| `is_active` | BOOL | Trạng thái hoạt động (dùng để block user). |
| `is_onboarded` | BOOL | Trạng thái đã hoàn thành onboarding hay chưa. |
| `current_level` | S | Trình độ hiện tại (A1, B1, B2, C1, ...). |
| `learning_goal` | S | Mục tiêu học tập của người dùng. |
| `current_streak` | N | Số ngày học liên tiếp hiện tại (Streak). |
| `last_completed_at` | S | Lần cuối hoàn thành một phiên học (để tính streak). |
| `total_words_learned` | N | Tổng số từ vựng đã lưu thành flashcard. |

#### Thực thể SCENARIO
| Thuộc tính | Kiểu | Mô tả |
|------------|------|-------|
| `scenario_title` | S | Tên hiển thị ngắn gọn của kịch bản (VD: "Phỏng vấn DevOps"). |
| `description` | S | Mô tả thêm để User hiểu ngữ cảnh trước khi vào học. |
| `scenario_prompt` | S | Kịch bản nội dung truyền vào Prompt. |
| `my_character` | S | Vai diễn mặc định của User. |
| `ai_character` | S | Vai diễn mặc định của AI. |
| `ai_gender` | S | Giới tính của AI (`male` / `female`). |
| `recommended_level` | S | Khuyến nghị trình độ phù hợp (VD: `B1-B2`). User vẫn luôn quyết định level thực tế ở Session. |
| `is_active` | BOOL | Nút gạt tắt/bật kịch bản trên App. |
| `usage_count` | N | Số lượt Session đã dùng kịch bản này. |

#### Thực thể SESSION
| Thuộc tính | Kiểu | Mô tả |
|------------|------|-------|
| `session_id` | S | ID của phiên |
| `user_id` | S | ID của người dùng. |
| `scenario` | S | Tình huống/kịch bản hội thoại (ví dụ: `Ordering food in a restaurant`). |
| `my_character` | S | Nhân vật mà người học đóng (ví dụ: `a customer`). |
| `ai_character` | S | Nhân vật mà AI đóng (ví dụ: `a waiter`). |
| `ai_gender` | S | Giới tính của nhân vật AI (`male` hoặc `female`) – dùng để chọn giọng TTS tương ứng. |
| `level` | S | Trình độ CEFR của người học đã chọn cho phiên này (`A1`-`C2`). |
| `connection_id` | S | WebSocket connectionId hiện tại. Cập nhật khi `$connect`, xóa khi `$disconnect`. Lambda dùng để push sự kiện về đúng client. |
| `status` | S | Trạng thái: `ACTIVE`, `COMPLETED`. |
| `hint_history` | M | Map lưu cache các gợi ý đã tạo. Khóa (key) là thứ tự lượt nói của AI (ví dụ `1`, `3`), giá trị (value) là nội dung gợi ý bằng tiếng Anh. |
| `total_turns` | N | Tổng số lượt nói trong session. |
| `user_turns` | N | Số lượt nói của người dùng. |
| `hint_used_count` | N | Số lần đã sử dụng gợi ý (hint). |
| `new_words_count` | N | Số từ mới đã lưu từ session này. |
| `overall_score` | N | Điểm trung bình của session (0-100). |
| `last_active_at` | S | Lần cuối có hoạt động trong session. |

#### Thực thể TURN (Hội thoại)
| Thuộc tính | Kiểu | Mô tả |
|------------|------|-------|
| `session_id` | S | Id của session |
| `turn_index` | N | Thứ tự của lượt nói trong session. |
| `speaker` | S | Người nói: `AI` hoặc `USER`. |
| `content` | S | Nội dung văn bản bằng tiếng Anh. |
| `translated_content` | S | **Bản dịch tiếng Việt (Lưu khi người dùng nhấn Translate).** |
| `audio_s3_key` | S | Đường dẫn file âm thanh giọng nói trên S3. |
| `stt_confidence` | N | Độ tin cậy của kết quả Speech-to-Text (0 đến 1). |
| `timestamp` | S | Thời điểm phát sinh câu nói. |
| `is_hint_used` | BOOL | Lượt nói này có dùng gợi ý không. |
| `ttl` | N | Unix timestamp để tự động dọn dẹp audio tham chiếu sau 90 ngày. |

#### Thực thể SCORING (Chấm điểm)
| Thuộc tính | Kiểu | Mô tả |
|------------|------|-------|
| `session_id` | S | ID của phiên trò chuyện|
| `user_id` | S | ID người dùng |
| `pronunciation_score`| N | Điểm phát âm. |
| `grammar_score` | N | Điểm ngữ pháp. |
| `vocabulary_score` | N | Điểm từ vựng. |
| `feedback_fluency` | S | Nhận xét chi tiết về độ trôi chảy. |
| `feedback_grammar` | S | Nhận xét chi tiết về ngữ pháp. |

#### Thực thể FLASHCARD (Từ vựng)
| Thuộc tính | Kiểu | Mô tả |
|------------|------|-------|
| `user_id` | S | Id của người dùng. |
| `word_id` | S | Id của từ. |
| `review_count` | N | Số lần đã ôn tập. |
| `interval_days` | N | Số ngày cho lần ôn tập tiếp theo. |
| `last_reviewed_at` | S | Ngày ôn tập gần nhất. |
| `next_review_at` | S | Ngày đến hạn ôn tập tiếp theo. |
| `difficulty` | N | Mức độ khó (0-5). |

---

### 5.2 Bảng WordCache

> PK đã mã hóa dạng chuẩn hóa: `WORD#<từ_viết_thường>`. Không cần attribute `word_normalized` riêng.

| Thuộc tính | Kiểu | Mô tả |
|------------|------|-------|
| `word` | S | Dạng gốc của từ — dùng để hiển thị. |
| `word_type` | S | Loại từ (adjective, noun, verb, ...). |
| `definition_vi` | S | Nghĩa tiếng Việt lưu trong cache. |
| `phonetic` | S | Phiên âm tiếng Anh. |
| `audio_s3_key` | S | Đường dẫn audio phát âm chuẩn của từ điển. |
| `example_sentence` | S | Câu ví dụ chứa từ. |
| `source_api` | S | Nguồn API cung cấp dữ liệu (ví dụ: `oxford_api`). |
