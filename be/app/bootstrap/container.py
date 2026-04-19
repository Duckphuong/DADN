from dataclasses import dataclass
from app.application.sensor_station.sensor_data_use_cases import GetLatestSensorDataUseCase, GetSensorClassificationUseCase
from app.infrastructure.persistence.mongo.repositories.sensor_data_repository import MongoSensorDataRepository
from app.application.auth.use_cases import (
    AuthenticateUserUseCase,
    DeleteUserUseCase,
    GetUserUseCase,
    ListUsersUseCase,
    LoginUserUseCase,
    LogoutUserUseCase,
    RegisterUserUseCase,
    UpdateUserUseCase,
)
from app.application.sensor_station.use_cases import (
    CreateSensorStationUseCase,
    DeleteSensorStationUseCase,
    GetSensorStationUseCase,
    ListSensorStationsUseCase,
    UpdateSensorStationUseCase,
)
from app.infrastructure.persistence.mongo.connection import get_mongo_database
from app.infrastructure.persistence.mongo.repositories.sensor_station_repository import (
    MongoSensorStationRepository,
)
from app.infrastructure.persistence.mongo.repositories.user_repository import (
    MongoUserRepository,
)
from app.infrastructure.security.bcrypt_password_hasher import BcryptPasswordHasher
from app.infrastructure.security.jwt_token_service import JwtTokenService


CONTAINER_EXTENSION_KEY = "application_container"


@dataclass(slots=True)
class ApplicationContainer:
    register_user_use_case: RegisterUserUseCase
    login_user_use_case: LoginUserUseCase
    logout_user_use_case: LogoutUserUseCase
    authenticate_user_use_case: AuthenticateUserUseCase
    list_users_use_case: ListUsersUseCase
    get_user_use_case: GetUserUseCase
    update_user_use_case: UpdateUserUseCase
    delete_user_use_case: DeleteUserUseCase
    create_sensor_station_use_case: CreateSensorStationUseCase
    list_sensor_stations_use_case: ListSensorStationsUseCase
    get_sensor_station_use_case: GetSensorStationUseCase
    update_sensor_station_use_case: UpdateSensorStationUseCase
    delete_sensor_station_use_case: DeleteSensorStationUseCase
    get_latest_sensor_data_use_case: GetLatestSensorDataUseCase
    get_sensor_classification_use_case: GetSensorClassificationUseCase

def build_container(config) -> ApplicationContainer:
    user_repository = MongoUserRepository(get_mongo_database)
    sensor_station_repository = MongoSensorStationRepository(get_mongo_database)
    password_hasher = BcryptPasswordHasher()
    sensor_data_repository = MongoSensorDataRepository(get_mongo_database)
    token_service = JwtTokenService(
        secret_key=config["JWT_SECRET_KEY"],
        expires_in_minutes=config["JWT_ACCESS_TOKEN_EXPIRES_MINUTES"],
    )

    return ApplicationContainer(
        get_latest_sensor_data_use_case=GetLatestSensorDataUseCase(sensor_data_repository),
        get_sensor_classification_use_case=GetSensorClassificationUseCase(sensor_data_repository),
        register_user_use_case=RegisterUserUseCase(user_repository, password_hasher),
        login_user_use_case=LoginUserUseCase(
            user_repository,
            password_hasher,
            token_service,
        ),
        logout_user_use_case=LogoutUserUseCase(),
        authenticate_user_use_case=AuthenticateUserUseCase(
            token_service,
            user_repository,
        ),
        list_users_use_case=ListUsersUseCase(user_repository),
        get_user_use_case=GetUserUseCase(user_repository),
        update_user_use_case=UpdateUserUseCase(user_repository),
        delete_user_use_case=DeleteUserUseCase(user_repository),
        create_sensor_station_use_case=CreateSensorStationUseCase(
            sensor_station_repository
        ),
        list_sensor_stations_use_case=ListSensorStationsUseCase(
            sensor_station_repository
        ),
        get_sensor_station_use_case=GetSensorStationUseCase(sensor_station_repository),
        update_sensor_station_use_case=UpdateSensorStationUseCase(
            sensor_station_repository
        ),
        delete_sensor_station_use_case=DeleteSensorStationUseCase(
            sensor_station_repository
        ),
    )
