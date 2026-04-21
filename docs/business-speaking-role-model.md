# Business Specification

## Lexi Speaking Role Model

**Version**: 1.0 | **Date**: April 2026 | **Status**: Draft

---

## 1. Mục đích

Tài liệu này chốt lại mô hình nghiệp vụ cho tính năng luyện nói tiếng Anh bằng AI của Lexi theo hướng MVP, dựa trên cách các sản phẩm tương tự đang triển khai roleplay/speaking practice trên thị trường.

Mục tiêu của tài liệu:

- Làm rõ tại sao scenario không nên lưu riêng `user_roles` và `ai_roles` như hai nguồn dữ liệu độc lập.
- Chốt mô hình đúng hơn cho nghiệp vụ: `scenario.roles[]` là danh sách vai của bối cảnh, còn session là nơi gán vai cho người học và AI.
- Định nghĩa rõ những rule cần áp dụng trước khi tạo session, trong session, và khi kết thúc session.
- Tạo nền tảng ổn định để backend thiết kế API, websocket, scoring, và prompt builder.

---

## 2. Tham chiếu thị trường

### 2.1 Duolingo Max / Roleplay

Từ các kết quả công khai trên trang Duolingo Max, roleplay được đặt như một tính năng trong ngữ cảnh học theo tình huống thực tế, không phải một mô hình data phức tạp tách riêng vai người học và vai AI ngay ở cấp scenario.

Nguồn tham chiếu công khai:

- https://blog.duolingo.com/duolingo-max/
- https://roleplay.duolingo.com/

Điểm quan trọng rút ra:

- Tính năng được đóng gói theo ngữ cảnh / side quest / scenario.
- Người học bước vào một tình huống để luyện phản xạ giao tiếp.
- Trọng tâm là trải nghiệm hội thoại và phản hồi, không phải quản trị nhiều lớp vai trong scenario.

### 2.2 ELSA Speak / Roleplays

ELSA công khai mô tả roleplay là luyện hội thoại theo tình huống thực tế, chọn topic/situation rồi nói với AI, sau đó nhận feedback ngay.

Nguồn tham chiếu công khai:

- https://elsaspeak.com/en/faqs/roleplays/
- https://elsaspeak.com/en/ai/
- https://elsaspeak.com/en/product

Điểm quan trọng rút ra:

- Người học chọn tình huống, không cần một mô hình role matrix phức tạp ở tầng scenario.
- AI đóng vai đối thoại/tutor trong session.
- Sau khi roleplay kết thúc, hệ thống trả feedback theo performance.

### 2.3 Kết luận tham chiếu

Best practice cho MVP của Lexi là:

- Scenario nên là dữ liệu trung tính của tình huống học.
- Session mới là nơi gán vai cho người học và AI.
- Người học có thể swap vai trước khi bắt đầu session.
- Sau khi session đã bắt đầu thì role assignment phải khóa để prompt, scoring, transcript, và audit không bị lệch.

---

## 3. Quyết định chốt

### 3.1 Không dùng `scenario.user_roles` và `scenario.ai_roles` như nguồn sự thật chính

Hai mảng này tạo cảm giác như scenario đã biết trước “đây là vai của user” và “đây là vai của AI”. Điều đó làm dữ liệu bị cứng và khó mở rộng.

Thay vào đó, scenario chỉ cần một danh sách vai:

- `scenario.roles[]`

Danh sách này mô tả các vai hợp lệ trong bối cảnh đó, ví dụ:

- Khách hàng
- Barista

Hoặc:

- Ứng viên
- Nhà tuyển dụng

### 3.2 Role assignment thuộc về session, không thuộc về scenario

Khi người học bắt đầu một phiên:

- hệ thống chọn một vai cho người học
- hệ thống gán vai còn lại cho AI
- người học được phép swap vai trước khi nhấn bắt đầu

Sau khi session đã tạo:

- role assignment trở thành bất biến
- prompt snapshot phải giữ nguyên theo assignment đã chọn
- transcript và scoring phải phản ánh đúng assignment đó

### 3.3 Trong MVP, mỗi scenario có đúng 2 vai

Đây là quyết định MVP tốt nhất cho Lexi ở giai đoạn hiện tại.

Lý do:

- Mỗi session chỉ có 1 người học và 1 AI.
- 2 vai là đủ để mô phỏng phần lớn tình huống luyện nói thực tế.
- Giữ mô hình đơn giản giúp backend, prompt, websocket và scoring ít nhánh hơn.
- Nếu sau này cần multi-party roleplay, có thể mở rộng sau bằng phiên bản dữ liệu khác.

---

## 4. Mô hình dữ liệu nghiệp vụ đề xuất

### 4.1 Scenario

Scenario là tình huống luyện nói chuẩn hóa.

Đề xuất các field chính:

- `scenario_id`
- `scenario_title`
- `context`
- `level`
- `roles[]`
- `goals[]`
- `is_active`
- `usage_count`
- `order`
- `notes`

Ví dụ:

```json
{
  "scenario_id": "cafe-order-001",
  "scenario_title": "Gọi cà phê",
  "context": "Tại quán cà phê",
  "level": "A1",
  "roles": [
    {
      "role_id": "customer",
      "label": "Khách hàng"
    },
    {
      "role_id": "barista",
      "label": "Barista"
    }
  ],
  "goals": ["Chọn đồ uống", "Chọn size", "Hỏi giá"],
  "is_active": true,
  "usage_count": 150,
  "order": 2
}
```

### 4.2 Role

Role là một vai trong bối cảnh luyện nói.

Đề xuất các field tối thiểu:

- `role_id`
- `label`
- `description` hoặc `hint` nếu cần cho prompt

Không nên lưu role theo nghĩa “user role” hay “ai role” ở cấp scenario.
Đó là trách nhiệm của session.

### 4.3 Session

Session là một lần luyện nói cụ thể của một người học.

Đề xuất các field chính:

- `session_id`
- `user_id`
- `scenario_id`
- `learner_role_id`
- `partner_role_id`
- `ai_gender`
- `level`
- `selected_goals[]`
- `prompt_version`
- `prompt_snapshot`
- `status`
- `total_turns`
- `user_turns`
- `hint_used_count`
- `turns[]`
- `scoring`
- `created_at`
- `updated_at`

### 4.4 Prompt Snapshot

Prompt snapshot không chỉ là một string ngẫu nhiên.

Nên có:

- prompt template version
- input variables
- final rendered prompt

Mục tiêu là:

- audit được buổi học
- debug được prompt
- thay template không phá dữ liệu cũ

---

## 5. Nghiệp vụ tạo session

### 5.1 Chọn scenario

Người học vào màn “Lộ trình luyện nói”, chọn một scenario phù hợp.

### 5.2 Chọn role

Hệ thống hiển thị 2 vai trong scenario.

Người học chọn:

- vai mình sẽ đóng
- vai AI sẽ đóng

Mặc định:

- role đầu tiên trong `scenario.roles[]` được gán cho người học
- role còn lại được gán cho AI

Người học có thể bấm swap trước khi bắt đầu.

### 5.3 Chọn goal

Người học có thể chọn một hoặc nhiều mục tiêu luyện tập trong scenario.

Rule chốt:

- nếu không chọn goal nào, hệ thống lấy toàn bộ goals của scenario làm mặc định
- tối thiểu phải có 1 goal hợp lệ để tạo prompt

### 5.4 Chọn level và giọng AI

Người học chọn level và giới tính giọng AI trước khi tạo session.

### 5.5 Validate trước khi tạo

Backend phải kiểm tra:

- scenario còn active
- scenario có đúng 2 roles cho MVP
- `learner_role_id` và `partner_role_id` đều thuộc `scenario.roles[]`
- hai role phải khác nhau
- selected goals phải thuộc scenario.goals
- level hợp lệ
- ai_gender hợp lệ

### 5.6 Tạo session

Khi tạo session, backend phải lưu nguyên assignment đã chọn.

Sau đó backend tạo prompt snapshot và trả session_id để frontend chuyển sang trang hội thoại.

---

## 6. Nghiệp vụ trong session

### 6.1 Khởi động session

Khi session screen mở:

- frontend kết nối websocket bằng token và session_id
- frontend gửi `START_SESSION`
- backend trả `upload_url` nếu có luồng ghi âm

### 6.2 Người học gửi text

Khi người học gửi tin nhắn:

- frontend tạo turn USER ở trạng thái pending
- backend lưu turn
- AI phản hồi bằng text chunk hoặc audio nếu có
- khi lưu xong, backend đánh dấu turn không còn pending

### 6.3 Ghi âm và upload

Khi người học dùng micro:

- client ghi âm
- upload audio lên S3 bằng presigned URL
- sau đó báo `AUDIO_UPLOADED`
- backend xử lý STT và sinh turn tương ứng

### 6.4 Xin hint

Hint là trợ giúp theo ngữ cảnh session.

Rule chốt:

- chỉ nên cho 1 hint active tại một thời điểm
- hint là feature hỗ trợ, không phải luồng chính
- backend nên trả hint theo scenario + trạng thái session

### 6.5 Dịch turn

Dịch chỉ nên hiểu là hỗ trợ đọc lại một turn đã có.

Rule chốt:

- translation gắn theo turn
- backend có thể cache theo turn để tránh gọi lại nhiều lần
- translation không được làm thay đổi transcript gốc

### 6.6 Nộp bài và chấm điểm

Khi người học nộp bài:

- session chuyển sang trạng thái submitted hoặc scoring
- turn mới bị khóa
- backend bắt đầu chấm điểm
- kết quả có thể trả đồng bộ hoặc bất đồng bộ, nhưng phải nhất quán với một cơ chế duy nhất

Nếu kết quả chưa sẵn sàng:

- UI hiển thị “đang tổng kết điểm”
- backend bắn event hoặc cho phép polling đến khi có scoring

---

## 7. Rule nghiệp vụ chốt

### 7.1 Rule về role

- Scenario chỉ chứa `roles[]` trung tính.
- Session mới chứa role assignment cụ thể.
- Người học được phép swap vai trước khi start.
- Sau khi start, role assignment khóa cứng.
- MVP chỉ hỗ trợ đúng 2 vai trong một scenario.

### 7.2 Rule về prompt

- Prompt phải sinh từ dữ liệu chuẩn hóa.
- Prompt snapshot phải được lưu cùng session.
- Prompt version phải có để truy vết.

### 7.3 Rule về scoring

- Scoring là bước cuối của session.
- Scoring phải trả tối thiểu: fluency, pronunciation, grammar, vocabulary, overall, feedback.
- Session có scoring xong thì mới được đánh dấu completed.

### 7.4 Rule về data ownership

- Scenario là master data.
- Session là transaction data.
- Profile là user preference data.
- Không để logic nghiệp vụ phụ thuộc vào hardcode ở frontend.

### 7.5 Rule về backward compatibility

Nếu sau này muốn hỗ trợ 3+ vai:

- không mở rộng bằng cách nhét thêm `user_roles` và `ai_roles`
- nên tạo version model mới cho role assignment hoặc role slots

---

## 8. Không làm trong MVP

Để tránh over-engineering, MVP này không nên làm các việc sau:

- multi-party roleplay nhiều hơn 2 vai
- auto unlock phức tạp theo graph prerequisite ngay từ đầu
- cho phép edit prompt thủ công trong session runtime
- lưu KPI dashboard dạng hardcode
- thêm skip turn nếu chưa có nghiệp vụ và UI hoàn chỉnh

---

## 9. Tiêu chí nghiệm thu

Một thiết kế được coi là đạt khi:

- người học chọn scenario xong có thể swap vai trước khi start
- backend lưu được role assignment của session một cách bất biến
- prompt snapshot tái tạo được chính buổi học đó
- session kết thúc thì scoring được trả về rõ ràng
- cùng một scenario có thể dùng lại nhiều lần mà không bị phụ thuộc vào assignment cố định ở scenario
- không còn mâu thuẫn giữa `user_roles` / `ai_roles` ở scenario và `selected_user_role` / `selected_ai_role` ở session

---

## 10. Kết luận

Best practice cho Lexi ở giai đoạn này là:

- Scenario chỉ là danh sách tình huống và vai hợp lệ.
- Session mới là nơi chốt vai người học và vai AI.
- Người học có thể swap vai trước khi bắt đầu.
- Khi đã vào session thì assignment phải khóa.
- Dữ liệu prompt và scoring phải được backend quản lý như nguồn sự thật.

Đây là mô hình đơn giản nhất nhưng vẫn đủ chặt để mở rộng sau này.
