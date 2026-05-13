from app.application.common.exceptions import (
    ApplicationError,
    AuthenticationError,
    ConflictError,
    ForbiddenError,
    InfrastructureError,
    NotFoundError,
    ValidationError,
)


def map_application_error(error: ApplicationError) -> tuple[dict, int]:
    if isinstance(error, ValidationError):
        return {"error": str(error)}, 400
    if isinstance(error, AuthenticationError):
        return {"error": str(error)}, 401
    if isinstance(error, ForbiddenError):
        return {"error": str(error)}, 403
    if isinstance(error, NotFoundError):
        return {"error": str(error)}, 404
    if isinstance(error, ConflictError):
        return {"error": str(error)}, 409
    if isinstance(error, InfrastructureError):
        return {"error": str(error)}, 503
    return {"error": "Internal server error"}, 500
