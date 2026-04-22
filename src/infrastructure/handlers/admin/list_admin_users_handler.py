import json
from infrastructure.persistence.dynamo_user_repo import DynamoDBUserRepo
from application.use_cases.admin.list_admin_users_uc import ListAdminUsersUseCase
from infrastructure.handlers.admin._shared import check_admin, _response

_user_repo = DynamoDBUserRepo()
_list_users_uc = ListAdminUsersUseCase(_user_repo)


def handler(event, context):
    """GET /admin/users"""
    _, err = check_admin(event, _user_repo)
    if err:
        return err

    query = event.get("queryStringParameters") or {}
    limit = min(int(query.get("limit", 20) or 20), 100)
    last_key_raw = query.get("last_key")
    last_key = json.loads(last_key_raw) if last_key_raw else None

    result = _list_users_uc.execute(limit=limit, last_key=last_key)

    if result.is_success:
        data = result.value
        # Serialize next_key sang JSON string để trả về client
        next_key = json.dumps(data["next_key"]) if data.get("next_key") else None
        return _response(200, {"users": data["users"], "next_key": next_key})

    return _response(500, {"error": result.error})
