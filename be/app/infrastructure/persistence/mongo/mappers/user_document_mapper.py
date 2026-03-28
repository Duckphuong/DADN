from app.domain.auth.user import User
from app.infrastructure.persistence.mongo.mappers.common import (
    parse_document_datetime,
    to_document_datetime,
)
from app.infrastructure.persistence.mongo.object_id import stringify_object_id


class UserDocumentMapper:
    @staticmethod
    def to_entity(document: dict | None) -> User | None:
        if not document:
            return None

        return User(
            id=stringify_object_id(document.get("_id")),
            full_name=document.get("fullName", ""),
            email=document.get("email", ""),
            password_hash=document.get("password", ""),
            url_avatar=document.get("urlAvatar", ""),
            role=document.get("role", ""),
            phone_number=document.get("phoneNumber", ""),
            status=document.get("status", ""),
            created_at=parse_document_datetime(document.get("createdAt")),
            updated_at=parse_document_datetime(document.get("updatedAt")),
        )

    @staticmethod
    def to_document(user: User) -> dict:
        return {
            "fullName": user.full_name,
            "email": user.email,
            "urlAvatar": user.url_avatar,
            "password": user.password_hash,
            "role": user.role,
            "phoneNumber": user.phone_number,
            "status": user.status,
            "createdAt": to_document_datetime(user.created_at),
            "updatedAt": to_document_datetime(user.updated_at),
        }
