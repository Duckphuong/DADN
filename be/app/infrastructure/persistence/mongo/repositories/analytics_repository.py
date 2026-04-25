from collections.abc import Callable
from datetime import timezone

from pymongo import ASCENDING
from pymongo.database import Database
from pymongo.errors import PyMongoError

from app.application.analytics.interfaces import AnalyticsRepository
from app.application.analytics.models import DateRange, TurbidityComparisonPoint
from app.application.common.exceptions import InfrastructureError
from app.infrastructure.persistence.mongo.object_id import parse_object_id


class MongoAnalyticsRepository(AnalyticsRepository):
    SENSOR_COLLECTION_NAME = "sensor_informations"
    MEASUREMENT_COLLECTION_NAME = "predictions"

    def __init__(self, database_provider: Callable[[], Database | None]) -> None:
        self._database_provider = database_provider
        self._indexes_ready = False

    def get_trend_bucket_averages(
        self,
        *,
        user_id: str,
        date_range: DateRange,
        timezone_name: str,
    ) -> dict[str, dict[str, float | None]]:
        active_sensors = self._get_active_sensor_documents(user_id)
        sensor_ids = self._build_sensor_id_lookup_values(active_sensors)
        if not sensor_ids:
            return {}

        pipeline = [
            {
                "$match": {
                    "idSensor": {"$in": sensor_ids},
                    "created_at": {
                        "$type": "date",
                        "$gte": self._to_utc_datetime(date_range.start_time),
                        "$lt": self._to_utc_datetime(date_range.end_time),
                    },
                }
            },
            {
                "$project": {
                    "bucket": self._bucket_switch_expression(timezone_name),
                    "ph": self._measurement_field_expression("pH"),
                    "temperature": self._measurement_field_expression("Temp"),
                    # TODO: Confirm the persisted conductivity field name with the
                    # device payload/schema. No fallback is used to avoid inventing a
                    # business rule outside the dashboard requirement.
                    "conductivity": self._measurement_field_expression("Conductivity"),
                    "dissolvedOxygen": self._measurement_field_expression("DO"),
                }
            },
            {
                "$group": {
                    "_id": "$bucket",
                    "phTrend": {"$avg": "$ph"},
                    "temperatureTrend": {"$avg": "$temperature"},
                    "conductivityTrend": {"$avg": "$conductivity"},
                    "dissolvedOxygenTrend": {"$avg": "$dissolvedOxygen"},
                }
            },
        ]

        try:
            rows = list(self._get_measurement_collection().aggregate(pipeline))
        except PyMongoError as exc:
            raise InfrastructureError("Failed to aggregate trend analytics") from exc

        metric_buckets: dict[str, dict[str, float | None]] = {
            "phTrend": {},
            "temperatureTrend": {},
            "conductivityTrend": {},
            "dissolvedOxygenTrend": {},
        }
        for row in rows:
            bucket = row.get("_id")
            if not bucket:
                continue
            for metric_name in metric_buckets:
                metric_buckets[metric_name][bucket] = row.get(metric_name)

        return metric_buckets

    def get_random_turbidity_comparison(
        self,
        *,
        user_id: str,
        date_range: DateRange,
        sample_size: int,
    ) -> list[TurbidityComparisonPoint]:
        active_sensors = self._get_active_sensor_documents(user_id)
        sensor_ids = self._build_sensor_id_lookup_values(active_sensors)
        if not sensor_ids:
            return []

        sensors_by_id = {str(sensor["_id"]): sensor for sensor in active_sensors}
        pipeline = [
            {
                "$match": {
                    "idSensor": {"$in": sensor_ids},
                    "created_at": {
                        "$type": "date",
                        "$gte": self._to_utc_datetime(date_range.start_time),
                        "$lt": self._to_utc_datetime(date_range.end_time),
                    },
                }
            },
            {
                "$project": {
                    "sensorId": {"$toString": "$idSensor"},
                    "turbidity": self._measurement_field_expression("Turbidity"),
                }
            },
            {
                "$match": {
                    "turbidity": {"$type": "number"},
                }
            },
            {
                "$group": {
                    "_id": "$sensorId",
                    "value": {"$avg": "$turbidity"},
                }
            },
            {"$sample": {"size": sample_size}},
        ]

        try:
            rows = list(self._get_measurement_collection().aggregate(pipeline))
        except PyMongoError as exc:
            raise InfrastructureError(
                "Failed to aggregate turbidity comparison"
            ) from exc

        result: list[TurbidityComparisonPoint] = []
        for row in rows:
            sensor_id = row.get("_id")
            sensor = sensors_by_id.get(sensor_id)
            value = row.get("value")
            if sensor is None or value is None:
                continue
            result.append(
                TurbidityComparisonPoint(
                    sensor_id=sensor_id,
                    sensor_name=sensor.get("sensorName", ""),
                    # TODO: Current SensorStation domain has no address field.
                    # Return the stored address when the schema provides it.
                    address=sensor.get("address"),
                    value=round(float(value), 2),
                )
            )

        return result

    def _get_active_sensor_documents(self, user_id: str) -> list[dict]:
        collection = self._get_sensor_collection()
        user_object_id = parse_object_id(user_id, field_name="userId")
        query = {
            "userId": user_object_id,
            "isDeleted": False,
            # TODO: The current SensorStation domain represents usable sensors as
            # status=ONLINE, while the dashboard requirement says "active".
            # Keep this filter isolated so it can be narrowed when a canonical
            # active flag/status is finalized.
            "$or": [
                {"active": True},
                {"isActive": True},
                {"status": {"$in": ["ACTIVE", "ONLINE"]}},
            ],
        }

        try:
            return list(
                collection.find(
                    query,
                    {
                        "_id": 1,
                        "sensorName": 1,
                        "address": 1,
                    },
                )
            )
        except PyMongoError as exc:
            raise InfrastructureError("Failed to fetch active sensors") from exc

    @staticmethod
    def _build_sensor_id_lookup_values(sensors: list[dict]) -> list:
        values = []
        for sensor in sensors:
            sensor_id = sensor.get("_id")
            if sensor_id is None:
                continue
            values.append(sensor_id)
            values.append(str(sensor_id))
        return values

    @staticmethod
    def _bucket_switch_expression(timezone_name: str) -> dict:
        local_hour = {"$hour": {"date": "$created_at", "timezone": timezone_name}}
        return {
            "$switch": {
                "branches": [
                    {"case": {"$lt": [local_hour, 4]}, "then": "00:00"},
                    {"case": {"$lt": [local_hour, 8]}, "then": "04:00"},
                    {"case": {"$lt": [local_hour, 12]}, "then": "08:00"},
                    {"case": {"$lt": [local_hour, 16]}, "then": "12:00"},
                    {"case": {"$lt": [local_hour, 20]}, "then": "16:00"},
                    {"case": {"$lt": [local_hour, 23]}, "then": "20:00"},
                ],
                "default": "23:00",
            }
        }

    @staticmethod
    def _to_utc_datetime(value):
        if value.tzinfo is None:
            return value
        return value.astimezone(timezone.utc)

    @staticmethod
    def _measurement_field_expression(field_name: str) -> dict:
        return {
            "$ifNull": [
                f"${field_name}",
                f"$sensor_data.{field_name}",
            ]
        }

    def _get_sensor_collection(self):
        database = self._get_database()
        collection = database[self.SENSOR_COLLECTION_NAME]
        self._ensure_indexes(database)
        return collection

    def _get_measurement_collection(self):
        database = self._get_database()
        collection = database[self.MEASUREMENT_COLLECTION_NAME]
        self._ensure_indexes(database)
        return collection

    def _ensure_indexes(self, database: Database) -> None:
        if self._indexes_ready:
            return
        try:
            self._ensure_collection_index(
                database[self.SENSOR_COLLECTION_NAME],
                [
                    ("userId", ASCENDING),
                    ("isDeleted", ASCENDING),
                    ("status", ASCENDING),
                ],
                name="analytics_sensor_owner_active_idx",
            )
            self._ensure_collection_index(
                database[self.MEASUREMENT_COLLECTION_NAME],
                [
                    ("idSensor", ASCENDING),
                    ("created_at", ASCENDING),
                ],
                name="analytics_measurement_sensor_time_idx",
            )
        except PyMongoError as exc:
            raise InfrastructureError("Failed to initialize analytics indexes") from exc
        self._indexes_ready = True

    @classmethod
    def _ensure_collection_index(cls, collection, keys: list[tuple[str, int]], *, name: str):
        if cls._has_matching_index(collection.list_indexes(), keys):
            return
        collection.create_index(keys, name=name)

    @staticmethod
    def _has_matching_index(indexes, keys: list[tuple[str, int]]) -> bool:
        expected_keys = list(keys)
        for index in indexes:
            index_key = index.get("key")
            if hasattr(index_key, "items"):
                existing_keys = list(index_key.items())
            else:
                existing_keys = list(index_key or [])
            if existing_keys == expected_keys:
                return True
        return False

    def _get_database(self) -> Database:
        database = self._database_provider()
        if database is None:
            raise InfrastructureError("MongoDB is not connected")
        return database
