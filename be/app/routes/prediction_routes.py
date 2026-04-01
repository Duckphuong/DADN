from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
from datetime import datetime

from app.infrastructure.persistence.mongo.connection import get_mongo_database
from app.services.ai_model_service import AIModelService
from app.domain.prediction.predict_module import PredictModule

prediction_bp = Blueprint('prediction', __name__, url_prefix="/prediction")

ai_service = AIModelService()

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
    if not data:
        return jsonify({"error": "No data provided"}), 400
    result = ai_service.predict(data)

    try:
        db = get_mongo_database()
        if db is not None:
            # Create PredictModule
            predict_module = PredictModule.create_new(
                wqi_score=result["wqi"]["score"],
                contamination_risk=result["contamination_risk"]["status"],
                forecast_24h=result["forecast_24h"]["trend"],
                predicted_wqi=f"{result['forecast_24h']['predicted_wqi_range'][0]}-{result['forecast_24h']['predicted_wqi_range'][1]}",
                confidence=result["forecast_24h"]["confidence_score"],
                message=f"WQI: {result['wqi']['score']}, Risk: {result['contamination_risk']['status']}",
                input_sensor_id="temp",  # placeholder
                id_sensor="sensor1",  # placeholder
            )
            coll = db.get_collection("predictModule")
            doc = {
                "wqi_score": predict_module.wqi_score,
                "contamination_risk": predict_module.contamination_risk,
                "forecast_24h": predict_module.forecast_24h,
                "predicted_wqi": predict_module.predicted_wqi,
                "confidence": predict_module.confidence,
                "message": predict_module.message,
                "status": predict_module.status,
                "time_ago": predict_module.time_ago,
                "inputSensorId": predict_module.input_sensor_id,
                "idSensor": predict_module.id_sensor,
                "is_email_processed": predict_module.is_email_processed,
                "created_at": predict_module.created_at,
                "updated_at": predict_module.updated_at,
            }
            coll.insert_one(doc)
    except Exception as e:
        print(f"Error saving prediction: {e}")

    return jsonify(result)

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