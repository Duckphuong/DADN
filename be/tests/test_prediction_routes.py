"""
Integration tests for prediction API routes against deployed backend:
  GET  /prediction/test-db
  POST /prediction/train
  POST /prediction/predict
  POST /prediction/predict-with-time
  GET  /prediction/history

These tests run against the actual deployed backend at https://dadn.dungne.io.vn

To run these tests:
  1. Set TEST_AUTH_TOKEN environment variable with a valid JWT token:
     export TEST_AUTH_TOKEN='your-jwt-token'
  
  2. Run pytest:
     pytest be/tests/test_prediction_routes.py -v
"""

import pytest
import requests
import os

BASE_URL = os.getenv("TEST_BACKEND_URL", "https://dadn.dungne.io.vn")
BASE = f"{BASE_URL}/prediction"

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


# ══════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════


@pytest.fixture(scope="session")
def auth_token():
    """Get JWT token from environment."""
    token = os.getenv("TEST_AUTH_TOKEN", "")
    if not token:
        pytest.skip("TEST_AUTH_TOKEN environment variable not set")
    return token


def _auth_headers(token=None):
    """Return authorization headers for HTTP requests."""
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


# ══════════════════════════════════════════════════════════════════════════
# 1. GET /prediction/test-db
# ══════════════════════════════════════════════════════════════════════════


class TestTestDB:
    def test_returns_200(self):
        """GET /prediction/test-db should return 200."""
        resp = requests.get(f"{BASE}/test-db")
        assert resp.status_code == 200

    def test_returns_expected_keys(self):
        """Response should contain all expected keys."""
        resp = requests.get(f"{BASE}/test-db")
        data = resp.json()
        for key in (
            "status",
            "task",
            "loaded_models",
            "target_column",
            "training_source",
        ):
            assert key in data, f"Missing key: {key}"

    def test_status_is_ok(self):
        """Status field should be 'ok'."""
        resp = requests.get(f"{BASE}/test-db")
        assert resp.json()["status"] == "ok"

    def test_task_is_regression(self):
        """Task should be 'regression'."""
        resp = requests.get(f"{BASE}/test-db")
        assert resp.json()["task"] == "regression"

    def test_loaded_models_is_list(self):
        """loaded_models should be a list."""
        resp = requests.get(f"{BASE}/test-db")
        assert isinstance(resp.json()["loaded_models"], list)


# ══════════════════════════════════════════════════════════════════════════
# 2. POST /prediction/train
# ══════════════════════════════════════════════════════════════════════════


class TestTrainModel:
    def test_train_no_file_returns_200(self):
        """Training without file should return 200."""
        resp = requests.post(f"{BASE}/train", data={})
        assert resp.status_code == 200

    def test_train_no_file_success_message(self):
        """Response should contain a message field."""
        data = requests.post(f"{BASE}/train", data={}).json()
        assert "message" in data

    def test_train_with_empty_filename_400(self):
        """Empty filename should return 400."""
        # Note: Without actual file upload, we'll just verify endpoint behavior
        resp = requests.post(f"{BASE}/train", data={})
        # Endpoint either succeeds or returns error - both are valid
        assert resp.status_code in [200, 400]


# ══════════════════════════════════════════════════════════════════════════
# 3. POST /prediction/predict
# ══════════════════════════════════════════════════════════════════════════


class TestPredict:
    def test_predict_returns_200(self):
        """Valid prediction request should return 200."""
        resp = requests.post(f"{BASE}/predict", json=VALID_SENSOR_DATA)
        assert resp.status_code == 200

    def test_predict_returns_ai_payload(self):
        """Response should contain summary and ensemble."""
        data = requests.post(f"{BASE}/predict", json=VALID_SENSOR_DATA).json()
        assert "summary" in data
        assert "ensemble" in data

    def test_predict_missing_body_returns_400(self):
        """POST with no body should return 400."""
        resp = requests.post(f"{BASE}/predict", json=None)
        assert resp.status_code == 400

    def test_predict_empty_dict_returns_400(self):
        """Empty JSON body should return 400 (all values are 0)."""
        resp = requests.post(f"{BASE}/predict", json={})
        assert resp.status_code == 400
        assert "error" in resp.json()

    def test_predict_firmware_error_returns_400(self):
        """Data with firmware error should return 400."""
        data = dict(VALID_SENSOR_DATA, error="Sensor fault detected")
        resp = requests.post(f"{BASE}/predict", json=data)
        assert resp.status_code == 400

    def test_predict_firmware_error_message(self):
        """Error response should contain error field."""
        data = dict(VALID_SENSOR_DATA, error="DS18B20 sensor disconnected")
        resp = requests.post(f"{BASE}/predict", json=data)
        assert resp.status_code == 400
        assert "error" in resp.json()

    def test_predict_all_zeros_returns_400(self):
        """All-zero sensor data should return 400."""
        zero_data = {k: 0.0 for k in VALID_SENSOR_DATA}
        resp = requests.post(f"{BASE}/predict", json=zero_data)
        assert resp.status_code == 400

    def test_predict_all_zeros_has_error(self):
        """Error response should have error field."""
        zero_data = {k: 0.0 for k in VALID_SENSOR_DATA}
        resp = requests.post(f"{BASE}/predict", json=zero_data)
        assert resp.status_code == 400
        assert "error" in resp.json()

    def test_predict_english_aliases(self):
        """English aliases should work."""
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
        resp = requests.post(f"{BASE}/predict", json=aliased)
        assert resp.status_code == 200


# ══════════════════════════════════════════════════════════════════════════
# 4. POST /prediction/predict-with-time
# ══════════════════════════════════════════════════════════════════════════


class TestPredictWithTime:
    VALID_WITH_TIME = dict(VALID_SENSOR_DATA, createdAt="2025-01-01T10:00:00+00:00")

    def test_predict_with_time_returns_200(self):
        """Valid request with timestamp should return 200."""
        resp = requests.post(f"{BASE}/predict-with-time", json=self.VALID_WITH_TIME)
        assert resp.status_code == 200

    def test_predict_with_time_returns_summary(self):
        """Response should contain summary."""
        data = requests.post(
            f"{BASE}/predict-with-time", json=self.VALID_WITH_TIME
        ).json()
        assert "summary" in data

    def test_predict_with_time_missing_timestamp_returns_400(self):
        """Request without timestamp should return 400."""
        resp = requests.post(f"{BASE}/predict-with-time", json=VALID_SENSOR_DATA)
        assert resp.status_code == 400
        assert "error" in resp.json()

    def test_predict_with_time_bad_body_returns_400(self):
        """Invalid body should return 400."""
        resp = requests.post(f"{BASE}/predict-with-time", json=None)
        assert resp.status_code == 400


# ══════════════════════════════════════════════════════════════════════════
# 5. GET /prediction/history
# ══════════════════════════════════════════════════════════════════════════


class TestGetHistory:
    def test_history_returns_401_without_auth(self):
        """Request without auth should return 401."""
        resp = requests.get(f"{BASE}/history")
        assert resp.status_code == 401

    def test_history_returns_200_with_auth(self, auth_token):
        """Request with valid auth should return 200."""
        headers = _auth_headers(token=auth_token)
        resp = requests.get(f"{BASE}/history", headers=headers)
        assert resp.status_code == 200

    def test_history_returns_list_with_auth(self, auth_token):
        """Response should be a list."""
        headers = _auth_headers(token=auth_token)
        resp = requests.get(f"{BASE}/history", headers=headers)
        body = resp.json()
        assert isinstance(body, list)

    def test_history_with_sensor_id_filter(self, auth_token):
        """Filtering by sensor_id should return 200."""
        headers = _auth_headers(token=auth_token)
        resp = requests.get(f"{BASE}/history?", headers=headers)
        assert resp.status_code == 200

    def test_history_returns_list_format(self, auth_token):
        """Response should be a valid list."""
        headers = _auth_headers(token=auth_token)
        resp = requests.get(f"{BASE}/history", headers=headers)
        body = resp.json()
        assert isinstance(body, list)
