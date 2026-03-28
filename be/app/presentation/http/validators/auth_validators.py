from app.application.auth.commands import LoginUserCommand, RegisterUserCommand
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
