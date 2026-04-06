# Chương 4: Domain-Driven Design (DDD) - Trái tim của ứng dụng

## 1. Mục tiêu (Learning Objectives)
*   Hiểu vị trí và vai trò của lớp Domain trong Clean Architecture (vòng tròn trung tâm).
*   Phân biệt được giữa **Entities** và **Value Objects**.
*   Học cách đóng gói logic nghiệp vụ (Business Rules) vào bên trong các Entity.
*   Sử dụng Factory Pattern để kiểm soát việc khởi tạo đối tượng phức tạp.

---

## 2. Phân tích mã nguồn (Code Analysis)

### Thành phần cốt lõi:
1.  **Entities (`task.py`):**
    - Là đối tượng có `ID`.
    - Chứa các phương thức hành vi: `start()`, `complete()`.
    - Có logic kiểm tra trạng thái: `if self.status != TaskStatus.TODO: raise ValueError(...)`.
2.  **Value Objects (`value_objects.py`):**
    - Không có định danh riêng, so sánh bằng giá trị.
    - Ví dụ: `Deadline` (chứa logic kiểm tra ngày quá hạn `is_overdue`), `Priority` (Enum).
3.  **Factories (`task_factory.py`):**
    - Đảm nhận việc khởi tạo đối tượng đảm bảo tất cả các ràng buộc nghiệp vụ được thỏa mãn ngay từ đầu.

### Kỹ thuật lập trình:
*   Sử dụng `@dataclass` với `field(init=False)` để bảo vệ các thuộc tính quan trọng (không cho phép gán bừa bãi lúc khởi tạo).
*   Dùng `Optional` và `NewType` từ chương 3 để tăng độ an toàn cho mã nguồn.

---

## 3. Ghi chú cá nhân (Personal Notes)
*   **Sai lầm phổ biến:** Nhiều người coi Entity chỉ là nơi chứa dữ liệu (Anemic Model), dẫn đến việc Logic nghiệp vụ bị văng ra khắp nơi. Clean Architecture khuyến khích "Fat Entities" (Thực thể giàu hành vi).
*   **Tính độc lập:** Mã nguồn ở đây là "tinh khiết" nhất. Nó có thể được copy sang một dự án dùng Django, Flask hay thậm chí là script chạy console mà không cần sửa đổi gì.
*   **Validation:** Đừng để các lớp ở ngoài kiểm tra dữ liệu, hãy để chính thực thể tự bảo vệ mình (`self-validating entities`).
