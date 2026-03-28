from dataclasses import dataclass
from datetime import datetime

from app.domain.exceptions import DomainValidationError
from app.domain.shared.time import utc_now


SENSOR_STATUS_ONLINE = "ONLINE"
SENSOR_STATUS_OFFLINE = "OFFLINE"
DEFAULT_SENSOR_STATUS = SENSOR_STATUS_OFFLINE


@dataclass(slots=True, frozen=True)
class GeoLocation:
    longitude: float
    latitude: float

    @classmethod
    def create(cls, *, longitude: float | int, latitude: float | int) -> "GeoLocation":
        normalized_longitude = cls._validate_longitude(longitude)
        normalized_latitude = cls._validate_latitude(latitude)
        return cls(longitude=normalized_longitude, latitude=normalized_latitude)

    @staticmethod
    def _validate_longitude(longitude: float | int) -> float:
        try:
            normalized_longitude = float(longitude)
        except (TypeError, ValueError) as exc:
            raise DomainValidationError("location.longitude must be a number") from exc

        if normalized_longitude < -180 or normalized_longitude > 180:
            raise DomainValidationError(
                "location.longitude must be between -180 and 180"
            )
        return normalized_longitude

    @staticmethod
    def _validate_latitude(latitude: float | int) -> float:
        try:
            normalized_latitude = float(latitude)
        except (TypeError, ValueError) as exc:
            raise DomainValidationError("location.latitude must be a number") from exc

        if normalized_latitude < -90 or normalized_latitude > 90:
            raise DomainValidationError("location.latitude must be between -90 and 90")
        return normalized_latitude


@dataclass(slots=True)
class SensorStation:
    sensor_name: str
    owner_id: str
    location: GeoLocation
    status: str
    is_deleted: bool
    date_created: datetime
    last_date_update: datetime
    id: str | None = None

    @classmethod
    def create_new(
        cls,
        *,
        sensor_name: str,
        owner_id: str,
        longitude: float | int,
        latitude: float | int,
        status: str | None = None,
    ) -> "SensorStation":
        timestamp = utc_now()
        return cls(
            sensor_name=cls._normalize_sensor_name(sensor_name),
            owner_id=cls._normalize_owner_id(owner_id),
            location=GeoLocation.create(longitude=longitude, latitude=latitude),
            status=cls.normalize_status(status),
            is_deleted=False,
            date_created=timestamp,
            last_date_update=timestamp,
        )

    def update(
        self,
        *,
        sensor_name: str | None = None,
        longitude: float | int | None = None,
        latitude: float | int | None = None,
        status: str | None = None,
    ) -> None:
        if sensor_name is not None:
            self.sensor_name = self._normalize_sensor_name(sensor_name)

        if longitude is not None or latitude is not None:
            next_longitude = self.location.longitude if longitude is None else longitude
            next_latitude = self.location.latitude if latitude is None else latitude
            self.location = GeoLocation.create(
                longitude=next_longitude,
                latitude=next_latitude,
            )

        if status is not None:
            self.status = self.normalize_status(status)

        self.last_date_update = utc_now()

    def soft_delete(self) -> None:
        self.is_deleted = True
        self.last_date_update = utc_now()

    @staticmethod
    def normalize_status(status: str | None) -> str:
        normalized_status = (status or DEFAULT_SENSOR_STATUS).strip().upper()
        if normalized_status not in {SENSOR_STATUS_ONLINE, SENSOR_STATUS_OFFLINE}:
            raise DomainValidationError("status must be ONLINE or OFFLINE")
        return normalized_status

    @staticmethod
    def _normalize_sensor_name(sensor_name: str) -> str:
        normalized_sensor_name = (sensor_name or "").strip()
        if not normalized_sensor_name:
            raise DomainValidationError("sensorName is required")
        return normalized_sensor_name

    @staticmethod
    def _normalize_owner_id(owner_id: str) -> str:
        normalized_owner_id = (owner_id or "").strip()
        if not normalized_owner_id:
            raise DomainValidationError("owner id is required")
        return normalized_owner_id
