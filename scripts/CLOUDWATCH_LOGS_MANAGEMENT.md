# CloudWatch Logs Management

Scripts để quản lý CloudWatch Log Groups cho Lambda functions.

## 📋 Tổng quan

Khi deploy SAM/CloudFormation nhiều lần, AWS tạo Lambda functions mới với tên khác nhau, dẫn đến:
- **Nhiều log groups cũ** không còn sử dụng
- **Chi phí lưu trữ** tăng theo thời gian
- **Khó theo dõi logs** do quá nhiều log groups

## 🛠 Scripts

### 1. cleanup_cloudwatch_logs.sh

Xóa log groups cũ và giữ lại log groups của Lambda functions đang active.

**Dry-run (kiểm tra trước khi xóa):**
```bash
./scripts/cleanup_cloudwatch_logs.sh --dry-run
```

**Thực thi xóa:**
```bash
./scripts/cleanup_cloudwatch_logs.sh
```

**Output:**
```
📋 Step 1: Getting active Lambda functions...
✅ Found 19 active Lambda functions

📋 Step 2: Getting all CloudWatch Log Groups...
✅ Found 47 log groups

📋 Step 3: Identifying log groups to delete...
✅ Log groups to keep: 19
⚠️  Log groups to delete: 28

⚠️  WARNING: This will permanently delete 28 log groups!
Continue? (yes/no): yes

🗑️  Step 4: Deleting old log groups...
✅ Cleanup complete!
   - Deleted: 28
   - Failed: 0
   - Kept: 19
```

---

### 2. set_log_retention.sh

Thiết lập retention policy tự động xóa logs cũ sau N ngày.

**Dry-run:**
```bash
./scripts/set_log_retention.sh --days 7 --dry-run
```

**Thiết lập retention 7 ngày:**
```bash
./scripts/set_log_retention.sh --days 7
```

**Thiết lập retention 30 ngày:**
```bash
./scripts/set_log_retention.sh --days 30
```

**Valid retention days:**
- 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1096, 1827, 2192, 2557, 2922, 3288, 3653

**Output:**
```
📋 Setting retention policy to 7 days for all lexi-be log groups...

📋 Step 1: Getting all CloudWatch Log Groups...
✅ Found 19 log groups

🔧 Step 2: Setting retention policy...
✅ Retention policy update complete!
   - Success: 19
   - Failed: 0
   - Retention: 7 days
```

---

### 3. monitor_lambda_logs.sh

Monitor logs của Lambda functions.

**Liệt kê tất cả functions có activity trong 1 giờ qua:**
```bash
./scripts/monitor_lambda_logs.sh
```

**Monitor logs của function cụ thể:**
```bash
./scripts/monitor_lambda_logs.sh --function lexi-be-SpeakingWebSocketFunction-81umaiNrJbfa
```

**Tail logs real-time:**
```bash
./scripts/monitor_lambda_logs.sh --function lexi-be-SpeakingWebSocketFunction-81umaiNrJbfa --tail
```

**Chỉ hiển thị errors:**
```bash
./scripts/monitor_lambda_logs.sh --errors-only
```

**Output:**
```
📋 Lambda Functions with Recent Activity (last 1 hour)...

✅ lexi-be-SpeakingWebSocketFunction-81umaiNrJbfa
   Last activity: 2026-04-27 10:25:52

✅ lexi-be-SpeakingSessionFunction-DMj2qTyWTsDP
   Last activity: 2026-04-27 10:20:15

💡 To monitor a specific function:
   ./scripts/monitor_lambda_logs.sh --function FUNCTION_NAME --tail
```

---

## 📊 Workflow khuyến nghị

### Lần đầu setup:

1. **Cleanup log groups cũ:**
   ```bash
   # Kiểm tra trước
   ./scripts/cleanup_cloudwatch_logs.sh --dry-run
   
   # Xóa
   ./scripts/cleanup_cloudwatch_logs.sh
   ```

2. **Thiết lập retention policy:**
   ```bash
   # Development: 7 days
   ./scripts/set_log_retention.sh --days 7
   
   # Production: 30 days
   ./scripts/set_log_retention.sh --days 30
   ```

### Hàng tuần:

```bash
# Cleanup log groups cũ sau mỗi lần deploy
./scripts/cleanup_cloudwatch_logs.sh
```

### Debug:

```bash
# Monitor logs real-time
./scripts/monitor_lambda_logs.sh --function FUNCTION_NAME --tail

# Xem errors gần đây
./scripts/monitor_lambda_logs.sh --errors-only
```

---

## 💰 Chi phí

**Trước cleanup:**
- 47 log groups × ~10 MB/group = ~470 MB
- Chi phí: ~$0.024/month (at $0.05/GB)

**Sau cleanup:**
- 19 log groups × ~10 MB/group = ~190 MB
- Chi phí: ~$0.010/month (at $0.05/GB)
- **Tiết kiệm: ~60%**

**Với retention policy 7 days:**
- Logs tự động xóa sau 7 ngày
- Chi phí giảm ~70-80% so với không có retention

---

## ⚠️ Lưu ý

1. **Backup logs quan trọng** trước khi cleanup
2. **Test với --dry-run** trước khi thực thi
3. **Retention policy** không thể undo - logs bị xóa vĩnh viễn
4. **Production environment** nên dùng retention 30-90 days
5. **Development environment** có thể dùng retention 7 days

---

## 🔗 AWS Documentation

- [CloudWatch Logs Pricing](https://aws.amazon.com/cloudwatch/pricing/)
- [Log Retention](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Working-with-log-groups-and-streams.html#SettingLogRetention)
- [Lambda Logging](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs.html)
