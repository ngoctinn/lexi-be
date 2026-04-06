# Chương 8: Testing Patterns - Kiểm thử trong Clean Architecture

## 1. Mục tiêu (Learning Objectives)
*   Hiểu tại sao Clean Architecture lại giúp việc kiểm thử trở nên dễ dàng.
*   Phân biệt các loại kiểm thử: Unit, Integration và Use Case testing.
*   Thành thạo kỹ thuật sử dụng **Mocks** và **Stubs** trong Python.
*   Học cách viết test case tập trung vào hành vi thay vì chi tiết triển khai.

---

## 2. Phân tích mã nguồn (Code Analysis)

### Chiến lược kiểm thử theo từng lớp:
1.  **Domain Layer (Unit Test):** 
    - Vì không có phụ thuộc (dependency), ta chỉ cần khởi tạo đối tượng và kiểm tra kết quả.
    - Ví dụ: `task.complete()` thì `status` phải là `DONE`.
2.  **Application Layer (Use Case Test):**
    - Sử dụng `Mock` cho Repositories.
    - Kiểm tra xem Use Case có gọi đúng các hàm lưu trữ và thông báo hay không.
3.  **Infrastructure Layer (Integration Test):**
    - Kiểm thử với Database thật hoặc File thật để đảm bảo logic lưu trữ chính xác.

### Kỹ thuật nâng cao:
*   **`unittest.mock`:** Dùng để thay thế các thành phần ngoại vi.
*   **`pytest.mark.parametrize`:** Chạy một kiểm thử với nhiều kịch bản (vd: tạo task bình thường, tạo task không tiêu đề, tạo task quá hạn).

---

## 3. Ghi chú cá nhân (Personal Notes)
*   **Quy tắc 1-1:** Mỗi Use Case nên có ít nhất một bộ test case tương ứng che phủ các trường hợp Thành công và Thất bại.
*   **Lợi ích kinh tế:** Nếu bạn phải mất 5 phút để chạy test vì nó cần Database, lập trình viên sẽ lười chạy test. Nếu test chạy trong 0.5 giây (nhờ Clean Arch), họ sẽ chạy nó sau mỗi dòng code -> Chất lượng phần mềm tăng vọt.
*   **Refactoring:** Nhờ có bộ test tốt, bạn có thể tự tin thay đổi cấu trúc mã nguồn (Refactor) mà không sợ làm hỏng các tính năng hiện có.
