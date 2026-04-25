from dataclasses import dataclass
from datetime import datetime

from app.domain.exceptions import DomainValidationError
from app.domain.shared.time import utc_now


USER_ROLE_MANAGER = "MANAGER"
USER_ROLE_ADMIN = "ADMIN"
USER_ROLE_USER = "USER"
USER_STATUS_ACTIVE = "ACTIVE"
USER_STATUS_INACTIVE = "INACTIVE"
DEFAULT_USER_ROLE = USER_ROLE_MANAGER
DEFAULT_USER_STATUS = USER_STATUS_ACTIVE
ALLOWED_USER_ROLES = {USER_ROLE_ADMIN, USER_ROLE_MANAGER, USER_ROLE_USER}
ALLOWED_USER_STATUSES = {USER_STATUS_ACTIVE, USER_STATUS_INACTIVE}


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

    def update(
        self,
        *,
        full_name: str | None = None,
        phone_number: str | None = None,
        url_avatar: str | None = None,
        role: str | None = None,
        status: str | None = None,
    ) -> None:
        if full_name is not None:
            self.full_name = self._normalize_full_name(full_name)
        if phone_number is not None:
            self.phone_number = phone_number.strip()
        if url_avatar is not None:
            self.url_avatar = url_avatar.strip()
        if role is not None:
            self.role = self.normalize_role(role)
        if status is not None:
            self.status = self.normalize_status(status)

        self.updated_at = utc_now()

    def soft_delete(self) -> None:
        self.status = USER_STATUS_INACTIVE
        self.updated_at = utc_now()

    def change_password(self, *, password_hash: str) -> None:
        self.password_hash = self._normalize_password_hash(password_hash)
        self.updated_at = utc_now()

    @staticmethod
    def normalize_email(email: str) -> str:
        normalized_email = (email or "").strip().lower()
        if not normalized_email:
            raise DomainValidationError("email is required")
        return normalized_email

    @staticmethod
    def normalize_role(role: str | None) -> str:
        normalized_role = (role or DEFAULT_USER_ROLE).strip().upper()
        if normalized_role not in ALLOWED_USER_ROLES:
            raise DomainValidationError("role must be ADMIN, MANAGER, or USER")
        return normalized_role

    @staticmethod
    def normalize_status(status: str | None) -> str:
        normalized_status = (status or DEFAULT_USER_STATUS).strip().upper()
        if normalized_status not in ALLOWED_USER_STATUSES:
            raise DomainValidationError("status must be ACTIVE or INACTIVE")
        return normalized_status

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
