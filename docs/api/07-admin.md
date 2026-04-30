# Admin API - VERIFIED

**Status**: ✅ Verified với code thực tế  
**Verified date**: 2026-04-30  
**Verified files**:
- `src/infrastructure/handlers/admin/list_admin_users_handler.py`
- `src/infrastructure/handlers/admin/update_admin_user_handler.py`
- `src/infrastructure/handlers/admin/list_admin_scenarios_handler.py`
- `src/infrastructure/handlers/admin/create_admin_scenario_handler.py`
- `src/infrastructure/handlers/admin/update_admin_scenario_handler.py`
- `src/interfaces/controllers/admin_controller.py`
- `src/interfaces/view_models/admin_vm.py`

---

## Authorization

**All admin endpoints require**:
1. Valid Cognito JWT token (via API Gateway Authorizer)
2. User must have `role: "admin"` in DynamoDB

**Unauthorized Response** (403 Forbidden):
```json
{
  "error": "Forbidden"
}
```

---

## User Management

### 1. List All Users

**Endpoint**: `GET /admin/users`

**Response** (200 OK):
```json
{
  "users": [
    {
      "user_id": "USER#xxx",
      "email": "user@example.com",
      "display_name": "John Doe",
      "role": "LEARNER",
      "is_active": true,
      "joined_at": "2026-04-01T10:00:00Z",
      "total_words_learned": 150
    },
    {
      "user_id": "Google_123456",
      "email": "admin@example.com",
      "display_name": "Admin User",
      "role": "ADMIN",
      "is_active": true,
      "joined_at": "2026-03-15T08:00:00Z",
      "total_words_learned": 0
    }
  ],
  "total_count": 2
}
```

**Fields**:
- `users`: Array of user objects
- `total_count`: Total number of users
- `role`: `"LEARNER"` | `"ADMIN"` (uppercase enum values)
- `joined_at`: Mapped from `last_completed_at` field

---

### 2. Update User

**Endpoint**: `PATCH /admin/users/{user_id}`

**Request Body**:
```json
{
  "is_active": false,
  "current_level": "B1",
  "target_level": "B2"
}
```

**All fields are optional**:
- `is_active` (boolean): Enable/disable user account
- `current_level` (string): CEFR level (A1, A2, B1, B2, C1, C2)
- `target_level` (string): CEFR level (A1, A2, B1, B2, C1, C2)

**Response** (200 OK):
```json
{
  "user_id": "USER#xxx",
  "email": "user@example.com",
  "display_name": "John Doe",
  "role": "learner",
  "is_active": false,
  "joined_at": "2026-04-01T10:00:00Z",
  "total_words_learned": 150
}
```

**Error Response** (404 Not Found):
```json
{
  "error": "User không tồn tại"
}
```

---

## Scenario Management

### 3. List All Scenarios

**Endpoint**: `GET /admin/scenarios`

**Response** (200 OK):
```json
{
  "scenarios": [
    {
      "scenario_id": "SCENARIO#01JGXXX",
      "scenario_title": "At the Restaurant",
      "context": "You are at a restaurant ordering food",
      "roles": ["Customer", "Waiter"],
      "goals": [
        "Order a meal",
        "Ask about menu items",
        "Request the bill"
      ],
      "is_active": true,
      "usage_count": 45,
      "difficulty_level": "A1",
      "order": 1,
      "notes": "Beginner level scenario",
      "created_at": "2026-04-01T10:00:00Z",
      "updated_at": "2026-04-15T14:30:00Z"
    }
  ],
  "total_count": 1
}
```

**Fields**:
- `scenarios`: Array of scenario objects
- `total_count`: Total number of scenarios
- `roles`: Array of 2 role names
- `goals`: Array of learning goals
- `difficulty_level`: CEFR level (A1, A2, B1, B2, C1, C2)
- `order`: Display order (integer)
- `notes`: Admin notes (optional)

---

### 4. Create Scenario

**Endpoint**: `POST /admin/scenarios`

**Request Body**:
```json
{
  "scenario_title": "At the Airport",
  "context": "You are at the airport checking in for your flight",
  "roles": ["Passenger", "Check-in Agent"],
  "goals": [
    "Check in for flight",
    "Ask about baggage allowance",
    "Get boarding pass"
  ],
  "difficulty_level": "A2",
  "order": 5,
  "notes": "Elementary level scenario",
  "is_active": true
}
```

**Required fields**:
- `scenario_title` (string)
- `context` (string)
- `roles` (array of 2 strings)
- `goals` (array of strings)
- `difficulty_level` (string): CEFR level

**Optional fields**:
- `order` (integer): Default 0
- `notes` (string): Default ""
- `is_active` (boolean): Default true

**Response** (201 Created):
```json
{
  "scenario_id": "SCENARIO#01JGYYY",
  "scenario_title": "At the Airport",
  "context": "You are at the airport checking in for your flight",
  "roles": ["Passenger", "Check-in Agent"],
  "goals": [
    "Check in for flight",
    "Ask about baggage allowance",
    "Get boarding pass"
  ],
  "is_active": true,
  "usage_count": 0,
  "difficulty_level": "A2",
  "order": 5,
  "notes": "Elementary level scenario",
  "created_at": "2026-04-30T10:00:00Z",
  "updated_at": "2026-04-30T10:00:00Z"
}
```

**Error Response** (400 Bad Request):
```json
{
  "error": "Invalid request data: ..."
}
```

---

### 5. Update Scenario

**Endpoint**: `PATCH /admin/scenarios/{scenario_id}`

**Request Body** (all fields optional):
```json
{
  "scenario_title": "At the Airport - Updated",
  "context": "Updated context...",
  "roles": ["Passenger", "Gate Agent"],
  "goals": ["Updated goal 1", "Updated goal 2"],
  "difficulty_level": "B1",
  "order": 10,
  "notes": "Updated notes",
  "is_active": false
}
```

**Response** (200 OK):
```json
{
  "scenario_id": "SCENARIO#01JGYYY",
  "scenario_title": "At the Airport - Updated",
  "context": "Updated context...",
  "roles": ["Passenger", "Gate Agent"],
  "goals": ["Updated goal 1", "Updated goal 2"],
  "is_active": false,
  "usage_count": 0,
  "difficulty_level": "B1",
  "order": 10,
  "notes": "Updated notes",
  "created_at": "2026-04-30T10:00:00Z",
  "updated_at": "2026-04-30T10:05:00Z"
}
```

**Error Response** (404 Not Found):
```json
{
  "error": "Scenario không tồn tại"
}
```

---

## Notes

1. **Response Format**: Direct body (không có `{success: true, ...}` wrapper)
2. **Authorization**: Checked in handler via `check_admin()` function
3. **User ID Format**: 
   - Native users: `USER#xxx`
   - Google users: `Google_123456`
4. **CEFR Levels**: A1, A2, B1, B2, C1, C2
5. **Scenario Order**: Used for display sorting in frontend
6. **Usage Count**: Automatically incremented when scenario is used in sessions
