# Chương 10: Clean Architecture Observability - Giám sát và Kiểm chứng

## 1. Mục tiêu (Learning Objectives)
*   Xây dựng hệ thống Logging và Tracing xuyên suốt các lớp ứng dụng.
*   Hiểu cách sử dụng Middleware để thu thập dữ liệu vận hành.
*   Học cách viết **Architectural Tests** để bảo vệ cấu trúc hệ thống.
*   Đảm bảo khả năng chẩn đoán lỗi nhanh chóng trong môi trường production.

---

## 2. Phân tích mã nguồn (Code Analysis)

### Ba trụ cột quan sát:
1.  **Logging (`logging/config.py`):** Cấu hình định dạng nhật ký tập trung, bao gồm thời gian, mức độ lỗi và Trace ID.
2.  **Tracing (`middleware.py`):** Theo dõi luồng đi của một Request. Giúp bạn trả lời câu hỏi: "Tại sao yêu cầu này lại chậm?" hoặc "Lỗi này xuất phát từ đâu?".
3.  **Verification (`test_source_folders.py`):** Tự động hóa việc kiểm tra:
    - Thư mục `domain` không được chứa các từ khóa như `sqlalchemy`, `flask`, `requests`.
    - Đảm bảo cấu trúc thư mục luôn đúng quy định.

### Architectural Tests:
- Sử dụng `pytest` để quét mã nguồn. 
- Đây là "chốt chặn" cuối cùng để đảm bảo dự án không bị biến thành "Big Ball of Mud" (một đống hỗn độn) theo thời gian.

---

## 3. Ghi chú cá nhân (Personal Notes)
*   **Kiến trúc không tự bảo vệ mình:** Nếu không có các bản kiểm thử kiến trúc, Clean Architecture sẽ dần bị phá vỡ bởi các lập trình viên mới hoặc do áp lực thời gian.
*   **Correlation ID là cứu cánh:** Trong một hệ thống lớn, nếu không có ID này, việc tìm lỗi trong hàng triệu dòng log là nhiệm vụ bất khả thi.
*   **Đầu tư xứng đáng:** Việc viết mã nguồn cho Observability có vẻ tốn thời gian ban đầu, nhưng nó sẽ tiết kiệm cho bạn hàng trăm giờ debug khi hệ thống gặp sự cố thật sự.
