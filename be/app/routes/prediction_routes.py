from datetime import datetime

from flask import Blueprint, g, jsonify, request

from app.application.common.exceptions import ValidationError
from app.domain.shared.time import ensure_utc_datetime, utc_now
from app.infrastructure.persistence.mongo.connection import get_mongo_database
from app.infrastructure.persistence.mongo.object_id import normalize_object_id_reference
from app.presentation.http.validators.prediction_validators import (
    validate_predict_request,
    validate_predict_request_with_time,
)
from app.domain.prediction import PredictModule
from app.services.ai_model_service import AIModelService
from app.services.sensor_health_service import SensorHealthService
from app.presentation.http.middleware.auth_middleware import jwt_required
from app.infrastructure.persistence.mongo.object_id import parse_object_id

prediction_bp = Blueprint('prediction', __name__, url_prefix="/prediction")

ai_service = AIModelService()
sensor_health = SensorHealthService()


@prediction_bp.route('/test-db', methods=['GET'])
def test_db():
    result = ai_service.test_db()
    return jsonify(result)


@prediction_bp.route('/train', methods=['POST'])
def train_model():
    if 'file' not in request.files:
        result = ai_service.train_model_from_db()
    else:
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        result = ai_service.train_model_from_file(file)
    return jsonify(result)


@prediction_bp.route('/predict', methods=['POST'])
def predict():
    data = request.get_json(silent=True)

    try:
        data = validate_predict_request(data)
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400

    # sensor_id = data.get("sensorId") or data.get("idSensor")
    sensor_id = "69ea674c5d325453fddc1733"

    if sensor_id:
        status = sensor_health.check_and_update(sensor_id, data)

        if status == "ERROR":
            firmware_error = data.get("error")
            error_msg = firmware_error if firmware_error else "Invalid sensor data (all values = 0)"
            return jsonify({"error": error_msg}), 400

    return _run_prediction_request(data, created_at=utc_now())


@prediction_bp.route('/predict-with-time', methods=['POST'])
def predict_with_time():
    try:
        data, created_at = validate_predict_request_with_time(
            request.get_json(silent=True)
        )
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400
    return _run_prediction_request(data, created_at=created_at)


@prediction_bp.route('/history', methods=['GET'])
@jwt_required
def get_history():
    try:
        db = get_mongo_database()
        if db is None:
            return jsonify({"error": "MongoDB not connected"}), 500
        coll = db.get_collection("predictions")

        sensor_id_param = request.args.get("sensor_id") or request.args.get("sensorId")
        query: dict = {}

        if sensor_id_param:
            query["idSensor"] = _normalize_sensor_reference(sensor_id_param)
        else:
            sensor_collection = db.get_collection("sensor_informations")
            owner_id = g.current_user.id if getattr(g, "current_user", None) else None
            if owner_id:
                owner_query = {"userId": parse_object_id(owner_id, field_name="user id"), "isDeleted": False}
                sensor_ids = [
                    str(sensor.get("_id"))
                    for sensor in sensor_collection.find(owner_query, {"_id": 1})
                    if sensor.get("_id") is not None
                ]
                if sensor_ids:
                    query["idSensor"] = {"$in": [_normalize_sensor_reference(sensor_id) for sensor_id in sensor_ids]}

        cursor = coll.find(query).sort("created_at", -1).limit(50)
        history = []
        for d in cursor:
            item = d.copy()
            _id = item.pop("_id", None)
            if _id is not None:
                item["id"] = str(_id)
            if "idSensor" in item and item["idSensor"] is not None:
                item["idSensor"] = str(item["idSensor"])
            created = item.get("created_at")
            if created is not None:
                try:
                    item["created_at"] = created.isoformat()
                except Exception:
                    pass
            history.append(item)
        return jsonify(history)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _normalize_sensor_reference(sensor_id: str):
    normalized = parse_object_id(sensor_id, field_name="sensor id")
    return normalized if normalized is not None else sensor_id


def _run_prediction_request(data: dict, *, created_at: datetime):
    sensor_id = data.get("sensorId") or data.get("idSensor")

    if sensor_id:
        status = sensor_health.check_and_update(sensor_id, data)

        if status == "ERROR":
            firmware_error = data.get("error")
            error_msg = firmware_error if firmware_error else "Invalid sensor data (all values = 0)"
            return jsonify({"error": error_msg}), 400

    result = ai_service.predict(data)
    _save_prediction(data, result, created_at=created_at)
    return jsonify(result)


def _save_prediction(data: dict, result: dict, *, created_at: datetime) -> None:
    normalized_created_at = ensure_utc_datetime(created_at)
    raw_sensor_id = data.get("sensorId") or data.get("idSensor") or "69ea674c5d325453fddc1733"
    sensor_reference = normalize_object_id_reference(raw_sensor_id)

    dataset_fields = [
        "Nhiệt độ",
        "pH",
        "DO",
        "Độ dẫn",
        "Độ kiềm",
        "N-NO2",
        "N-NH4",
        "P-PO4",
        "H2S",
        "TSS",
        "COD",
        "Aeromonas tổng số",
        "Coliform",
    ]

    try:
        db = get_mongo_database()
        if db is None:
            return

        coll = db.get_collection("predictions")
        # Normalize field names to canonical Vietnamese names before saving
        normalized_data = ai_service.normalize_sensor_data(data)
        doc = {field: float(normalized_data.get(field, 0)) for field in dataset_fields}
        print(f"Normalized data for saving: {doc}")
        doc["prediction"] = result
        doc["created_at"] = normalized_created_at
        if sensor_reference is not None:
            doc["idSensor"] = sensor_reference
        insert_result = coll.insert_one(doc)
        saved_prediction_id = str(insert_result.inserted_id)

        summary = result["summary"]
        wqi_score = summary["wqi"]["score"]
        risk_status = summary["risk"]["status"]

        if wqi_score >= 50 and risk_status not in ["High Risk", "Critical"]:
            return

        actual_sensor_id = sensor_reference or "unknown"

        predict_module = PredictModule.create_new(
            wqi_score=wqi_score,
            contamination_risk=risk_status,
            forecast_24h=summary["forecast_24h"]["trend"],
            predicted_wqi=(
                f"{summary['forecast_24h']['predicted_wqi_range'][0]}-"
                f"{summary['forecast_24h']['predicted_wqi_range'][1]}"
            ),
            confidence=summary["forecast_24h"]["confidence_score"],
            message=f"WQI: {(wqi_score):.2f}, Risk: {risk_status}",
            input_sensor_id=saved_prediction_id,
            id_sensor=actual_sensor_id,
            timestamp=normalized_created_at,
        )

        predict_coll = db.get_collection("predict_module")
        predict_doc = {
            "wqi_score": predict_module.wqi_score,
            "contamination_risk": predict_module.contamination_risk,
            "forecast_24h": predict_module.forecast_24h,
            "predicted_wqi": predict_module.predicted_wqi,
            "confidence": predict_module.confidence,
            "message": predict_module.message,
            "status": predict_module.status,
            "time_ago": predict_module.time_ago,
            "input_sensor_id": predict_module.input_sensor_id,
            "id_sensor": predict_module.id_sensor,
            "is_email_processed": predict_module.is_email_processed,
            "created_at": predict_module.created_at,
            "updated_at": predict_module.updated_at,
        }
        predict_coll.insert_one(predict_doc)
    except Exception as e:
        print(f"Error saving prediction: {e}")
