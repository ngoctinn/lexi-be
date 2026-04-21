# Business Specification

## Lexi Learning Platform Proposal

**Version**: 1.0 | **Date**: April 2026 | **Status**: Draft

---

## 1. Mục đích

Tài liệu này mô tả nghiệp vụ tổng thể của dự án Lexi theo góc nhìn sản phẩm, để người học, admin, backend, frontend, QA và người theo dõi dự án đều hiểu rõ ứng dụng đang làm gì, vận hành ra sao, và mỗi luồng chính cần xử lý như thế nào.

Mục tiêu của Lexi là tạo một nền tảng học tiếng Anh theo hướng thực hành:

- Người học luyện nói với AI theo tình huống thực tế.
- Người học được dịch nghĩa trong lúc trò chuyện.
- Người học có thể lưu từ vựng quan trọng vào flashcard để ôn lại sau.
- Admin quản lý nội dung học, người dùng, và chất lượng lộ trình.

Đây là bản proposal nghiệp vụ, không phải bản confirm UI. Tài liệu này đi theo logic sản phẩm, không theo chi tiết giao diện.

---

## 2. Tóm tắt sản phẩm

Lexi gồm 4 lớp giá trị chính:

1. **Học nói bằng AI**
   - Người học chọn một tình huống.
   - Người học chọn vai của mình trước khi bắt đầu.
   - AI đóng vai đối thoại còn lại.
   - Cuộc trò chuyện diễn ra theo thời gian thực.

2. **Sửa lỗi và giải thích ngay trong lúc học**
   - Người học có thể xin gợi ý.
   - Người học có thể dịch từ, cụm từ, hoặc cả lượt hội thoại.
   - Hệ thống trả feedback sau khi kết thúc phiên.

3. **Lưu từ vựng để học lại**
   - Người học có thể lưu từ/ cụm từ quan trọng từ cuộc trò chuyện vào flashcard.
   - Flashcard được đưa vào lịch ôn tập SRS.

4. **Quản trị nội dung và người dùng**
   - Admin quản lý scenario, level, trạng thái mở/ẩn, thứ tự hiển thị.
   - Admin quản lý người dùng, trạng thái học, và ghi chú nội bộ.

---

## 3. Vai trò trong hệ thống

### 3.1 Learner

Learner là người học tiếng Anh trên Lexi. Đây là actor chính của sản phẩm.

Learner có thể:

- đăng ký và đăng nhập
- hoàn thành onboarding
- cập nhật hồ sơ cá nhân
- chọn lộ trình luyện nói
- bắt đầu phiên hội thoại với AI
- swap vai trước khi vào bài
- dịch từ vựng trong lúc học
- lưu từ vựng vào flashcard
- kết thúc phiên và xem điểm
- ôn flashcard theo SRS

### 3.2 Admin

Admin là người quản trị nội dung và người dùng trên hệ thống.

Admin có thể:

- xem dashboard quản trị
- quản lý danh sách người dùng
- quản lý danh sách scenario
- bật/ẩn scenario
- cập nhật level, trạng thái, ghi chú của user
- cập nhật scenario, goals, roles, thứ tự hiển thị

### 3.3 System

System không phải actor nghiệp vụ chính, nhưng là phần vận hành nền tảng.

System chịu trách nhiệm:

- xác thực người dùng
- kiểm tra trạng thái onboarding
- tạo session
- kết nối real-time trong phiên học
- xử lý upload âm thanh
- lưu transcript, scoring, flashcard
- áp dụng luật SRS

---

## 4. Mô hình sản phẩm theo hành trình người dùng

## 4.1 Người học mở app

Khi người học mở app, hệ thống đi theo thứ tự sau:

1. Nếu là trang công khai, người học thấy landing/marketing page.
2. Nếu đã đăng nhập, hệ thống kiểm tra profile.
3. Nếu là user mới, hệ thống chuyển sang onboarding.
4. Nếu không phải user mới, hệ thống cho vào dashboard.

### Ý nghĩa nghiệp vụ

- Landing page là nơi giới thiệu sản phẩm.
- Login/signup là bước vào hệ thống.
- Onboarding là bước bắt buộc cho user mới.
- Dashboard là nơi bắt đầu học.

---

## 4.2 Onboarding

Onboarding là bước đầu tiên để cá nhân hóa trải nghiệm học.

Người học cần cung cấp:

- tên hiển thị
- trình độ hiện tại
- mục tiêu học
- avatar hoặc ảnh đại diện nếu muốn

### Rule nghiệp vụ

- User mới phải qua onboarding trước khi vào học.
- Onboarding chỉ cần ngắn gọn, không được làm người dùng mệt.
- Sau khi hoàn tất onboarding, hệ thống đánh dấu user đã sẵn sàng học.
- Dữ liệu onboarding phải trở thành dữ liệu profile chính thức.

### Kết quả mong đợi

Sau onboarding, người học nhìn thấy dashboard cá nhân hóa.

---

## 4.3 Dashboard của người học

Dashboard là trung tâm điều hướng của learner.

Tại đây người học có thể:

- vào lộ trình luyện nói
- vào flashcards
- xem lịch sử session gần đây
- đi tới profile

### Ý nghĩa nghiệp vụ

Dashboard không phải nơi học chính, mà là nơi quyết định bước tiếp theo.
Nó phải giúp người học trả lời nhanh 2 câu hỏi:

- Hôm nay tôi nên luyện nói gì?
- Hôm nay tôi nên ôn từ nào?

---

## 4.4 Chọn lộ trình luyện nói

Người học vào màn luyện nói để chọn một scenario phù hợp.

Một scenario là một tình huống học, ví dụ:

- gọi cà phê
- hỏi đường
- phỏng vấn xin việc
- check-in khách sạn

### Rule nghiệp vụ

- Scenario phải được admin chuẩn bị trước.
- Scenario chỉ xuất hiện nếu đang active.
- Scenario có level khuyến nghị.
- Scenario có danh sách goal.
- Scenario có danh sách role hợp lệ cho bài học.

### Mục tiêu của màn này

Người học không chọn một bài học trừu tượng.
Người học chọn một tình huống giao tiếp cụ thể để nhập vai và luyện phản xạ.

---

## 4.5 Chọn vai trước khi bắt đầu session

Đây là phần rất quan trọng của nghiệp vụ.

Lexi không chốt vai người học và vai AI ngay từ scenario.
Thay vào đó:

- scenario chỉ cung cấp danh sách role hợp lệ
- session mới là nơi chốt ai đóng vai nào

### Quy tắc chốt

- Một scenario trong MVP chỉ có 2 role hợp lệ.
- Người học được chọn một trong 2 role.
- AI nhận role còn lại.
- Người học được phép swap vai trước khi nhấn bắt đầu.
- Khi session đã bắt đầu, role assignment bị khóa.

### Vì sao làm như vậy

- Giữ sản phẩm đơn giản.
- Tách dữ liệu master của scenario khỏi dữ liệu runtime của session.
- Tránh nhồi hai khái niệm khác nhau vào cùng một model.
- Dễ audit prompt, transcript và scoring.

### Kết luận thiết kế

Không dùng `scenario.user_roles` và `scenario.ai_roles` như nguồn sự thật chính.
Thay vào đó:

- `scenario.roles[]` là danh sách vai hợp lệ của scenario
- `session.learner_role_id` là vai người học đã chọn
- `session.ai_role_id` là vai AI đã nhận

---

## 4.6 Bắt đầu phiên hội thoại

Khi người học nhấn bắt đầu:

1. Hệ thống kiểm tra scenario còn active.
2. Hệ thống kiểm tra role hợp lệ.
3. Hệ thống kiểm tra goal hợp lệ.
4. Hệ thống tạo session mới.
5. Hệ thống sinh prompt snapshot.
6. Người học được chuyển vào màn hội thoại.

### Dữ liệu phải khóa trong session

- scenario đã chọn
- role assignment
- goals đã chọn
- level đã chọn
- giọng AI đã chọn
- prompt snapshot

### Ý nghĩa nghiệp vụ

Session là một bản ghi thực thi của một buổi học cụ thể.
Sau khi tạo session, dữ liệu này không được tự ý đổi lại từ scenario gốc.

---

## 4.7 Trong lúc trò chuyện

Khi session đang diễn ra, người học có thể tương tác theo nhiều cách.

### 4.7.1 Gửi câu trả lời bằng text

Người học nhập câu trả lời bằng tiếng Anh.

Hệ thống phải:

- lưu câu trả lời vào transcript
- đánh dấu lượt nói mới
- cho AI phản hồi tiếp

### 4.7.2 Ghi âm bằng micro

Người học có thể nói bằng giọng thật thay vì gõ text.

Hệ thống cần:

- cho phép ghi âm
- upload audio
- xử lý speech-to-text
- đưa kết quả vào transcript

### 4.7.3 Xin gợi ý

Người học có thể xin hint khi bí ý.

Hint cần có tính ngữ cảnh:

- bám vào scenario
- bám vào role hiện tại
- bám vào diễn tiến của session

Hint không phải đáp án cứng.
Hint là trợ giúp để người học tiếp tục nói được.

### 4.7.4 Dịch từ vựng hoặc lượt hội thoại

Người học có thể dịch:

- một từ
- một cụm từ
- một lượt hội thoại

### Rule nghiệp vụ

- Dịch không được làm thay đổi nội dung gốc của transcript.
- Bản dịch chỉ là lớp trợ giúp.
- Khi dịch xong, hệ thống có thể hiển thị nghĩa, gợi ý dùng từ, hoặc giải thích ngắn.

### 4.7.5 Lưu từ vựng vào flashcard

Đây là luồng rất quan trọng của sản phẩm.

Người học có thể chọn một từ hoặc cụm từ quan trọng trong lúc trò chuyện và lưu lại để học sau.

#### Luồng nghiệp vụ đề xuất

1. Người học chọn một từ hoặc cụm từ từ nội dung đang học.
2. Hệ thống hiển thị nghĩa hoặc thông tin dịch.
3. Người học bấm “Lưu vào flashcard”.
4. Hệ thống tạo flashcard mới cho người học.
5. Flashcard xuất hiện trong deck học sau.

#### Flashcard tạo từ cuộc trò chuyện nên chứa gì

- từ hoặc cụm từ
- nghĩa tiếng Việt
- câu ví dụ từ ngữ cảnh thật
- phiên âm nếu có
- nguồn tạo: session_id và turn_index
- lịch ôn tập SRS ban đầu

#### Ý nghĩa nghiệp vụ

Mục tiêu không chỉ là hiểu nghĩa ngay lúc học, mà còn biến từ vựng đó thành tài sản học lại về sau.

---

## 4.8 Kết thúc session và chấm điểm

Khi người học nộp bài:

- session chuyển sang trạng thái kết thúc/chấm điểm
- AI và các action realtime dừng lại
- hệ thống tổng hợp kết quả
- người học xem điểm tổng kết

### Điểm cần hiển thị

- fluency
- pronunciation
- grammar
- vocabulary
- overall
- feedback tổng quát

### Ý nghĩa nghiệp vụ

Phiên học không kết thúc ở việc nói xong.
Phiên học kết thúc bằng feedback để người học biết mình tiến bộ ở đâu.

---

## 4.9 Xem lại lịch sử session

Người học có thể mở lại các session gần đây.

Lịch sử này giúp họ:

- nhớ lại bài đã học
- quay lại session chưa hoàn thành
- xem điểm và feedback trước đó

### Rule nghiệp vụ

- Session cũ phải giữ được transcript và summary.
- Session cũ không bị ảnh hưởng khi admin sửa scenario về sau.
- Nếu scenario thay đổi, session cũ vẫn phải giữ snapshot cũ để audit.

---

## 4.10 Học flashcard sau buổi nói

Flashcard là phần retention của sản phẩm.

Sau khi lưu từ vựng từ cuộc trò chuyện, người học vào flashcards để ôn lại.

### Luồng nghiệp vụ

1. Hệ thống hiển thị danh sách thẻ đến hạn.
2. Người học mở một thẻ.
3. Người học xem nghĩa, ví dụ, phiên âm.
4. Người học tự đánh giá mức độ nhớ:
   - quên
   - khó
   - tốt
   - dễ
5. Hệ thống cập nhật lịch SRS.

### Rule nghiệp vụ SRS

- Nếu “quên”, thẻ có thể quay lại trong cùng phiên ôn.
- Nếu “tốt” hoặc “dễ”, thẻ được đẩy lịch xa hơn.
- Nếu hết thẻ đến hạn, hệ thống hiển thị trạng thái hoàn thành.

### Ý nghĩa nghiệp vụ

Flashcard là cơ chế biến nội dung vừa học thành trí nhớ dài hạn.

---

## 4.11 Hồ sơ cá nhân

Người học có thể vào profile để chỉnh lại thông tin cá nhân.

Có thể cập nhật:

- tên hiển thị
- avatar
- trình độ hiện tại
- mục tiêu học

### Rule nghiệp vụ chốt

Để rõ nghĩa và dễ mở rộng, nên tách thành 3 khái niệm:

- `current_level`: trình độ hiện tại
- `target_level`: trình độ muốn đạt
- `learning_goal_text`: mục tiêu học mô tả bằng chữ

### Vì sao cần tách

Vì một field như `learning_goal` nếu vừa mang nghĩa level vừa mang nghĩa mục tiêu bằng chữ thì sẽ gây nhập nhằng cho cả backend lẫn UX.

---

## 5. Hành trình của Admin

## 5.1 Admin mở app

Admin vào app bằng quyền quản trị.

Sau khi đăng nhập, admin được chuyển vào khu vực quản trị.

### Mục tiêu của admin

- kiểm tra chất lượng nội dung
- quản lý người học
- quản lý scenario
- giữ cho dữ liệu học luôn sạch và dùng được

---

## 5.2 Dashboard admin

Dashboard admin là nơi nhìn nhanh sức khỏe hệ thống.

Nên có các thông tin như:

- số người dùng đang hoạt động
- số người dùng cần theo dõi
- số scenario đang mở
- số lượt dùng scenario

### Ý nghĩa nghiệp vụ

Admin không chỉ sửa dữ liệu.
Admin cần thấy bức tranh tổng thể của sản phẩm.

---

## 5.3 Quản lý người dùng

Admin có thể:

- xem danh sách learner
- tìm theo tên, email, level, mục tiêu
- xem trạng thái học
- xem streak và số buổi đã học
- cập nhật thông tin cần thiết

### Trạng thái user

Một learner có thể ở các trạng thái như:

- invited
- active
- paused
- review

### Ý nghĩa nghiệp vụ

- invited: đã được mời hoặc tạo nhưng chưa hoàn tất học
- active: đang học bình thường
- paused: tạm dừng
- review: cần hỗ trợ hoặc cần theo dõi thêm

### Rule nghiệp vụ

- Admin chỉ sửa các thông tin quản trị.
- Admin không được làm mất dữ liệu học của người dùng.
- Update user phải phản ánh đúng trên hệ thống ngay sau khi lưu.

---

## 5.4 Quản lý scenario

Admin quản lý kho tình huống luyện nói.

Mỗi scenario cần có:

- tiêu đề
- chủ đề/ngữ cảnh
- level khuyến nghị
- 2 role hợp lệ
- danh sách goal
- trạng thái mở/ẩn
- thứ tự hiển thị
- ghi chú nội bộ

### Rule nghiệp vụ quan trọng

- Scenario đang ẩn thì không được dùng cho session mới.
- Scenario đã dùng trong session cũ không được sửa phá lịch sử.
- Nếu sửa scenario, session cũ vẫn giữ snapshot đã tạo ở thời điểm cũ.

### Chất lượng nội dung

Admin phải đảm bảo scenario:

- đúng trình độ
- đúng ngữ cảnh
- đủ tự nhiên để đóng vai
- có goal rõ ràng
- không mâu thuẫn giữa vai và chủ đề

---

## 5.5 Cập nhật lộ trình học

Admin có thể sắp xếp thứ tự hiển thị scenario và xác định cái nào xuất hiện trước.

### Ý nghĩa nghiệp vụ

Lộ trình học không phải danh sách ngẫu nhiên.
Nó là chuỗi tình huống có chủ đích để dẫn người học đi từ dễ đến khó.

---

## 6. Mô hình dữ liệu nghiệp vụ chốt

## 6.1 Scenario

Scenario là tình huống học chuẩn hóa.

Các field nghiệp vụ chính:

- scenario_id
- scenario_title
- context
- level
- roles[]
- goals[]
- is_active
- usage_count
- order
- notes

### Quy tắc

- Trong MVP, mỗi scenario có đúng 2 roles.
- roles là danh sách vai trung tính, không gắn sẵn user hay AI.

## 6.2 Role

Role là một vai trong tình huống.

Ví dụ:

- Khách hàng
- Barista
- Ứng viên
- Nhà tuyển dụng

Role không phải là user role hay admin role.
Role là một vai diễn trong bài học.

## 6.3 Session

Session là một phiên học của người học.

Các field nghiệp vụ chính:

- session_id
- user_id
- scenario_id
- learner_role_id
- ai_role_id
- ai_gender
- level
- selected_goals[]
- prompt_version
- prompt_snapshot
- status
- turns[]
- scoring
- hint_used_count
- total_turns
- user_turns
- created_at
- updated_at

### Quy tắc

- Session phải lưu role assignment đã chọn.
- Role assignment bị khóa sau khi bắt đầu.
- Prompt snapshot phải đi theo session, không đi theo scenario.

## 6.4 Turn

Turn là một lượt nói trong session.

Turn có thể là:

- USER
- AI

Các thông tin thường đi kèm:

- nội dung gốc
- bản dịch nếu có
- audio_url nếu có
- trạng thái pending hay đã lưu
- cờ cho biết có dùng hint hay không

## 6.5 Flashcard

Flashcard là đơn vị ôn tập sau khi người học học được một từ hoặc cụm từ.

Các field nghiệp vụ chính:

- flashcard_id
- user_id
- word hoặc phrase
- definition_vi
- phonetic
- example_sentence
- audio_url
- review_count
- interval_days
- difficulty
- last_reviewed_at
- next_review_at
- source_session_id
- source_turn_index

### Quy tắc

- Flashcard phải gắn được với nguồn gốc tạo ra nó.
- Flashcard tạo từ session phải quay về deck học của chính người dùng đó.

## 6.6 SRS

SRS là cơ chế xếp lịch ôn lại.

Mức đánh giá chuẩn:

- forgot
- hard
- good
- easy

### Ý nghĩa

- forgot: phải gặp lại sớm
- hard: cần ôn sớm hơn bình thường
- good: đã nhớ tương đối tốt
- easy: có thể giãn lịch xa hơn

---

## 7. Quy tắc nghiệp vụ chốt

### 7.1 Quy tắc về trạng thái người dùng

- User mới phải qua onboarding.
- User cũ đi thẳng vào dashboard.
- Nếu profile cho biết user chưa hoàn tất onboarding, hệ thống phải chặn đường vào app học chính.

### 7.2 Quy tắc về session

- Chỉ learner sở hữu session hoặc admin được phép xem session đó.
- Session đang active không được đổi role ngẫu nhiên.
- Session đã completed không được ghi đè transcript.
- Nếu scoring chưa xong, UI phải thể hiện trạng thái đang tổng kết.

### 7.3 Quy tắc về role model

- Scenario chỉ giữ roles[] trung tính.
- Session mới chốt learner_role_id và ai_role_id.
- Người học có thể swap trước start.
- Sau start thì khóa.
- Không dùng hai mảng user_roles / ai_roles như nguồn sự thật chính.

### 7.4 Quy tắc về dịch và lưu flashcard

- Dịch là lớp hỗ trợ, không thay đổi nội dung gốc.
- Người học có thể dịch một từ, cụm từ, hoặc lượt hội thoại.
- Người học có thể lưu từ vựng được dịch vào flashcard.
- Flashcard phải giữ ngữ cảnh nguồn để học lại hiệu quả hơn.

### 7.5 Quy tắc về flashcard review

- Nếu người học quên, thẻ có thể lặp lại trong cùng buổi ôn.
- Nếu người học nhớ tốt, lịch SRS phải giãn ra.
- Nếu hết thẻ đến hạn, hệ thống hiển thị trạng thái hoàn thành.

### 7.6 Quy tắc về admin

- Admin có thể sửa dữ liệu quản trị nhưng không được phá lịch sử học đã tạo.
- Scenario cũ đã dùng cho session cũ vẫn phải giữ đúng snapshot.
- Bất kỳ thay đổi content nào cũng phải giữ được tính audit.

### 7.7 Quy tắc về dữ liệu hiển thị

- Các số liệu trên dashboard phải có nguồn thật.
- Không hardcode KPI trong production.
- Empty state và loading state phải rõ ràng.

---

## 8. Luồng chính theo use case

### 8.1 Use case: Learner mở app và bắt đầu học

1. Mở landing page.
2. Đăng ký hoặc đăng nhập.
3. Nếu là user mới thì hoàn tất onboarding.
4. Vào dashboard.
5. Chọn học nói hoặc ôn flashcards.
6. Nếu chọn học nói, vào màn chọn scenario.
7. Chọn role, goal, level, giọng AI.
8. Bắt đầu session.
9. Trò chuyện với AI bằng text hoặc voice.
10. Dịch từ hoặc câu nếu cần.
11. Lưu từ vựng vào flashcard nếu muốn.
12. Nộp bài và xem tổng kết.
13. Sau đó quay lại flashcards để ôn lại.

### 8.2 Use case: Learner ôn flashcards

1. Mở flashcards.
2. Xem thẻ đến hạn.
3. Nghe phát âm hoặc xem nghĩa.
4. Chấm mức độ nhớ.
5. Hệ thống cập nhật lịch SRS.
6. Nếu quên, thẻ có thể xuất hiện lại trong cùng phiên.

### 8.3 Use case: Admin quản lý nội dung

1. Đăng nhập admin.
2. Vào dashboard quản trị.
3. Kiểm tra người dùng và scenario.
4. Cập nhật user khi cần.
5. Tạo hoặc sửa scenario.
6. Bật hoặc ẩn scenario.
7. Sắp xếp thứ tự hiển thị.
8. Giữ dữ liệu ổn định cho learner.

---

## 9. Non-goals cho phiên bản đầu

Để giữ sản phẩm đơn giản và đúng MVP, các nội dung sau không nên đẩy vào bản đầu:

- hội thoại nhiều hơn 2 vai trong cùng một session
- chỉnh prompt thủ công trong runtime
- social feed hoặc cộng đồng chia sẻ bài học
- hệ thống unlock phức tạp theo graph quá nhiều nhánh
- hardcode số liệu dashboard
- quá nhiều loại flashcard trong cùng một lúc

---

## 10. Tiêu chí nghiệm thu nghiệp vụ

Một thiết kế được coi là đạt khi:

- người học mở app, hiểu ngay mình phải làm gì tiếp theo
- user mới được đưa qua onboarding một cách rõ ràng
- learner chọn scenario và có thể swap vai trước khi vào session
- role assignment được khóa sau khi session bắt đầu
- người học có thể dịch từ vựng trong lúc trò chuyện
- người học có thể lưu từ vựng vào flashcard để học lại sau
- kết thúc session có scoring và feedback rõ ràng
- flashcard review có SRS và có trạng thái hoàn thành
- admin quản lý user/scenario mà không phá lịch sử học
- tài liệu này đủ rõ để dev, QA, PO và stakeholder đều hiểu sản phẩm đang làm gì

---

## 11. Kết luận

Lexi là một nền tảng học tiếng Anh bằng AI theo hướng thực hành thực tế, không phải chỉ là một chatbot nói chuyện.

Cốt lõi sản phẩm là:

- chọn đúng tình huống
- chọn đúng vai
- trò chuyện với AI
- hiểu nghĩa ngay khi cần
- lưu lại từ vựng quan trọng
- quay lại ôn bằng flashcard
- admin giữ nội dung sạch và lộ trình đúng

Mô hình tốt nhất cho phiên bản đầu là:

- `scenario.roles[]` là danh sách vai hợp lệ của bối cảnh
- `session` là nơi chốt vai người học và vai AI
- role có thể swap trước khi bắt đầu
- sau khi bắt đầu thì khóa assignment
- flashcard là kết quả của học tập, không phải dữ liệu phụ
- admin quản lý content và người dùng, không can thiệp vào history học
