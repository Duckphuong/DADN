from flask import Blueprint, jsonify, request

from app.application.common.exceptions import ApplicationError
from app.presentation.http.dependencies import get_container
from app.presentation.http.errors import map_application_error
from app.presentation.http.middleware.auth_middleware import jwt_required
from app.presentation.http.serializers.auth_serializers import (
    serialize_login_response,
    serialize_logout_response,
    serialize_register_response,
)
from app.presentation.http.validators.auth_validators import (
    validate_login_request,
    validate_register_request,
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
