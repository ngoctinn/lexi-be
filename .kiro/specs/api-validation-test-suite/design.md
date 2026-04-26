# API Validation Test Suite - Design

**Feature Name**: api-validation-test-suite  
**Version**: 1.0  
**Status**: In Progress

---

## 1. Architecture Overview

```
tests/
├── conftest.py                 # Pytest fixtures & setup
├── test_api_client.py          # HTTP client wrapper
├── test_websocket_client.py    # WebSocket client wrapper
├── integration/
│   ├── test_onboarding.py      # Task 1
│   ├── test_profile.py         # Task 2
│   ├── test_vocabulary.py      # Tasks 3-4
│   ├── test_flashcard.py       # Tasks 5-9
│   ├── test_scenario.py        # Task 10
│   ├── test_session.py         # Tasks 11-15
│   ├── test_websocket.py       # Tasks 16-21
│   ├── test_admin.py           # Tasks 22-26
│   └── test_workflows.py       # Task 27
└── fixtures/
    ├── test_data.py            # Test data generators
    └── mock_responses.py       # Mock external services
```

---

## 2. Core Components

### 2.1 Test Client Wrapper (test_api_client.py)

```python
class APIClient:
    """HTTP client for API testing"""
    
    def __init__(self, base_url: str, token: str = None):
        self.base_url = base_url
        self.token = token
        self.session = requests.Session()
    
    def get(self, endpoint: str, **kwargs) -> Response:
        """GET request with auth header"""
        
    def post(self, endpoint: str, data: dict, **kwargs) -> Response:
        """POST request with auth header"""
        
    def patch(self, endpoint: str, data: dict, **kwargs) -> Response:
        """PATCH request with auth header"""
        
    def validate_response(self, response: Response, expected_status: int):
        """Validate response status and schema"""
```

### 2.2 WebSocket Client Wrapper (test_websocket_client.py)

```python
class WebSocketClient:
    """WebSocket client for real-time testing"""
    
    async def connect(self, url: str, token: str):
        """Connect to WebSocket with JWT token"""
        
    async def send_action(self, action: str, payload: dict):
        """Send action and wait for response"""
        
    async def wait_for_event(self, event_type: str, timeout: int = 5):
        """Wait for specific event"""
        
    async def close(self):
        """Close connection"""
```

### 2.3 Fixtures (conftest.py)

```python
@pytest.fixture
def api_client():
    """Authenticated API client"""
    token = get_test_token()
    return APIClient(BASE_URL, token)

@pytest.fixture
def admin_client():
    """Admin API client"""
    token = get_admin_token()
    return APIClient(BASE_URL, token)

@pytest.fixture
def public_client():
    """Unauthenticated client"""
    return APIClient(BASE_URL)

@pytest.fixture
async def ws_client():
    """WebSocket client"""
    token = get_test_token()
    client = WebSocketClient()
    await client.connect(WS_URL, token)
    yield client
    await client.close()

@pytest.fixture
def test_scenario():
    """Create test scenario"""
    # Create via API
    # Cleanup after test
    
@pytest.fixture
def test_session(test_scenario):
    """Create test session"""
    # Create via API
    # Cleanup after test
```

### 2.4 Test Data Generators (fixtures/test_data.py)

```python
class TestDataFactory:
    """Generate test data"""
    
    @staticmethod
    def valid_onboarding_data():
        return {
            "display_name": "Test User",
            "current_level": "A1",
            "target_level": "B2",
            "preferred_topics": ["business"]
        }
    
    @staticmethod
    def valid_flashcard_data():
        return {
            "vocab": "run",
            "vocab_type": "verb",
            "translation_vi": "chạy",
            "example_sentence": "She runs every day.",
            "phonetic": "/rʌn/",
            "audio_url": "https://example.com/audio.mp3"
        }
    
    # ... more generators
```

### 2.5 Response Validators (fixtures/validators.py)

```python
class ResponseValidator:
    """Validate API responses against schema"""
    
    @staticmethod
    def validate_success_response(response: dict, expected_keys: list):
        """Validate success response structure"""
        assert response["success"] == True
        assert "message" in response
        assert "data" in response
        for key in expected_keys:
            assert key in response["data"]
    
    @staticmethod
    def validate_error_response(response: dict, expected_error_code: str):
        """Validate error response structure"""
        assert response["success"] == False
        assert response["error"] == expected_error_code
        assert "message" in response
    
    @staticmethod
    def validate_pagination(response: dict):
        """Validate pagination structure"""
        assert "next_key" in response or response["next_key"] is None
```

---

## 3. Test Implementation Pattern

### 3.1 Happy Path Test

```python
def test_get_profile_success(api_client):
    """Test: GET /profile returns user profile"""
    response = api_client.get("/profile")
    
    assert response.status_code == 200
    data = response.json()
    
    ResponseValidator.validate_success_response(data, [
        "user_id", "email", "display_name", "current_level"
    ])
    
    assert data["data"]["email"] == TEST_USER_EMAIL
```

### 3.2 Error Case Test

```python
def test_get_profile_unauthorized(public_client):
    """Test: GET /profile without token returns 401"""
    response = public_client.get("/profile")
    
    assert response.status_code == 401
    data = response.json()
    
    ResponseValidator.validate_error_response(data, "UNAUTHORIZED")
```

### 3.3 Validation Error Test

```python
def test_create_flashcard_missing_field(api_client):
    """Test: POST /flashcards without vocab returns 422"""
    payload = {
        "vocab_type": "verb",
        "translation_vi": "chạy"
        # Missing: vocab, translation_vi
    }
    
    response = api_client.post("/flashcards", payload)
    
    assert response.status_code == 422
    data = response.json()
    
    ResponseValidator.validate_error_response(data, "VALIDATION_ERROR")
```

### 3.4 Integration Test

```python
def test_vocabulary_to_flashcard_workflow(api_client):
    """Test: Translate word → Create flashcard → Review"""
    
    # Step 1: Translate word
    translate_response = api_client.post("/vocabulary/translate", {
        "word": "run",
        "context": "I run every morning"
    })
    assert translate_response.status_code == 200
    translate_data = translate_response.json()["data"]
    
    # Step 2: Create flashcard using translation data
    flashcard_response = api_client.post("/flashcards", {
        "vocab": "run",
        "vocab_type": "verb",
        "translation_vi": translate_data["translation_vi"],
        "example_sentence": translate_data["definitions"][0]["example_en"],
        "phonetic": translate_data["phonetic"]
    })
    assert flashcard_response.status_code == 201
    flashcard_id = flashcard_response.json()["data"]["flashcard_id"]
    
    # Step 3: Review flashcard
    review_response = api_client.post(f"/flashcards/{flashcard_id}/review", {
        "rating": "good"
    })
    assert review_response.status_code == 200
```

---

## 4. WebSocket Test Pattern

```python
@pytest.mark.asyncio
async def test_websocket_start_session(ws_client, test_session):
    """Test: WebSocket start_session action"""
    
    # Send action
    await ws_client.send_action("start_session", {
        "session_id": test_session["session_id"]
    })
    
    # Wait for response
    event = await ws_client.wait_for_event("SESSION_READY", timeout=5)
    
    assert "upload_url" in event
    assert "s3_key" in event
    assert event["session_id"] == test_session["session_id"]
```

---

## 5. Error Handling Strategy

### 5.1 Expected Error Codes

| Error Code | HTTP Status | Scenario |
|-----------|------------|----------|
| BAD_REQUEST | 400 | Invalid JSON, missing fields |
| VALIDATION_ERROR | 422 | Invalid data types, constraints |
| UNAUTHORIZED | 401 | Missing/invalid JWT token |
| FORBIDDEN | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Resource doesn't exist |
| WORD_NOT_FOUND | 404 | Word not in dictionary |
| DICTIONARY_SERVICE_ERROR | 503 | External service down |
| SERVICE_ERROR | 500 | Internal server error |

### 5.2 Test Each Error Code

```python
def test_translate_word_not_found(api_client):
    """Test: POST /vocabulary/translate with non-existent word"""
    response = api_client.post("/vocabulary/translate", {
        "word": "xyzabc123notaword"
    })
    
    assert response.status_code == 404
    assert response.json()["error"] == "WORD_NOT_FOUND"

def test_create_flashcard_validation_error(api_client):
    """Test: POST /flashcards with invalid data"""
    response = api_client.post("/flashcards", {
        "vocab": "run",
        "vocab_type": "invalid_type",  # Invalid
        "translation_vi": "chạy"
    })
    
    assert response.status_code == 422
    assert response.json()["error"] == "VALIDATION_ERROR"
```

---

## 6. Authentication Strategy

### 6.1 Token Management

```python
class TokenManager:
    """Manage JWT tokens for testing"""
    
    @staticmethod
    def get_user_token():
        """Get test user token from Cognito"""
        # Use admin-initiate-auth
        # Cache token with expiry
        
    @staticmethod
    def get_admin_token():
        """Get admin user token"""
        
    @staticmethod
    def get_expired_token():
        """Get expired token for testing"""
        
    @staticmethod
    def refresh_token_if_needed(token):
        """Refresh token if close to expiry"""
```

### 6.2 Test Cases

```python
def test_api_with_valid_token(api_client):
    """Test: API with valid JWT token"""
    # Should succeed
    
def test_api_with_invalid_token(api_client):
    """Test: API with invalid JWT token"""
    # Should return 401
    
def test_api_with_expired_token(api_client):
    """Test: API with expired JWT token"""
    # Should return 401
    
def test_api_without_token(public_client):
    """Test: API without JWT token (except /scenarios)"""
    # Should return 401
```

---

## 7. Pagination Testing

```python
def test_list_flashcards_pagination(api_client):
    """Test: GET /flashcards with pagination"""
    
    # First page
    response1 = api_client.get("/flashcards", params={"limit": 5})
    data1 = response1.json()["data"]
    
    assert len(data1["cards"]) <= 5
    
    if data1["next_key"]:
        # Second page
        response2 = api_client.get("/flashcards", params={
            "limit": 5,
            "last_key": data1["next_key"]
        })
        data2 = response2.json()["data"]
        
        # Verify no overlap
        ids1 = [c["flashcard_id"] for c in data1["cards"]]
        ids2 = [c["flashcard_id"] for c in data2["cards"]]
        assert len(set(ids1) & set(ids2)) == 0
```

---

## 8. Test Execution Flow

```
1. Setup Phase
   ├── Initialize API client with token
   ├── Initialize WebSocket client
   └── Create test fixtures (scenarios, sessions)

2. Test Execution
   ├── Run REST API tests (Tasks 1-10, 22-26)
   ├── Run WebSocket tests (Tasks 16-21)
   ├── Run integration tests (Task 27)
   └── Collect results

3. Cleanup Phase
   ├── Delete test data
   ├── Close WebSocket connections
   └── Generate report
```

---

## 9. Test Report Format

```json
{
  "total_tests": 27,
  "passed": 27,
  "failed": 0,
  "skipped": 0,
  "duration_seconds": 120,
  "coverage": {
    "endpoints": "27/27 (100%)",
    "error_cases": "95%",
    "happy_path": "100%"
  },
  "results": [
    {
      "task": "Task 1: Onboarding API",
      "status": "PASSED",
      "tests": 5,
      "duration": 2.5
    }
  ]
}
```

---

## 10. Implementation Checklist

- [ ] Create test directory structure
- [ ] Implement APIClient wrapper
- [ ] Implement WebSocketClient wrapper
- [ ] Create pytest fixtures
- [ ] Create test data generators
- [ ] Create response validators
- [ ] Implement all 27 test modules
- [ ] Add error case tests
- [ ] Add integration tests
- [ ] Add WebSocket tests
- [ ] Generate test report
- [ ] Document test execution

