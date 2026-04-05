# Chương 6: The Interface Adapters Layer - Bộ điều hợp giao diện

## 1. Mục tiêu (Learning Objectives)
*   Hiểu vai trò của lớp Interface Adapters như một "bộ phiên dịch" dữ liệu.
*   Phân biệt rõ chức năng của **Controllers**, **Presenters** và **ViewModels**.
*   Cách giữ cho lớp lõi (Core) hoàn toàn độc lập với các công nghệ hiển thị (Web, CLI, Mobile).

---

## 2. Phân tích mã nguồn (Code Analysis)

### Ba thành phần chủ chốt:
1.  **Controllers (`task_controller.py`):**
    - Tiếp nhận dữ liệu thô (vd: từ `input()` hoặc lợp `JSON`).
    - Chuyển đổi dữ liệu thành `RequestDTO`.
    - Gọi thực thi `UseCase`.
2.  **Presenters (`cli.py`):**
    - Nhận `ResponseDTO` từ Use Case.
    - Chứa logic định dạng (formatting) để chuẩn bị dữ liệu cho UI.
    - Trả về một `ViewModel`.
3.  **ViewModels (`task_vm.py`):**
    - Là một cấu trúc dữ liệu thuần túy (POPO - Plain Old Python Object).
    - Chỉ chứa các thông tin cần thiết để hiển thị.

### Flow dữ liệu chuẩn:
`Input (CLI/Web)` -> `Controller` -> `RequestDTO` -> `Use Case` -> `ResponseDTO` -> `Presenter` -> `ViewModel` -> `UI`.

---

## 3. Ghi chú cá nhân (Personal Notes)
*   **Tại sao cần Presenter?** Nếu bạn muốn đổi định dạng ngày từ `2026-04-05` sang `05/04/2026`, bạn chỉ cần sửa ở `Presenter`. Logic nghiệp vụ của bạn vẫn hoàn toàn đứng vững.
*   **Quy tắc ngón tay cái:** Nếu trong Controller có quá 5 dòng logic, hãy xem xét việc đẩy chúng vào Use Case hoặc Presenter.
*   **Tầm quan trọng:** Lớp này bảo vệ hệ thống khỏi những thay đổi của các thư viện UI hoặc Framework Web. Nó biến các chi tiết hạ tầng thành các "Dependency" mà lõi ứng dụng có thể sử dụng mà không cần hiểu rõ chúng.
