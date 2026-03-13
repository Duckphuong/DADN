from sqlalchemy import or_

from app.database.db import db
from app.models.user_model import User
from app.utils.jwt_handler import generate_token
from app.utils.password_hash import hash_password, verify_password


class AuthService:
    @staticmethod
    def register_user(username, email, password):
        existing_user = User.query.filter(
            or_(User.username == username, User.email == email)
        ).first()
        if existing_user:
            field = "username" if existing_user.username == username else "email"
            return {"error": f"{field} already exists"}, 409

        user = User(
            username=username.strip(),
            email=email.strip().lower(),
            password_hash=hash_password(password),
        )
        db.session.add(user)
        db.session.commit()

        return {"message": "User registered successfully", "user": user.to_dict()}, 201

    @staticmethod
    def login_user(identifier, password):
        user = User.query.filter(
            or_(User.username == identifier, User.email == identifier.lower())
        ).first()
        if not user or not verify_password(password, user.password_hash):
            return {"error": "Invalid credentials"}, 401

        token = generate_token(user.id)
        return {
            "message": "Login successful",
            "access_token": token,
            "user": user.to_dict(),
        }, 200

    @staticmethod
    def logout_user():
        return {"message": "Logout successful. Remove the token on the client."}, 200
