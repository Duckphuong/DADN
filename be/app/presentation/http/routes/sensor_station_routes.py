from flask import Blueprint, g, jsonify, request

from app.application.common.exceptions import ApplicationError
from app.presentation.http.dependencies import get_container
from app.presentation.http.errors import map_application_error
from app.presentation.http.middleware.auth_middleware import jwt_required
from app.presentation.http.serializers.sensor_station_serializers import (
    serialize_sensor_station_list_response,
    serialize_sensor_station_response,
)
from app.presentation.http.validators.sensor_station_validators import (
    validate_create_sensor_station_request,
    validate_delete_sensor_station_request,
    validate_get_sensor_station_request,
    validate_list_sensor_stations_request,
    validate_update_sensor_station_request,
)


sensor_station_bp = Blueprint("sensor_station", __name__, url_prefix="/api/sensors")


@sensor_station_bp.post("")
@jwt_required
def create_sensor():
    try:
        command = validate_create_sensor_station_request(
            request.get_json(silent=True) or {},
            owner_id=g.current_user.id or "",
        )
        sensor_station = get_container().create_sensor_station_use_case.execute(command)
        return jsonify(
            serialize_sensor_station_response(
                "Sensor station created successfully",
                sensor_station,
            )
        ), 201
    except ApplicationError as exc:
        payload, status_code = map_application_error(exc)
        return jsonify(payload), status_code


@sensor_station_bp.get("")
@jwt_required
def list_sensors():
    try:
        query = validate_list_sensor_stations_request(
            owner_id=g.current_user.id or "",
            page=request.args.get("page", 1),
            limit=request.args.get("limit", 10),
            status=request.args.get("status"),
        )
        page_result = get_container().list_sensor_stations_use_case.execute(query)
        return jsonify(serialize_sensor_station_list_response(page_result)), 200
    except ApplicationError as exc:
        payload, status_code = map_application_error(exc)
        return jsonify(payload), status_code


@sensor_station_bp.get("/<sensor_id>")
@jwt_required
def get_sensor(sensor_id):
    try:
        query = validate_get_sensor_station_request(
            owner_id=g.current_user.id or "",
            sensor_id=sensor_id,
        )
        sensor_station = get_container().get_sensor_station_use_case.execute(query)
        return jsonify(
            serialize_sensor_station_response(
                "Sensor station fetched successfully",
                sensor_station,
            )
        ), 200
    except ApplicationError as exc:
        payload, status_code = map_application_error(exc)
        return jsonify(payload), status_code


@sensor_station_bp.patch("/<sensor_id>")
@jwt_required
def update_sensor(sensor_id):
    try:
        command = validate_update_sensor_station_request(
            request.get_json(silent=True) or {},
            owner_id=g.current_user.id or "",
            sensor_id=sensor_id,
        )
        sensor_station = get_container().update_sensor_station_use_case.execute(command)
        return jsonify(
            serialize_sensor_station_response(
                "Sensor station updated successfully",
                sensor_station,
            )
        ), 200
    except ApplicationError as exc:
        payload, status_code = map_application_error(exc)
        return jsonify(payload), status_code


@sensor_station_bp.delete("/<sensor_id>")
@jwt_required
def delete_sensor(sensor_id):
    try:
        command = validate_delete_sensor_station_request(
            owner_id=g.current_user.id or "",
            sensor_id=sensor_id,
        )
        sensor_station = get_container().delete_sensor_station_use_case.execute(command)
        return jsonify(
            serialize_sensor_station_response(
                "Sensor station deleted successfully",
                sensor_station,
            )
        ), 200
    except ApplicationError as exc:
        payload, status_code = map_application_error(exc)
        return jsonify(payload), status_code
