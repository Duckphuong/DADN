from collections.abc import Callable

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
