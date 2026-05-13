from typing import Protocol

from app.domain.auth.user import User


class UserRepository(Protocol):
    def get_by_id(self, user_id: str) -> User | None:
        raise NotImplementedError

    def get_by_email(self, email: str) -> User | None:
        raise NotImplementedError

    def create(self, user: User) -> User:
        raise NotImplementedError

    def get_all(self) -> list[User]:
        raise NotImplementedError

    def update(self, user: User) -> User:
        raise NotImplementedError

    def soft_delete(self, user: User) -> User:
        raise NotImplementedError
