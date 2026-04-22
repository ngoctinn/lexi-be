from infrastructure.persistence.dynamo_user_repo import DynamoDBUserRepo
from application.use_cases.admin.update_admin_user_uc import UpdateAdminUserUseCase
from infrastructure.handlers.admin._shared import check_admin, parse_body, _response

_user_repo = DynamoDBUserRepo()
_update_user_uc = UpdateAdminUserUseCase(_user_repo)


def handler(event, context):
    """PATCH /admin/users/{user_id}"""
    _, err = check_admin(event, _user_repo)
    if err:
        return err

    path_params = event.get("pathParameters") or {}
    target_user_id = path_params.get("user_id", "")
    if not target_user_id:
        return _response(400, {"error": "Thiếu user_id"})

    body = parse_body(event)
    result = _update_user_uc.execute(
        target_user_id=target_user_id,
        is_active=body.get("is_active"),
        current_level=body.get("current_level"),
        target_level=body.get("target_level"),
    )

    if result.is_success:
        return _response(200, {"success": True, "user": result.value})

    if "không tồn tại" in result.error:
        return _response(404, {"error": result.error})
    return _response(400, {"error": result.error})
