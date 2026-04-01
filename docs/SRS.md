# SOFTWARE REQUIREMENTS SPECIFICATION (SRS)
## LexiLearn — AI-Powered Speaking Practice Platform
**Version**: 3.0 | **Date**: April 2026 | **Status**: Draft

---

## 1. Giới thiệu

### 1.1 Mục đích
Tài liệu này mô tả đầy đủ yêu cầu chức năng, phi chức năng, kiến trúc AWS chi tiết, luồng xử lý, và **kiến trúc phần mềm Clean Architecture** cho nền tảng **LexiLearn** — ứng dụng luyện kỹ năng nói tiếng Anh với AI Partner thời gian thực, tích hợp hệ thống Flashcard cá nhân và Spaced Repetition System (SRS).

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
| **Entity** | Domain object thuần túy, không phụ thuộc framework nào |
| **Use Case** | Application logic điều phối nghiệp vụ cụ thể |
| **Port** | Interface (abstract class) tại ranh giới Use Case ↔ Infrastructure |
| **Adapter** | Cài đặt cụ thể của Port (DynamoDB, Bedrock, S3, ...) |

---

## 2. Kiến trúc phần mềm — Clean Architecture

> **Nguyên tắc vàng**: Sự phụ thuộc chỉ hướng vào trong. Infrastructure phụ thuộc vào Domain — không bao giờ ngược lại.

### 2.1 Sơ đồ vòng tròn đồng tâm

```
╔══════════════════════════════════════════════════════════════╗
║  LAYER 4: FRAMEWORKS & DRIVERS (Infrastructure)              ║
║  ┌──────────────────────────────────────────────────────┐   ║
║  │  LAYER 3: INTERFACE ADAPTERS                         │   ║
║  │  ┌────────────────────────────────────────────────┐  │   ║
║  │  │  LAYER 2: APPLICATION (Use Cases + Ports)      │  │   ║
║  │  │  ┌──────────────────────────────────────────┐  │  │   ║
║  │  │  │  LAYER 1: DOMAIN (Entities)              │  │  │   ║
║  │  │  │  UserProfile, Session, Turn, FlashCard   │  │  │   ║
║  │  │  │  Scoring, Scenario                       │  │  │   ║
║  │  │  └──────────────────────────────────────────┘  │  │   ║
║  │  │  Use Cases: CreateSession, ConversationLoop... │  │   ║
║  │  │  Ports: ISessionRepo, IBedrockPort, ...        │  │   ║
║  │  └────────────────────────────────────────────────┘  │   ║
║  │  Controllers (Lambda Handlers), Presenters, DTOs      │   ║
║  └──────────────────────────────────────────────────────┘   ║
║  DynamoDB, Bedrock, Transcribe, Polly, S3, SQS, Cognito     ║
╚══════════════════════════════════════════════════════════════╝

Hướng phụ thuộc:  Infrastructure → Adapters → Use Cases → Domain
                                                    ↑
                                           (chỉ biết Entities)
```

### 2.2 Cấu trúc thư mục dự án (ánh xạ theo lớp)

```
lexi-be/
├── template.yaml                       ← LAYER 4: AWS SAM (Infrastructure as Code)
│                                          Định nghĩa API Gateway, Lambda, DynamoDB, SQS
│
├── src/
│   ├── domain/                         ← LAYER 1: DOMAIN (Pure Python — zero AWS dependency)
│   │   ├── entities/
│   │   │   ├── user.py                 →  UserProfile
│   │   │   ├── session.py              →  Session
│   │   │   ├── turn.py                 →  Turn
│   │   │   ├── flash_card.py           →  FlashCard
│   │   │   ├── scoring.py              →  Scoring
│   │   │   └── scenario.py             →  Scenario
│   │   └── services/
│   │       └── prompt_builder.py       →  build_system_prompt() (Domain Service)
│   │
│   ├── application/                    ← LAYER 2: APPLICATION (không biết AWS tồn tại)
│   │   ├── use_cases/
│   │   │   ├── create_session.py       →  CreateSessionUseCase
│   │   │   ├── run_conversation.py     →  RunConversationUseCase
│   │   │   ├── score_session.py        →  ScoreSessionUseCase
│   │   │   ├── lookup_word.py          →  LookupWordUseCase
│   │   │   └── review_flashcard.py     →  ReviewFlashCardUseCase
│   │   ├── ports/                      ← Interfaces (Dependency Inversion)
│   │   │   ├── session_repo.py         →  ISessionRepo (abstract)
│   │   │   ├── flashcard_repo.py       →  IFlashCardRepo (abstract)
│   │   │   ├── bedrock_port.py         →  IBedrockPort (abstract)
│   │   │   ├── transcribe_port.py      →  ITranscribePort (abstract)
│   │   │   ├── polly_port.py           →  IPollyPort (abstract)
│   │   │   ├── storage_port.py         →  IStoragePort (abstract)
│   │   │   └── sqs_port.py             →  ISQSPort (abstract)
│   │   └── dtos/
│   │       ├── session_dto.py          →  CreateSessionDTO, SessionResponseDTO
│   │       ├── turn_dto.py             →  TurnDTO
│   │       └── flashcard_dto.py        →  FlashCardDTO
│   │
│   ├── interfaces/                     ← LAYER 3: INTERFACE ADAPTERS
│   │   ├── controllers/                ← Nhận DTO → gọi Use Case → trả Entity/DTO
│   │   │   ├── session_controller.py
│   │   │   ├── flashcard_controller.py
│   │   │   ├── word_controller.py
│   │   │   └── ws_controller.py
│   │   └── presenters/                 ← Chuyển đổi Entity → HTTP Response dict
│   │       ├── session_presenter.py
│   │       └── flashcard_presenter.py
│   │
│   └── infrastructure/                 ← LAYER 4: FRAMEWORKS & DRIVERS
│       ├── handlers/                   ← Lambda Handlers (thin entry points)
│       │   ├── session_handler.py      →  fn_session_handler  (lambda_handler)
│       │   ├── flashcard_handler.py    →  fn_flashcard_handler
│       │   ├── ws_auth_handler.py      →  fn_ws_auth_handler
│       │   ├── ws_conv_handler.py      →  fn_ws_conversation_handler
│       │   ├── word_handler.py         →  fn_word_lookup_handler
│       │   ├── scoring_worker.py       →  fn_scoring_worker
│       │   └── presigned_handler.py    →  fn_presigned_url_handler
│       ├── persistence/                ← DynamoDB Adapters (impl Ports)
│       │   ├── dynamo_session_repo.py  →  DynamoDBSessionRepo  impl ISessionRepo
│       │   └── dynamo_flashcard_repo.py→  DynamoDBFlashCardRepo impl IFlashCardRepo
│       └── ai/
│           ├── bedrock_adapter.py      →  BedrockAdapter  impl IBedrockPort
│           ├── transcribe_adapter.py   →  TranscribeAdapter impl ITranscribePort
│           ├── polly_adapter.py        →  PollyAdapter impl IPollyPort
│           └── s3_adapter.py           →  S3Adapter impl IStoragePort
│
└── tests/
    ├── unit/                           ← Test Entity + Use Case (không cần AWS)
    ├── integration/                    ← Test Adapter với LocalStack
    └── e2e/                            ← Test toàn bộ luồng qua SAM Local
```

> **Nguyên tắc**: `template.yaml` và `infrastructure/` là 2 phần của Layer 4 — một phần định nghĩa hạ tầng AWS, một phần là code kết nối với hạ tầng đó.

### 2.3 Mô tả chi tiết từng lớp

#### LAYER 1 — Domain (Entities + Domain Services)
**Vị trí**: `src/domain/`

Lớp trong cùng. **Không import boto3, không import bất kỳ AWS SDK nào**. Chứa các Python dataclass thuần túy và Domain Service thuần logic.

| Entity | Nghiệp vụ cốt lõi |
|--------|-------------------|
| `UserProfile` | Quản lý tài khoản, level, streak, role (LEARNER/ADMIN) |
| `Session` | Vòng đời hội thoại, trạng thái (ACTIVE/PAUSED/COMPLETED), scenario |
| `Turn` | Lượt nói (USER/AI), hint/skip, lazy translation |
| `FlashCard` | Thẻ từ vựng + đầy đủ SRS fields (SM-2 algorithm) |
| `Scoring` | Kết quả chấm điểm 4 kỹ năng (Fluency, Pronunciation, Grammar, Vocabulary) |
| `Scenario` | Mẫu kịch bản roleplay do Admin tạo, có usage_count |

**Domain Service** `src/domain/services/prompt_builder.py`:
```python
# Thuần Python — nhận tham số, trả chuỗi. Không biết AWS tồn tại.
def build_system_prompt(scenario: str, my_character: str, ai_character: str, level: str) -> str:
    ...
```

---

#### LAYER 2 — Application (Use Cases + Ports + DTOs)
**Vị trí**: `src/application/`

Điều phối luồng dữ liệu, gọi Domain Entities, tương tác với Infrastructure **chỉ qua Port (abstract interface)**. Lớp này **không biết nó đang chạy trên AWS Lambda**.

**Ports** (Dependency Inversion — abstract interfaces):
```python
# src/application/ports/session_repo.py
from abc import ABC, abstractmethod
from domain.entities.session import Session

class ISessionRepo(ABC):
    @abstractmethod
    def save(self, session: Session) -> None: ...
    @abstractmethod
    def get_by_id(self, session_id: str) -> Session: ...

# src/application/ports/bedrock_port.py
class IBedrockPort(ABC):
    @abstractmethod
    def stream_response(self, system_prompt: str, history: list) -> Iterator[str]: ...
```

**Use Case** (business flow orchestration):
```python
# src/application/use_cases/create_session.py
class CreateSessionUseCase:
    def __init__(self, repo: ISessionRepo, bedrock: IBedrockPort):
        self._repo = repo
        self._bedrock = bedrock

    def execute(self, dto: CreateSessionDTO) -> Session:
        # Tạo Session entity (Domain logic)
        session = Session(session_id=generate_ulid(), **dto.__dict__)
        # Lưu qua Port — không biết đây là DynamoDB
        self._repo.save(session)
        return session
```

**DTOs** — đối tượng vận chuyển dữ liệu qua ranh giới lớp:
```python
# src/application/dtos/session_dto.py
@dataclass
class CreateSessionDTO:
    user_id: str
    scenario: str
    my_character: str
    ai_character: str
    ai_gender: str
    level: str
```

---

#### LAYER 3 — Interface Adapters (Controllers + Presenters)
**Vị trí**: `src/interfaces/`

**Controllers** nhận dữ liệu thô từ Lambda Handler, tạo DTO, gọi Use Case:
```python
# src/interfaces/controllers/session_controller.py
class SessionController:
    def __init__(self, create_use_case: CreateSessionUseCase):
        self._create = create_use_case

    def create(self, raw_body: dict, user_id: str) -> Session:
        dto = CreateSessionDTO(user_id=user_id, **raw_body)
        return self._create.execute(dto)  # trả về Domain Entity
```

**Presenters** chuyển đổi Domain Entity → HTTP response dict theo chuẩn API Gateway:
```python
# src/interfaces/presenters/session_presenter.py
class SessionPresenter:
    @staticmethod
    def to_response(session: Session) -> dict:
        return {
            "statusCode": 201,
            "body": json.dumps({
                "session_id": session.session_id,
                "status": session.status,
                "scenario": session.scenario,
            })
        }
```

---

#### LAYER 4 — Infrastructure (Frameworks & Drivers)
**Vị trí**: `src/infrastructure/` + `template.yaml`

Gồm hai phần:

**A. Lambda Handlers** — entry points mỏng nhất có thể, là cầu nối giữa AWS và Controller:
```python
# src/infrastructure/handlers/session_handler.py
import json
from interfaces.controllers.session_controller import SessionController
from interfaces.presenters.session_presenter import SessionPresenter
from infrastructure.persistence.dynamo_session_repo import DynamoDBSessionRepo
from application.use_cases.create_session import CreateSessionUseCase

def lambda_handler(event, context):
    # 1. Wiring: inject Infrastructure Adapters vào Use Case
    repo = DynamoDBSessionRepo(table_name=os.environ["TABLE_NAME"])
    use_case = CreateSessionUseCase(repo=repo)
    controller = SessionController(create_use_case=use_case)

    # 2. Trích xuất dữ liệu từ AWS event
    user_id = event["requestContext"]["authorizer"]["claims"]["sub"]
    body = json.loads(event["body"])

    # 3. Gọi Controller — Lambda Handler không chứa business logic
    session = controller.create(raw_body=body, user_id=user_id)

    # 4. Presenter format kết quả thành HTTP response cho API Gateway
    return SessionPresenter.to_response(session)
```

> **Nguyên tắc tối thượng**: Lambda Handler phải mỏng nhất có thể. **Không viết business logic hay truy vấn DB trực tiếp trong `lambda_handler`.**

**B. Infrastructure Adapters** — cài đặt cụ thể cho các Port:
```python
# src/infrastructure/persistence/dynamo_session_repo.py
class DynamoDBSessionRepo(ISessionRepo):  # implements Port
    def save(self, session: Session) -> None:
        item = {
            "PK": f"SESSION#{session.session_id}",
            "SK": "METADATA",
            **dataclasses.asdict(session)
        }
        self._table.put_item(Item=item)  # boto3 chỉ ở đây, không lên trên
```

**C. `template.yaml`** — định nghĩa toàn bộ hạ tầng AWS (API Gateway, Lambda, DynamoDB, SQS).

### 2.4 Luồng dữ liệu qua các ranh giới kiến trúc

```
HTTP Request từ Client
        │
        ▼  API Gateway kích hoạt Lambda
┌─────────────────────────────────────────────────────┐
│ [LAYER 4] Lambda Handler  (infrastructure/handlers/) │
│  • Nhận AWS event + context                          │
│  • Wiring: tạo Adapters, inject vào Use Cases        │
│  • Trích xuất user_id từ JWT claims                  │
│  • Gọi Controller → nhận kết quả → gọi Presenter    │
│  • Trả dict { statusCode, body } cho API Gateway     │
└─────────────────────────────────────────────────────┘
        │                              ▲
     raw_body, user_id          HTTP response dict
        │                              │
        ▼                              │
┌─────────────────────────────────────────────────────┐
│ [LAYER 3] Controller  (interfaces/controllers/)      │
│  • Validate input, tạo Request DTO                  │
│  • Gọi Use Case.execute(dto)                        │
│                                                     │
│ [LAYER 3] Presenter   (interfaces/presenters/)       │
│  • Nhận Domain Entity từ Use Case                   │
│  • Chuyển đổi → { statusCode, body: json }          │
└─────────────────────────────────────────────────────┘
        │                              ▲
     Request DTO                  Domain Entity
        │                              │
        ▼                              │
┌─────────────────────────────────────────────────────┐
│ [LAYER 2] Use Case  (application/use_cases/)         │
│  • Orchestrate business flow                        │
│  • Gọi Domain Entity methods                        │
│  • Gọi Port interfaces (ISessionRepo, IBedrockPort) │
│  • Không biết boto3, không biết Lambda tồn tại      │
└─────────────────────────────────────────────────────┘
        │                              ▲
    Port.method()             Entity / result
        │                              │
        ▼                              │
┌─────────────────────────────────────────────────────┐
│ [LAYER 1] Domain Entity  (domain/entities/)          │
│  • Pure Python dataclass                            │
│  • Business rules (SM-2, status transitions...)     │
│  • Zero AWS dependency                              │
└─────────────────────────────────────────────────────┘
        ▲
        │ implements Port
┌─────────────────────────────────────────────────────┐
│ [LAYER 4] Infrastructure Adapters                    │
│  (infrastructure/persistence/, infrastructure/ai/)   │
│  • DynamoDB boto3 calls                             │
│  • Bedrock API calls                                │
│  • S3, Polly, Transcribe, SQS operations            │
└─────────────────────────────────────────────────────┘
```

### 2.5 Dependency Inversion trong thực tế

```
Domain Entity (Session)
        ▲
        │ sử dụng
Use Case (CreateSession)
        │ phụ thuộc vào (Abstraction)
        ▼
  ISessionRepo (Port/Interface)
        ▲
        │ cài đặt (implements)
DynamoDBSessionRepo (Infrastructure)
        │ phụ thuộc vào
        ▼
   boto3 + DynamoDB schema
```

> **Lợi ích thực tế**: Có thể thay `DynamoDBSessionRepo` bằng `InMemorySessionRepo` cho unit test mà không cần AWS, không cần mock boto3.

### 2.6 Mapping Lambda Function → Clean Architecture Layer

> Lambda Function trong AWS SAM **không phải là Controller**. Đây là **Infrastructure entry point** — càng mỏng càng tốt.

| Thành phần | CA Layer | File | Nhiệm vụ |
|-----------|----------|------|----------|
| `fn_session_handler` | **Layer 4** Infrastructure | `infrastructure/handlers/session_handler.py` | Nhận AWS event → wiring → gọi SessionController |
| `fn_profile_handler` | **Layer 4** Infrastructure | `infrastructure/handlers/profile_handler.py` | Nhận AWS event → gọi ProfileController |
| `fn_ws_auth_handler` | **Layer 4** Infrastructure | `infrastructure/handlers/ws_auth_handler.py` | Verify JWT từ event query string |
| `fn_ws_conversation_handler` | **Layer 4** Infrastructure | `infrastructure/handlers/ws_conv_handler.py` | Nhận WS event → gọi ConversationController |
| `fn_word_lookup_handler` | **Layer 4** Infrastructure | `infrastructure/handlers/word_handler.py` | Nhận AWS event → gọi WordController |
| `fn_flashcard_handler` | **Layer 4** Infrastructure | `infrastructure/handlers/flashcard_handler.py` | Nhận AWS event → gọi FlashCardController |
| `fn_scoring_worker` | **Layer 4** Infrastructure | `infrastructure/handlers/scoring_worker.py` | Nhận SQS event → gọi ScoreSessionUseCase |
| `SessionController` | **Layer 3** Interface Adapter | `interfaces/controllers/session_controller.py` | Parse DTO → gọi Use Cases → trả Entity |
| `FlashCardController` | **Layer 3** Interface Adapter | `interfaces/controllers/flashcard_controller.py` | Parse DTO → gọi Use Cases → trả Entity |
| `SessionPresenter` | **Layer 3** Interface Adapter | `interfaces/presenters/session_presenter.py` | Entity → HTTP response dict |
| `CreateSessionUseCase` | **Layer 2** Application | `application/use_cases/create_session.py` | Orchestrate: tạo Session, lưu qua ISessionRepo |
| `ScoreSessionUseCase` | **Layer 2** Application | `application/use_cases/score_session.py` | Query Turns → gọi Bedrock → lưu Scoring |
| `ISessionRepo` | **Layer 2** Port | `application/ports/session_repo.py` | Abstract interface — ranh giới Application/Infrastructure |
| `DynamoDBSessionRepo` | **Layer 4** Infrastructure | `infrastructure/persistence/dynamo_session_repo.py` | Implements `ISessionRepo` bằng boto3 |
| `BedrockAdapter` | **Layer 4** Infrastructure | `infrastructure/ai/bedrock_adapter.py` | Implements `IBedrockPort` bằng boto3 |
| `Session`, `Turn`, `FlashCard`... | **Layer 1** Domain | `domain/entities/*.py` | Pure Python dataclass, zero dependency |

### 2.7 Chiến lược kiểm thử theo Kim tự tháp

```
         ▲
        /E2E\         Ít nhất — Integration test toàn bộ luồng AWS
       /──────\
      / Integ  \      Trung bình — Test Adapter với LocalStack/DynamoDB local
     /──────────\
    /  Unit Test \    Nhiều nhất — Test Entity + Use Case, không cần AWS
   /______________\
```

| Test Type | Target | Cách chạy |
|-----------|--------|-----------|
| **Unit** | Domain Entities, Use Cases | `pytest` — không cần AWS, dùng `InMemoryRepo` |
| **Integration** | Infrastructure Adapters | `pytest` + LocalStack / DynamoDB Local |
| **E2E** | Lambda Handler → DynamoDB → Bedrock | AWS SAM Local / Staging env |

```python
# Ví dụ Unit Test — không cần mock boto3
def test_create_session_sets_active_status():
    repo = InMemorySessionRepo()  # Fake implementation của ISessionRepo
    use_case = CreateSessionUseCase(repo=repo)
    dto = CreateSessionDTO(user_id="user-1", scenario="Job interview", ...)

    session = use_case.execute(dto)

    assert session.status == "ACTIVE"
    assert repo.find_by_id(session.session_id) is not None
```

---

## 3. Kiến trúc hệ thống AWS

### 3.1 Sơ đồ tổng thể

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
│ │(UP)      │ │   │                    │   │ (verify JWT từ UP)   │
│ └──────────┘ │   │ Routes:            │   │                      │
│ ┌──────────┐ │   │ /sessions          │   │ Routes:              │
│ │Identity  │ │   │ /flashcards        │   │ $connect             │
│ │Pool (IP) │ │   │ /word/lookup       │   │ $disconnect          │
│ └──────────┘ │   │ /profile           │   │ audio/{sessionId}    │
└──────────────┘   └────────┬───────────┘   └──────────┬───────────┘
                            │                           │
                ┌───────────▼───────────────────────────▼──────────┐
                │         AWS Lambda Functions (Layer 3 — Controllers)│
                │         Python 3.12 — SAM Serverless              │
                │                                                   │
                │  fn_session_handler    fn_ws_conversation_handler │
                │  fn_flashcard_handler  fn_word_lookup_handler     │
                │  fn_profile_handler    fn_scoring_worker          │
                └──┬────────────┬──────────────────┬───────────────┘
                   │            │                  │
       ┌───────────▼──┐  ┌──────▼──────┐  ┌───────▼──────────────┐
       │  Amazon      │  │  Amazon S3  │  │  Amazon SQS          │
       │  DynamoDB    │  │             │  │                      │
       │  Tables:     │  │  lexi-audio │  │  scoring-jobs.fifo   │
       │  - LexiApp   │  │  lexi-dict  │  │  scoring-dlq (DLQ)   │
       │  - WordCache │  └──────┬──────┘  └──────────┬───────────┘
       └──────────────┘         │                    │ Event Source Mapping
                                ▼                    ▼
                    ┌─────────────────┐  ┌──────────────────────┐
                    │  CloudFront CDN │  │  fn_scoring_worker   │
                    └─────────────────┘  └──────────────────────┘
                                                    │
                ┌───────────────────────────────────▼──────────────┐
                │                AWS AI Services                    │
                │  Amazon Transcribe (STT) | Bedrock Claude (LLM)  │
                │  Amazon Polly (TTS)                               │
                └────────────────────────────────────────────────────┘

                ┌────────────────────────────────────────────────────┐
                │           Observability & Operations               │
                │  CloudWatch Logs (Lambda) + X-Ray (tracing)        │
                │  CloudWatch Alarms → SNS → Email notification       │
                └────────────────────────────────────────────────────┘
```

### 3.2 Giải thích từng dịch vụ AWS

| Dịch vụ | Vai trò | Chi tiết cấu hình |
|---------|---------|-------------------|
| **Amazon Cognito User Pool** | Quản lý tài khoản, đăng ký, đăng nhập, MFA | Phát hành JWT (IdToken 15 phút, RefreshToken 30 ngày). Email/Password + Google OAuth2 |
| **Amazon Cognito Identity Pool** | Cấp IAM credentials tạm thời cho client | Client dùng IdToken đổi lấy AWS credentials để upload audio trực tiếp lên S3 |
| **AWS API Gateway (REST)** | REST CRUD endpoints | Cognito Authorizer native — tự động verify JWT |
| **AWS API Gateway (WebSocket)** | Real-time conversation channel | Lambda Authorizer verify JWT từ query string. Routes: `$connect`, `$disconnect`, `audio` |
| **AWS Lambda** | Layer 3 Controllers | Python 3.12, AWS SAM. Mỗi Lambda = một Controller cụ thể |
| **Amazon Transcribe Streaming** | STT real-time | PCM 16kHz → transcript real-time < 2 giây |
| **Amazon Bedrock (Claude 3 Haiku)** | LLM hội thoại | `InvokeModelWithResponseStream` — stream text, latency thấp |
| **Amazon Bedrock (Claude 3 Sonnet)** | LLM chấm điểm | Chạy async qua SQS — accuracy cao hơn |
| **Amazon Polly** | TTS | Neural Engine. `SynthesizeSpeech` → MP3 → S3 |
| **Amazon S3** | Lưu trữ audio | `lexi-audio`: audio hội thoại (TTL 90 ngày). `lexi-dict`: audio từ điển |
| **Amazon DynamoDB** | Database chính | Bảng `LexiApp` + `WordCache` (PAY_PER_REQUEST, PITR=true) |
| **Amazon SQS FIFO** | Async scoring queue | `scoring-jobs.fifo` — mỗi session chấm điểm đúng 1 lần. DLQ cho failed jobs |
| **Amazon CloudFront** | CDN audio | Serve audio từ S3 với signed URL |
| **Amazon CloudWatch** | Logging & Monitoring | Log Group mỗi Lambda. Alarms cho DLQ > 0, Error rate > 1% |
| **AWS X-Ray** | Distributed tracing | Toàn bộ luồng API Gateway → Lambda → DynamoDB → Bedrock |

---

## 4. Luồng xử lý chi tiết

### 4.1 Luồng Đăng ký / Đăng nhập (AWS Cognito)

```
CLIENT                    COGNITO USER POOL              API GATEWAY
  │                              │                           │
  │─── POST /register ──────────►│                           │
  │    { email, password }       │ SignUp → Send verify email│
  │◄── 200 { userSub } ─────────│                           │
  │                              │                           │
  │─── POST /confirm-email ─────►│ ConfirmSignUp             │
  │◄── 200 OK ──────────────────│                           │
  │                              │                           │
  │─── POST /login ─────────────►│ InitiateAuth              │
  │◄── 200 { IdToken, AccessToken, RefreshToken } ───────────│
  │                              │                           │
  │─── GET /sessions ───────────────────────────────────────►│
  │    Authorization: Bearer {IdToken}                       │
  │                              │ Cognito Authorizer verify │
  │◄── 200 [ sessions ] ─────────────────────────────────────│
```

> **Cognito `sub`** (UUID immutable) được dùng làm `user_id` xuyên suốt DynamoDB: `UserProfile.user_id`, `Session.user_id`, `FlashCard.user_id`.

---

### 4.2 Luồng Hội thoại thời gian thực

```
CLIENT       API GW (WS)   Lambda (Controller)   Transcribe   Bedrock   Polly   S3/DynamoDB
  │               │                │                  │           │         │          │
  │─[CONNECT]────►│                │                  │           │         │          │
  │ ?token=JWT    │ Lambda Auth    │                  │           │         │          │
  │◄[200 OK]─────│                │                  │           │         │          │
  │               │                │                  │           │         │          │
  │─[START_SESSION]►│─ invoke ────►│                  │           │         │          │
  │               │                │─ Use Case: LoadSession ──────────────────────────►│
  │◄[SESSION_READY]─│◄────────────│                  │           │         │          │
  │               │                │                  │           │         │          │
  │─[AUDIO_UPLOADED]►│─ invoke ───►│                  │           │         │          │
  │ { s3_key }    │                │─ TranscribePort.stream ─────►│         │          │
  │               │                │◄─ transcript + confidence ───│         │          │
  │◄[STT_RESULT]──│◄──────────────│                  │           │         │          │
  │               │                │─ Domain: Turn(USER) ─────────────────────────────►│
  │               │                │─ Domain: build_system_prompt()    │    │          │
  │               │                │─ BedrockPort.stream_response ────────►│           │
  │◄[AI_TEXT_CHUNK]►│◄── stream ──│◄── text chunks ──────────────────│               │
  │               │                │─ PollyPort.synthesize ─────────────────►│         │
  │               │                │─ S3Port.put_object(mp3) ────────────────────────►│
  │◄[AI_AUDIO_URL]─│◄─────────────│                  │           │         │          │
  │               │                │─ Domain: Turn(AI) ───────────────────────────────►│
```

---

### 4.3 Luồng Kết thúc & Chấm điểm Async

```
CLIENT    API GW (REST)   Lambda (Controller)   SQS FIFO   Lambda (Scoring Worker)   DynamoDB
  │            │                 │                  │                │                    │
  │─PATCH /sessions/{id}────────►│                  │                │                    │
  │ { status: COMPLETE }         │─ Use Case: EndSession ────────────────────────────────►│
  │            │                 │─ SQSPort.send({ session_id }) ───►│                    │
  │◄── 200 OK ─│◄───────────────│                  │                │                    │
  │            │                 │                  │─ trigger ──────►│                    │
  │            │                 │                  │         Use Case: ScoreSession       │
  │            │                 │                  │         BedrockPort.invoke(Sonnet)   │
  │            │                 │                  │                │─ Scoring Entity ───►│
  │            │                 │                  │                │─ Update USER stats─►│
  │─ GET /sessions/{id} ────────────────────────────────────────────────────────────────  │
  │◄── 200 { status: COMPLETED, scoring: {...} } ──────────────────────────────────────── │
```

---

### 4.4 Luồng Tra từ & Lưu Flashcard

```
CLIENT     API GW     Lambda (Controller)   WordCache (DynamoDB)   Polly   S3
  │           │               │                     │                │      │
  │─POST /word/lookup─────────►│                     │                │      │
  │           │               │─ Use Case: LookupWord                │      │
  │           │               │─ WordCacheRepo.get(word) ───────────►│      │
  │           │   CACHE HIT   │◄── word data ────────│                │      │
  │◄── 200 { word data } ─────│                     │                │      │
  │           │               │                     │                │      │
  │           │   CACHE MISS  │─ Oxford API (external)               │      │
  │           │               │─ PollyPort.synthesize ──────────────►│      │
  │           │               │─ S3Port.put(dict/word.mp3) ────────────────►│
  │           │               │─ WordCacheRepo.put(word, TTL+60d) ──►│      │
  │◄── 200 { word data } ─────│                     │                │      │
  │           │               │                     │                │      │
  │─POST /flashcards──────────►│                     │                │      │
  │           │               │─ Use Case: SaveFlashCard            │      │
  │           │               │  FlashCard Entity (SM-2 init)        │      │
  │           │               │─ FlashCardRepo.save ────────────────►│      │
  │◄── 200 { flashcard_id }───│                     │                │      │
```

---

### 4.5 Luồng Ôn tập Flashcard (SM-2)

```
CLIENT        API GW        Lambda (Controller)       DynamoDB GSI2
  │               │                 │                       │
  │─GET /flashcards/review──────────►│                       │
  │               │                 │─ Use Case: GetDueCards │
  │               │                 │─ FlashCardRepo.query_due ─────►│
  │               │                 │  GSI2PK=USER#id, GSI2SK≤today  │
  │◄── 200 [ cards due ] ───────────│◄────[ FlashCard entities ] ────│
  │               │                 │                       │
  │─PATCH /flashcards/{id}/review───►│                       │
  │ { quality: 2 }│                 │─ Use Case: ReviewFlashCard     │
  │               │                 │  Domain: SM-2 algorithm        │
  │               │                 │  FlashCard.update_srs(quality) │
  │               │                 │─ FlashCardRepo.update ────────►│
  │◄── 200 { next_review_at }───────│                       │
```

---

## 5. Yêu cầu chức năng (Functional Requirements)

### UC01 — Xác thực người dùng

| ID | Yêu cầu |
|----|---------|
| FR-01.1 | Người dùng đăng ký bằng Email + Password qua Cognito User Pool `SignUp` API |
| FR-01.2 | Cognito gửi email xác minh; người dùng `ConfirmSignUp` với OTP |
| FR-01.3 | Người dùng đăng nhập bằng Google OAuth2 qua Cognito Hosted UI + Federated Identity |
| FR-01.4 | Thành công: Cognito cấp `IdToken` (15 phút), `RefreshToken` (30 ngày) |
| FR-01.5 | `IdToken.sub` (Cognito UUID) — dùng làm `user_id` trong toàn hệ thống |
| FR-01.6 | API Gateway REST dùng **Cognito Authorizer** (không cần code) để verify JWT |
| FR-01.7 | API Gateway WebSocket dùng **Lambda Authorizer** verify JWT từ `?token=` query |
| FR-01.8 | `PostConfirmation` Lambda trigger tự động tạo `UserProfile` entity trong DynamoDB |

---

### UC02 — Thiết lập phiên học

| ID | Yêu cầu |
|----|---------|
| FR-02.1 | Người dùng chọn **Kịch bản** từ danh sách Scenario hoặc tạo tự do. Ghi: `scenario`, `my_character`, `ai_character`, `ai_gender` |
| FR-02.2 | Người dùng chọn **Trình độ** (level): `A1`–`C2` |
| FR-02.3 | Lambda tạo `Session` entity → `PutItem PK=SESSION#[ULID], SK=METADATA` |
| FR-02.4 | `Domain Service: build_system_prompt()` build prompt động theo scenario + level |
| FR-02.5 | Lambda gọi Bedrock Claude Haiku để sinh lời chào mở đầu (Turn#00001, speaker=AI) |
| FR-02.6 | Polly tổng hợp lời chào thành MP3 → S3 → Pre-signed URL cho client |
| FR-02.7 | WebSocket `$connect`: Lambda cập nhật `connection_id` vào `Session` entity |

---

### UC03 — Thực hiện hội thoại

| ID | Yêu cầu |
|----|---------|
| FR-03.1 | Client ghi âm PCM 16kHz, nhận Pre-signed S3 URL, upload trực tiếp lên S3 |
| FR-03.2 | Client gửi `AUDIO_UPLOADED { s3_key }` qua WebSocket; Lambda trigger Transcribe |
| FR-03.3 | Transcribe Streaming nhận dạng âm thanh, trả `transcript` + `confidence` < 2 giây |
| FR-03.4 | Nếu `confidence < 0.85`, client nhận `STT_LOW_CONFIDENCE` |
| FR-03.5 | Lambda `PutItem` `Turn(USER)` entity vào DynamoDB |
| FR-03.6 | Lambda gọi Bedrock Haiku với `InvokeModelWithResponseStream` |
| FR-03.7 | Text stream từng chunk forward qua WebSocket `AI_TEXT_CHUNK` events |
| FR-03.8 | Câu hoàn chỉnh (dấu `.`, `?`, `!`) → Polly `SynthesizeSpeech` → MP3 → S3 |
| FR-03.9 | CloudFront Signed URL → gửi `AI_AUDIO_URL` cho client |
| FR-03.10 | `PutItem` `Turn(AI)` entity sau khi audio upload xong |
| FR-03.11 | Khi user nhấn "Dịch": cập nhật `Turn.translated_content` (lazy translation) |

---

### UC04 — Hint & Skip

| ID | Yêu cầu |
|----|---------|
| FR-04.1 | Client gửi WebSocket event `USE_HINT { session_id }` |
| FR-04.2 | Lambda gọi Bedrock sinh câu gợi ý phù hợp ngữ cảnh + level |
| FR-04.3 | TURN ghi với `Turn.is_hint_used=true` |
| FR-04.4 | `Session.hint_used_count` tăng 1 (DynamoDB Atomic Counter) |
| FR-04.5 | `SKIP_TURN` → ghi `Turn.is_skipped=true`, tăng `Session.skip_used_count` |

---

### UC05 — Pause & Resume

| ID | Yêu cầu |
|----|---------|
| FR-05.1 | App lifecycle event → Client gửi REST `PATCH /sessions/{id} { status: PAUSED }` |
| FR-05.2 | Lambda `UpdateItem Session.status=PAUSED, last_active_at=NOW` |
| FR-05.3 | Danh sách session lấy từ GSI1 (`USER#id#SESSION`), sort desc |
| FR-05.4 | "Học tiếp": Client WebSocket mới → `START_SESSION { session_id }` |
| FR-05.5 | Lambda Query tất cả `Turn` entities → rebuild conversation history → Bedrock prompt |

---

### UC06 — Kết thúc & Chấm điểm Async

| ID | Yêu cầu |
|----|---------|
| FR-06.1 | Client gửi `PATCH /sessions/{id} { status: COMPLETE }` |
| FR-06.2 | Lambda cập nhật `Session.status=PROCESSING_SCORING`, push SQS FIFO Queue |
| FR-06.3 | Lambda trả 200 ngay, client hiển thị "Đang phân tích..." |
| FR-06.4 | SQS trigger `fn_scoring_worker`: Query `Turn` entities, build scoring prompt |
| FR-06.5 | Bedrock Claude 3 Sonnet chấm điểm `Scoring` entity (4 kỹ năng 0–100) |
| FR-06.6 | `Turn.is_hint_used=true` → trừ điểm Fluency; `Turn.is_skipped=true` → trừ nặng hơn |
| FR-06.7 | Worker `PutItem Scoring`, `UpdateItem Session.status=COMPLETED`, tăng `UserProfile.total_sessions` |

---

### UC07 — Tra từ tức thì

| ID | Yêu cầu |
|----|---------|
| FR-07.1 | Client tap từ → `POST /word/lookup { word }` |
| FR-07.2 | Lambda normalize lowercase, `GetItem` WordCache |
| FR-07.3 | **Cache Hit** (< 100ms): tăng `hit_count`, trả data ngay |
| FR-07.4 | **Cache Miss**: gọi Oxford Dictionaries API (external) |
| FR-07.5 | Polly `SynthesizeSpeech` → MP3 → S3 `lexi-dict` |
| FR-07.6 | `PutItem` WordCache với `TTL = now + 60 days` |
| FR-07.7 | Response: `{ word, phonetic, word_type, definition_vi, audio_url, example }` |

---

### UC08 — Lưu Flashcard

| ID | Yêu cầu |
|----|---------|
| FR-08.1 | Client gửi `POST /flashcards { word, session_id, example_sentence }` |
| FR-08.2 | Lambda kiểm tra trùng lặp: Query `FlashCard` entities của user |
| FR-08.3 | Tạo `FlashCard` entity: `PK=USER#id, SK=FLASHCARD#[ULID]` |
| FR-08.4 | Copy `audio_s3_key` từ WordCache → `FlashCard.audio_s3_key` (độc lập với cache TTL) |
| FR-08.5 | Khởi tạo SRS: `easiness_factor=2.5`, `interval_days=1`, `next_review_at=tomorrow` |
| FR-08.6 | `UpdateItem Session.new_words_count += 1` |

---

### UC09 — Ôn tập Flashcard (SRS)

| ID | Yêu cầu |
|----|---------|
| FR-09.1 | `GET /flashcards/review` → Query GSI2: `GSI2PK=USER#id`, `GSI2SK <= today` |
| FR-09.2 | User đánh giá: Dễ/Ổn/Khó/Không nhớ (quality 5/3/2/0) |
| FR-09.3 | Domain logic SM-2: cập nhật `FlashCard.easiness_factor`, `interval_days`, `next_review_at` |
| FR-09.4 | `PATCH /flashcards/{id}/review { quality }` → `UpdateItem` SRS fields |
| FR-09.5 | Audio phát âm qua CloudFront từ S3 `lexi-dict` bucket |

---

### UC10 — Quản lý phiên

| ID | Yêu cầu |
|----|---------|
| FR-10.1 | `GET /sessions` → Query GSI1 `USER#id#SESSION`, sort desc |
| FR-10.2 | `GET /sessions/{id}` → Query base table `PK=SESSION#{id}`, trả `Turn` entities + `Scoring` entity |
| FR-10.3 | `DELETE /sessions/{id}` → `BatchWriteItem` xóa toàn bộ Item Collection |
| FR-10.4 | Audio S3 bị xóa qua **S3 Lifecycle Rule** sau 90 ngày |

---

### UC11 — Quản lý Kịch bản mẫu (Admin)

| ID | Yêu cầu |
|----|---------|
| FR-11.1 | Admin (`UserProfile.role="ADMIN"`) CRUD kịch bản qua `/admin/scenarios` |
| FR-11.2 | Lambda tạo `Scenario` entity → `PK=SYSTEM#SCENARIOS, SK=SCENARIO#[ULID]` |
| FR-11.3 | Users gọi `GET /scenarios` → danh sách `Scenario.is_active=true` |
| FR-11.4 | Scoring Worker tăng `Scenario.usage_count += 1` sau mỗi session |

---

### UC12 — Quản lý Người dùng (Admin)

| ID | Yêu cầu |
|----|---------|
| FR-12.1 | Admin lấy danh sách User qua `GET /admin/users` (Query GSI3 + Pagination) |
| FR-12.2 | Admin Block/Unblock: `PATCH /admin/users/{id} { is_active: false }` |
| FR-12.3 | Lambda update `UserProfile.is_active` + gọi Cognito `AdminDisableUser` |
| FR-12.4 | Cognito Authorizer tự động từ chối token của user bị block → HTTP 401 |

---

## 6. Yêu cầu phi chức năng

### 6.1 Hiệu năng

| ID | Yêu cầu | SLA |
|----|---------|-----|
| NFR-P01 | STT (Transcribe Streaming) phản hồi | < 2 giây |
| NFR-P02 | Tra từ Cache Hit (DynamoDB GetItem) | < 100 ms |
| NFR-P03 | Tra từ Cache Miss (Oxford + Polly + S3) | < 3 giây |
| NFR-P04 | Lưu Flashcard | < 200 ms |
| NFR-P05 | AI first token (Bedrock Haiku stream) | < 1.5 giây |
| NFR-P06 | Serving audio (CloudFront CDN) | < 50 ms (cached) |

### 6.2 Bảo mật

| ID | Yêu cầu |
|----|---------|
| NFR-SEC01 | REST API: Cognito Authorizer native trên API Gateway |
| NFR-SEC02 | WebSocket `$connect`: Lambda Authorizer verify JWT |
| NFR-SEC03 | Audio S3: chỉ serve qua CloudFront Signed URL hoặc Pre-signed URL (15 phút TTL) |
| NFR-SEC04 | IAM Role mỗi Lambda: Least Privilege |
| NFR-SEC05 | DynamoDB `SSEEnabled=true` bảng `LexiApp` |
| NFR-SEC06 | Cognito User Pool: MFA optional, Password policy (min 8 ký tự) |

### 6.3 Khả năng mở rộng

| ID | Yêu cầu |
|----|---------|
| NFR-S01 | DynamoDB `PAY_PER_REQUEST` — tự scale |
| NFR-S02 | Lambda auto-scale theo concurrent invocations |
| NFR-S03 | SQS FIFO Queue scale tự động |
| NFR-S04 | WordCache có thể thêm DAX Cluster khi hit_count cực cao |

### 6.4 Độ tin cậy

| ID | Yêu cầu |
|----|---------|
| NFR-R01 | SQS FIFO retry 3 lần (exponential backoff) trước khi vào DLQ |
| NFR-R02 | CloudWatch Alarm báo động khi DLQ > 0 → SNS Email |
| NFR-R03 | DynamoDB `PointInTimeRecovery=true` |
| NFR-R04 | Lambda Reserved Concurrency = 10 cho `fn_scoring_worker` |

---

## 7. Data Model

### 7.1 DynamoDB Access Patterns

| # | Use Case | Op | Index | Key Pattern |
|---|----------|----|-------|-------------|
| 1 | Lấy profile user | GetItem | Base | `PK=USER#id, SK=PROFILE` |
| 2 | Tạo session | PutItem | Base | `PK=SESSION#[ULID], SK=METADATA` |
| 3 | Lấy toàn bộ session data | Query | Base | `PK=SESSION#id` |
| 4 | Danh sách sessions của user | Query | GSI1 | `GSI1PK=USER#id#SESSION, sort desc` |
| 5 | Ghi 1 TURN | PutItem | Base | `PK=SESSION#id, SK=TURN#00001` |
| 6 | Ghi kết quả scoring | PutItem | Base | `PK=SESSION#id, SK=SCORING` |
| 7 | Danh sách flashcard | Query | Base | `PK=USER#id, begins_with(SK, FLASHCARD#)` |
| 8 | Cards đến hạn ôn tập | Query | GSI2 | `GSI2PK=USER#id, GSI2SK <= today` |
| 9 | Tra từ (WordCache) | GetItem | WordCache | `PK=WORD#word, SK=METADATA` |
| 10 | Tăng counter session | UpdateItem | Base | ADD `hint_used_count`, `new_words_count` |

### 7.2 Entity ↔ DynamoDB Mapping

| Domain Entity | DynamoDB PK | DynamoDB SK | Indexes |
|----------------|-------------|-------------|---------|
| `UserProfile` | `USER#{user_id}` | `PROFILE` | GSI3 (admin list) |
| `Session` | `SESSION#{ulid}` | `METADATA` | GSI1 (`USER#id#SESSION`) |
| `Turn` | `SESSION#{ulid}` | `TURN#{index}` | — |
| `Scoring` | `SESSION#{ulid}` | `SCORING` | — |
| `FlashCard` | `USER#{user_id}` | `FLASHCARD#{ulid}` | GSI1 (list), GSI2 (SRS due) |
| `Scenario` | `SYSTEM#SCENARIOS` | `SCENARIO#{ulid}` | — |

### 7.3 Session State Machine

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
            │ (Scoring Worker ghi Scoring entity xong)
            ▼
        COMPLETED  ← Final state
```

### 7.4 Thuật toán SM-2 (Domain Logic — FlashCard entity)

```python
# Domain logic thuần túy — nằm trong FlashCard entity hoặc Domain Service
# quality: 0=Không nhớ, 2=Khó, 3=Ổn, 5=Dễ
def update_srs(card: FlashCard, quality: int) -> FlashCard:
    if quality < 3:
        card.interval_days = 1
        card.review_count = 0        # reset — học lại từ đầu
    else:
        if card.review_count == 0:   card.interval_days = 1
        elif card.review_count == 1: card.interval_days = 6
        else: card.interval_days = round(card.interval_days * card.easiness_factor)
        card.review_count += 1

    card.easiness_factor = max(1.3,
        card.easiness_factor + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
    )
    card.next_review_at = datetime.utcnow() + timedelta(days=card.interval_days)
    # next_review_at → ghi vào GSI2SK → enable SRS query
    return card
```

---

## 8. API Endpoints

### 8.1 REST API

| Method | Endpoint | Lambda (Controller) | Mô tả |
|--------|----------|---------------------|-------|
| `GET` | `/profile` | fn_profile_handler | Lấy `UserProfile` entity |
| `PUT` | `/profile` | fn_profile_handler | Cập nhật profile (level) |
| `POST` | `/sessions` | fn_session_handler | Tạo `Session` entity mới |
| `GET` | `/sessions` | fn_session_handler | Danh sách sessions (GSI1) |
| `GET` | `/sessions/{id}` | fn_session_handler | `Session` + `Turn[]` + `Scoring` |
| `PATCH` | `/sessions/{id}` | fn_session_handler | Cập nhật `Session.status` |
| `DELETE` | `/sessions/{id}` | fn_session_handler | Xóa toàn bộ Item Collection |
| `POST` | `/upload-url` | fn_presigned_url_handler | S3 Pre-signed URL upload audio |
| `POST` | `/word/lookup` | fn_word_lookup_handler | Tra từ (cache-aside) |
| `GET` | `/flashcards` | fn_flashcard_handler | Danh sách `FlashCard` entities |
| `POST` | `/flashcards` | fn_flashcard_handler | Tạo `FlashCard` entity |
| `GET` | `/flashcards/review` | fn_flashcard_handler | Cards đến hạn (GSI2) |
| `PATCH` | `/flashcards/{id}/review` | fn_flashcard_handler | Cập nhật SRS fields (SM-2) |
| `DELETE` | `/flashcards/{id}` | fn_flashcard_handler | Xóa `FlashCard` entity |
| `GET` | `/scenarios` | fn_scenario_handler | Danh sách `Scenario` active |
| `POST` | `/admin/scenarios` | fn_scenario_handler | Tạo `Scenario` entity (Admin) |
| `GET` | `/admin/users` | fn_profile_handler | Danh sách `UserProfile` (Admin) |
| `PATCH` | `/admin/users/{id}` | fn_profile_handler | Block/Unblock user (Admin) |

### 8.2 WebSocket API

| Route | Lambda | Payload | Mô tả |
|-------|--------|---------|-------|
| `$connect` | fn_ws_auth_handler | `?token=IdToken` | Verify JWT, cập nhật `Session.connection_id` |
| `$disconnect` | fn_ws_conversation_handler | — | Cleanup, auto-pause session |
| `audio` | fn_ws_conversation_handler | `{ action, session_id, s3_key? }` | Core conversation route |

**Client → Server events:**

| Action | Payload | Mô tả |
|--------|---------|-------|
| `START_SESSION` | `{ session_id }` | Bắt đầu / tiếp tục session |
| `AUDIO_UPLOADED` | `{ session_id, s3_key }` | Thông báo audio upload xong |
| `USE_HINT` | `{ session_id }` | Yêu cầu gợi ý |
| `SKIP_TURN` | `{ session_id }` | Bỏ qua lượt |
| `END_SESSION` | `{ session_id }` | Kết thúc phiên |

**Server → Client events:**

| Event | Payload | Mô tả |
|-------|---------|-------|
| `SESSION_READY` | `{ upload_url }` | S3 Pre-signed URL upload audio |
| `STT_RESULT` | `{ text, confidence }` | Kết quả nhận dạng giọng nói |
| `STT_LOW_CONFIDENCE` | `{ confidence }` | Cảnh báo âm thanh không rõ |
| `AI_TEXT_CHUNK` | `{ chunk, done }` | Stream text từ AI |
| `AI_AUDIO_URL` | `{ url, text }` | CloudFront URL phát audio AI |
| `TURN_SAVED` | `{ turn_index }` | Xác nhận `Turn` entity đã lưu DB |
| `HINT_TEXT` | `{ hint }` | Câu gợi ý từ AI |
| `SCORING_COMPLETE` | `{ session_id }` | `Scoring` entity hoàn tất |

---

## 9. Phụ lục

### 9.1 S3 Bucket Structure

```
lexi-audio/                    ← Audio hội thoại (Lifecycle: delete 90 ngày)
  sessions/
    {session_ulid}/
      turn_00001_ai.mp3
      turn_00002_user.mp3

lexi-dict/                     ← Audio từ điển (Lifecycle: move to IA 90 ngày, KHÔNG xóa)
  dictionary/
    en/
      scalable.mp3
      passionate.mp3
```

### 9.2 CloudWatch Alarms

| Alarm | Metric | Threshold | Action |
|-------|--------|-----------|--------|
| ScoringDLQNotEmpty | SQS ApproximateNumberOfMessagesVisible (DLQ) | > 0 | SNS Email |
| LambdaHighErrorRate | Lambda Errors (fn_scoring_worker) | > 2 / 5 phút | SNS Email |
| TranscribeLatencyHigh | Custom metric từ Lambda | p95 > 3000ms | SNS Email |
| DynamoDBThrottled | DynamoDB ThrottledRequests | > 10 / phút | SNS Email |

### 9.3 Roadmap triển khai Clean Architecture

| Giai đoạn | Việc cần làm | Trạng thái |
|-----------|-------------|-----------|
| **Foundation** | Domain Entities (`user.py`, `session.py`, `turn.py`, `flash_card.py`, `scoring.py`, `scenario.py`) | ✅ Hoàn thành |
| **Foundation** | Domain Service (`build_system_prompt()`) | ✅ Hoàn thành |
| **Application** | Tạo `src/layers/application/ports/` — abstract interfaces | 🔲 Cần tạo |
| **Application** | Tạo `src/layers/application/use_cases/` — business flows | 🔲 Cần tạo |
| **Application** | Tạo `src/layers/application/dtos/` — request/response objects | 🔲 Cần tạo |
| **Integration** | Tạo `infrastructure/persistence/` — DynamoDB adapters | 🔲 Cần tạo |
| **Integration** | Tạo `infrastructure/ai/` — Bedrock, Transcribe, Polly adapters | 🔲 Cần tạo |
| **Integration** | Hoàn thiện `src/handlers/` — Controllers inject adapters vào use cases | 🔲 Cần hoàn thiện |
| **Testing** | Unit tests cho Entities + Use Cases (không cần AWS) | 🔲 Cần tạo |
| **Testing** | Integration tests với LocalStack / DynamoDB Local | 🔲 Cần tạo |
