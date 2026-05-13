from dataclasses import dataclass


@dataclass(slots=True)
class CreateSensorStationCommand:
    owner_id: str
    sensor_name: str
    longitude: float
    latitude: float
    status: str | None = None


@dataclass(slots=True)
class ListSensorStationsQuery:
    owner_id: str
    page: int = 1
    limit: int = 10
    status: str | None = None


@dataclass(slots=True)
class GetSensorStationQuery:
    owner_id: str
    sensor_id: str


@dataclass(slots=True)
class UpdateSensorStationCommand:
    owner_id: str
    sensor_id: str
    sensor_name: str | None = None
    longitude: float | None = None
    latitude: float | None = None
    status: str | None = None


@dataclass(slots=True)
class DeleteSensorStationCommand:
    owner_id: str
    sensor_id: str
