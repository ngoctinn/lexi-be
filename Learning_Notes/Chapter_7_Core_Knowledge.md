# Chương 7: Frameworks and Drivers - Hạ tầng và các chi tiết kỹ thuật

## 1. Mục tiêu (Learning Objectives)
*   Hiểu vai trò của lớp ngoài cùng (Infrastructure) trong Clean Architecture.
*   Cách triển khai thực tế cho các Interface (Ports) đã định nghĩa ở lớp lõi.
*   Kỹ thuật **Bootstrapping** để kết nối toàn bộ hệ thống.
*   Quản lý cấu hình và Dependency Injection chuyên nghiệp.

---

## 2. Phân tích mã nguồn (Code Analysis)

### Các thành phần hạ tầng:
1.  **Persistence (`file.py`, `memory.py`):**
    - Thực thi logic lưu trữ thực tế (đọc/ghi file, truy vấn DB).
    - Đây là nơi chứa các thư viện như `SQLAlchemy`, `PyMongo`, v.v.
2.  **External Services (`sendgrid.py`):**
    - Chứa mã nguồn để gọi API bên thứ ba.
    - Chuyển đổi lỗi của thư viện bên ngoài thành các Exception mà lớp Domain có thể hiểu.
3.  **UI Frameworks (`click_cli_app.py`):**
    - Sử dụng các thư viện UI (vd: `FastAPI`, `Click`) để nhận đầu vào từ thế giới thực.

### Dependency Injection (DI) Container:
- Sử dụng một "Container" trung tâm để khai báo các mối quan hệ (vd: `NotificationPort` -> `SendGridNotifier`).
- Giúp ứng dụng linh hoạt: Đổi từ `MemoryRepository` sang `PostgresRepository` chỉ bằng 1 dòng cấu hình.

---

## 3. Ghi chú cá nhân (Personal Notes)
*   **Quy tắc vàng:** Hạ tầng (Infrastructure) phụ thuộc vào Lõi (Core), chứ Lõi không bao giờ được phụ thuộc vào Hạ tầng.
*   **Trái ngọt:** Nhờ tách biệt này, bạn có thể viết Unit Test cực nhanh với `MemoryRepository` mà không cần setup Database thật phức tạp.
*   **Sự linh hoạt:** Nếu ngày mai SendGrid tăng giá, bạn chỉ cần viết một lớp `AwsSesNotifier` và đổi cấu hình trong Container. Toàn bộ logic gửi thông báo của hệ thống vẫn giữ nguyên.
