from collections.abc import Callable

from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database
from pymongo.errors import PyMongoError

from app.application.common.exceptions import InfrastructureError
from app.application.common.models import PageResult
from app.application.sensor_station.interfaces import SensorStationRepository
from app.domain.sensor_station.sensor_station import SensorStation
from app.infrastructure.persistence.mongo.mappers.sensor_station_document_mapper import (
    SensorStationDocumentMapper,
)
from app.infrastructure.persistence.mongo.object_id import parse_object_id


class MongoSensorStationRepository(SensorStationRepository):
    COLLECTION_NAME = "sensor_informations"

    def __init__(self, database_provider: Callable[[], Database | None]) -> None:
        self._database_provider = database_provider
        self._indexes_ready = False

    def create(self, sensor_station: SensorStation) -> SensorStation:
        collection = self._get_collection()
        document = SensorStationDocumentMapper.to_document(sensor_station)
        document["userId"] = parse_object_id(sensor_station.owner_id, field_name="user id")

        try:
            inserted_id = collection.insert_one(document).inserted_id
            return SensorStationDocumentMapper.to_entity(collection.find_one({"_id": inserted_id}))
        except PyMongoError as exc:
            raise InfrastructureError("Failed to create sensor station") from exc

    def get_by_id_for_owner(
        self,
        sensor_id: str,
        owner_id: str,
        *,
        include_deleted: bool = False,
    ) -> SensorStation | None:
        collection = self._get_collection()
        query = {
            "_id": parse_object_id(sensor_id, field_name="sensor id"),
            "userId": parse_object_id(owner_id, field_name="user id"),
        }
        if not include_deleted:
            query["isDeleted"] = False

        try:
            return SensorStationDocumentMapper.to_entity(collection.find_one(query))
        except PyMongoError as exc:
            raise InfrastructureError("Failed to fetch sensor station") from exc

    def list_by_owner(
        self,
        owner_id: str,
        *,
        page: int,
        limit: int,
        status: str | None = None,
    ) -> PageResult[SensorStation]:
        collection = self._get_collection()
        query = {
            "userId": parse_object_id(owner_id, field_name="user id"),
            "isDeleted": False,
        }
        if status is not None:
            query["status"] = status

        try:
            total = collection.count_documents(query)
            cursor = (
                collection.find(query)
                .sort("lastDateUpdate", DESCENDING)
                .skip((page - 1) * limit)
                .limit(limit)
            )
            items = [
                sensor_station
                for sensor_station in (
                    SensorStationDocumentMapper.to_entity(document) for document in cursor
                )
                if sensor_station is not None
            ]
        except PyMongoError as exc:
            raise InfrastructureError("Failed to fetch sensor stations") from exc

        return PageResult(items=items, page=page, limit=limit, total=total)

    def update(self, sensor_station: SensorStation) -> SensorStation:
        collection = self._get_collection()
        if sensor_station.id is None:
            raise InfrastructureError("Sensor station id is required for update")

        try:
            collection.update_one(
                {
                    "_id": parse_object_id(sensor_station.id, field_name="sensor id"),
                    "userId": parse_object_id(sensor_station.owner_id, field_name="user id"),
                    "isDeleted": False,
                },
                {
                    "$set": {
                        "sensorName": sensor_station.sensor_name,
                        "location": {
                            "longitude": sensor_station.location.longitude,
                            "latitude": sensor_station.location.latitude,
                        },
                        "status": sensor_station.status,
                        "lastDateUpdate": sensor_station.last_date_update,
                    }
                },
            )
            updated_document = collection.find_one(
                {"_id": parse_object_id(sensor_station.id, field_name="sensor id")}
            )
            return SensorStationDocumentMapper.to_entity(updated_document)
        except PyMongoError as exc:
            raise InfrastructureError("Failed to update sensor station") from exc

    def soft_delete(self, sensor_station: SensorStation) -> SensorStation:
        collection = self._get_collection()
        if sensor_station.id is None:
            raise InfrastructureError("Sensor station id is required for delete")

        try:
            collection.update_one(
                {
                    "_id": parse_object_id(sensor_station.id, field_name="sensor id"),
                    "userId": parse_object_id(sensor_station.owner_id, field_name="user id"),
                    "isDeleted": False,
                },
                {
                    "$set": {
                        "isDeleted": True,
                        "lastDateUpdate": sensor_station.last_date_update,
                    }
                },
            )
            deleted_document = collection.find_one(
                {"_id": parse_object_id(sensor_station.id, field_name="sensor id")}
            )
            return SensorStationDocumentMapper.to_entity(deleted_document)
        except PyMongoError as exc:
            raise InfrastructureError("Failed to delete sensor station") from exc

    def _get_collection(self):
        database = self._database_provider()
        if database is None:
            raise InfrastructureError("MongoDB is not connected")

        collection = database[self.COLLECTION_NAME]
        if not self._indexes_ready:
            try:
                collection.create_index(
                    [
                        ("userId", ASCENDING),
                        ("isDeleted", ASCENDING),
                        ("lastDateUpdate", DESCENDING),
                    ],
                    name="sensor_owner_active_updated_idx",
                )
                collection.create_index(
                    [
                        ("userId", ASCENDING),
                        ("isDeleted", ASCENDING),
                        ("status", ASCENDING),
                    ],
                    name="sensor_owner_active_status_idx",
                )
            except PyMongoError as exc:
                raise InfrastructureError("Failed to initialize sensor collection") from exc
            self._indexes_ready = True

        return collection
