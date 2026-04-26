# Quick Start - Turn Analysis Feature

## 🚀 Deploy trong 5 phút

### Bước 1: Build
```bash
sam build
```

### Bước 2: Deploy
```bash
sam deploy --guided
```

Trả lời các câu hỏi:
- Stack Name: `lexi-be` ✅
- AWS Region: `ap-southeast-1` ✅
- Confirm changes: `Y` ✅
- Allow IAM role creation: `Y` ✅
- Save config: `Y` ✅

### Bước 3: Test
```javascript
// Frontend code
ws.send(JSON.stringify({
  action: 'ANALYZE_TURN',
  session_id: 'your-session-id',
  turn_index: 1
}));

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.event === 'TURN_ANALYSIS') {
    console.log(data.analysis.markdown.vi);
  }
};
```

## ✅ Xong!

Hệ thống đã sẵn sàng sử dụng.

## 🎯 Tính năng hoạt động như thế nào?

1. **User nói**: "I go to school yesterday"
2. **User bấm "Analyze"**: Gửi `ANALYZE_TURN` qua WebSocket
3. **AI phân tích**: Tìm lỗi sai, điểm mạnh, cải thiện
4. **Trả về feedback**: Markdown bilingual (Vietnamese + English)
5. **Level-adaptive**: Feedback phù hợp với trình độ A1-C2

## 📚 Docs đầy đủ

- `docs/TURN_ANALYSIS_FEATURE.md` - Chi tiết feature
- `API_DOCUMENTATION.md` - API reference

## ❓ Troubleshooting

### Analysis không hoạt động?
```bash
# Check logs
aws logs tail /aws/lambda/lexi-be-SpeakingWebSocketFunction-xxx --follow
```

## 🎉 Done!

Feature đã sẵn sàng sử dụng!
