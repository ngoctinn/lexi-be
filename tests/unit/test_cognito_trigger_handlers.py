import importlib

import pytest

from shared.result import Result


def test_pre_signup_external_provider_sets_response_flags_and_links(monkeypatch):
    pre = importlib.import_module("infrastructure.handlers.auth.pre_signup_handler")

    called = {"linked": False}

    def fake_find_user_by_email(email: str):
        assert email == "u@example.com"
        return {"Username": "existing-user"}

    def fake_link_provider_for_user(existing_username: str, provider_name: str, provider_user_id: str):
        assert existing_username == "existing-user"
        assert provider_name == "Google"
        assert provider_user_id == "abc_123"
        called["linked"] = True

    monkeypatch.setattr(pre, "_find_user_by_email", fake_find_user_by_email)
    monkeypatch.setattr(pre, "_link_provider_for_user", fake_link_provider_for_user)

    event = {
        "triggerSource": "PreSignUp_ExternalProvider",
        "userName": "Google_abc_123",
        "request": {"userAttributes": {"email": "u@example.com"}},
        "response": {},
    }

    out = pre.handler(event, None)

    assert out is event
    assert out["response"]["autoConfirmUser"] is True
    assert out["response"]["autoVerifyEmail"] is True
    assert called["linked"] is True


def test_pre_signup_non_external_provider_is_noop(monkeypatch):
    pre = importlib.import_module("infrastructure.handlers.auth.pre_signup_handler")

    event = {
        "triggerSource": "PreSignUp_SignUp",
        "userName": "user",
        "request": {"userAttributes": {"email": "u@example.com"}},
        "response": {},
    }

    out = pre.handler(event, None)
    assert out is event
    assert out["response"] == {}


def test_post_confirmation_calls_controller_and_returns_event(monkeypatch):
    monkeypatch.setenv("LEXI_TABLE_NAME", "DummyTable")

    mod = importlib.import_module("infrastructure.handlers.auth.post_confirmation_handler")
    mod = importlib.reload(mod)

    class FakeController:
        def __init__(self):
            self.called = False

        def handle_post_confirmation(self, event):
            self.called = True
            return Result.success(None)

    fake = FakeController()
    monkeypatch.setattr(mod, "auth_controller", fake)

    event = {
        "triggerSource": "PostConfirmation_ConfirmSignUp",
        "userName": "user-1",
        "request": {"userAttributes": {"email": "u@example.com"}},
        "response": {},
    }

    out = mod.handler(event, None)

    assert out is event
    assert fake.called is True


def test_post_authentication_attempts_profile_create_and_returns_event(monkeypatch):
    monkeypatch.setenv("LEXI_TABLE_NAME", "DummyTable")

    mod = importlib.import_module("infrastructure.handlers.auth.post_authentication_handler")
    mod = importlib.reload(mod)

    class FakeUseCase:
        def __init__(self):
            self.called = False

        def execute(self, command):
            self.called = True
            assert command.user_id == "user-1"
            assert command.email == "u@example.com"
            return Result.failure("already exists")

    fake_uc = FakeUseCase()
    monkeypatch.setattr(mod, "create_profile_use_case", fake_uc)

    event = {
        "triggerSource": "PostAuthentication_Authentication",
        "userName": "user-1",
        "request": {"userAttributes": {"email": "u@example.com"}},
        "response": {},
    }

    out = mod.handler(event, None)
    assert out is event
    assert fake_uc.called is True
