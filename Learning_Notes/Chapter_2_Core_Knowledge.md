# Chương 2: Nền tảng SOLID trong Python

## 1. Mục tiêu (Learning Objectives)
*   Hiểu rõ 5 nguyên lý SOLID và cách áp dụng chúng trong ngữ cảnh ngôn ngữ Python.
*   Học cách refactor code từ dạng "monolithic" (liền khối) sang dạng module hóa.
*   Nắm vững kỹ thuật lập trình hướng giao diện thông qua Dependency Inversion.

---

## 2. Phân tích mã nguồn (Code Analysis)

### 5 Nguyên lý thực chiến:
1.  **SRP (Đơn nhiệm):** Tách biệt **Thực thể** (vd: `User`) khỏi **Dịch vụ** (vd: `ProfileManager`). Lớp dữ liệu chỉ nên giữ dữ liệu.
2.  **OCP (Đóng/Mở):** Dùng tính đa hình. Khi muốn thêm hình học mới hoặc phương thức thanh toán mới, ta tạo lớp con thay vì sửa hàm `calculate` hiện tại.
3.  **LSP (Thay thế Liskov):** Đảm bảo lớp con tuân thủ logic của lớp cha. Ví dụ: Mọi `PowerSource` đều phải có phương thức `consume` trả về cùng một kiểu dữ liệu.
4.  **ISP (Phân tách Giao diện):** Chia nhỏ các Interface. Một trình phát nhạc (`MusicPlayer`) không cần phải có phương thức `apply_video_filter`.
5.  **DIP (Đảo ngược phụ thuộc):** Thành phần cốt lõi mạnh mẽ nhất. Lớp `UserEntity` phụ thuộc vào `DatabaseInterface` trừu tượng, không phụ thuộc vào `MySQLDatabase` cụ thể.

### Các thành phần quan trọng trong mã mẫu:
*   **`DatabaseInterface`**: "Vỏ bọc" cho mọi loại cơ sở dữ liệu.
*   **`MockDatabase`**: Công cụ tuyệt vời để chạy thử nghiệm (testing) mà không cần hạ tầng phức tạp.

---

## 3. Ghi chú cá nhân (Personal Notes)
*   **Sự khác biệt:** SOLID trong Python linh hoạt hơn Java/C# nhờ Duck Typing, nhưng vẫn cần kỷ luật để không làm mất đi tính cấu trúc.
*   **Mẹo hay:** Khi thấy một lớp có quá nhiều phương thức hoặc hàm `__init__` nhận quá nhiều tham số, đó là dấu hiệu của việc vi phạm SRP.
*   **Tầm quan trọng của DIP:** Đây là xương sống của Clean Architecture. Nếu bạn làm tốt DIP, bạn có thể thay thế Database hoặc Framework mà không cần chạm vào logic nghiệp vụ của ứng dụng.
