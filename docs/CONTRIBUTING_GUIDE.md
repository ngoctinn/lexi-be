# CONTRIBUTING GUIDE

## 1. Purpose

Tài liệu này quy định tiêu chuẩn code và cách đóng góp nhằm:

* Đảm bảo code dễ đọc, dễ maintain
* Đồng bộ cách làm trong team
* Giảm lỗi do hiểu sai logic

---

## 2. Nguyên tắc chung

* Code phải **dễ đọc trước, tối ưu sau**
* Ưu tiên **rõ ràng hơn ngắn gọn**
* Tuân thủ **Clean Architecture**
* Mọi thay đổi phải qua **Pull Request (PR)**

---

## 3. Coding Standards

### 3.1 Naming

* Đặt tên rõ nghĩa, không viết tắt

❌ Bad:

```python
tp = p * q
```

✅ Good:

```python
total_price = price * quantity
```

---

### 3.2 Structure

Tuân theo structure:

```
/domain
/application
/infrastructure
/interfaces
```

---

### 3.3 Function

* 1 function = 1 trách nhiệm
* ≤ 30 dòng
* Tránh nested > 3 cấp

---

## 4. Comment Rules (Vietnamese)

### 4.1 Nguyên tắc

* Comment giải thích **TẠI SAO**, không phải **LÀM GÌ**
* Code phải tự rõ ràng → nếu không phải refactor
* Comment ngắn, rõ, đúng

---

### 4.2 Ngôn ngữ

* Dùng **tiếng Việt có dấu**
* Thuật ngữ kỹ thuật giữ nguyên tiếng Anh

Ví dụ:

```python
# Business rule: user chỉ được rút tiền 3 lần/ngày
```

---

### 4.3 Bắt buộc comment khi

* Business rule
* Logic phức tạp
* Workaround / hack
* Edge case

Ví dụ:

```python
# Workaround: API bên thứ 3 luôn trả 200
```

---

### 4.4 Không được comment

❌ Code hiển nhiên

```python
# tăng i lên 1
i += 1
```

❌ Lặp lại tên biến

```python
# danh sách user
users = []
```

❌ Che code xấu

```python
# hàm này hơi rối nhưng đang chạy ổn
```

---

### 4.5 Docstring (BẮT BUỘC)

```python
def create_user(email: str):
    """
    Tạo user mới.

    Rule:
    - Email phải unique
    """
```

---

### 4.6 TODO format

```python
# TODO(TinNN, 2026-04-05): tối ưu query (hiện O(n^2))
```

---

### 4.7 Format

* ≤ 2 dòng / comment
* Không lan man
* Luôn update khi sửa code

---

## 5. Git Commit Convention

Format:

```
type(scope): description
```

Ví dụ:

```
feat(auth): thêm login usecase
fix(user): xử lý email null
refactor(payment): đơn giản hóa logic
```

---

## 6. Pull Request (PR)

### 6.1 Trước khi tạo PR

* Code chạy OK
* Không còn debug code
* Comment đã cập nhật

---

### 6.2 PR cần có

* Mô tả thay đổi
* Lý do thay đổi
* Ảnh hưởng (nếu có)

---

### 6.3 Checklist review

* [ ] Code dễ đọc
* [ ] Naming rõ ràng
* [ ] Comment đúng, không dư
* [ ] Không có comment lỗi thời
* [ ] Business rule được ghi rõ
* [ ] TODO đúng format

---

## 7. Clean Architecture Rules

### Domain

* Không phụ thuộc framework
* Ít comment, tập trung business

### Application

* Bắt buộc có docstring
* Flow rõ ràng

### Infrastructure

* Comment phần tích hợp (API, DB, AWS...)

---

## 8. Forbidden (CẤM)

* Comment từng dòng code
* Comment hiển nhiên
* Comment lỗi thời
* TODO không rõ ràng
* Dùng comment để che code xấu

---

## 9. Summary

> Comment bằng tiếng Việt (có dấu), chỉ giải thích WHY (business rule, logic khó, workaround).
> Code rõ ràng quan trọng hơn comment.

---

## 10. Contact

Trao đổi trực tiếp trong PR hoặc channel team khi có thắc mắc.
