from app.database.db import db
from app.models.sensor_model import SensorData
from app.services.ai_client import AIClient, AIClientError
from app.services.alert_service import AlertService, AlertServiceError


class SensorService:
    @staticmethod
    def process_sensor_data(payload):
        device_id = (payload.get("device_id") or "").strip()
        raw_value = payload.get("x")

        if not device_id:
            return {"error": "device_id is required"}, 400
        if raw_value is None:
            return {"error": "x is required"}, 400

        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            return {"error": "x must be a number"}, 400

        try:
            ai_result = AIClient.predict(value)
        except AIClientError as exc:
            return {"error": str(exc)}, 502

        status = ai_result.get("status")
        predicted_value = ai_result.get("value", value)

        if status not in {"NORMAL", "WARNING"}:
            return {"error": "AI service returned an unsupported status"}, 502

        try:
            normalized_value = float(predicted_value)
        except (TypeError, ValueError):
            return {"error": "AI service returned an invalid value"}, 502

        if status == "NORMAL":
            sensor_data = SensorData(
                device_id=device_id,
                value=normalized_value,
                status=status,
            )
            db.session.add(sensor_data)
            db.session.commit()
            return {
                "message": "Sensor data saved successfully",
                "data": sensor_data.to_dict(),
            }, 201

        try:
            AlertService.send_warning_email(device_id=device_id, value=normalized_value)
        except AlertServiceError as exc:
            return {
                "error": str(exc),
                "data": {
                    "device_id": device_id,
                    "value": SensorService._serialize_value(normalized_value),
                    "status": status,
                },
            }, 502

        return {
            "message": "Warning detected. Alert email sent successfully",
            "data": {
                "device_id": device_id,
                "value": SensorService._serialize_value(normalized_value),
                "status": status,
                "alert_sent": True,
            },
        }, 200

    @staticmethod
    def _serialize_value(value):
        return int(value) if float(value).is_integer() else value