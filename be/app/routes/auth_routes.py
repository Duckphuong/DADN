from flask import Blueprint, jsonify, request

from app.middleware.jwt_middleware import jwt_required
from app.services.auth_service import AuthService


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.post("/register")
def register():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    email = (payload.get("email") or "").strip()
    password = payload.get("password") or ""

    if not username or not email or not password:
        return jsonify({"error": "username, email, and password are required"}), 400

    response, status_code = AuthService.register_user(username, email, password)
    return jsonify(response), status_code


@auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    identifier = (payload.get("username") or payload.get("email") or "").strip()
    password = payload.get("password") or ""

    if not identifier or not password:
        return jsonify({"error": "username/email and password are required"}), 400

    response, status_code = AuthService.login_user(identifier, password)
    return jsonify(response), status_code


@auth_bp.post("/logout")
@jwt_required
def logout():
    response, status_code = AuthService.logout_user()
    return jsonify(response), status_code
