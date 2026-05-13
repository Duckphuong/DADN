from app.application.common.exceptions import NotFoundError, ValidationError
from app.application.common.models import PageResult
from app.application.sensor_station.commands import (
    CreateSensorStationCommand,
    DeleteSensorStationCommand,
    GetSensorStationQuery,
    ListSensorStationsQuery,
    UpdateSensorStationCommand,
)
from app.application.sensor_station.interfaces import SensorStationRepository
from app.domain.exceptions import DomainValidationError
from app.domain.sensor_station.sensor_station import SensorStation


class CreateSensorStationUseCase:
    def __init__(self, sensor_station_repository: SensorStationRepository) -> None:
        self._sensor_station_repository = sensor_station_repository

    def execute(self, command: CreateSensorStationCommand) -> SensorStation:
        try:
            sensor_station = SensorStation.create_new(
                sensor_name=command.sensor_name,
                owner_id=command.owner_id,
                longitude=command.longitude,
                latitude=command.latitude,
                status=command.status,
            )
        except DomainValidationError as exc:
            raise ValidationError(str(exc)) from exc

        return self._sensor_station_repository.create(sensor_station)


class ListSensorStationsUseCase:
    def __init__(self, sensor_station_repository: SensorStationRepository) -> None:
        self._sensor_station_repository = sensor_station_repository

    def execute(
        self,
        query: ListSensorStationsQuery,
    ) -> PageResult[SensorStation]:
        if query.page < 1:
            raise ValidationError("page must be a positive integer")
        if query.limit < 1:
            raise ValidationError("limit must be a positive integer")

        normalized_status = None
        if query.status is not None:
            try:
                normalized_status = SensorStation.normalize_status(query.status)
            except DomainValidationError as exc:
                raise ValidationError(str(exc)) from exc

        return self._sensor_station_repository.list_by_owner(
            query.owner_id,
            page=query.page,
            limit=min(query.limit, 100),
            status=normalized_status,
        )


class GetSensorStationUseCase:
    def __init__(self, sensor_station_repository: SensorStationRepository) -> None:
        self._sensor_station_repository = sensor_station_repository

    def execute(self, query: GetSensorStationQuery) -> SensorStation:
        sensor_station = self._sensor_station_repository.get_by_id_for_owner(
            query.sensor_id,
            query.owner_id,
        )
        if sensor_station is None:
            raise NotFoundError("Sensor station not found")
        return sensor_station


class UpdateSensorStationUseCase:
    def __init__(self, sensor_station_repository: SensorStationRepository) -> None:
        self._sensor_station_repository = sensor_station_repository

    def execute(self, command: UpdateSensorStationCommand) -> SensorStation:
        sensor_station = self._sensor_station_repository.get_by_id_for_owner(
            command.sensor_id,
            command.owner_id,
        )
        if sensor_station is None:
            raise NotFoundError("Sensor station not found")

        if (
            command.sensor_name is None
            and command.longitude is None
            and command.latitude is None
            and command.status is None
        ):
            raise ValidationError("No valid fields provided for update")

        try:
            sensor_station.update(
                sensor_name=command.sensor_name,
                longitude=command.longitude,
                latitude=command.latitude,
                status=command.status,
            )
        except DomainValidationError as exc:
            raise ValidationError(str(exc)) from exc

        return self._sensor_station_repository.update(sensor_station)


class DeleteSensorStationUseCase:
    def __init__(self, sensor_station_repository: SensorStationRepository) -> None:
        self._sensor_station_repository = sensor_station_repository

    def execute(self, command: DeleteSensorStationCommand) -> SensorStation:
        sensor_station = self._sensor_station_repository.get_by_id_for_owner(
            command.sensor_id,
            command.owner_id,
        )
        if sensor_station is None:
            raise NotFoundError("Sensor station not found")

        sensor_station.soft_delete()
        return self._sensor_station_repository.soft_delete(sensor_station)
