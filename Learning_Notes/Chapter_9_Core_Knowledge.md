# Chương 9: Adding Web UI - Tính linh hoạt của giao diện

## 1. Mục tiêu (Learning Objectives)
*   Chứng minh khả năng đa giao diện của Clean Architecture.
*   Tích hợp ứng dụng với các Web Framework (Flask, FastAPI) mà không làm ô nhiễm lớp lõi.
*   Học cách xây dựng Web Controllers và Presenters cho HTML/JSON.
*   Xây dựng hệ thống Template (View) dựa trên ViewModels.

---

## 2. Phân tích mã nguồn (Code Analysis)

### Quy trình Web-to-Core:
1.  **Request:** Trình duyệt gửi HTTP Request (Form data/JSON).
2.  **Route Handler (Infrastructure):** Trích xuất dữ liệu, chuyển thành `RequestDTO`.
3.  **Controller (Interface Adapter):** Gọi Use Case thực thi.
4.  **Presenter (Interface Adapter):** Nhận kết quả, định dạng thành `WebViewModel` (kèm các thông tin cho UI như CSS classes).
5.  **View (Templates):** Render dữ liệu từ `ViewModel` ra giao diện người dùng.

### Các thành phần mới:
*   **Web Adapters:** Các file định nghĩa routes.
*   **Templates:** Các file HTML (Jinja2) chỉ dùng để hiển thị dữ liệu thuần túy.

---

## 3. Ghi chú cá nhân (Personal Notes)
*   **Web chỉ là một chi tiết:** Đừng bao giờ `import flask` hay `import fastapi` vào trong thư mục `domain` hay `application`.
*   **Tái sử dụng:** Toàn bộ code bạn viết từ chương 1 đến chương 5 được giữ nguyên 100% khi bạn thêm giao diện Web. Đây chính là giá trị lớn nhất của kiến trúc sạch.
*   **Trải nghiệm người dùng:** Nhờ có lớp `Presenter`, bạn có thể dễ dàng tùy biến thông điệp lỗi hoặc định dạng ngày tháng riêng cho bản Web mà không làm ảnh hưởng đến bản CLI của ứng dụng.
