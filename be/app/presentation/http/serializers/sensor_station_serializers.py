from app.application.common.models import PageResult
from app.domain.sensor_station.sensor_station import SensorStation
from app.presentation.http.serializers.common import serialize_utc_datetime


def serialize_sensor_station(sensor_station: SensorStation) -> dict:
    payload = {
        "sensorName": sensor_station.sensor_name,
        "userId": sensor_station.owner_id,
        "location": {
            "longitude": sensor_station.location.longitude,
            "latitude": sensor_station.location.latitude,
        },
        "status": sensor_station.status,
        "isDeleted": sensor_station.is_deleted,
        "dateCreated": serialize_utc_datetime(sensor_station.date_created),
        "lastDateUpdate": serialize_utc_datetime(sensor_station.last_date_update),
    }
    if sensor_station.id is not None:
        payload["_id"] = sensor_station.id
    return payload


def serialize_sensor_station_response(message: str, sensor_station: SensorStation) -> dict:
    return {
        "message": message,
        "sensor": serialize_sensor_station(sensor_station),
    }


def serialize_sensor_station_list_response(
    page_result: PageResult[SensorStation],
) -> dict:
    return {
        "message": "Sensor stations fetched successfully",
        "data": [serialize_sensor_station(item) for item in page_result.items],
        "pagination": {
            "page": page_result.page,
            "limit": page_result.limit,
            "total": page_result.total,
            "totalPages": page_result.total_pages,
        },
    }
