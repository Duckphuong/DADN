from datetime import datetime

from flask import Blueprint, jsonify, request

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
from app.services.solution_ai_service import SolutionAIService
from app.infrastructure.external.weather_service import get_weather_data

prediction_bp = Blueprint('prediction', __name__, url_prefix="/prediction")

ai_service = AIModelService()
sensor_health = SensorHealthService()
solution_service = SolutionAIService()


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
    data = request.get_json()

    sensor_id = data.get("sensorId") or data.get("idSensor")

    if sensor_id:
        status = sensor_health.check_and_update(sensor_id, data)

        if status == "ERROR":
            return jsonify({
                "error": "Invalid sensor data (all values = 0)"
            }), 400

    result = ai_service.predict(data)

    # =======================================================
    # SOLUTION AI - TÍCH HỢP GIẢI PHÁP TỪ GEMINI
    # =======================================================
    try:
        # Lấy thời tiết (Mặc định tọa độ HCM) - TỐT NHẤT NÊN LẤY THEO KINH ĐỘ VÀ VĨ ĐỘ CỦA SENSOR
        weather_info = get_weather_data(10.8231, 106.6297)
        
        # Sinh giải pháp
        final_solution = solution_service.generate_advanced_solution(
            sensor_data=data,
            ai_prediction_result=result,
            weather_data=weather_info
        )
        
        result['solution'] = final_solution 
        result['weather_forecast'] = weather_info
        
    except Exception as e:
        print(f"Lỗi phần Solution AI: {e}")
        result['solution'] = "Hệ thống đang phân tích dữ liệu..."

    # =======================================================
    # SOLUTION AI - TÍCH HỢP GIẢI PHÁP TỪ GEMINI
    # =======================================================

    try:
        data = validate_predict_request(request.get_json(silent=True))
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400
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
def get_history():
    try:
        db = get_mongo_database()
        if db is None:
            return jsonify({"error": "MongoDB not connected"}), 500
        coll = db.get_collection("predictions")
        cursor = coll.find().sort("created_at", -1).limit(50)
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


def _run_prediction_request(data: dict, *, created_at: datetime):
    sensor_id = data.get("sensorId") or data.get("idSensor")

    if sensor_id:
        status = sensor_health.check_and_update(sensor_id, data)

        if status == "ERROR":
            return jsonify({
                "error": "Invalid sensor data (all values = 0)"
            }), 400

    result = ai_service.predict(data)
    _save_prediction(data, result, created_at=created_at)
    return jsonify(result)


def _save_prediction(data: dict, result: dict, *, created_at: datetime) -> None:
    normalized_created_at = ensure_utc_datetime(created_at)
    raw_sensor_id = data.get("sensorId") or data.get("idSensor")
    sensor_reference = normalize_object_id_reference(raw_sensor_id)

    try:
        db = get_mongo_database()
        if db is None:
            return

        coll = db.get_collection("predictions")
        doc = {
            "Temp": float(data.get("Temp", 0)),
            "Turbidity": float(data.get("Turbidity", 0)),
            "DO": float(data.get("DO", 0)),
            "BOD": float(data.get("BOD", 0)),
            "CO2": float(data.get("CO2", 0)),
            "pH": float(data.get("pH", 0)),
            "Alkalinity": float(data.get("Alkalinity", 0)),
            "Hardness": float(data.get("Hardness", 0)),
            "Calcium": float(data.get("Calcium", 0)),
            "Ammonia": float(data.get("Ammonia", 0)),
            "Nitrite": float(data.get("Nitrite", 0)),
            "Phosphorus": float(data.get("Phosphorus", 0)),
            "H2S": float(data.get("H2S", 0)),
            "Plankton": float(data.get("Plankton", 0)),
            "prediction": result,
            "created_at": normalized_created_at,
        }
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
            message=f"WQI: {wqi_score}, Risk: {risk_status}",
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
