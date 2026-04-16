# Database Specification (LexiLearn)

Tài liệu này đã được cập nhật để phản ánh chính xác các trường hiện có trong các `dataclass` tại `src/domain/entities`.

Lưu ý: phần "Kiểu" bên dưới mô tả kiểu Python trong dataclass (Ví dụ: `ULID`, `str`, `datetime`, `Enum`). Khi lưu vào DynamoDB, các kiểu này cần được serialize (ULID → string, Enum → string, datetime → ISO8601 string, v.v.).

---

## 1. Tổng quan các bảng (Table List)

| Table Name  | Billing Mode    | Partition Key (PK) | Sort Key (SK) | Mô tả                                                                                                           |
| ----------- | --------------- | ------------------ | ------------- | --------------------------------------------------------------------------------------------------------------- |
| `LexiApp`   | PAY_PER_REQUEST | String (S)         | String (S)    | Bảng chính (Single-Table Design) chứa dữ liệu nghiệp vụ: Profile, Scenario, Session, Turn, Scoring, Flashcards. |
| `WordCache` | PAY_PER_REQUEST | String (S)         | String (S)    | Bảng cache từ vựng (Vocabulary) chung cho tất cả người dùng.                                                    |

---

## 2. Đặc tả bảng LexiApp (Single-Table Design)

Bảng `LexiApp` gom nhiều loại thực thể vào một bảng duy nhất nhằm tối ưu hóa hiệu năng truy vấn.

### 2.1 Các Loại Thực Thể (Entity Types)

| Thực thể         | PK                     | SK                         | Entity ID Field (dataclass type)                 |
| ---------------- | ---------------------- | -------------------------- | ------------------------------------------------ |
| **USER_PROFILE** | `USER#<user_id>`       | `PROFILE`                  | `user_id: str`                                   |
| **SCENARIO**     | `SYSTEM#SCENARIOS`     | `SCENARIO#<scenario_id>`   | `scenario_id: ULID`                              |
| **SESSION**      | `SESSION#<session_id>` | `METADATA`                 | `session_id: ULID`                               |
| **TURN**         | `SESSION#<session_id>` | `TURN#<turn_index>`        | composite: `session_id: ULID`, `turn_index: int` |
| **SCORING**      | `SESSION#<session_id>` | `SCORING`                  | `scoring_id: ULID`                               |
| **FLASHCARD**    | `USER#<user_id>`       | `FLASHCARD#<flashcard_id>` | `flashcard_id: str`                              |

### 2.2 Các Chỉ Mục Phụ (GSIs)

- **GSI1: `GSI1-UserEntity-Time`**
  - **GSI1PK**: `<USER#id>#<ENTITY_TYPE>` (ví dụ `USER#123#SESSION`)
  - **GSI1SK**: thường là `ULID` hoặc `ISO8601` timestamp (dùng để sắp xếp theo thời gian)
- **GSI2: `GSI2-SRS-ReviewQueue`**
  - **GSI2PK**: `USER#<user_id>`
  - **GSI2SK**: `next_review_at` (ISO8601) — sắp xếp theo hạn ôn tập
- **GSI3: `GSI3-Admin-EntityList`**
  - **GSI3PK**: `EntityType` (ví dụ `USER_PROFILE`)
  - **GSI3SK**: `joined_at` (timestamp kỹ thuật)

---

## 3. Đặc tả bảng WordCache (Vocabulary Entity)

Bảng này hoạt động như một tầng cache dùng chung để lưu định nghĩa và thông tin từ điển.

- **PK**: `WORD#<word_normalized>` (từ đã viết thường)
- **SK**: `METADATA`
- **TTL**: Tự động xóa sau 60 ngày nếu không có cập nhật mới (`ttl` attribute) — trong code, `Vocabulary` là dataclass và không chứa TTL; TTL được quản lý ở tầng persistence.

---

## 4. Mô hình truy cập (Access Patterns)

| #   | Use Case (Nghiệp vụ)    | Operation | Index     | Key Pattern                                      |
| --- | ----------------------- | --------- | --------- | ------------------------------------------------ |
| 1   | Lấy profile người dùng  | `GetItem` | Base      | `PK=USER#id, SK=PROFILE`                         |
| 2   | Lấy danh sách Scenarios | `Query`   | Base      | `PK=SYSTEM#SCENARIOS, SK begins_with(SCENARIO#)` |
| 3   | Tạo session mới         | `PutItem` | Base      | `PK=SESSION#[id], SK=METADATA`                   |
| 4   | Lấy danh sách session   | `Query`   | GSI1      | `GSI1PK=USER#id#SESSION, GSI1SK desc`            |
| 5   | Lấy hội thoại session   | `Query`   | Base      | `PK=SESSION#id, SK begins_with(TURN#)`           |
| 6   | Lưu lượt nói & bản dịch | `PutItem` | Base      | `PK=SESSION#id, SK=TURN#index`                   |
| 7   | Ghi chấm điểm session   | `PutItem` | Base      | `PK=SESSION#id, SK=SCORING`                      |
| 8   | Flashcards theo User    | `Query`   | GSI1      | `GSI1PK=USER#id#FLASHCARD, GSI1SK desc`          |
| 9   | Flashcards cần ôn (SRS) | `Query`   | GSI2      | `GSI2PK=USER#id, GSI2SK <= today`                |
| 10  | Tra cứu từ điển cache   | `GetItem` | WordCache | `PK=WORD#word, SK=METADATA`                      |

---

## 5. Đặc tả chi tiết thuộc tính (Attribute Reference)

> Phần này liệt kê chính xác các trường hiện có trong `dataclass` tại `src/domain/entities` (phiên bản hiện tại của mã nguồn).

### 5.1 Bảng LexiApp (theo dataclass)

#### Thực thể `UserProfile` (`src/domain/entities/user_profile.py`)

| Thuộc tính            | Kiểu (dataclass)          | Ghi chú/serialize                                                              |
| --------------------- | ------------------------- | ------------------------------------------------------------------------------ |
| `user_id`             | `str`                     | ID định danh hệ thống (trùng với auth id). Lưu DynamoDB: string                |
| `email`               | `str`                     | Email đăng ký                                                                  |
| `display_name`        | `str`                     | Tên hiển thị                                                                   |
| `avatar_url`          | `str`                     | URL ảnh đại diện (thêm trong dataclass, không có trong spec cũ)                |
| `current_level`       | `ProficiencyLevel` (Enum) | Serialize → string                                                             |
| `learning_goal`       | `ProficiencyLevel` (Enum) | Serialize → string                                                             |
| `role`                | `Role` (Enum)             | Serialize → string (LEARNER/ADMIN)                                             |
| `is_active`           | `bool`                    | Lưu DynamoDB: BOOL                                                             |
| `is_new_user`         | `bool`                    | Flag onboarding cá nhân                                                        |
| `current_streak`      | `int`                     | Số ngày học liên tục                                                           |
| `last_completed_at`   | `str`                     | Trong dataclass là ISO string; khi dùng `datetime` thì serialize thành ISO8601 |
| `total_words_learned` | `int`                     | Tổng số từ đã học                                                              |

#### Thực thể `Scenario` (`src/domain/entities/scenario.py`)

| Thuộc tính       | Kiểu (dataclass) | Ghi chú                                                |
| ---------------- | ---------------- | ------------------------------------------------------ |
| `scenario_id`    | `ULID`           | `ulid.ULID` ở code — serialize → string                |
| `scenario_title` | `str`            | Tiêu đề kịch bản                                       |
| `context`        | `str`            | Context label (ví dụ: `cafe`, `interview`)             |
| `my_character`   | `str`            | Nhân vật người dùng                                    |
| `ai_character`   | `str`            | Nhân vật AI                                            |
| `goals`          | `List[str]`      | Danh sách các goal (ví dụ: `order drink`)              |
| `user_roles`     | `List[str]`      | Các vai trò người dùng có thể chọn (ví dụ: `customer`) |
| `ai_roles`       | `List[str]`      | Các vai trò AI có thể đóng (ví dụ: `barista`)          |
| `is_active`      | `bool`           | Trạng thái kích hoạt                                   |
| `usage_count`    | `int`            | Số phiên đã dùng kịch bản này                          |

> Ghi chú: dataclass hiện tại không có `usage_count` (một method `increment_usage()` tham chiếu `self.usage_count` — đây là điểm không khớp trong code).

#### Thực thể `Session` (`src/domain/entities/session.py`)

| Thuộc tính        | Kiểu (dataclass)          | Ghi chú                                                                |
| ----------------- | ------------------------- | ---------------------------------------------------------------------- |
| `session_id`      | `ULID`                    | ID phiên học                                                           |
| `scenario_id`     | `ULID`                    | ID kịch bản                                                            |
| `user_id`         | `str`                     | ID người dùng (dataclass mặc định `""` nhưng `__post_init__` bắt buộc) |
| `ai_gender`       | `Gender` (Enum)           | Serialize → string                                                     |
| `level`           | `ProficiencyLevel` (Enum) | Serialize → string                                                     |
| `prompt_snapshot` | `str`                     | Prompt hoàn chỉnh được dùng cho session (lưu để replay/debug)          |
| `total_turns`     | `int`                     | Tổng số lượt thoại                                                     |
| `user_turns`      | `int`                     | Số lượt của user                                                       |
| `hint_used_count` | `int`                     | Số lần dùng gợi ý                                                      |

> Ghi chú: thứ tự trường trong dataclass có một trường có default (`user_id`) trước trường không-default (`scenario_id`) — điều này có thể gây lỗi khi khởi tạo nếu truyền positional args.

#### Thực thể `Turn` (`src/domain/entities/turn.py`)

| Thuộc tính           | Kiểu (dataclass) | Ghi chú                      |
| -------------------- | ---------------- | ---------------------------- |
| `session_id`         | `ULID`           | Liên kết tới session         |
| `turn_index`         | `int`            | Thứ tự lượt nói (mặc định 0) |
| `speaker`            | `Speaker` (Enum) | `AI` hoặc `USER`             |
| `content`            | `str`            | Nội dung văn bản             |
| `audio_url`          | `str`            | URL file âm thanh            |
| `translated_content` | `str`            | Bản dịch                     |
| `is_hint_used`       | `bool`           | Flag gợi ý                   |

> Ghi chú: dataclass không có `turn_id`; hệ thống hiện dùng composite (`session_id`, `turn_index`) làm định danh lượt thoại.

#### Thực thể `Scoring` (`src/domain/entities/scoring.py`)

| Thuộc tính         | Kiểu (dataclass) | Ghi chú              |
| ------------------ | ---------------- | -------------------- |
| `scoring_id`       | `ULID`           | ID bản ghi chấm điểm |
| `session_id`       | `ULID`           | Liên kết tới session |
| `grammar_score`    | `int`            | 0-100                |
| `vocabulary_score` | `int`            | 0-100                |
| `overall_score`    | `int`            | Điểm tổng kết        |
| `feedback`         | `str`            | Nhận xét từ AI       |

> Ghi chú quan trọng: trong code, một số method (`__post_init__`, `calculate_overall`, `add_feedback`) tham chiếu tới `fluency_score`, `coherence_score` hoặc `feedback_fluency` nhưng những trường này **không có** trong dataclass hiện tại — đây là điểm cần fix trong code hoặc dataclass nếu muốn giữ logic đó.

#### Thực thể `FlashCard` (`src/domain/entities/flashcard.py`)

| Thuộc tính         | Kiểu (dataclass)     | Ghi chú                                     |
| ------------------ | -------------------- | ------------------------------------------- |
| `flashcard_id`     | `str`                | ULID/str định danh thẻ                      |
| `user_id`          | `str`                | ID người sở hữu                             |
| `word`             | `str`                | Từ vựng liên kết                            |
| `review_count`     | `int`                | Số lần ôn                                   |
| `interval_days`    | `int`                | Khoảng cách ôn (ngày)                       |
| `difficulty`       | `int`                | 0-5                                         |
| `last_reviewed_at` | `Optional[datetime]` | `datetime` trong code — serialize → ISO8601 |
| `next_review_at`   | `datetime`           | `datetime` trong code — serialize → ISO8601 |

---

### 5.2 Bảng `Vocabulary` (`src/domain/entities/vocabulary.py`)

| Thuộc tính         | Kiểu (dataclass)   | Ghi chú                                      |
| ------------------ | ------------------ | -------------------------------------------- |
| `word`             | `str`              | Từ vựng (lowercased & trimmed) — dùng làm ID |
| `word_type`        | `VocabType` (Enum) | Serialize → string                           |
| `definition_vi`    | `str`              | Định nghĩa tiếng Việt                        |
| `phonetic`         | `str`              | Phiên âm (IPA)                               |
| `audio_url`        | `str`              | URL file phát âm                             |
| `example_sentence` | `str`              | Câu ví dụ                                    |
| `source_api`       | `Optional[str]`    | Nguồn dữ liệu                                |
