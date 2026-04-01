from src.infrastructure.handlers.auth._di import build_auth_controller

_ctrl = build_auth_controller()

def handler(event, context):
    return _ctrl.handle_reset_password(event)
