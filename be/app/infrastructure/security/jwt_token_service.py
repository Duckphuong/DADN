from datetime import datetime, timedelta, timezone

import jwt

from app.application.common.exceptions import AuthenticationError
from app.application.common.interfaces.security import TokenPayload, TokenService


class JwtTokenService(TokenService):
    def __init__(self, secret_key: str, expires_in_minutes: int) -> None:
        self._secret_key = secret_key
        self._expires_in_minutes = expires_in_minutes

    def issue_access_token(
        self,
        *,
        subject: str,
        email: str | None = None,
        role: str | None = None,
    ) -> str:
        expires_delta = timedelta(minutes=self._expires_in_minutes)
        payload = {
            "sub": subject,
            "email": email,
            "role": role,
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + expires_delta,
        }
        return jwt.encode(payload, self._secret_key, algorithm="HS256")

    def decode_access_token(self, token: str) -> TokenPayload:
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=["HS256"])
        except jwt.ExpiredSignatureError as exc:
            raise AuthenticationError("Token has expired") from exc
        except jwt.InvalidTokenError as exc:
            raise AuthenticationError("Invalid token") from exc

        return TokenPayload(
            subject=str(payload["sub"]),
            email=payload.get("email"),
            role=payload.get("role"),
        )
