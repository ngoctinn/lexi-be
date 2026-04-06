# Chương 1: Kiến thức Cốt lõi về Clean Architecture

## 1. Mục tiêu (Learning Objectives)
*   Hiểu bản chất của sự trừu tượng hóa (Abstraction) trong lập trình hướng đối tượng.
*   Nắm vững sự khác biệt giữa **Nominal Typing** (ABC) và **Structural Typing** (Protocol).
*   Thực hành nguyên lý **Dependency Injection** (Tiêm phụ thuộc) để tăng tính linh hoạt của mã nguồn.

---

## 2. Phân tích mã nguồn (Code Analysis)

### Các thành phần chính:
*   **Interface (Bản hợp đồng):** 
    - `Notifier (ABC)`: Yêu cầu kế thừa rõ ràng.
    - `Notifier (Protocol)`: Kiểm tra kiểu cấu trúc tại thời điểm kiểm tra tĩnh (Mypy).
*   **Concrete Implementations (Triển khai cụ thể):** 
    - `EmailNotifier` và `SMSNotifier`: Chứa logic gửi thực tế.
*   **Orchestrator (Điều phối):** 
    - `NotificationService`: Không quan tâm mình đang gửi bằng gì, chỉ gọi phương thức `send_notification`.

### So sánh ABC vs Protocol:
1.  **ABC:** Chắc chắn và ràng buộc. Phải dùng `from abc import ABC`.
2.  **Protocol:** Hiện đại và linh hoạt. Giảm sự phụ thuộc chéo (coupling) vì các lớp triển khai không cần biết gì về `Notifier`.

---

## 3. Ghi chú cá nhân (Personal Notes)
*   **Lợi ích lớn nhất:** Việc thay đổi phương thức gửi thông báo từ Email sang một dịch vụ khác (vd: Zalo) sẽ không làm ảnh hưởng đến mã nguồn của lớp `NotificationService`.
*   **Nhắc nhở:** Luôn ưu tiên dùng `Protocol` nếu bạn muốn giữ cho các module hoàn toàn độc lập với nhau.
*   **Kiểm thử:** Khi viết Unit Test, ta có thể dễ dàng tạo một lớp `MockNotifier` để kiểm tra lớp `NotificationService` mà không cần thực sự gửi email hay tin nhắn nào.
