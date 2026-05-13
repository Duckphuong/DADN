from collections.abc import Callable
from typing import Optional

from pymongo.database import Database
from pymongo.errors import PyMongoError

from app.application.common.exceptions import InfrastructureError
from app.application.sensor_station.sensor_data_interfaces import SensorDataRepository
from app.infrastructure.persistence.mongo.object_id import parse_object_id


class MongoSensorDataRepository(SensorDataRepository):
    COLLECTION_NAME = "input_sensors"

    def __init__(self, database_provider: Callable[[], Database | None]) -> None:
        self._database_provider = database_provider

    def get_latest(self, sensor_id: Optional[str] = None) -> Optional[dict]:
        collection = self._get_collection()

        query: dict = {}
        if sensor_id:
            try:
                query["idSensor"] = parse_object_id(sensor_id, field_name="sensor id")
            except Exception:
                query["idSensor"] = sensor_id

        try:
            doc = collection.find_one(query, sort=[("created_at", -1)])
        except PyMongoError as exc:
            raise InfrastructureError("Failed to fetch latest sensor data") from exc

        if doc is None:
            return None

        # Chuẩn hoá _id và idSensor về string để serialize an toàn
        doc["_id"] = str(doc["_id"])
        if "idSensor" in doc:
            doc["idSensor"] = str(doc["idSensor"])

        # Chuẩn hoá created_at về ISO string
        created_at = doc.get("created_at")
        if hasattr(created_at, "isoformat"):
            doc["created_at"] = created_at.isoformat()

        return doc

    def _get_collection(self):
        database = self._database_provider()
        if database is None:
            raise InfrastructureError("MongoDB is not connected")
        return database[self.COLLECTION_NAME]