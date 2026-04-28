# Lambda Handler Pattern Guide

## Overview

All Lambda handlers follow a standardized pattern using `BaseHandler` class. This ensures:
- ✅ Consistent authentication & authorization
- ✅ Consistent error handling & logging
- ✅ Lazy dependency initialization (singleton pattern)
- ✅ Easy testing & mocking

## Architecture

```
BaseHandler (abstract)
├── Handles: auth extraction, error handling, logging
├── Enforces: build_dependencies() + handle() implementation
└── Provides: extract_user_id(), extract_path_param(), extract_query_param()

AdminBaseHandler (extends BaseHandler)
├── Adds: admin role authorization check
└── Provides: check_admin_role()
```

## Pattern: Regular Handler

### 1. Create Handler Class

```python
from infrastructure.handlers.base_handler import BaseHandler
from interfaces.controllers.my_controller import MyController

class MyHandler(BaseHandler[MyController]):
    """Handler for my endpoint."""

    def build_dependencies(self) -> MyController:
        """Build controller with dependencies."""
        repo = RepositoryFactory.create_my_repository()
        uc = MyUseCase(repo)
        return MyController(uc)

    def handle(self, user_id: str, event: dict, context: Any) -> dict:
        """Handle the request."""
        controller = self.get_dependencies()
        result = controller.my_method(user_id, event)
        
        if result.is_success:
            return self.presenter.present_success(result.value)
        else:
            return self.presenter._format_response(400, {
                "error": result.error.message,
                "code": result.error.code
            })
```

### 2. Create Module-Level Handler Instance

```python
# Module-level handler instance (singleton)
_handler = MyHandler()

def handler(event, context):
    """Lambda handler entry point."""
    return _handler(event, context)
```

## Pattern: Admin Handler

### 1. Create Admin Handler Class

```python
from infrastructure.handlers.admin_base_handler import AdminBaseHandler
from interfaces.controllers.admin_controller import AdminController

class MyAdminHandler(AdminBaseHandler[AdminController]):
    """Handler for admin endpoint."""

    def build_dependencies(self) -> AdminController:
        """Build admin controller with dependencies."""
        # ... build dependencies
        return AdminController(...)

    def handle(self, user_id: str, event: dict, context: Any) -> dict:
        """Handle the request (user is already verified as admin)."""
        controller = self.get_dependencies()
        result = controller.my_admin_method(user_id, event)
        
        if result.is_success:
            return self.presenter.present_created(result.value)
        else:
            return self.presenter._format_response(400, {
                "error": result.error.message,
                "code": result.error.code
            })
```

### 2. Create Module-Level Handler Instance

```python
_handler = MyAdminHandler()

def handler(event, context):
    """Lambda handler entry point."""
    return _handler(event, context)
```

## Extracting Parameters

### User ID (Automatic)

```python
# Automatically extracted in __call__()
# Available in handle() method as parameter
def handle(self, user_id: str, event: dict, context: Any) -> dict:
    # user_id is already authenticated
    pass
```

### Path Parameters

```python
def handle(self, user_id: str, event: dict, context: Any) -> dict:
    # Raises ValueError if missing
    flashcard_id = self.extract_path_param(event, "flashcard_id")
    
    # Your logic here
    return self.presenter.present_success(result)
```

### Query Parameters

```python
def handle(self, user_id: str, event: dict, context: Any) -> dict:
    # Returns None if missing
    limit = self.extract_query_param(event, "limit", default="20")
    
    # Your logic here
    return self.presenter.present_success(result)
```

## Error Handling

### Automatic Error Handling

The `__call__()` method automatically handles:

```python
# 1. AuthenticationError → 401 Unauthorized
# 2. AuthorizationError → 403 Forbidden (admin only)
# 3. ValueError → 400 Bad Request
# 4. Other exceptions → re-raised (Lambda logs + CloudWatch)
```

### Custom Error Handling in handle()

```python
def handle(self, user_id: str, event: dict, context: Any) -> dict:
    try:
        controller = self.get_dependencies()
        result = controller.my_method(user_id, event)
        
        if result.is_success:
            return self.presenter.present_success(result.value)
        else:
            # Map business errors to HTTP status codes
            if result.error.code == "NOT_FOUND":
                return self.presenter._format_response(404, {
                    "error": result.error.message,
                    "code": "NOT_FOUND"
                })
            elif result.error.code == "PERMISSION_DENIED":
                return self.presenter._format_response(403, {
                    "error": result.error.message,
                    "code": "FORBIDDEN"
                })
            else:
                return self.presenter._format_response(400, {
                    "error": result.error.message,
                    "code": result.error.code
                })
    except PermissionError:
        return self.presenter._format_response(403, {
            "error": "Forbidden",
            "code": "FORBIDDEN"
        })
    except KeyError:
        return self.presenter._format_response(404, {
            "error": "Not found",
            "code": "NOT_FOUND"
        })
```

## Logging

Logging is automatic and consistent:

```python
# Automatically logged in __call__():
# - Handler invoked: "MyHandler invoked"
# - Authentication errors: "Authentication failed: ..."
# - Authorization errors: "Authorization failed: ..."
# - Validation errors: "Validation error: ..."
# - Unhandled errors: "Unhandled error in MyHandler"

# All logs include context:
# extra={"context": {"user_id": user_id, ...}}
```

## Testing

### Mock Handler

```python
from unittest.mock import Mock
from infrastructure.handlers.base_handler import BaseHandler

class TestMyHandler:
    def test_success(self):
        # Create mock controller
        mock_controller = Mock()
        mock_controller.my_method.return_value = OperationResult(
            success={"id": "123"}
        )
        
        # Create handler and inject mock
        handler = MyHandler()
        handler._dependencies = mock_controller
        
        # Test
        event = {
            "requestContext": {
                "authorizer": {"claims": {"sub": "user123"}}
            },
            "body": "{}"
        }
        result = handler(event, {})
        
        assert result["statusCode"] == 200
```

## Migration Checklist

When refactoring existing handlers:

- [ ] Create handler class extending `BaseHandler` or `AdminBaseHandler`
- [ ] Implement `build_dependencies()` method
- [ ] Implement `handle()` method
- [ ] Remove old `_get_or_build_*()` functions
- [ ] Remove old `_unauthorized_response()` function
- [ ] Create module-level handler instance
- [ ] Update `handler()` function to call `_handler(event, context)`
- [ ] Test with existing test cases
- [ ] Verify logging format in CloudWatch

## Benefits

| Aspect | Before | After |
|--------|--------|-------|
| Auth extraction | 3+ patterns | 1 pattern (BaseHandler) |
| Error handling | Inconsistent | Consistent (presenter) |
| Logging | Inconsistent | Consistent (extra context) |
| DI pattern | 3+ patterns | 1 pattern (get_dependencies) |
| Admin check | Manual in handler | Automatic (AdminBaseHandler) |
| Testing | Hard to mock | Easy (inject _dependencies) |
| Lines of code | 50-100 | 20-30 |

## Examples

See these handlers for reference:
- `flashcard/create_flashcard_handler.py` - Basic handler
- `flashcard/delete_flashcard_handler.py` - Handler with path params
- `profile/get_profile_handler.py` - Handler with controller
- `admin/create_admin_scenario_handler.py` - Admin handler
- `onboarding/complete_onboarding_handler.py` - Handler with lazy DI
- `vocabulary/translate_vocabulary_handler.py` - Handler with error mapping
