# SOFTWARE REQUIREMENTS SPECIFICATION (SRS)
## LexiLearn — AI-Powered Speaking Practice Platform
**Version**: 2.0 | **Date**: April 2026 | **Status**: Draft

---

## 1. Giới thiệu

### 1.1 Mục đích
Tài liệu này mô tả đầy đủ yêu cầu chức năng, phi chức năng, kiến trúc AWS chi tiết, và luồng xử lý cho nền tảng **LexiLearn** — ứng dụng luyện kỹ năng nói tiếng Anh với AI Partner thời gian thực, tích hợp hệ thống Flashcard cá nhân và Spaced Repetition System (SRS).

### 1.2 Phạm vi
| Layer | Thành phần |
|-------|-----------|
| **Frontend** | Mobile App (React Native) / Web App (Next.js) |
| **Auth** | AWS Cognito User Pool + Identity Pool |
| **API** | AWS API Gateway (REST + WebSocket) |
| **Compute** | AWS Lambda (Python 3.12, SAM) |
| **AI/STT** | Amazon Transcribe (STT) + Amazon Bedrock Claude (LLM) |
| **TTS** | Amazon Polly |
| **Storage** | Amazon DynamoDB + Amazon S3 |
| **Async** | Amazon SQS + Lambda Event Source Mapping |
| **CDN** | Amazon CloudFront |
| **Observability** | Amazon CloudWatch Logs + X-Ray |

### 1.3 Từ điển thuật ngữ
| Thuật ngữ | Định nghĩa |
|-----------|-----------| 
| **Session** | Một buổi hội thoại luyện nói hoàn chỉnh với AI |
| **Turn** | Một lượt nói đơn lẻ trong session (USER hoặc AI) |
| **Scoring** | Kết quả chấm điểm 4 kỹ năng sau khi session kết thúc |
| **Flashcard** | Thẻ từ vựng cá nhân của người dùng, được tạo từ hội thoại |
| **SRS** | Spaced Repetition System — thuật toán ôn tập tối ưu (SM-2) |
| **STT** | Speech-to-Text — Amazon Transcribe |
| **TTS** | Text-to-Speech — Amazon Polly |
| **WordCache** | DynamoDB table chia sẻ toàn user, cache dữ liệu từ điển |
| **ULID** | Universally Unique Lexicographically Sortable Identifier |
| **Cognito UP** | Cognito User Pool — quản lý danh tính người dùng |
| **Cognito IP** | Cognito Identity Pool — cấp IAM credentials tạm thời |

---

## 2. Kiến trúc hệ thống AWS (System Architecture)

### 2.1 Sơ đồ tổng thể

```
┌────────────────────────────────────────────────────────────────────┐
│                     FRONTEND (Client Layer)                        │
│              Mobile App (React Native) / Web App (Next.js)         │
│                                                                    │
│  [Amplify SDK]  ──────►  AWS Cognito (Auth)                        │
│  [REST calls]   ──────►  API Gateway (REST)                        │
│  [WS connect]   ──────►  API Gateway (WebSocket)                   │
│  [Audio/Media]  ──────►  CloudFront → S3 (Pre-signed URL)          │
└─────────┬────────────────────┬───────────────────────┬────────────┘
          │                    │                       │
          ▼                    ▼                       ▼
┌──────────────┐   ┌────────────────────┐   ┌──────────────────────┐
│  Amazon      │   │  AWS API Gateway   │   │  AWS API Gateway     │
│  Cognito     │   │  (REST API)        │   │  (WebSocket API)     │
│              │   │                    │   │                      │
│ ┌──────────┐ │   │ Authorizer:        │   │ Authorizer:          │
│ │User Pool │ │   │ Cognito Authorizer │   │ Lambda Authorizer    │
│ │(UP)      │ │   │                   │   │ (verify JWT từ UP)   │
│ └──────────┘ │   │ Routes:            │   │                      │
│ ┌──────────┐ │   │ /sessions          │   │ Routes:              │
│ │Identity  │ │   │ /flashcards        │   │ $connect             │
│ │Pool (IP) │ │   │ /word/lookup       │   │ $disconnect          │
│ └──────────┘ │   │ /profile           │   │ audio/{sessionId}    │
└──────────────┘   └────────┬───────────┘   └──────────┬───────────┘
                            │                           │
                ┌───────────▼───────────────────────────▼──────────┐
                │              AWS Lambda Functions                  │
                │         (Python 3.12 — SAM Serverless)            │
                │                                                   │
                │  fn_session_handler    fn_ws_conversation_handler │
                │  fn_flashcard_handler  fn_word_lookup_handler     │
                │  fn_profile_handler    fn_scoring_worker          │
                └──┬────────────┬──────────────────┬───────────────┘
                   │            │                  │
       ┌───────────▼──┐  ┌──────▼──────┐  ┌───────▼──────────────┐
       │  Amazon      │  │  Amazon S3  │  │  Amazon SQS          │
       │  DynamoDB    │  │             │  │                      │
       │              │  │  Buckets:   │  │  Queue:              │
       │  Tables:     │  │  lexi-audio │  │  scoring-jobs.fifo   │
       │  - LexiApp   │  │  lexi-dict  │  │                      │
       │  - WordCache │  │             │  │  DLQ:                │
       └──────────────┘  └──────┬──────┘  │  scoring-dlq         │
                                │         └──────────┬───────────┘
                                │                    │ Event Source
                    ┌───────────▼──────┐             │ Mapping
                    │  CloudFront CDN  │  ┌──────────▼───────────┐
                    │  (audio serving) │  │  Lambda              │
                    └──────────────────┘  │  fn_scoring_worker   │
                                          └──────────────────────┘
                                                     │
                ┌────────────────────────────────────▼──────────────┐
                │                AWS AI Services                     │
                │                                                    │
                │  ┌─────────────────┐  ┌───────────────────────┐   │
                │  │ Amazon          │  │ Amazon Bedrock        │   │
                │  │ Transcribe      │  │ Model: Claude 3 Haiku │   │
                │  │ (STT)           │  │ (LLM - hội thoại)     │   │
                │  │                 │  │                       │   │
                │  │ Streaming mode  │  │ Model: Claude 3 Sonnet│   │
                │  │ (real-time)     │  │ (LLM - chấm điểm)    │   │
                │  └─────────────────┘  └───────────────────────┘   │
                │  ┌─────────────────┐                               │
                │  │ Amazon Polly    │  Voices: Joanna, Matthew,    │
                │  │ (TTS)           │  Ivy (SSML neural voices)    │
                │  └─────────────────┘                               │
                └────────────────────────────────────────────────────┘

                ┌────────────────────────────────────────────────────┐
                │           Observability & Operations                │
                │  CloudWatch Logs (Lambda) + X-Ray (tracing)        │
                │  CloudWatch Alarms → SNS → Email notification       │
                └────────────────────────────────────────────────────┘
```

### 2.2 Giải thích từng dịch vụ AWS

| Dịch vụ | Vai trò | Chi tiết cấu hình |
|---------|---------|-------------------|
| **Amazon Cognito User Pool** | Quản lý tài khoản, đăng ký, đăng nhập, MFA | Phát hành JWT (IdToken, AccessToken 15 phút, RefreshToken 30 ngày). Hỗ trợ Email/Password + Google Federated Identity |
| **Amazon Cognito Identity Pool** | Cấp IAM credentials tạm thời cho client | Client dùng IdToken đổi lấy AWS credentials để upload audio trực tiếp lên S3 (không qua Lambda) |
| **AWS API Gateway (REST)** | REST CRUD endpoints | Cognito Authorizer tích hợp native — không cần viết Lambda Authorizer. Verify JWT tự động |
| **AWS API Gateway (WebSocket)** | Real-time conversation channel | Lambda Authorizer để verify JWT từ query string khi kết nối. Routes: `$connect`, `$disconnect`, `audio` |
| **AWS Lambda** | Xử lý business logic | Python 3.12, triển khai bằng AWS SAM. Mỗi Lambda một responsibility |
| **Amazon Transcribe Streaming** | STT real-time | Nhận audio stream PCM 16kHz, trả về transcript real-time qua WebSocket response stream |
| **Amazon Bedrock (Claude 3 Haiku)** | LLM cho hội thoại | Invoke `InvokeModelWithResponseStream` để stream text response. Latency thấp, cost thấp |
| **Amazon Bedrock (Claude 3 Sonnet)** | LLM cho chấm điểm | Dùng cho Scoring Worker — accuracy cao hơn, chạy async nên latency không quan trọng |
| **Amazon Polly** | TTS | Neural Engine. `SynthesizeSpeech` → trả về audio stream MP3 → Lambda ghi lên S3 |
| **Amazon S3** | Lưu trữ audio | Bucket `lexi-audio`: audio hội thoại. Bucket `lexi-dict`: audio phát âm từ điển. CloudFront làm CDN |
| **Amazon DynamoDB** | Database chính | Bảng `LexiApp` (PAY_PER_REQUEST, PITR=true). Bảng `WordCache` (PAY_PER_REQUEST) |
| **Amazon SQS FIFO** | Async scoring queue | Queue `scoring-jobs.fifo` — đảm bảo mỗi session chỉ chấm điểm 1 lần. DLQ lưu failed jobs |
| **Amazon CloudFront** | CDN cho audio | Serve audio từ S3 với signed URL. Cache audio từ điển (từ bucket `lexi-dict`) toàn cầu |
| **Amazon CloudWatch** | Logging & Monitoring | Log Group cho mỗi Lambda. Metric Alarms cho SQS DLQ > 0, Lambda Error rate > 1% |
| **AWS X-Ray** | Distributed tracing | Theo dõi toàn bộ luồng từ API Gateway → Lambda → DynamoDB → Bedrock |

---

## 3. Luồng chi tiết từng tính năng (Detailed Flow)

### 3.1 Luồng Đăng ký / Đăng nhập (AWS Cognito)

```
CLIENT                    COGNITO USER POOL              API GATEWAY
  │                              │                           │
  │─── POST /register ──────────►│                           │
  │    { email, password }       │                           │
  │                              │ SignUp → Send verify email│
  │◄── 200 { userSub } ─────────│                           │
  │                              │                           │
  │─── POST /confirm-email ─────►│                           │
  │    { code }                  │ ConfirmSignUp             │
  │◄── 200 OK ──────────────────│                           │
  │                              │                           │
  │─── POST /login ─────────────►│                           │
  │    { email, password }       │ InitiateAuth              │
  │◄── 200 {                    │                           │
  │    IdToken,                  │                           │
  │    AccessToken,              │                           │
  │    RefreshToken              │                           │
  │    } ────────────────────────│                           │
  │                              │                           │
  │─── GET /sessions ───────────────────────────────────────►│
  │    Header: Authorization: Bearer {IdToken}               │
  │                              │ Cognito Authorizer        │
  │                              │ verifies JWT              │
  │◄── 200 [ sessions ] ─────────────────────────────────────│

Luồng Google OAuth2 (Federated Identity):
  CLIENT → Cognito Hosted UI → Google Login → Redirect với code
  CLIENT → Cognito: exchange code → nhận IdToken/RefreshToken
  (Hoàn toàn managed bởi Cognito, không cần code backend)
```

> **Cognito User Pool ID** được lưu trong `USER_PROFILE.PK = USER#{Cognito sub}`. Cognito `sub` là UUID immutable — dùng làm ID duy nhất của user trong toàn bộ hệ thống.

---

### 3.2 Luồng Hội thoại thời gian thực (WebSocket + Transcribe + Bedrock + Polly)

```
CLIENT          API GW (WS)       Lambda (WS)      Transcribe      Bedrock      Polly        S3 / DynamoDB
  │                 │                  │                │             │            │                │
  │─[CONNECT]──────►│                  │                │             │            │                │
  │ ?token=IdToken  │                  │                │             │            │                │
  │                 │ Lambda Auth      │                │             │            │                │
  │                 │ verify JWT ──────│                │             │            │                │
  │◄[200 Connected]─│                  │                │             │            │                │
  │                 │                  │                │             │            │                │
  │─[START_SESSION]►│─ invoke ────────►│                │             │            │                │
  │ { session_id }  │                  │─ Query TURNs ──────────────────────────────────────────────►│
  │                 │                  │◄──────────────────────────────────────────────────────────── │
  │                 │                  │ Build context  │             │            │                │
  │◄[SESSION_READY]─│◄────────────────│                │             │            │                │
  │                 │                  │                │             │            │                │
  │─[AUDIO_CHUNK]──►│─ invoke ────────►│                │             │            │                │
  │ (PCM bytes)     │                  │─ StartStream──►│             │            │                │
  │─[AUDIO_CHUNK]──►│─────────────────►│─ SendAudio ───►│             │            │                │
  │─[AUDIO_CHUNK]──►│─────────────────►│─ SendAudio ───►│             │            │                │
  │─[AUDIO_END]────►│─────────────────►│                │             │            │                │
  │                 │                  │◄──TranscriptEvent(text, confidence)        │                │
  │                 │                  │                │             │            │                │
  │◄[STT_RESULT]────│◄────────────────│                │             │            │                │
  │ { text, conf }  │                  │                │             │            │                │
  │                 │                  │                │             │            │                │
  │                 │                  │─ PutItem TURN(USER) ──────────────────────────────────────►│
  │                 │                  │─ S3.PutObject(audio) ─────────────────────────────────────►│
  │                 │                  │                │             │            │                │
  │                 │                  │─ InvokeModelStream ─────────►│            │                │
  │                 │                  │  (Haiku + system_prompt      │            │                │
  │                 │                  │   + full TURN history)       │            │                │
  │◄[AI_TEXT_CHUNK]─│◄────── stream ──│◄── text chunk ──│            │            │                │
  │◄[AI_TEXT_CHUNK]─│◄───────────────│◄── text chunk ──│            │            │                │
  │                 │                  │                │             │            │                │
  │                 │                  │ (complete sentence detected) │            │                │
  │                 │                  │─ SynthesizeSpeech ──────────────────────►│                │
  │                 │                  │◄─────────────────────────── MP3 stream ──│                │
  │                 │                  │─ S3.PutObject(ai_audio.mp3)──────────────────────────────►│
  │                 │                  │─ CloudFront.CreateSignedUrl  │            │                │
  │◄[AI_AUDIO_URL]──│◄────────────────│                │             │            │                │
  │ { url, text }   │                  │                │             │            │                │
  │ (play audio)    │                  │                │             │            │                │
  │                 │                  │─ PutItem TURN(AI) ─────────────────────────────────────────►│
  │◄[TURN_SAVED]────│◄────────────────│                │             │            │                │
  │                 │                  │                │             │            │                │
  │  [lặp lại...]  │                  │                │             │            │                │
```

> **Lưu ý quan trọng về audio upload**: Client KHÔNG gửi audio qua WebSocket message (quá chậm, size limit). Thay vào đó:
> 1. Lambda trả về **Pre-signed S3 URL** upload ngay khi session bắt đầu.
> 2. Client upload audio file trực tiếp lên S3 qua Pre-signed URL (bypass Lambda, tốc độ cao nhất).
> 3. Lambda nhận thông báo qua WebSocket message `AUDIO_UPLOADED { s3_key }` rồi mới gọi Transcribe.

---

### 3.3 Luồng Kết thúc phiên và Chấm điểm Async (SQS + Lambda Worker)

```
CLIENT        API GW (REST)    Lambda (Session)      SQS FIFO         Lambda (Scoring Worker)      DynamoDB
  │                │                 │                   │                      │                      │
  │─PATCH /sessions/{id}────────────►│                   │                      │                      │
  │ { status: "COMPLETE" }           │                   │                      │                      │
  │                │                 │─UpdateItem STATUS=PROCESSING_SCORING ──────────────────────────►│
  │                │                 │─ SQS.SendMessage ►│                      │                      │
  │                │                 │  { session_id }   │                      │                      │
  │◄── 200 OK ─────│◄────────────────│                   │                      │                      │
  │ (hiển thị      │                 │                   │                      │                      │
  │  "Đang phân    │                 │                   │                      │                      │
  │   tích...")    │                 │                   │                      │                      │
  │                │                 │                   │─ Event Source ───────►│                      │
  │                │                 │                   │  Mapping trigger      │                      │
  │                │                 │                   │                      │─ Query items PK=SESSION# ►│
  │                │                 │                   │                      │◄──────────────────────────│
  │                │                 │                   │          Filter TURN(USER), build scoring prompt │
  │                │                 │                   │                      │                      │
  │                │                 │                   │                      │─ Bedrock.InvokeModel  │
  │                │                 │                   │          Claude Sonnet│  (scoring prompt)     │
  │                │                 │                   │                      │◄─ JSON scores + text  │
  │                │                 │                   │                      │                      │
  │                │                 │                   │                      │─ PutItem SK=SCORING ──►│
  │                │                 │                   │                      │─ UpdateItem STATUS=COMPLETED ►│
  │                │                 │                   │                      │─ UpdateItem total_sessions++ ►│
  │                │                 │                   │                      │                      │
  │─ GET /sessions/{id} ────────────────────────────────────────────────────────────────────────────   │
  │ (Client polling hoặc WebSocket notification)         │                      │                      │
  │◄── 200 { status: COMPLETED, scoring: {...} } ────────────────────────────────────────────────────  │

SQS FIFO đảm bảo:
  - MessageGroupId = session_id → mỗi session chỉ được xử lý 1 message
  - Nếu Lambda Worker fail → SQS retry 3 lần với exponential backoff
  - Sau 3 lần fail → Message vào Dead Letter Queue (DLQ)
  - CloudWatch Alarm: DLQ ApproximateNumberOfMessagesVisible > 0 → SNS Alert
```

---

### 3.4 Luồng Tra từ và Lưu Flashcard (DynamoDB Cache + Polly)

```
CLIENT          API GW (REST)       Lambda (WordLookup)       DynamoDB (WordCache)    Polly     S3
  │                  │                      │                         │                 │        │
  │─POST /word/lookup►                      │                         │                 │        │
  │ { word: "scalable" }                    │                         │                 │        │
  │                  │─ invoke ────────────►│                         │                 │        │
  │                  │                      │─ normalize(lower) ─────►│                 │        │
  │                  │                      │  GetItem(WORD#scalable) │                 │        │
  │                  │                      │                         │                 │        │
  │          ┌── CACHE HIT? ───────────────────────────────────────────────────────────────────┐│
  │          │ YES                           │◄── item (word data) ────│                 │        │
  │          │                              │─ IncrementHitCount ─────►│                 │        │
  │          │◄── 200 { word data } ────────│                         │                 │        │
  │          │                              │                         │                 │        │
  │          │ NO (Cache Miss)              │                         │                 │        │
  │          │                              │─ call Oxford API ────────────────────────────────  │
  │          │                              │◄─ { definition, phonetic, type }                   │
  │          │                              │─ Polly.SynthesizeSpeech ─────────────────►│        │
  │          │                              │◄───────────────────────────── MP3 stream ─│        │
  │          │                              │─ S3.PutObject(dict/scalable.mp3) ─────────────────►│
  │          │                              │─ PutItem(WordCache) ────►│                 │        │
  │          │                              │  TTL = now + 60 days     │                 │        │
  │          │◄── 200 { word data } ────────│                         │                 │        │
  │          └────────────────────────────────────────────────────────────────────────────────── │
  │                  │                      │                         │                 │        │
  │ [User bấm "Lưu Flashcard"]             │                         │                 │        │
  │─POST /flashcards ►                      │                         │                 │        │
  │ { word, session_id, example_sentence }  │                         │                 │        │
  │                  │─ invoke Lambda (Flashcard handler)             │                 │        │
  │                  │  1. Check duplicate: Query PK=USER#id,        │                 │        │
  │                  │     filter_expr word=scalable                  │                 │        │
  │                  │  2. PutItem FLASHCARD#[ULID]                   │                 │        │
  │                  │     copy audio_s3_key from WordCache lookup     │                 │        │
  │                  │  3. UpdateItem SESSION new_words_count += 1     │                 │        │
  │◄── 200 { flashcard_id } ────────────────────────────────────────────────────────────────── │
```

---

### 3.5 Luồng Ôn tập Flashcard SRS (GSI2 + SM-2)

```
CLIENT             API GW (REST)        Lambda (Flashcard)       DynamoDB GSI2
  │                     │                      │                      │
  │─GET /flashcards/review                     │                      │
  │ ?date=2024-03-25 ──►│─ invoke ────────────►│                      │
  │                     │                      │─ Query GSI2 ────────►│
  │                     │                      │  GSI2PK=USER#id       │
  │                     │                      │  GSI2SK <= today      │
  │                     │                      │◄─── [ cards due ] ────│
  │◄── 200 [ cards ] ───│◄────────────────────│                      │
  │                     │                      │                      │
  │ [User đánh giá: "Khó" = quality 2]        │                      │
  │─PATCH /flashcards/{id}/review ────────────►│                      │
  │ { quality: 2 }      │                      │                      │
  │                     │                      │ SM-2 Algorithm:      │
  │                     │                      │ EF = max(1.3, EF +   │
  │                     │                      │  0.1 - (5-2)*(0.08   │
  │                     │                      │  + (5-2)*0.02))       │
  │                     │                      │ interval_days = 1     │
  │                     │                      │ next_review_at += 1d  │
  │                     │                      │                      │
  │                     │                      │─ UpdateItem ────────►│
  │                     │                      │  easiness_factor      │
  │                     │                      │  interval_days        │
  │                     │                      │  next_review_at       │
  │                     │                      │  review_count += 1    │
  │◄── 200 { next_review_at } ─────────────────│                      │
```

---

## 4. Chi tiết Lambda Functions

| Lambda Function | Trigger | Mô tả | AWS Services gọi |
|-----------------|---------|-------|-------------------|
| `fn_session_handler` | API GW REST `/sessions` | CRUD session metadata | DynamoDB |
| `fn_profile_handler` | API GW REST `/profile` | CRUD user profile | DynamoDB |
| `fn_ws_auth_handler` | API GW WS `$connect` | Verify JWT từ query param | Cognito JWKS endpoint |
| `fn_ws_conversation_handler` | API GW WS `audio` route | Core conversation loop: STT → Bedrock → Polly | Transcribe, Bedrock, Polly, S3, DynamoDB |
| `fn_word_lookup_handler` | API GW REST `POST /word/lookup` | Cache-aside từ điển | DynamoDB (WordCache), Polly, S3, Oxford API |
| `fn_flashcard_handler` | API GW REST `/flashcards` | CRUD + duplicate check | DynamoDB |
| `fn_scoring_worker` | SQS Event Source Mapping | Async scoring sau session | DynamoDB, Bedrock (Sonnet) |
| `fn_presigned_url_handler` | API GW REST `POST /upload-url` | Cấp S3 Pre-signed URL upload | S3 |

---

## 5. Yêu cầu chức năng (Functional Requirements)

### UC01 — Xác thực người dùng (AWS Cognito)

| ID | Yêu cầu |
|----|---------|
| FR-01.1 | Người dùng đăng ký bằng Email + Password qua Cognito User Pool `SignUp` API |
| FR-01.2 | Cognito gửi email xác minh; người dùng `ConfirmSignUp` với OTP |
| FR-01.3 | Người dùng đăng nhập bằng Google OAuth2 qua Cognito Hosted UI + Federated Identity |
| FR-01.4 | Thành công: Cognito cấp `IdToken` (15 phút), `RefreshToken` (30 ngày) |
| FR-01.5 | `IdToken` chứa `sub` (Cognito UUID) — dùng làm `user_id` xuyên suốt hệ thống |
| FR-01.6 | API Gateway REST dùng **Cognito Authorizer** (native, không cần code) để verify JWT |
| FR-01.7 | API Gateway WebSocket dùng **Lambda Authorizer** verify JWT từ `?token=` query string |
| FR-01.8 | Sau đăng ký thành công, Lambda trigger `PostConfirmation` tự động tạo `USER_PROFILE` trong DynamoDB |

---

### UC02 — Thiết lập phiên học (Session Setup)

| ID | Yêu cầu |
|----|---------|
| FR-02.1 | Người dùng chọn một mẫu **Kịch bản** (scenario) từ danh sách do Admin tạo sẵn, hoặc thiết lập tự do tự động. Hệ thống ghi lại: `scenario`, `my_character`, `ai_character`, `ai_gender`. |
| FR-02.2 | Người dùng chọn **Trình độ** (level): `A1`, `A2`, `B1`, `B2`, `C1`, `C2` |
| FR-02.4 | Lambda tạo SESSION item vào DynamoDB (`PutItem PK=SESSION#[ULID], SK=METADATA`) |
| FR-02.5 | Session ID là ULID — tự sắp xếp thời gian không cần index phụ |
| FR-02.6 | System prompt được build động theo `scenario`, `my_character`, `ai_character`, và `level` — không hardcode |
| FR-02.7 | Lambda gọi Bedrock Claude Haiku để sinh lời chào mở đầu (Turn#00001, speaker=AI) |
| FR-02.8 | Polly tổng hợp lời chào thành audio MP3 → lưu S3 → trả Pre-signed URL cho client |
| FR-02.9 | Khi client kết nối WebSocket (`$connect`), Lambda cập nhật `connection_id` vào SESSION item |
| FR-02.10 | Khi client ngắt kết nối (`$disconnect`), Lambda xóa `connection_id` khỏi SESSION item |

---

### UC03 — Thực hiện hội thoại (Conversation Loop)

| ID | Yêu cầu |
|----|---------|
| FR-03.1 | Client ghi âm PCM 16kHz, nhận Pre-signed S3 URL và upload trực tiếp lên S3 |
| FR-03.2 | Client gửi `AUDIO_UPLOADED { s3_key }` qua WebSocket; Lambda trigger Amazon Transcribe |
| FR-03.3 | Transcribe Streaming nhận dạng âm thanh, trả `transcript` + `confidence` trong < 2 giây |
| FR-03.4 | Nếu `confidence < 0.85`, client nhận `STT_LOW_CONFIDENCE` và được hỏi thu âm lại |
| FR-03.5 | Lambda `PutItem` TURN(USER) vào DynamoDB (async, không block response) |
| FR-03.6 | Lambda gọi Bedrock Claude Haiku với `InvokeModelWithResponseStream` |
| FR-03.7 | Text stream từng chunk được forward qua WebSocket `AI_TEXT_CHUNK` events |
| FR-03.8 | Khi phát hiện câu hoàn chỉnh (dấu `.`, `?`, `!`), Lambda gọi Polly `SynthesizeSpeech` |
| FR-03.9 | Audio MP3 lưu S3 → tạo CloudFront Signed URL → gửi `AI_AUDIO_URL` cho client |
| FR-03.10 | Lambda `PutItem` TURN(AI) vào DynamoDB sau khi audio đã upload xong |
| FR-03.11 | Khi người dùng nhấn "Dịch", nội dung tương ứng sẽ được lưu vào thuộc tính `translated_content` trong `TURN` item để tránh dịch lại lần sau. |

---

### UC04 — Hint & Skip

| ID | Yêu cầu |
|----|---------|
| FR-04.1 | Client gửi WebSocket event `USE_HINT { session_id }` |
| FR-04.2 | Lambda gọi Bedrock để sinh câu gợi ý phù hợp với ngữ cảnh + level |
| FR-04.3 | Khi user nói sau khi dùng hint, TURN được ghi với `is_hint_used=true` |
| FR-04.4 | `hint_used_count` trong SESSION tăng 1 bằng DynamoDB Atomic Counter (`ADD 1`) |
| FR-04.5 | Client gửi `SKIP_TURN { session_id }` → Lambda ghi TURN rỗng `is_skipped=true` |
| FR-04.6 | `skip_used_count` tăng 1 bằng Atomic Counter |

---

### UC05 — Pause & Resume

| ID | Yêu cầu |
|----|---------|
| FR-05.1 | App lifecycle event (background/close) → Client gửi REST `PATCH /sessions/{id} { status: PAUSED }` |
| FR-05.2 | Lambda `UpdateItem` status=PAUSED, last_active_at=NOW |
| FR-05.3 | Danh sách session lấy từ GSI1 (`USER#id#SESSION`), sort by `GSI1SK` desc |
| FR-05.4 | "Học tiếp": Client kết nối WebSocket mới → gửi `START_SESSION { session_id }` |
| FR-05.5 | Lambda `Query` tất cả TURN của session → build conversation history → inject vào Bedrock prompt |

---

### UC06 — Kết thúc & Chấm điểm Async

| ID | Yêu cầu |
|----|---------|
| FR-06.1 | Client gửi `PATCH /sessions/{id} { status: COMPLETE }` |
| FR-06.2 | Lambda cập nhật `status=PROCESSING_SCORING`, gửi message vào **SQS FIFO Queue** `scoring-jobs` |
| FR-06.3 | Lambda trả 200 ngay, client hiển thị "Đang phân tích kết quả..." |
| FR-06.4 | SQS trigger `fn_scoring_worker`: Query tất cả TURNs, build scoring prompt |
| FR-06.5 | Bedrock Claude 3 Sonnet chấm điểm 4 kỹ năng (0–100): Fluency, Pronunciation, Grammar, Vocabulary |
| FR-06.6 | `is_hint_used=true` trên TURN → trừ điểm Fluency; `is_skipped=true` → trừ nặng hơn |
| FR-06.7 | Worker `PutItem SK=SCORING`, `UpdateItem status=COMPLETED`, tăng `total_sessions` user |
| FR-06.8 | Client nhận notification qua WebSocket hoặc polling `GET /sessions/{id}` |

---

### UC07 — Tra từ tức thì

| ID | Yêu cầu |
|----|---------|
| FR-07.1 | Client tap vào từ → `POST /word/lookup { word }` với JWT header |
| FR-07.2 | Lambda normalize lowercase, `GetItem` từ DynamoDB **WordCache** |
| FR-07.3 | **Cache Hit** (< 100ms): tăng `hit_count`, trả data ngay |
| FR-07.4 | **Cache Miss**: gọi Oxford Dictionaries API (external) |
| FR-07.5 | Gọi **Amazon Polly** `SynthesizeSpeech` → lưu MP3 lên **S3 bucket `lexi-dict`** |
| FR-07.6 | `PutItem` vào WordCache với `TTL = now + 60 days` |
| FR-07.7 | Trả response JSON: `{ word, phonetic, word_type, definition_vi, audio_url, example }` |

---

### UC08 — Lưu Flashcard

| ID | Yêu cầu |
|----|---------|
| FR-08.1 | Client gửi `POST /flashcards { word, session_id, example_sentence }` |
| FR-08.2 | Lambda kiểm tra trùng lặp: `Query PK=USER#id` filter `word=X` (tránh tạo card trùng) |
| FR-08.3 | Tạo item `PK=USER#id, SK=FLASHCARD#[ULID]` với đầy đủ data từ WordCache |
| FR-08.4 | Copy `audio_s3_key` từ WordCache vào Flashcard để phát âm không phụ thuộc cache |
| FR-08.5 | Khởi tạo SRS: `easiness_factor=2.5`, `interval_days=1`, `next_review_at=tomorrow` |
| FR-08.6 | `UpdateItem SESSION new_words_count += 1` (Atomic Counter) |
| FR-08.7 | Toàn bộ thao tác < 200ms — không block UI |

---

### UC09 — Ôn tập Flashcard (SRS)

| ID | Yêu cầu |
|----|---------|
| FR-09.1 | `GET /flashcards/review` → Lambda query **GSI2**: `GSI2PK=USER#id`, `GSI2SK <= today` |
| FR-09.2 | Ôn tập: User đánh giá Dễ/Ổn/Khó/Không nhớ (quality 5/3/2/0) |
| FR-09.3 | Lambda tính SM-2: cập nhật `easiness_factor`, `interval_days`, `next_review_at` |
| FR-09.4 | `PATCH /flashcards/{id}/review { quality }` → `UpdateItem` 4 SRS fields |
| FR-09.5 | Audio phát âm được phục vụ qua **CloudFront** từ S3 `lexi-dict` bucket |

---

### UC10 — Quản lý phiên

| ID | Yêu cầu |
|----|---------|
| FR-10.1 | `GET /sessions` → Query **GSI1** `USER#id#SESSION`, sort desc theo `GSI1SK` |
| FR-10.2 | `GET /sessions/{id}` → Query base table `PK=SESSION#{id}`, trả toàn bộ TURNs + SCORING |
| FR-10.3 | `DELETE /sessions/{id}` → `BatchWriteItem` xóa tất cả items trong Item Collection |
| FR-10.4 | Audio trên S3 bị xóa thông qua **S3 Lifecycle Rule** sau 90 ngày (không xóa thủ công) |
| FR-10.5 | Dashboard call **REST API** để lấy progress theo tuần qua `Query GSI1` với range condition |

---

### UC11 — Quản lý Tình huống mẫu (Admin)

| ID | Yêu cầu |
|----|---------|
| FR-11.1 | Admin (có `role="ADMIN"`) có quyền CRUD tình huống mẫu thông qua `/admin/scenarios`. |
| FR-11.2 | Lambda tạo/Update item vào DynamoDB `PK=SYSTEM#SCENARIOS`, `SK=SCENARIO#[ULID]`. |
| FR-11.3 | Users gọi `GET /scenarios` để lấy danh sách các kịch bản đang `is_active=true` (`Query` base table). |
| FR-11.4 | Khi session kết thúc, worker cập nhật `usage_count += 1` cho Scenario tương tự (phục vụ thống kê kịch bản hot). |

---

### UC12 — Quản lý Người dùng (Admin)

| ID | Yêu cầu |
|----|---------|
| FR-12.1 | Admin lấy danh sách User qua `GET /admin/users` (Gọi Lambda, Lambda Query GSI3 `GSI3PK=USER_PROFILE` + Pagination). |
| FR-12.2 | Admin có thể Block/Unblock học viên: `PATCH /admin/users/{id} { is_active: false }`. |
| FR-12.3 | Lambda update DynamoDB `USER_PROFILE` và đồng thời gọi API Cognito `AdminDisableUser` để chặn login. |
| FR-12.4 | Hệ thống Cognito Authorizer tự động từ chối AccessToken của User bị chặn, API Gateway trả HTTP 401. |

---

## 6. Yêu cầu phi chức năng (Non-Functional Requirements)

### 6.1 Hiệu năng (Performance)

| ID | Yêu cầu | SLA |
|----|---------|-----|
| NFR-P01 | STT (Transcribe Streaming) phản hồi | < 2 giây |
| NFR-P02 | Tra từ Cache Hit (DynamoDB GetItem) | < 100 ms |
| NFR-P03 | Tra từ Cache Miss (Oxford + Polly + S3) | < 3 giây |
| NFR-P04 | Lưu Flashcard | < 200 ms |
| NFR-P05 | AI first token (Bedrock Haiku stream) | < 1.5 giây |
| NFR-P06 | Serving audio (CloudFront CDN) | < 50 ms (cached) |

### 6.2 Bảo mật (Security)

| ID | Yêu cầu |
|----|---------|
| NFR-SEC01 | Tất cả REST API: **Cognito Authorizer** native trên API Gateway — không cần Lambda |
| NFR-SEC02 | WebSocket `$connect`: **Lambda Authorizer** verify JWT từ `?token=` query param |
| NFR-SEC03 | S3 audio: chỉ serve qua **CloudFront Signed URL** hoặc **S3 Pre-signed URL** (15 phút TTL) |
| NFR-SEC04 | IAM Role cho mỗi Lambda: **Least Privilege** — chỉ access đúng table và đúng bucket |
| NFR-SEC05 | DynamoDB `SSEEnabled=true` (AWS managed key) cho bảng `LexiApp` |
| NFR-SEC06 | Cognito User Pool: bật **MFA optional**, **Password policy** (min 8 ký tự, mix) |
| NFR-SEC07 | Cognito `PostConfirmation` Lambda trigger phải verify event source từ đúng User Pool ARN |
| NFR-SEC08 | VPC không cần thiết cho Lambda (DynamoDB, S3, Cognito đều có VPC Endpoint nếu cần) |

### 6.3 Khả năng mở rộng (Scalability)

| ID | Yêu cầu |
|----|---------|
| NFR-S01 | DynamoDB `PAY_PER_REQUEST` — tự scale, không cần capacity planning |
| NFR-S02 | Lambda auto-scale theo concurrent invocations (mặc định 1000/region) |
| NFR-S03 | SQS FIFO Queue scale tự động — không bottleneck scoring worker |
| NFR-S04 | WordCache có thể thêm **DAX Cluster** khi `hit_count` trên popular words cực cao |
| NFR-S05 | CloudFront serve audio dictionary toàn cầu với < 50ms latency |

### 6.4 Độ tin cậy (Reliability)

| ID | Yêu cầu |
|----|---------|
| NFR-R01 | SQS FIFO retry 3 lần (exponential backoff) trước khi vào **DLQ** |
| NFR-R02 | **CloudWatch Alarm** báo động khi DLQ > 0 → **SNS** gửi email developer |
| NFR-R03 | DynamoDB `PointInTimeRecovery=true` cho bảng `LexiApp` |
| NFR-R04 | Lambda **Reserved Concurrency** = 10 cho `fn_scoring_worker` — tránh throttle |
| NFR-R05 | Transcribe session timeout sau 60 giây không nhận audio → auto-close |

---

## 7. Data Model Summary

### 7.1 Access Patterns

| # | Use Case | Op | Index | Key Pattern |
|---|----------|----|-------|-------------|
| 1 | Lấy profile user | GetItem | Base | `PK=USER#id, SK=PROFILE` |
| 2 | Tạo session | PutItem | Base | `PK=SESSION#[ULID], SK=METADATA` |
| 3 | Lấy toàn bộ session data | Query | Base | `PK=SESSION#id` |
| 4 | Danh sách sessions của user | Query | GSI1 | `GSI1PK=USER#id#SESSION, sort desc` |
| 5 | Ghi 1 TURN | PutItem | Base | `PK=SESSION#id, SK=TURN#00001` |
| 6 | Ghi kết quả scoring | PutItem | Base | `PK=SESSION#id, SK=SCORING` |
| 7 | Danh sách flashcard mới nhất | Query | Base | `PK=USER#id, begins_with(SK, FLASHCARD#)` |
| 8 | Cards đến hạn ôn tập | Query | GSI2 | `GSI2PK=USER#id, GSI2SK <= today` |
| 9 | Tra từ (cache lookup) | GetItem | WordCache | `PK=WORD#word, SK=METADATA` |
| 10 | Tăng counter session | UpdateItem | Base | ADD `hint_used_count`, `new_words_count` |

### 7.2 Session State Machine

```
  SETUP ──► ACTIVE ◄────────────────────┐
              │                          │
              │ (user thoát app)         │ (bấm "Học tiếp")
              ▼                          │
            PAUSED ─────────────────────┘
              │
              │ (bấm "Kết thúc")
              ▼
      PROCESSING_SCORING  ← SQS Worker đang xử lý
              │
              │ (Worker ghi SCORING item xong)
              ▼
          COMPLETED  ← Final state
```

### 7.3 Thuật toán SM-2 (Spaced Repetition)

```python
# quality: 0=Không nhớ, 2=Khó, 3=Ổn, 5=Dễ
def update_srs(card, quality: int):
    if quality < 3:
        card.interval_days = 1
        card.review_count = 0       # reset — học lại từ đầu
    else:
        if card.review_count == 0:   card.interval_days = 1
        elif card.review_count == 1: card.interval_days = 6
        else: card.interval_days = round(card.interval_days * card.easiness_factor)
        card.review_count += 1

    card.easiness_factor = max(1.3,
        card.easiness_factor + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
    )
    card.next_review_at = datetime.utcnow() + timedelta(days=card.interval_days)
    # next_review_at được ghi vào GSI2SK → enable SRS query
```

---

## 8. API Endpoints

### 8.1 REST API (qua API Gateway + Cognito Authorizer)

| Method | Endpoint | Lambda | Mô tả |
|--------|----------|--------|-------|
| `GET` | `/profile` | fn_profile_handler | Lấy user profile |
| `PUT` | `/profile` | fn_profile_handler | Cập nhật profile (level) |
| `POST` | `/sessions` | fn_session_handler | Tạo session mới |
| `GET` | `/sessions` | fn_session_handler | Danh sách sessions |
| `GET` | `/sessions/{id}` | fn_session_handler | Chi tiết session + turns |
| `PATCH` | `/sessions/{id}` | fn_session_handler | Cập nhật status |
| `DELETE` | `/sessions/{id}` | fn_session_handler | Xóa session |
| `POST` | `/upload-url` | fn_presigned_url_handler | Lấy S3 Pre-signed URL để upload audio |
| `POST` | `/word/lookup` | fn_word_lookup_handler | Tra từ (cache-aside) |
| `GET` | `/flashcards` | fn_flashcard_handler | Danh sách flashcards |
| `POST` | `/flashcards` | fn_flashcard_handler | Tạo flashcard |
| `GET` | `/flashcards/review` | fn_flashcard_handler | Cards đến hạn ôn tập |
| `PATCH` | `/flashcards/{id}/review` | fn_flashcard_handler | Cập nhật kết quả ôn (SM-2) |
| `DELETE` | `/flashcards/{id}` | fn_flashcard_handler | Xóa flashcard |

### 8.2 WebSocket API (qua API Gateway + Lambda Authorizer)

| Route | Lambda | Payload | Mô tả |
|-------|--------|---------|-------|
| `$connect` | fn_ws_auth_handler | `?token=IdToken` | Verify JWT, lưu connectionId |
| `$disconnect` | fn_ws_conversation_handler | — | Cleanup, auto-pause session |
| `audio` | fn_ws_conversation_handler | `{ action, session_id, s3_key? }` | Core conversation route |

**WebSocket Client → Server events:**

| Action | Payload | Mô tả |
|--------|---------|-------|
| `START_SESSION` | `{ session_id }` | Bắt đầu / tiếp tục session |
| `AUDIO_UPLOADED` | `{ session_id, s3_key }` | Thông báo audio upload xong |
| `USE_HINT` | `{ session_id }` | Yêu cầu gợi ý |
| `SKIP_TURN` | `{ session_id }` | Bỏ qua lượt |
| `END_SESSION` | `{ session_id }` | Kết thúc phiên |

**WebSocket Server → Client events:**

| Event | Payload | Mô tả |
|-------|---------|-------|
| `SESSION_READY` | `{ upload_url }` | S3 Pre-signed URL để upload audio |
| `STT_RESULT` | `{ text, confidence }` | Kết quả nhận dạng giọng nói |
| `STT_LOW_CONFIDENCE` | `{ confidence }` | Cảnh báo âm thanh không rõ |
| `AI_TEXT_CHUNK` | `{ chunk, done }` | Stream text từ AI |
| `AI_AUDIO_URL` | `{ url, text }` | CloudFront URL phát audio AI |
| `TURN_SAVED` | `{ turn_index }` | Xác nhận turn đã lưu DB |
| `HINT_TEXT` | `{ hint }` | Câu gợi ý từ AI |
| `SCORING_COMPLETE` | `{ session_id }` | Chấm điểm xong (push từ server) |

---

## 9. Phụ lục

### 9.1 Mapping Nghiệp vụ ↔ DynamoDB ↔ AWS Service

| Nghiệp vụ | DynamoDB Item | AWS Service xử lý |
|-----------|--------------|-------------------|
| Đăng ký / Đăng nhập | `USER#id / PROFILE` (auto-create) | Cognito User Pool + Lambda Trigger |
| Tạo phiên học | `SESSION#[ULID] / METADATA` | API GW + Lambda + DynamoDB |
| Nói & nhận dạng | `SESSION#id / TURN#NNNNN` | Transcribe + S3 + DynamoDB |
| AI phản hồi | `SESSION#id / TURN#NNNNN` | Bedrock Claude Haiku + Polly + S3 |
| Chấm điểm | `SESSION#id / SCORING` | SQS + Lambda + Bedrock Sonnet |
| Tra từ | `WORD#word / METADATA` (WordCache) | Oxford API + Polly + S3 + CloudFront |
| Lưu Flashcard | `USER#id / FLASHCARD#[ULID]` | API GW + Lambda + DynamoDB |
| Ôn tập SRS | `USER#id / FLASHCARD#[ULID]` (GSI2) | API GW + Lambda + CloudFront |

### 9.2 S3 Bucket Structure

```
lexi-audio/                    ← Bucket audio hội thoại (Lifecycle: delete 90 ngày)
  sessions/
    {session_ulid}/
      turn_00001_ai.mp3
      turn_00002_user.mp3
      ...

lexi-dict/                     ← Bucket audio từ điển (Lifecycle: move to IA sau 90 ngày, KHÔNG xóa)
  dictionary/
    en/
      scalable.mp3
      passionate.mp3
      ...
```

### 9.3 CloudWatch Alarms Configuration

| Alarm | Metric | Threshold | Action |
|-------|--------|-----------|--------|
| ScoringDLQNotEmpty | `SQS ApproximateNumberOfMessagesVisible` (DLQ) | > 0 | SNS Email |
| LambdaHighErrorRate | `Lambda Errors` (fn_scoring_worker) | > 2 / 5 phút | SNS Email |
| TranscribeLatencyHigh | Custom metric từ Lambda | p95 > 3000ms | SNS Email |
| DynamoDBThrottled | `DynamoDB ThrottledRequests` | > 10 / phút | SNS Email |
