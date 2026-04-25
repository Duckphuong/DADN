from dataclasses import dataclass

from app.domain.auth.user import User


@dataclass(slots=True)
class RegisterUserCommand:
    full_name: str
    email: str
    password: str
    url_avatar: str = ""
    phone_number: str = ""
    role: str = ""


@dataclass(slots=True)
class LoginUserCommand:
    email: str
    password: str


@dataclass(slots=True)
class LoginUserResult:
    access_token: str
    user: User


@dataclass(slots=True)
class UpdateUserCommand:
    user_id: str
    full_name: str | None = None
    phone_number: str | None = None
    url_avatar: str | None = None
    role: str | None = None
    status: str | None = None


@dataclass(slots=True)
class ChangePasswordCommand:
    user_id: str
    current_password: str
    new_password: str
