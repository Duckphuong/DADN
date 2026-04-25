from app.application.auth.commands import (
    ChangePasswordCommand,
    LoginUserCommand,
    LoginUserResult,
    RegisterUserCommand,
    UpdateUserCommand,
)
from app.application.auth.interfaces import UserRepository
from app.application.common.exceptions import (
    AuthenticationError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.application.common.interfaces.security import PasswordHasher, TokenService
from app.domain.auth.user import User
from app.domain.exceptions import DomainValidationError


class RegisterUserUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        self._user_repository = user_repository
        self._password_hasher = password_hasher

    def execute(self, command: RegisterUserCommand) -> User:
        try:
            normalized_email = User.normalize_email(command.email)
        except DomainValidationError as exc:
            raise ValidationError(str(exc)) from exc

        existing_user = self._user_repository.get_by_email(normalized_email)
        if existing_user is not None:
            raise ConflictError("Email already exists")

        try:
            user = User.create_new(
                full_name=command.full_name,
                email=normalized_email,
                password_hash=self._password_hasher.hash(command.password),
                url_avatar=command.url_avatar,
                role=command.role,
                phone_number=command.phone_number,
            )
        except DomainValidationError as exc:
            raise ValidationError(str(exc)) from exc

        return self._user_repository.create(user)


class LoginUserUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        token_service: TokenService,
    ) -> None:
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._token_service = token_service

    def execute(self, command: LoginUserCommand) -> LoginUserResult:
        try:
            normalized_email = User.normalize_email(command.email)
        except DomainValidationError as exc:
            raise ValidationError(str(exc)) from exc

        user = self._user_repository.get_by_email(normalized_email)
        if user is None or not self._password_hasher.verify(
            command.password, user.password_hash
        ):
            raise AuthenticationError("Invalid credentials")

        if not user.is_active:
            raise ForbiddenError("User is not active")

        access_token = self._token_service.issue_access_token(
            subject=user.id or "",
            email=user.email,
            role=user.role,
        )
        return LoginUserResult(access_token=access_token, user=user)


class AuthenticateUserUseCase:
    def __init__(
        self,
        token_service: TokenService,
        user_repository: UserRepository,
    ) -> None:
        self._token_service = token_service
        self._user_repository = user_repository

    def execute(self, token: str) -> User:
        token_payload = self._token_service.decode_access_token(token)
        user = self._user_repository.get_by_id(token_payload.subject)

        if user is None:
            raise NotFoundError("User not found")
        if not user.is_active:
            raise ForbiddenError("User is not active")

        return user


class LogoutUserUseCase:
    def execute(self) -> str:
        return "Logout successful. Remove the token on the client."


class ListUsersUseCase:
    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    def execute(self) -> list[User]:
        return self._user_repository.get_all()


class GetUserUseCase:
    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    def execute(self, user_id: str) -> User:
        user = self._user_repository.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")

        return user


class UpdateUserUseCase:
    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    def execute(self, command: UpdateUserCommand) -> User:
        user = self._user_repository.get_by_id(command.user_id)
        if user is None:
            raise NotFoundError("User not found")

        if (
            command.full_name is None
            and command.phone_number is None
            and command.url_avatar is None
            and command.role is None
            and command.status is None
        ):
            raise ValidationError("No valid fields provided for update")

        try:
            user.update(
                full_name=command.full_name,
                phone_number=command.phone_number,
                url_avatar=command.url_avatar,
                role=command.role,
                status=command.status,
            )
        except DomainValidationError as exc:
            raise ValidationError(str(exc)) from exc

        return self._user_repository.update(user)


class ChangePasswordUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        self._user_repository = user_repository
        self._password_hasher = password_hasher

    def execute(self, command: ChangePasswordCommand) -> User:
        normalized_user_id = (command.user_id or "").strip()
        if not normalized_user_id:
            raise ValidationError("user id is required")
        if not command.current_password:
            raise ValidationError("currentPassword is required")
        if not command.new_password:
            raise ValidationError("newPassword is required")

        user = self._user_repository.get_by_id(normalized_user_id)
        if user is None:
            raise NotFoundError("User not found")

        if not self._password_hasher.verify(
            command.current_password,
            user.password_hash,
        ):
            raise AuthenticationError("Current password is incorrect")

        user.change_password(
            password_hash=self._password_hasher.hash(command.new_password)
        )
        return self._user_repository.update(user)


class DeleteUserUseCase:
    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    def execute(self, user_id: str) -> User:
        user = self._user_repository.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")

        user.soft_delete()
        return self._user_repository.soft_delete(user)
