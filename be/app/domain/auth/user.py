from dataclasses import dataclass
from datetime import datetime

from app.domain.exceptions import DomainValidationError
from app.domain.shared.time import utc_now


USER_ROLE_MANAGER = "MANAGER"
USER_STATUS_ACTIVE = "ACTIVE"
DEFAULT_USER_ROLE = USER_ROLE_MANAGER
DEFAULT_USER_STATUS = USER_STATUS_ACTIVE


@dataclass(slots=True)
class User:
    full_name: str
    email: str
    password_hash: str
    url_avatar: str
    role: str
    phone_number: str
    status: str
    created_at: datetime
    updated_at: datetime
    id: str | None = None

    @classmethod
    def create_new(
        cls,
        *,
        full_name: str,
        email: str,
        password_hash: str,
        url_avatar: str = "",
        role: str | None = None,
        phone_number: str = "",
    ) -> "User":
        timestamp = utc_now()
        return cls(
            full_name=cls._normalize_full_name(full_name),
            email=cls.normalize_email(email),
            password_hash=cls._normalize_password_hash(password_hash),
            url_avatar=(url_avatar or "").strip(),
            role=cls.normalize_role(role),
            phone_number=(phone_number or "").strip(),
            status=DEFAULT_USER_STATUS,
            created_at=timestamp,
            updated_at=timestamp,
        )

    @property
    def is_active(self) -> bool:
        return self.status == USER_STATUS_ACTIVE

    @staticmethod
    def normalize_email(email: str) -> str:
        normalized_email = (email or "").strip().lower()
        if not normalized_email:
            raise DomainValidationError("email is required")
        return normalized_email

    @staticmethod
    def normalize_role(role: str | None) -> str:
        normalized_role = (role or DEFAULT_USER_ROLE).strip().upper()
        if not normalized_role:
            raise DomainValidationError("role is required")
        return normalized_role

    @staticmethod
    def _normalize_full_name(full_name: str) -> str:
        normalized_full_name = (full_name or "").strip()
        if not normalized_full_name:
            raise DomainValidationError("fullName is required")
        return normalized_full_name

    @staticmethod
    def _normalize_password_hash(password_hash: str) -> str:
        normalized_password_hash = (password_hash or "").strip()
        if not normalized_password_hash:
            raise DomainValidationError("password hash is required")
        return normalized_password_hash
