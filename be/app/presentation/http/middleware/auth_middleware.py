from functools import wraps

from flask import g, jsonify, request

from app.application.common.exceptions import ApplicationError
from app.presentation.http.dependencies import get_container
from app.presentation.http.errors import map_application_error


def jwt_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "").strip()
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authorization token is missing"}), 401

        token = auth_header.split(" ", 1)[1].strip()
        if not token:
            return jsonify({"error": "Authorization token is missing"}), 401

        try:
            current_user = get_container().authenticate_user_use_case.execute(token)
        except ApplicationError as exc:
            body, status_code = map_application_error(exc)
            return jsonify(body), status_code

        g.current_user = current_user
        return fn(*args, **kwargs)

    return wrapper
