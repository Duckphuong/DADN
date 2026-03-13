from app.services.ai_model_service import AIModelService


class AIClientError(Exception):
    pass


class AIClient:
    @staticmethod
    def predict(sensor_data):
        try:
            ai_service = AIModelService()
            result = ai_service.predict(sensor_data)
            return result
        except Exception as exc:
            raise AIClientError("Failed to predict") from exc
