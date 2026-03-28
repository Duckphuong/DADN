from app.domain.sensor_station.sensor_station import GeoLocation, SensorStation
from app.infrastructure.persistence.mongo.mappers.common import (
    parse_document_datetime,
    to_document_datetime,
)
from app.infrastructure.persistence.mongo.object_id import stringify_object_id


class SensorStationDocumentMapper:
    @staticmethod
    def to_entity(document: dict | None) -> SensorStation | None:
        if not document:
            return None

        location = document.get("location") or {}
        return SensorStation(
            id=stringify_object_id(document.get("_id")),
            sensor_name=document.get("sensorName", ""),
            owner_id=stringify_object_id(document.get("userId")) or "",
            location=GeoLocation.create(
                longitude=location.get("longitude"),
                latitude=location.get("latitude"),
            ),
            status=document.get("status", ""),
            is_deleted=bool(document.get("isDeleted", False)),
            date_created=parse_document_datetime(document.get("dateCreated")),
            last_date_update=parse_document_datetime(document.get("lastDateUpdate")),
        )

    @staticmethod
    def to_document(sensor_station: SensorStation) -> dict:
        return {
            "sensorName": sensor_station.sensor_name,
            "userId": sensor_station.owner_id,
            "location": {
                "longitude": sensor_station.location.longitude,
                "latitude": sensor_station.location.latitude,
            },
            "status": sensor_station.status,
            "isDeleted": sensor_station.is_deleted,
            "dateCreated": to_document_datetime(sensor_station.date_created),
            "lastDateUpdate": to_document_datetime(sensor_station.last_date_update),
        }
