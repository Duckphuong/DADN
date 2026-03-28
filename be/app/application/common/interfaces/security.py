from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class TokenPayload:
    subject: str
    email: str | None = None
    role: str | None = None


class PasswordHasher(Protocol):
    def hash(self, plain_password: str) -> str:
        raise NotImplementedError

    def verify(self, plain_password: str, password_hash: str) -> bool:
        raise NotImplementedError


class TokenService(Protocol):
    def issue_access_token(
        self,
        *,
        subject: str,
        email: str | None = None,
        role: str | None = None,
    ) -> str:
        raise NotImplementedError

    def decode_access_token(self, token: str) -> TokenPayload:
        raise NotImplementedError
