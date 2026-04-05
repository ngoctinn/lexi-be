# Chương 5: The Application Layer - Điều phối và các Ca sử dụng

## 1. Mục tiêu (Learning Objectives)
*   Hiểu vai trò của lớp Application trong việc điều phối các Entities.
*   Cách định nghĩa và sử dụng **Ports** (Giao diện ngoại vi) như Repository và Notification Service.
*   Sử dụng **DTOs** để bảo vệ lớp Domain khỏi các tác động bên ngoài.
*   Áp dụng **Result Pattern** để quản lý kết quả thực thi một cách nhất quán.

---

## 2. Phân tích mã nguồn (Code Analysis)

### Quy trình của một Use Case chuẩn:
1.  **Nhận Request:** Sử dụng `RequestDTO` để đảm bảo dữ liệu đầu vào đúng cấu trúc.
2.  **Lấy dữ liệu:** Gọi `Repository.get(id)` để lấy thực thể từ DB.
3.  **Thực thi Domain Logic:** Gọi các phương thức của thực thể (vd: `task.complete()`). *Lưu ý: Logic kiểm tra điều kiện phải nằm ở Thực thể.*
4.  **Lưu trữ:** Gọi `Repository.save(entity)` để cập nhật trạng thái.
5.  **Tương tác ngoại vi:** Gửi thông báo, email hoặc log (thông qua các Ports).
6.  **Trả về kết quả:** Dùng `Result.success` kèm theo `ResponseDTO`.

### Thành phần quan trọng:
*   **`Result` class:** Đóng gói kết quả (Value hoặc Error).
*   **`Repository Interface`:** Bản thiết kế cho các lớp lưu trữ dữ liệu ở vòng tròn ngoài.
*   **`Port Interface`:** Bản thiết kế cho các dịch vụ bên thứ ba (Email, SMS, Cloud).

---

## 3. Ghi chú cá nhân (Personal Notes)
*   **Tránh rò rỉ (Leaking):** Đừng bao giờ trả về nguyên mẫu lợp `Task` (Entity) cho người dùng. Nếu lớp Domain thay đổi cấu trúc, bạn không muốn API của mình cũng bị vỡ theo. Hãy dùng DTO.
*   **Độ mỏng của Use Case:** Nếu thấy Use Case của bạn có quá nhiều câu lệnh `if-else` kiểm tra luật nghiệp vụ, hãy đẩy các logic đó vào lớp Domain (Entities).
*   **Thử nghiệm (Testing):** Lớp Application cực kỳ dễ viết Unit Test vì chúng ta có thể Mock toàn bộ các Ports (Repositories/Services) một cách dễ dàng.
