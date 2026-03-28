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
