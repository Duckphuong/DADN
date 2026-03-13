from functools import wraps

import jwt
from flask import g, jsonify, request

from app.database.db import db
from app.models.user_model import User
from app.utils.jwt_handler import decode_token


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
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        user = db.session.get(User, int(payload["sub"]))
        if not user:
            return jsonify({"error": "User not found"}), 404

        g.current_user = user
        return fn(*args, **kwargs)

    return wrapper
