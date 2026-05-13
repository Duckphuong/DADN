from typing import Protocol

from app.application.common.models import PageResult
from app.domain.sensor_station.sensor_station import SensorStation


class SensorStationRepository(Protocol):
    def create(self, sensor_station: SensorStation) -> SensorStation:
        raise NotImplementedError

    def get_by_id_for_owner(
        self,
        sensor_id: str,
        owner_id: str,
        *,
        include_deleted: bool = False,
    ) -> SensorStation | None:
        raise NotImplementedError

    def list_by_owner(
        self,
        owner_id: str,
        *,
        page: int,
        limit: int,
        status: str | None = None,
    ) -> PageResult[SensorStation]:
        raise NotImplementedError

    def update(self, sensor_station: SensorStation) -> SensorStation:
        raise NotImplementedError

    def soft_delete(self, sensor_station: SensorStation) -> SensorStation:
        raise NotImplementedError
