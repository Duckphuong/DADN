from datetime import datetime, timedelta, timezone

import jwt
from flask import current_app


def generate_token(user_id):
    expires_delta = timedelta(
        minutes=current_app.config.get("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", 60)
    )
    payload = {
        "sub": str(user_id),
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + expires_delta,
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")


def decode_token(token):
    return jwt.decode(
        token,
        current_app.config["JWT_SECRET_KEY"],
        algorithms=["HS256"],
    )
