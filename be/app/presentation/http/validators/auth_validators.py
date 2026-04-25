from app.application.auth.commands import (
    ChangePasswordCommand,
    LoginUserCommand,
    RegisterUserCommand,
    UpdateUserCommand,
)
from app.application.common.exceptions import ValidationError


def validate_register_request(payload: dict) -> RegisterUserCommand:
    if not isinstance(payload, dict):
        raise ValidationError("Invalid JSON payload")

    full_name = (payload.get("fullName") or "").strip()
    email = (payload.get("email") or "").strip()
    password = payload.get("password") or ""

    if not full_name or not email or not password:
        raise ValidationError("fullName, email, and password are required")

    return RegisterUserCommand(
        full_name=full_name,
        email=email,
        password=password,
        url_avatar=(payload.get("urlAvatar") or "").strip(),
        phone_number=(payload.get("phoneNumber") or "").strip(),
        role=(payload.get("role") or "").strip(),
    )


def validate_login_request(payload: dict) -> LoginUserCommand:
    if not isinstance(payload, dict):
        raise ValidationError("Invalid JSON payload")

    email = (payload.get("email") or "").strip()
    password = payload.get("password") or ""
    if not email or not password:
        raise ValidationError("email and password are required")

    return LoginUserCommand(email=email, password=password)


def validate_update_user_request(payload: dict, *, user_id: str) -> UpdateUserCommand:
    if not isinstance(payload, dict):
        raise ValidationError("Invalid JSON payload")

    forbidden_fields = {"_id", "id", "email", "password", "passwordHash", "createdAt"}
    provided_forbidden_fields = sorted(forbidden_fields.intersection(payload.keys()))
    if provided_forbidden_fields:
        raise ValidationError(
            f"{', '.join(provided_forbidden_fields)} cannot be updated here"
        )

    role = _get_optional_string(payload, "role")
    status = _get_optional_string(payload, "status")
    if role == "":
        raise ValidationError("role must be ADMIN, MANAGER, or USER")
    if status == "":
        raise ValidationError("status must be ACTIVE or INACTIVE")

    return UpdateUserCommand(
        user_id=validate_user_id(user_id),
        full_name=_get_optional_string(payload, "fullName"),
        phone_number=_get_optional_string(payload, "phoneNumber"),
        url_avatar=_get_optional_string(payload, "urlAvatar"),
        role=role,
        status=status,
    )


def validate_change_password_request(
    payload: dict,
    *,
    user_id: str,
) -> ChangePasswordCommand:
    if not isinstance(payload, dict):
        raise ValidationError("Invalid JSON payload")

    current_password = _get_required_password(payload, "currentPassword")
    new_password = _get_required_password(payload, "newPassword")

    return ChangePasswordCommand(
        user_id=validate_user_id(user_id),
        current_password=current_password,
        new_password=new_password,
    )


def validate_user_id(user_id: str) -> str:
    normalized_user_id = (user_id or "").strip()
    if not normalized_user_id:
        raise ValidationError("user id is required")
    return normalized_user_id


def _get_optional_string(payload: dict, field_name: str) -> str | None:
    if field_name not in payload:
        return None

    value = payload.get(field_name)
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string")

    return value.strip()


def _get_required_password(payload: dict, field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or value == "":
        raise ValidationError(f"{field_name} is required")
    return value
