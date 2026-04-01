from src.infrastructure.handlers.auth._di import build_auth_controller

_ctrl = build_auth_controller()

def handler(event, context):
    return _ctrl.handle_confirm_sign_up(event)
