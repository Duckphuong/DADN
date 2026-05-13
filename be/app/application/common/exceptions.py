class ApplicationError(Exception):
    """Base class for application-layer errors."""


class ValidationError(ApplicationError):
    pass


class AuthenticationError(ApplicationError):
    pass


class ForbiddenError(ApplicationError):
    pass


class NotFoundError(ApplicationError):
    pass


class ConflictError(ApplicationError):
    pass


class InfrastructureError(ApplicationError):
    pass
