from collections.abc import Callable

from pymongo import DESCENDING
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.application.auth.interfaces import UserRepository
from app.application.common.exceptions import ConflictError, InfrastructureError
from app.domain.auth.user import User
from app.infrastructure.persistence.mongo.mappers.user_document_mapper import UserDocumentMapper
from app.infrastructure.persistence.mongo.object_id import parse_object_id


class MongoUserRepository(UserRepository):
    COLLECTION_NAME = "users"

    def __init__(self, database_provider: Callable[[], Database | None]) -> None:
        self._database_provider = database_provider
        self._indexes_ready = False

    def get_by_id(self, user_id: str) -> User | None:
        collection = self._get_collection()
        object_id = parse_object_id(user_id, field_name="user id")
        try:
            return UserDocumentMapper.to_entity(collection.find_one({"_id": object_id}))
        except PyMongoError as exc:
            raise InfrastructureError("Failed to fetch user") from exc

    def get_by_email(self, email: str) -> User | None:
        collection = self._get_collection()
        try:
            return UserDocumentMapper.to_entity(collection.find_one({"email": email}))
        except PyMongoError as exc:
            raise InfrastructureError("Failed to query users collection") from exc

    def create(self, user: User) -> User:
        collection = self._get_collection()
        try:
            inserted_id = collection.insert_one(UserDocumentMapper.to_document(user)).inserted_id
            return UserDocumentMapper.to_entity(collection.find_one({"_id": inserted_id}))
        except DuplicateKeyError as exc:
            raise ConflictError("email already exists") from exc
        except PyMongoError as exc:
            raise InfrastructureError("Failed to create user") from exc

    def _get_collection(self):
        database = self._database_provider()
        if database is None:
            raise InfrastructureError("MongoDB is not connected")

        collection = database[self.COLLECTION_NAME]
        if not self._indexes_ready:
            try:
                collection.create_index("email", unique=True, name="users_email_unique")
            except PyMongoError as exc:
                raise InfrastructureError("Failed to initialize users collection") from exc
            self._indexes_ready = True

        return collection

    def get_all(self) -> list[User]:
        collection = self._get_collection()
        try:
            cursor = collection.find().sort("createdAt", DESCENDING)
            return [
                user
                for user in (UserDocumentMapper.to_entity(document) for document in cursor)
                if user is not None
            ]
        except PyMongoError as exc:
            raise InfrastructureError("Failed to fetch users") from exc

    def update(self, user: User) -> User:
        collection = self._get_collection()
        if user.id is None:
            raise InfrastructureError("User id is required for update")

        object_id = parse_object_id(user.id, field_name="user id")
        try:
            collection.update_one(
                {"_id": object_id},
                {
                    "$set": {
                        "fullName": user.full_name,
                        "password": user.password_hash,
                        "urlAvatar": user.url_avatar,
                        "role": user.role,
                        "phoneNumber": user.phone_number,
                        "status": user.status,
                        "updatedAt": user.updated_at,
                    }
                },
            )
            updated_document = collection.find_one({"_id": object_id})
            updated_user = UserDocumentMapper.to_entity(updated_document)
            if updated_user is None:
                raise InfrastructureError("Failed to fetch updated user")
            return updated_user
        except PyMongoError as exc:
            raise InfrastructureError("Failed to update user") from exc

    def soft_delete(self, user: User) -> User:
        collection = self._get_collection()
        if user.id is None:
            raise InfrastructureError("User id is required for delete")

        object_id = parse_object_id(user.id, field_name="user id")
        try:
            collection.update_one(
                {"_id": object_id},
                {
                    "$set": {
                        "status": user.status,
                        "updatedAt": user.updated_at,
                    }
                },
            )
            deleted_document = collection.find_one({"_id": object_id})
            deleted_user = UserDocumentMapper.to_entity(deleted_document)
            if deleted_user is None:
                raise InfrastructureError("Failed to fetch deleted user")
            return deleted_user
        except PyMongoError as exc:
            raise InfrastructureError("Failed to delete user") from exc
