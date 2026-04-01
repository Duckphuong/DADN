from flask import Blueprint, jsonify, request

from app.application.common.exceptions import ApplicationError
from app.presentation.http.dependencies import get_container
from app.presentation.http.errors import map_application_error
from app.presentation.http.serializers.sensor_data_serializers import (
    serialize_classification,
    serialize_latest_sensor,
)
from app.application.sensor_station.sensor_data_commands import (
    GetLatestSensorDataQuery,
    GetSensorClassificationQuery,
)


sensor_data_bp = Blueprint("sensor_data", __name__, url_prefix="/api/v1/sensors")


@sensor_data_bp.get("/latest")
def get_latest_sensor():
    """
    GET /api/v1/sensors/latest?sensor_id=<optional>

    Trả về toàn bộ chỉ số cảm biến mới nhất.
    FE dùng để render SensorCard và AIPredictionPanel.
    """
    try:
        query = GetLatestSensorDataQuery(
            sensor_id=request.args.get("sensor_id")
        )
        doc = get_container().get_latest_sensor_data_use_case.execute(query)
        return jsonify(serialize_latest_sensor(doc)), 200
    except ApplicationError as exc:
        payload, status_code = map_application_error(exc)
        return jsonify(payload), status_code


@sensor_data_bp.get("/classification")
def get_sensor_classification():
    """
    GET /api/v1/sensors/classification?sensor_id=<optional>

    Trả về phân loại nước: Hard/Soft Water, Salinity, Alkalinity, Temperature.
    FE dùng để render WaterClassificationPanel.
    """
    try:
        query = GetSensorClassificationQuery(
            sensor_id=request.args.get("sensor_id")
        )
        result = get_container().get_sensor_classification_use_case.execute(query)
        return jsonify(serialize_classification(result)), 200
    except ApplicationError as exc:
        payload, status_code = map_application_error(exc)
        return jsonify(payload), status_code