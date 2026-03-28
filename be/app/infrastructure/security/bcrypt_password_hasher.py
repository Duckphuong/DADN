import bcrypt

from app.application.common.interfaces.security import PasswordHasher


class BcryptPasswordHasher(PasswordHasher):
    def hash(self, plain_password: str) -> str:
        return bcrypt.hashpw(
            plain_password.encode("utf-8"),
            bcrypt.gensalt(rounds=10),
        ).decode("utf-8")

    def verify(self, plain_password: str, password_hash: str) -> bool:
        if not password_hash:
            return False

        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                password_hash.encode("utf-8"),
            )
        except ValueError:
            return False
