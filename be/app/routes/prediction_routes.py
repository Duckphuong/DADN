from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os

from app.database.db import db
from app.models.input_model import InputModel, OutputModel
from app.services.ai_model_service import AIModelService

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
        record = OutputModel(
            Temp=float(data.get("Temp", 0)),
            Turbidity=float(data.get("Turbidity", 0)),
            DO=float(data.get("DO", 0)),
            BOD=float(data.get("BOD", 0)),
            CO2=float(data.get("CO2", 0)),
            pH=float(data.get("pH", 0)),
            Alkalinity=float(data.get("Alkalinity", 0)),
            Hardness=float(data.get("Hardness", 0)),
            Calcium=float(data.get("Calcium", 0)),
            Ammonia=float(data.get("Ammonia", 0)),
            Nitrite=float(data.get("Nitrite", 0)),
            Phosphorus=float(data.get("Phosphorus", 0)),
            H2S=float(data.get("H2S", 0)),
            Plankton=float(data.get("Plankton", 0)),
            quality_label=result.get("quality_label"),
            quality_name=result.get("quality_name"),
            solution=result.get("solution"),
        )
        db.session.add(record)
        db.session.commit()
    except Exception:
        pass

    return jsonify(result)

@prediction_bp.route('/history', methods=['GET'])
def get_history():
    try:
        records = OutputModel.query.order_by(OutputModel.created_at.desc()).limit(50).all()
        history = [record.to_dict() for record in records]
        return jsonify(history)
    except Exception as e:
        return jsonify({"error": str(e)}), 500