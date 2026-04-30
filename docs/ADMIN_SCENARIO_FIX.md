# Admin Scenario Update Fix

## Vấn đề
Khi ẩn/bật kịch bản trong giao diện admin, API trả về lỗi "Internal server error" (500/502).

## Nguyên nhân
Có 2 vấn đề chính:

### 1. DynamoDB Reserved Keyword Error
**Lỗi**: `ValidationException: Invalid UpdateExpression: Attribute name is a reserved keyword; reserved keyword: roles`

**Nguyên nhân**: Trong `dynamo_scenario_repo.py`, method `update()` sử dụng `roles` trực tiếp trong UpdateExpression mà không dùng `ExpressionAttributeNames`. `roles` là reserved keyword trong DynamoDB.

**Code lỗi**:
```python
UpdateExpression=(
    "SET scenario_title = :st, context = :ctx, roles = :r, goals = :g, ..."
),
ExpressionAttributeNames={"#ord": "order"},  # Chỉ có order
```

**Giải pháp**: Thêm `roles` vào `ExpressionAttributeNames`:
```python
UpdateExpression=(
    "SET scenario_title = :st, context = :ctx, #r = :roles, goals = :g, ..."
),
ExpressionAttributeNames={
    "#r": "roles",      # roles là reserved word
    "#ord": "order",    # order là reserved word
},
ExpressionAttributeValues={
    ":roles": scenario.roles,  # Đổi từ :r thành :roles
    ...
}
```

### 2. Lambda Timeout Quá Ngắn
**Lỗi**: Lambda function timeout sau 3 giây (default timeout)

**Nguyên nhân**: Không có `Timeout` được cấu hình trong `template.yaml`, nên Lambda sử dụng default timeout 3 giây. Với cold start + DynamoDB query, 3 giây không đủ.

**Giải pháp**: Thêm `Timeout: 30` vào cả `CreateAdminScenarioFunction` và `UpdateAdminScenarioFunction` trong `template.yaml`:
```yaml
UpdateAdminScenarioFunction:
  Type: AWS::Serverless::Function
  Properties:
    CodeUri: src/
    Handler: infrastructure.handlers.admin.update_admin_scenario_handler.handler
    Runtime: python3.12
    Timeout: 30  # Thêm dòng này
    Environment:
      Variables:
        LEXI_TABLE_NAME:
          Fn::ImportValue: !Sub "${DatabaseStackName}-LexiAppTableName"
```

## Files đã sửa
1. `lexi-be/src/infrastructure/persistence/dynamo_scenario_repo.py`
   - Sửa method `update()` để handle reserved keyword `roles`

2. `lexi-be/template.yaml`
   - Thêm `Timeout: 30` cho `CreateAdminScenarioFunction`
   - Thêm `Timeout: 30` cho `UpdateAdminScenarioFunction`

## Deployment
```bash
cd lexi-be
sam build --use-container
sam deploy --stack-name lexi-be --region ap-southeast-1 --no-confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```

## Verification
Test ẩn kịch bản:
```bash
curl -X PATCH "https://mnjxcw3o1e.execute-api.ap-southeast-1.amazonaws.com/Prod/admin/scenarios/a1-greeting-introduction" \
  -H "Authorization: <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'
```

Kết quả mong đợi:
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "scenario_id": "a1-greeting-introduction",
    "is_active": false,
    ...
  }
}
```

## Status
✅ **FIXED** - Đã deploy thành công lúc 2026-04-30 21:13 (UTC+7)

## Related Issues
- Admin CRUD endpoints đã được test và hoạt động đúng
- GET /admin/users - ✅ Working
- GET /admin/scenarios - ✅ Working  
- POST /admin/scenarios - ✅ Working (sau khi fix timeout)
- PATCH /admin/scenarios/{id} - ✅ Working (sau khi fix reserved keyword + timeout)
