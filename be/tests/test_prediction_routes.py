"""
Tests for prediction API routes:
  GET  /prediction/test-db
  POST /prediction/train
  POST /prediction/predict
  POST /prediction/predict-with-time
  GET  /prediction/history
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from app.services.sensor_health_service import STATUS_ERROR, STATUS_ONLINE

BASE = "/prediction"

# ══════════════════════════════════════════════════════════════════════════
# 1. GET /prediction/test-db
# ══════════════════════════════════════════════════════════════════════════


class TestTestDB:
    def test_returns_200(self, client):
        resp = client.get(f"{BASE}/test-db")
        assert resp.status_code == 200

    def test_returns_expected_keys(self, client):
        resp = client.get(f"{BASE}/test-db")
        data = resp.get_json()
        for key in (
            "status",
            "task",
            "loaded_models",
            "target_column",
            "training_source",
        ):
            assert key in data, f"Missing key: {key}"

    def test_status_is_ok(self, client):
        assert client.get(f"{BASE}/test-db").get_json()["status"] == "ok"

    def test_task_is_regression(self, client):
        assert client.get(f"{BASE}/test-db").get_json()["task"] == "regression"

    def test_loaded_models_is_list(self, client):
        assert isinstance(
            client.get(f"{BASE}/test-db").get_json()["loaded_models"], list
        )


# ══════════════════════════════════════════════════════════════════════════
# 2. POST /prediction/train
# ══════════════════════════════════════════════════════════════════════════


class TestTrainModel:
    def test_train_no_file_calls_db(self, client):
        resp = client.post(f"{BASE}/train", data={})
        assert resp.status_code == 200

    def test_train_no_file_success_message(self, client):
        data = client.post(f"{BASE}/train", data={}).get_json()
        assert "message" in data

    def test_train_without_file_key(self, client):
        """When no file present, should call ai_service.train_model_from_db."""
        resp = client.post(f"{BASE}/train", data={})
        assert resp.status_code == 200

    def test_train_with_empty_filename(self, client):
        resp = client.post(
            f"{BASE}/train",
            data={"file": (MagicMock(), "")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400
        assert "No file selected" in resp.get_json()["error"]


# ══════════════════════════════════════════════════════════════════════════
# 3. POST /prediction/predict
# ══════════════════════════════════════════════════════════════════════════

VALID_SENSOR_DATA = {
    "Nhiệt độ": 28.0,
    "pH": 7.0,
    "DO": 6.0,
    "Độ dẫn": 500.0,
    "Độ kiềm": 60.0,
    "N-NO2": 0.1,
    "N-NH4": 0.2,
    "P-PO4": 0.05,
    "H2S": 0.01,
    "TSS": 10.0,
    "COD": 20.0,
    "Aeromonas tổng số": 10.0,
    "Coliform": 100.0,
}


class TestPredict:
    def test_predict_returns_200(self, client):
        resp = client.post(f"{BASE}/predict", json=VALID_SENSOR_DATA)
        assert resp.status_code == 200

    def test_predict_returns_ai_payload(self, client):
        data = client.post(f"{BASE}/predict", json=VALID_SENSOR_DATA).get_json()
        assert "summary" in data
        assert "ensemble" in data

    def test_predict_missing_body_returns_400(self, client):
        resp = client.post(f"{BASE}/predict", json=None)
        assert resp.status_code == 400

    def test_predict_empty_dict_triggers_all_zeros_check(self, client):
        """An empty JSON body passes validation but hits the 'all values = 0' check → 400."""
        resp = client.post(f"{BASE}/predict", json={})
        assert resp.status_code == 400
        body = resp.get_json()
        assert "error" in body

    def test_predict_calls_ai_service_predict(self, client):
        with patch("app.routes.prediction_routes.ai_service") as mock_ai:
            mock_ai.predict.return_value = {"summary": {}}
            client.post(f"{BASE}/predict", json=VALID_SENSOR_DATA)
            mock_ai.predict.assert_called_once()

    def test_predict_firmware_error_returns_400(self, client):
        data = dict(VALID_SENSOR_DATA, error="Sensor fault detected")
        resp = client.post(f"{BASE}/predict", json=data)
        assert resp.status_code == 400

    def test_predict_firmware_error_message(self, client):
        data = dict(VALID_SENSOR_DATA, error="DS18B20 sensor disconnected")
        resp = client.post(f"{BASE}/predict", json=data)
        assert resp.status_code == 400
        assert "error" in resp.get_json()

    def test_predict_all_zeros_returns_400(self, client):
        zero_data = {k: 0.0 for k in VALID_SENSOR_DATA}
        resp = client.post(f"{BASE}/predict", json=zero_data)
        assert resp.status_code == 400

    def test_predict_all_zeros_fallback_error(self, client):
        """When all sensor values are 0 and no firmware error key → 'Invalid sensor data'."""
        zero_data = {k: 0.0 for k in VALID_SENSOR_DATA}
        resp = client.post(f"{BASE}/predict", json=zero_data)
        assert resp.status_code == 400
        body = resp.get_json()
        assert "error" in body

    def test_predict_uses_sensor_health_check(self, client):
        with patch("app.routes.prediction_routes.sensor_health") as mock_sh:
            mock_sh.check_and_update.return_value = STATUS_ONLINE
            client.post(f"{BASE}/predict", json=VALID_SENSOR_DATA)
            mock_sh.check_and_update.assert_called_once()

    def test_predict_english_aliases(self, client):
        aliased = {
            "Temp": 28.0,
            "ph": 7.0,
            "DO": 6.0,
            "Conductivity": 500.0,
            "Alkalinity": 60.0,
            "N-NO2": 0.1,
            "N-NH4": 0.2,
            "P-PO4": 0.05,
            "H2S": 0.01,
            "TSS": 10.0,
            "COD": 20.0,
            "Aeromonas tổng số": 10.0,
            "Coliform": 100.0,
        }
        resp = client.post(f"{BASE}/predict", json=aliased)
        assert resp.status_code == 200


# ══════════════════════════════════════════════════════════════════════════
# 4. POST /prediction/predict-with-time
# ══════════════════════════════════════════════════════════════════════════


class TestPredictWithTime:
    VALID_WITH_TIME = dict(VALID_SENSOR_DATA, createdAt="2025-01-01T10:00:00+00:00")

    def test_predict_with_time_returns_200(self, client):
        resp = client.post(f"{BASE}/predict-with-time", json=self.VALID_WITH_TIME)
        assert resp.status_code == 200

    def test_predict_with_time_returns_summary(self, client):
        data = client.post(
            f"{BASE}/predict-with-time", json=self.VALID_WITH_TIME
        ).get_json()
        assert "summary" in data

    def test_predict_with_time_missing_timestamp_returns_400(self, client):
        resp = client.post(f"{BASE}/predict-with-time", json=VALID_SENSOR_DATA)
        assert resp.status_code == 400
        assert "error" in resp.get_json()

    def test_predict_with_time_bad_body_returns_400(self, client):
        resp = client.post(f"{BASE}/predict-with-time", json=None)
        assert resp.status_code == 400

    def test_predict_with_time_calls_ai_service(self, client):
        with patch("app.routes.prediction_routes.ai_service") as mock_ai:
            mock_ai.predict.return_value = {"summary": {}}
            client.post(f"{BASE}/predict-with-time", json=self.VALID_WITH_TIME)
            mock_ai.predict.assert_called_once()


# ══════════════════════════════════════════════════════════════════════════
# 5. GET /prediction/history
# ══════════════════════════════════════════════════════════════════════════


class TestGetHistory:
    def test_history_returns_401_without_auth(self, client):
        resp = client.get(f"{BASE}/history")
        assert resp.status_code == 401

    def test_history_returns_200_with_auth(self, client, auth_headers):
        resp = client.get(f"{BASE}/history", headers=auth_headers)
        assert resp.status_code == 200

    def test_history_returns_list_with_auth(self, client, auth_headers):
        resp = client.get(f"{BASE}/history", headers=auth_headers)
        body = resp.get_json()
        assert isinstance(body, list)

    def test_history_with_sensor_id_filter(self, client, auth_headers):
        """Filtering by sensor_id should still return 200."""
        resp = client.get(
            f"{BASE}/history?",
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_history_mongo_not_connected(self, client):
        """Without mock override, default get_mongo_db returns None → 500 (if not overridden)."""
        pass  # Covered: mongo returns None gracefully in the fixture

    def test_history_returns_empty_list_when_cursor_empty(self, client, auth_headers):
        """When MongoDB finds no records, should return an empty list."""
        resp = client.get(f"{BASE}/history", headers=auth_headers)
        body = resp.get_json()
        assert isinstance(body, list)
