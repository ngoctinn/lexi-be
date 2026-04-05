# Chương 11: Legacy to Clean - Từ mã nguồn cũ sang Kiến trúc sạch

## 1. Mục tiêu (Learning Objectives)
*   Nhận diện các dấu hiệu của mã nguồn "bẩn" (Legacy Code).
*   Áp dụng mô hình **Strangler Fig** để chuyển đổi hệ thống một cách an toàn.
*   Kỹ thuật tách biệt logic nghiệp vụ khỏi các API và Database cũ.
*   Xây dựng lộ trình Refactoring mà không làm gián đoạn vận hành.

---

## 2. Phân tích mã nguồn (Code Analysis)

### Các bước chuyển đổi:
1.  **Giai đoạn 1 (Bao bọc):** Tạo các Interface cho các truy cập Database hiện có. Chuyển logic từ hàm xử lý Web sang Repository.
2.  **Giai đoạn 2 (Trích xuất):** Tìm các luật nghiệp vụ (vd: tính thuế, kiểm tra điều kiện giảm giá) và đưa về lớp Domain.
3.  **Giai đoạn 3 (Sắp xếp):** Tổ chức lại thư mục theo cấu trúc Clean Architecture: `domain`, `application`, `infrastructure`.

### Ví dụ điển hình (`EcomApp`):
- Từ một file `app.py` duy nhất chứa 500 dòng code.
- Chuyển thành cấu trúc đa lớp giúp việc thêm phương thức thanh toán mới (vd: từ Stripe sang PayPal) trở nên cực kỳ đơn giản.

---

## 3. Ghi chú cá nhân (Personal Notes)
*   **An toàn là trên hết:** Luôn giữ phiên bản cũ chạy song song cho đến khi phiên bản "sạch" đã vượt qua 100% các bản kiểm thử.
*   **Tư duy thực tế:** Không phải lúc nào cũng cần làm sạch 100% mã nguồn ngay lập tức. Hãy ưu tiên làm sạch những phần thường xuyên phải sửa đổi hoặc hay xảy ra lỗi.
*   **Phần thưởng:** Sau khi hoàn thành, dự án từ một "nỗi sợ hãi" của lập trình viên sẽ trở thành một hệ thống dễ hiểu, dễ mở rộng và cực kỳ tự tin khi triển khai.
