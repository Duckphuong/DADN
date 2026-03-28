from app.application.common.exceptions import ValidationError
from app.application.sensor_station.commands import (
    CreateSensorStationCommand,
    DeleteSensorStationCommand,
    GetSensorStationQuery,
    ListSensorStationsQuery,
    UpdateSensorStationCommand,
)


def validate_create_sensor_station_request(
    payload: dict,
    *,
    owner_id: str,
) -> CreateSensorStationCommand:
    if not isinstance(payload, dict):
        raise ValidationError("Invalid JSON payload")
    if "userId" in payload:
        raise ValidationError("userId cannot be provided by client")

    location = payload.get("location")
    if not isinstance(location, dict):
        raise ValidationError("location is required")

    return CreateSensorStationCommand(
        owner_id=owner_id,
        sensor_name=payload.get("sensorName"),
        longitude=location.get("longitude"),
        latitude=location.get("latitude"),
        status=payload.get("status"),
    )


def validate_list_sensor_stations_request(
    *,
    owner_id: str,
    page: str | int | None,
    limit: str | int | None,
    status: str | None,
) -> ListSensorStationsQuery:
    return ListSensorStationsQuery(
        owner_id=owner_id,
        page=_parse_positive_int(page, field_name="page"),
        limit=_parse_positive_int(limit, field_name="limit"),
        status=(status or "").strip() or None,
    )


def validate_get_sensor_station_request(
    *,
    owner_id: str,
    sensor_id: str,
) -> GetSensorStationQuery:
    return GetSensorStationQuery(owner_id=owner_id, sensor_id=sensor_id)


def validate_update_sensor_station_request(
    payload: dict,
    *,
    owner_id: str,
    sensor_id: str,
) -> UpdateSensorStationCommand:
    if not isinstance(payload, dict):
        raise ValidationError("Invalid JSON payload")
    if "userId" in payload:
        raise ValidationError("userId cannot be provided by client")

    location = payload.get("location")
    if location is not None and not isinstance(location, dict):
        raise ValidationError("location must be an object")

    return UpdateSensorStationCommand(
        owner_id=owner_id,
        sensor_id=sensor_id,
        sensor_name=payload.get("sensorName"),
        longitude=None if location is None else location.get("longitude"),
        latitude=None if location is None else location.get("latitude"),
        status=payload.get("status"),
    )


def validate_delete_sensor_station_request(
    *,
    owner_id: str,
    sensor_id: str,
) -> DeleteSensorStationCommand:
    return DeleteSensorStationCommand(owner_id=owner_id, sensor_id=sensor_id)


def _parse_positive_int(value, *, field_name: str) -> int:
    try:
        normalized_value = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field_name} must be a positive integer") from exc

    if normalized_value < 1:
        raise ValidationError(f"{field_name} must be a positive integer")
    return normalized_value
