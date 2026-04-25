from flask import Blueprint, g, jsonify, request

from app.application.common.exceptions import ApplicationError, ForbiddenError
from app.domain.auth.user import USER_ROLE_ADMIN
from app.presentation.http.dependencies import get_container
from app.presentation.http.errors import map_application_error
from app.presentation.http.middleware.auth_middleware import jwt_required
from app.presentation.http.serializers.auth_serializers import (
    serialize_change_password_response,
    serialize_current_user_response,
    serialize_login_response,
    serialize_logout_response,
    serialize_register_response,
    serialize_user_list_response,
    serialize_user_response,
)
from app.presentation.http.validators.auth_validators import (
    validate_change_password_request,
    validate_login_request,
    validate_register_request,
    validate_update_user_request,
    validate_user_id,
)


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.post("/register")
def register():
    try:
        command = validate_register_request(request.get_json(silent=True) or {})
        user = get_container().register_user_use_case.execute(command)
        return jsonify(serialize_register_response(user)), 201
    except ApplicationError as exc:
        payload, status_code = map_application_error(exc)
        return jsonify(payload), status_code


@auth_bp.post("/login")
def login():
    try:
        command = validate_login_request(request.get_json(silent=True) or {})
        result = get_container().login_user_use_case.execute(command)
        return jsonify(serialize_login_response(result)), 200
    except ApplicationError as exc:
        payload, status_code = map_application_error(exc)
        return jsonify(payload), status_code


@auth_bp.post("/logout")
@jwt_required
def logout():
    try:
        message = get_container().logout_user_use_case.execute()
        return jsonify(serialize_logout_response(message)), 200
    except ApplicationError as exc:
        payload, status_code = map_application_error(exc)
        return jsonify(payload), status_code


@auth_bp.get("/me")
@jwt_required
def get_current_user():
    return jsonify(serialize_current_user_response(g.current_user)), 200


@auth_bp.patch("/password")
@jwt_required
def change_password():
    try:
        command = validate_change_password_request(
            request.get_json(silent=True) or {},
            user_id=g.current_user.id or "",
        )
        get_container().change_password_use_case.execute(command)
        return jsonify(
            serialize_change_password_response("Password changed successfully")
        ), 200
    except ApplicationError as exc:
        payload, status_code = map_application_error(exc)
        return jsonify(payload), status_code


@auth_bp.get("/users")
@jwt_required
def list_users():
    try:
        _require_admin()
        users = get_container().list_users_use_case.execute()
        return jsonify(serialize_user_list_response(users)), 200
    except ApplicationError as exc:
        payload, status_code = map_application_error(exc)
        return jsonify(payload), status_code


@auth_bp.get("/users/<user_id>")
@jwt_required
def get_user(user_id):
    try:
        _require_admin()
        user = get_container().get_user_use_case.execute(validate_user_id(user_id))
        return jsonify(serialize_user_response(user)), 200
    except ApplicationError as exc:
        payload, status_code = map_application_error(exc)
        return jsonify(payload), status_code


@auth_bp.patch("/users/<user_id>")
@jwt_required
def update_user(user_id):
    try:
        _require_admin()
        command = validate_update_user_request(
            request.get_json(silent=True) or {},
            user_id=user_id,
        )
        user = get_container().update_user_use_case.execute(command)
        return jsonify(serialize_user_response(user)), 200
    except ApplicationError as exc:
        payload, status_code = map_application_error(exc)
        return jsonify(payload), status_code


@auth_bp.delete("/users/<user_id>")
@jwt_required
def delete_user(user_id):
    try:
        _require_admin()
        user = get_container().delete_user_use_case.execute(validate_user_id(user_id))
        return jsonify(serialize_user_response(user)), 200
    except ApplicationError as exc:
        payload, status_code = map_application_error(exc)
        return jsonify(payload), status_code


def _require_admin() -> None:
    if g.current_user.role != USER_ROLE_ADMIN:
        raise ForbiddenError("Admin role is required")
