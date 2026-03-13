from flask import Blueprint, jsonify, request

from app.services.sensor_service import SensorService


sensor_bp = Blueprint("sensor", __name__, url_prefix="/sensor")


@sensor_bp.post("/data")
def receive_sensor_data():
    payload = request.get_json(silent=True) or {}
    response, status_code = SensorService.process_sensor_data(payload)
    return jsonify(response), status_code