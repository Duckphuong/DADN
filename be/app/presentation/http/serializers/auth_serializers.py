from app.application.auth.commands import LoginUserResult
from app.domain.auth.user import User
from app.presentation.http.serializers.common import serialize_utc_datetime


def serialize_user(user: User) -> dict:
    payload = {
        "fullName": user.full_name,
        "email": user.email,
        "urlAvatar": user.url_avatar,
        "role": user.role,
        "phoneNumber": user.phone_number,
        "status": user.status,
        "createdAt": serialize_utc_datetime(user.created_at),
        "updatedAt": serialize_utc_datetime(user.updated_at),
    }
    if user.id is not None:
        payload["id"] = user.id
        payload["_id"] = user.id
    return payload


def serialize_register_response(user: User) -> dict:
    return {
        "message": "User registered successfully",
        "user": serialize_user(user),
    }


def serialize_login_response(result: LoginUserResult) -> dict:
    return {
        "message": "Login successful",
        "access_token": result.access_token,
        "user": serialize_user(result.user),
    }


def serialize_logout_response(message: str) -> dict:
    return {"message": message}


def serialize_change_password_response(message: str) -> dict:
    return {"message": message}


def serialize_current_user_response(user: User) -> dict:
    return serialize_user(user)


def serialize_user_list_response(users: list[User]) -> list[dict]:
    return [serialize_user(user) for user in users]


def serialize_user_response(user: User) -> dict:
    return serialize_user(user)
