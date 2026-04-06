# Chương 12: Your Clean Architecture Journey - Hành trình tiếp theo

## 1. Mục tiêu (Learning Objectives)
*   Học cách áp dụng Clean Architecture một cách linh hoạt và thực tế (Pragmatism).
*   Thực hành ghi chép các quyết định kiến trúc qua **ADR**.
*   Mở rộng hệ thống với mô hình **Event-Driven**.
*   Định hướng phát triển từ Monolith sang Microservices dựa trên nền tảng đã học.

---

## 2. Phân tích mã nguồn (Code Analysis)

### Kỹ thuật nâng cao:
1.  **FastAPI Integration:** Tận dụng sức mạnh của Pydantic cho việc validation ở lớp ngoài cùng (Frameworks) và chuyển đổi sang các DTO nội bộ trước khi đi vào lớp lõi.
2.  **Domain Events:** Thực thể phát đi sự kiện khi trạng thái thay đổi. Use Case điều phối việc phát tán sự kiện này thông qua một giao diện `EventPublisher` trừu tượng.
3.  **Hồ sơ ADR:** Công cụ quản trị dự án giúp duy trì tính thống nhất về mặt kỹ thuật giữa các thành viên.

### Các thành phần chính trong ADR:
- **Context:** Tại sao chúng ta cần đưa ra quyết định này?
- **Decision:** Quyết định cuối cùng là gì? (vd: Chấp nhận dùng Pydantic ở domain).
- **Consequences:** Chúng ta được gì và mất gì (Trade-offs).

---

## 3. Ghi chú cá nhân (Personal Notes)
*   **Lời khuyên cuối cùng:** Một kiến trúc hoàn hảo không phải là kiến trúc không bao giờ thay đổi, mà là kiến trúc chịu được sự thay đổi với chi phí thấp nhất.
*   **Tầm quan trọng của ADR:** File ADR chính là file "di chúc kỹ thuật" quý giá nhất cho những người sẽ tiếp quản code của bạn sau này.
*   **Kết thúc là khởi đầu:** Bạn đã có bản đồ trong tay. Hãy bắt đầu xây dựng những ứng dụng Python mạnh mẽ, dễ bảo trì và trường tồn với thời gian!
