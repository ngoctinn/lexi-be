# Chương 3: Type-Enhanced Python - Tăng cường sức mạnh cho Clean Architecture

## 1. Mục tiêu (Learning Objectives)
*   Hiểu lợi ích của Type Hinting trong việc phát triển hệ thống lớn.
*   Nắm vững cách xử lý linh hoạt các kiểu dữ liệu với `Union` và `Optional`.
*   Áp dụng `NewType` để bảo vệ Domain Logic khỏi lỗi logic về kiểu.
*   Sử dụng công cụ `Mypy` để tự động hóa việc kiểm tra mã nguồn.

---

## 2. Phân tích mã nguồn (Code Analysis)

### Các kỹ thuật quan trọng:
1.  **Chú thích kiểu cơ bản:** 
    - Định nghĩa rõ `parameter: type` và `-> return_type`.
2.  **Kỹ thuật nâng cao với `typing`:**
    - `Union`: Xử lý giá trị đa kiểu.
    - `Optional`: Xử lý giá trị có thể là `None` (ngăn chặn lỗi logic phổ biến nhất).
3.  **Domain Integrity với `NewType`:**
    - Giúp phân biệt các giá trị như `UserId(1)` và `ProductId(1)`. Dù cùng là số 1, nhưng chúng không thể thay thế cho nhau trong mã nguồn.

### Cấu hình công cụ (Mypy):
*   Sử dụng file `.ini` để cá nhân hóa luật kiểm tra.
*   Các cờ quan trọng: `strict_optional`, `warn_unused_ignores`, `warn_unreachable`.

---

## 3. Ghi chú cá nhân (Personal Notes)
*   **Thay đổi tư duy:** Type hinting trong Python không làm code chạy nhanh hơn về mặt vật lý, nhưng làm cho **lập trình viên chạy nhanh hơn** vì ít phải debug lỗi runtime.
*   **Điểm lưu ý:** `NewType` là một "virtual type", nó không tồn tại ở runtime (không tốn tài nguyên), nó chỉ phục vụ cho việc kiểm tra mã nguồn (static checking).
*   **Ứng dụng:** Trình IDE (như VS Code/PyCharm) sẽ dựa vào các thông tin này để gợi ý code (IntelliSense) chuẩn xác 100%.
