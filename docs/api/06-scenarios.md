# Scenarios

## Overview

Danh sách các kịch bản luyện tập speaking. **Public endpoint** - không cần authentication.

## Endpoints

### List Scenarios

**Endpoint**: `GET /scenarios`

**Handler**: `scenarios_handler.py`

**Authentication**: None (Public)

#### Query Parameters

Không có query parameters. API trả về tất cả scenarios active, đã sắp xếp theo `order`.

#### Response (200)

```json
{
  "statusCode": 200,
  "body": {
    "scenarios": [
      {
        "scenario_id": "scn_beginner_01",
        "scenario_title": "Chào hỏi và giới thiệu bản thân",
        "context": "Giao tiếp xã hội",
        "roles": ["Người mới", "Bạn mới quen"],
        "goals": ["Chào hỏi lịch sự", "Giới thiệu tên và quốc tịch", "Hỏi thăm sức khỏe"],
        "difficulty_level": "A1",
        "order": 1,
        "is_active": true,
        "usage_count": 0
      },
      {
        "scenario_id": "scn_beginner_02",
        "scenario_title": "Gọi đồ uống tại quán cà phê",
        "context": "Ẩm thực & Nhà hàng",
        "roles": ["Khách hàng", "Barista"],
        "goals": ["Chọn đồ uống", "Hỏi về size và giá", "Thanh toán đơn giản"],
        "difficulty_level": "A1",
        "order": 2,
        "is_active": true,
        "usage_count": 0
      }
    ],
    "total": 24
  }
}
```

#### Example

```bash
curl -X GET "https://mnjxcw3o1e.execute-api.ap-southeast-1.amazonaws.com/Prod/scenarios"
```

## Scenario Structure

### Fields

- `scenario_id` (string): Unique identifier
- `scenario_title` (string): Tên kịch bản
- `context` (string): Context label (dùng cho icon lookup ở frontend)
- `roles` (array): Đúng 2 vai trong kịch bản
- `goals` (array): Danh sách mục tiêu học tập
- `difficulty_level` (string): CEFR level (`A1`, `A2`, `B1`, `B2`, `C1`, `C2`)
- `order` (number): Thứ tự hiển thị trên lộ trình
- `is_active` (boolean): Kịch bản có đang active không
- `usage_count` (number): Số lần được sử dụng

## Difficulty Levels (CEFR)

- **A1**: Beginner - Cơ bản nhất
- **A2**: Elementary - Sơ cấp
- **B1**: Intermediate - Trung cấp
- **B2**: Upper Intermediate - Trung cấp cao
- **C1**: Advanced - Nâng cao
- **C2**: Proficiency - Thành thạo

## Context Labels

Context được dùng để map với icon ở frontend:
- Giao tiếp xã hội
- Ẩm thực & Nhà hàng
- Đi lại & Hỏi đường
- Đời sống hàng ngày
- Mua sắm
- Du lịch & Khách sạn
- Sức khỏe & Y tế
- Tài chính & Ngân hàng
- Du lịch & Hàng không
- Công việc & Sự nghiệp
- Công sở & Hội họp
- Kinh doanh & Thuyết trình
- Xã hội & Thế giới
- Dịch vụ khách hàng
- Pháp lý & Tư vấn
- Học thuật & Nghiên cứu
- Truyền thông & Báo chí

## Notes

- Endpoint này **không yêu cầu authentication**
- Dùng để hiển thị danh sách scenarios cho user chưa đăng nhập
- Admin có thể quản lý scenarios qua `/admin/scenarios` endpoints
