# 📚 Lexi Backend - Complete Documentation Index

**Mục đích**: Hướng dẫn toàn bộ hệ thống hội thoại cho Frontend team

---

## 📖 Tài Liệu Chính

### 1. 🏗️ [CONVERSATION_ARCHITECTURE.md](./CONVERSATION_ARCHITECTURE.md) - **START HERE**
**Dành cho**: Architects, Tech Leads, Senior Developers  
**Nội dung**:
- Tổng quan kiến trúc hệ thống
- Clean Architecture pattern
- Luồng hội thoại chi tiết (5 phases)
- API endpoints đầy đủ
- Data models (Session, Turn, Scenario)
- Real-time streaming (WebSocket)
- Error handling
- Metrics & performance
- Performance targets

**Thời gian đọc**: 30-45 phút  
**Khi nào dùng**: Hiểu toàn bộ hệ thống trước khi code

---

### 2. ⚡ [FRONTEND_QUICK_START.md](./FRONTEND_QUICK_START.md) - **FOR DEVELOPERS**
**Dành cho**: Frontend developers, React/Vue developers  
**Nội dung**:
- 5 bước workflow chính
- Code examples (TypeScript/JavaScript)
- UI components cần thiết
- Audio handling
- Error handling patterns
- State management (React hooks)
- Local testing guide
- Implementation checklist

**Thời gian đọc**: 15-20 phút  
**Khi nào dùng**: Bắt đầu implement feature

---

### 3. 📊 [API_RESPONSE_EXAMPLES.md](./API_RESPONSE_EXAMPLES.md) - **REFERENCE**
**Dành cho**: Frontend developers, QA, API testers  
**Nội dung**:
- Response format standard
- Tất cả endpoint examples
- Success responses (201, 200)
- Error responses (400, 401, 404, 500)
- Data type reference
- Typical session flow
- Notes for frontend

**Thời gian đọc**: 10-15 phút (reference)  
**Khi nào dùng**: Khi implement API calls, debugging

---

## 🔗 Tài Liệu Bổ Sung

### Existing Documentation
- [VERIFICATION_REPORT.md](./VERIFICATION_REPORT.md) - Issues fixed, test results
- [BEDROCK_STREAMING_FIX.md](./BEDROCK_STREAMING_FIX.md) - Bedrock streaming implementation
- [README.md](./README.md) - Project overview

---

## 🎯 Quick Navigation by Role

### 👨‍💼 Product Manager
1. Read: CONVERSATION_ARCHITECTURE.md (Overview section)
2. Understand: Luồng hội thoại chi tiết
3. Reference: Performance targets

### 🏗️ Tech Lead / Architect
1. Read: CONVERSATION_ARCHITECTURE.md (Complete)
2. Review: Clean Architecture pattern
3. Check: Error handling & metrics

### 💻 Frontend Developer
1. Read: FRONTEND_QUICK_START.md (Complete)
2. Reference: API_RESPONSE_EXAMPLES.md
3. Implement: 5-step workflow
4. Test: Local testing guide

### 🧪 QA / Tester
1. Read: FRONTEND_QUICK_START.md (Testing section)
2. Reference: API_RESPONSE_EXAMPLES.md
3. Use: Local testing guide
4. Check: Error handling scenarios

### 🔧 Backend Developer
1. Read: CONVERSATION_ARCHITECTURE.md (Architecture section)
2. Review: Data models
3. Check: Error handling
4. Monitor: Metrics & performance

---

## 📋 Implementation Checklist

### Phase 1: Setup
- [ ] Read CONVERSATION_ARCHITECTURE.md
- [ ] Read FRONTEND_QUICK_START.md
- [ ] Setup local backend (SAM)
- [ ] Test API endpoints locally

### Phase 2: Core Features
- [ ] Implement scenario selector
- [ ] Implement session creation
- [ ] Implement turn submission loop
- [ ] Display conversation history
- [ ] Play AI audio

### Phase 3: Advanced Features
- [ ] Record user audio (optional)
- [ ] Show metrics (TTFT, latency, cost)
- [ ] Implement session completion
- [ ] Show scoring results
- [ ] Error handling

### Phase 4: Polish
- [ ] Test with real backend
- [ ] Performance optimization
- [ ] Accessibility review
- [ ] Mobile responsiveness

---

## 🔄 Typical Development Flow

```
1. Read CONVERSATION_ARCHITECTURE.md
   ↓
2. Read FRONTEND_QUICK_START.md
   ↓
3. Setup local backend
   ↓
4. Implement scenario selector
   ↓
5. Implement session creation
   ↓
6. Implement turn submission loop
   ↓
7. Reference API_RESPONSE_EXAMPLES.md for details
   ↓
8. Test locally
   ↓
9. Deploy to staging
   ↓
10. Test with real backend
```

---

## 🚀 Key Concepts

### Session
- Phiên hội thoại giữa user và AI
- Có status: ACTIVE, COMPLETED, PAUSED
- Chứa danh sách turns (user + AI)
- Lưu metrics (TTFT, latency, cost)

### Turn
- Một lượt thoại (user hoặc AI)
- Turn index: 0, 1, 2, 3, ... (sequential)
- User turns: index chẵn (0, 2, 4, ...)
- AI turns: index lẻ (1, 3, 5, ...)

### Scenario
- Kịch bản hội thoại mẫu
- Có 2 roles (learner + AI)
- Có learning goals
- Có difficulty level (A1-C2)

### Metrics
- TTFT: Time to first token (ms)
- Latency: Total response time (ms)
- Tokens: Input/output token count
- Cost: USD per turn

---

## 📞 Support & Questions

### Common Questions

**Q: Làm sao để test locally?**  
A: Xem FRONTEND_QUICK_START.md → Testing Locally section

**Q: API response format là gì?**  
A: Xem API_RESPONSE_EXAMPLES.md → Response Format Standard

**Q: Làm sao handle errors?**  
A: Xem FRONTEND_QUICK_START.md → Error Handling section

**Q: Metrics là gì?**  
A: Xem CONVERSATION_ARCHITECTURE.md → Metrics & Performance section

**Q: Bedrock streaming hoạt động như thế nào?**  
A: Xem CONVERSATION_ARCHITECTURE.md → Real-time Streaming section

---

## 📊 Documentation Statistics

| Document | Size | Read Time | Type |
|----------|------|-----------|------|
| CONVERSATION_ARCHITECTURE.md | 27 KB | 30-45 min | Architecture |
| FRONTEND_QUICK_START.md | 11 KB | 15-20 min | Guide |
| API_RESPONSE_EXAMPLES.md | 13 KB | 10-15 min | Reference |
| **Total** | **51 KB** | **55-80 min** | - |

---

## 🔐 Important Notes

1. **Authentication**: Tất cả endpoints yêu cầu JWT token
2. **Fallback**: Nếu Bedrock fail, backend trả về mock response
3. **Metrics**: Chỉ có trên AI turns, không có trên user turns
4. **Audio URLs**: S3 presigned URLs, valid 1 hour
5. **Decimal Fields**: Trả về dưới dạng string, parse khi cần

---

## 🎓 Learning Path

### Beginner (0-2 hours)
1. Read FRONTEND_QUICK_START.md
2. Understand 5-step workflow
3. Setup local backend
4. Test basic endpoints

### Intermediate (2-4 hours)
1. Read CONVERSATION_ARCHITECTURE.md
2. Understand data models
3. Implement core features
4. Reference API_RESPONSE_EXAMPLES.md

### Advanced (4+ hours)
1. Implement advanced features
2. Optimize performance
3. Handle edge cases
4. Deploy to production

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-25 | Initial documentation |

---

## 🔗 Related Links

- [AWS Bedrock Docs](https://docs.aws.amazon.com/bedrock/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [REST API Best Practices](https://restfulapi.net/)
- [WebSocket Guide](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)

---

## 📧 Contact

**Backend Team**: backend@lexi.com  
**Frontend Team**: frontend@lexi.com  
**Questions**: Slack #lexi-dev

---

**Last Updated**: 2026-04-25  
**Maintained By**: Backend Team  
**Status**: ✅ Complete & Ready for Development
