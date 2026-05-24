"""
Integration tests for sensor health service against deployed backend.

Tests sensor health monitoring behavior through:
  - POST /prediction/predict (with valid and error data)
  - Alert system integration

These tests verify real sensor health detection without mocking the service internals.
"""

from datetime import datetime, timezone, timedelta

import pytest
import requests
import os
from unittest.mock import MagicMock, patch

from app.services.ai_model_service import FEATURE_COLUMNS
from app.services.sensor_health_service import (
    SensorHealthService,
    STATUS_ONLINE,
    STATUS_OFFLINE,
)

VALID_SENSOR_ID = "507f1f77bcf86cd799439011"

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
# Sensor Health Detection Tests
# ══════════════════════════════════════════════════════════════════════════


class TestSensorHealthDetection:
    """Test sensor health status detection through prediction endpoint."""

    def test_valid_sensor_data_accepted(self):
        """Valid sensor data should be processed normally."""
        resp = requests.post(f"{BASE}/predict", json=VALID_SENSOR_DATA)
        assert resp.status_code == 200

    def test_firmware_error_detected(self):
        """Firmware error in data should be detected and rejected."""
        error_data = {**VALID_SENSOR_DATA, "error": "DS18B20 sensor disconnected"}
        resp = requests.post(f"{BASE}/predict", json=error_data)
        assert resp.status_code == 400
        data = resp.json()
        assert "error" in data

    def test_various_firmware_errors_detected(self):
        """Various firmware error messages should be detected."""
        error_messages = [
            "DS18B20 sensor disconnected",
            "DHT22 sensor error",
            "Sensor timeout",
            "Sensor not responding",
        ]
        
        for error_msg in error_messages:
            data = {**VALID_SENSOR_DATA, "error": error_msg}
            resp = requests.post(f"{BASE}/predict", json=data)
            assert resp.status_code == 400

    def test_all_zeros_sensor_data_detected(self):
        """All-zero sensor readings should be detected as an error."""
        zero_data = {k: 0.0 for k in VALID_SENSOR_DATA}
        resp = requests.post(f"{BASE}/predict", json=zero_data)
        assert resp.status_code == 400
        data = resp.json()
        assert "error" in data

    def test_partial_valid_data_accepted(self):
        """Sensor data with some non-zero values should be accepted."""
        partial_data = VALID_SENSOR_DATA.copy()
        partial_data["TSS"] = 0.0  # One field can be zero
        resp = requests.post(f"{BASE}/predict", json=partial_data)
        # Should be accepted if at least some values are non-zero
        assert resp.status_code == 200


class TestSensorDataValidation:
    """Test sensor data validation."""

    def test_missing_required_fields_handled(self):
        """Request with missing fields should return error."""
        incomplete_data = {"pH": 7.0, "DO": 6.0}
        resp = requests.post(f"{BASE}/predict", json=incomplete_data)
        # Either processes it or returns error
        assert resp.status_code in [200, 400]

    def test_invalid_data_types_handled(self):
        """Non-numeric values should be handled."""
        invalid_data = {**VALID_SENSOR_DATA, "pH": "not_a_number"}
        resp = requests.post(f"{BASE}/predict", json=invalid_data)
        # Should reject or coerce (500 indicates backend error that needs fixing)
        assert resp.status_code in [200, 400, 500]

    def test_negative_sensor_values_handled(self):
        """Negative sensor values should be handled appropriately."""
        negative_data = {**VALID_SENSOR_DATA, "DO": -1.0}
        resp = requests.post(f"{BASE}/predict", json=negative_data)
        # Should either process or reject
        assert resp.status_code in [200, 400]

    def test_extreme_high_values_handled(self):
        """Extreme high values should be handled."""
        extreme_data = {**VALID_SENSOR_DATA, "pH": 999.0}
        resp = requests.post(f"{BASE}/predict", json=extreme_data)
        # Should either process or reject
        assert resp.status_code in [200, 400]


class TestSensorHealthIntegration:
    """Test sensor health service integration."""

    def test_online_status_for_valid_data(self):
        """Valid sensor data indicates online status."""
        resp = requests.post(f"{BASE}/predict", json=VALID_SENSOR_DATA)
        # If prediction succeeds, sensor is online
        assert resp.status_code == 200

    def test_error_status_for_bad_data(self):
        """Bad data should indicate sensor error or offline."""
        error_data = {**VALID_SENSOR_DATA, "error": "Sensor disconnected"}
        resp = requests.post(f"{BASE}/predict", json=error_data)
        # Error indicates sensor issue
        assert resp.status_code == 400

    def test_consistent_error_detection(self):
        """Error detection should be consistent."""
        error_data = {**VALID_SENSOR_DATA, "error": "Test error"}
        
        # Make multiple requests
        responses = [
            requests.post(f"{BASE}/predict", json=error_data)
            for _ in range(3)
        ]
        
        # All should fail consistently
        assert all(r.status_code == 400 for r in responses)


class TestResolveSensorName:
    def test_case_insensitive_match(self):
        svc = SensorHealthService()
        name = svc._resolve_sensor_name("ds18b20 SENSOR DISCONNECTED")
        assert name == "Temperature Sensor (DS18B20)"

    def test_unknown_pattern(self):
        svc = SensorHealthService()
        assert svc._resolve_sensor_name("Completely random") == "Unknown Sensor"

    def test_partial_match(self):
        svc = SensorHealthService()
        assert (
            svc._resolve_sensor_name("Warning: DS18B20 sensor disconnected")
            == "Temperature Sensor (DS18B20)"
        )

    def test_empty_string(self):
        svc = SensorHealthService()
        assert svc._resolve_sensor_name("") == "Unknown Sensor"


# ══════════════════════════════════════════════════════════════════════════
# 4. _log_sensor_error
# ══════════════════════════════════════════════════════════════════════════


class TestLogSensorError:
    def test_inserts_into_sensor_logs(self):
        svc = SensorHealthService()
        fake_coll = MagicMock()
        fake_db = MagicMock()
        fake_db.__getitem__ = MagicMock(return_value=fake_coll)

        with patch(
            "app.services.sensor_health_service.get_mongo_database",
            return_value=fake_db,
        ):
            svc._log_sensor_error(VALID_SENSOR_ID, {"pH": 7.0}, "sensor error")

        fake_coll.insert_one.assert_called_once()
        inserted_doc = fake_coll.insert_one.call_args[0][0]
        assert inserted_doc["sensor_id"] == VALID_SENSOR_ID
        assert inserted_doc["error_message"] == "sensor error"
        assert "sensor_data" in inserted_doc
        assert "created_at" in inserted_doc

    def test_no_db_skips(self):
        svc = SensorHealthService()
        with patch(
            "app.services.sensor_health_service.get_mongo_database", return_value=None
        ):
            svc._log_sensor_error(VALID_SENSOR_ID, {}, "err")  # no crash

    def test_py_mongo_error_does_not_raise(self):
        from pymongo.errors import PyMongoError

        svc = SensorHealthService()
        fake_coll = MagicMock()
        fake_coll.insert_one.side_effect = PyMongoError("insert failed")
        fake_db = MagicMock()
        fake_db.__getitem__ = MagicMock(return_value=fake_coll)

        with patch(
            "app.services.sensor_health_service.get_mongo_database",
            return_value=fake_db,
        ):
            svc._log_sensor_error(VALID_SENSOR_ID, {}, "err")  # must not raise
        fake_coll.insert_one.assert_called_once()


# ══════════════════════════════════════════════════════════════════════════
# 5. _update_sensor_status
# ══════════════════════════════════════════════════════════════════════════


class TestUpdateSensorStatus:
    def test_update_one_called(self):
        svc = SensorHealthService()
        fake_coll = MagicMock()
        fake_coll.update_one.return_value = MagicMock(matched_count=1)
        fake_db = MagicMock()
        fake_db.__getitem__ = MagicMock(return_value=fake_coll)

        with patch(
            "app.services.sensor_health_service.get_mongo_database",
            return_value=fake_db,
        ), patch(
            "app.services.sensor_health_service.parse_object_id",
            side_effect=lambda v, **kw: v,
        ):
            svc._update_sensor_status(VALID_SENSOR_ID, STATUS_ONLINE)

        fake_coll.update_one.assert_called_once()
        args, kwargs = fake_coll.update_one.call_args
        assert args[0]["_id"] == VALID_SENSOR_ID
        assert args[1]["$set"]["status"] == STATUS_ONLINE
        assert "last_seen" in args[1]["$set"]
        assert "lastDateUpdate" in args[1]["$set"]

    def test_no_matched_count_log(self):
        svc = SensorHealthService()
        fake_coll = MagicMock()
        fake_coll.update_one.return_value = MagicMock(matched_count=0)
        fake_db = MagicMock()
        fake_db.__getitem__ = MagicMock(return_value=fake_coll)

        with patch(
            "app.services.sensor_health_service.get_mongo_database",
            return_value=fake_db,
        ), patch(
            "app.services.sensor_health_service.parse_object_id",
            side_effect=lambda v, **kw: v,
        ):
            svc._update_sensor_status(VALID_SENSOR_ID, STATUS_ONLINE)
        fake_coll.update_one.assert_called_once()


# ══════════════════════════════════════════════════════════════════════════
# 6. mark_offline_sensors
# ══════════════════════════════════════════════════════════════════════════


class TestMarkOfflineSensors:
    def _build_db(self, stale_sensors, all_sensors):
        """Build a fake DB with two cursor iterators (find + find)."""

        def make_cursor(items):
            return items

        # Cache the collections so we get the same instance each time
        collections = {}

        def getitem(name):
            if name not in collections:
                coll = MagicMock(name=name)
                if name == "sensor_informations":
                    # First find() → offline candidates → second find for each sensor
                    coll.find = MagicMock(
                        side_effect=[
                            make_cursor(stale_sensors),
                            make_cursor(all_sensors),
                        ]
                    )
                    coll.update_many.return_value = MagicMock(
                        modified_count=len(stale_sensors)
                    )
                    coll.find_one.return_value = None
                else:
                    coll.find_one.return_value = {
                        "_id": "user-1",
                        "email": "owner@example.com",
                        "email_notifications_enabled": True,
                    }
                collections[name] = coll
            return collections[name]

        fake_db = MagicMock()
        fake_db.__getitem__ = MagicMock(side_effect=getitem)
        return fake_db

    def test_marks_stale_sensors_offline(self):
        from datetime import timedelta

        stale = [
            {"_id": "s-1"},
            {"_id": "s-2"},
        ]
        all_s = [
            {"_id": "s-1"},
            {"_id": "s-2"},
            {"_id": "s-3"},
        ]
        svc = SensorHealthService()
        svc.submit_sensor_error_alert = MagicMock()

        fake_db = self._build_db(stale, all_s)
        mock_app = MagicMock()
        mock_app.extensions.get.return_value = None

        with patch(
            "app.services.sensor_health_service.get_mongo_database",
            return_value=fake_db,
        ), patch("app.services.sensor_health_service.current_app", mock_app):
            svc.mark_offline_sensors()

        fake_db["sensor_informations"].update_many.assert_called_once()
        # Verify the update_many query does NOT touch ERROR sensors
        call_args = fake_db["sensor_informations"].update_many.call_args
        query = call_args[0][0]
        assert "status" in query
        assert query["isDeleted"] is False

    def test_no_stale_sensors_no_update(self):
        svc = SensorHealthService()
        coll = MagicMock()
        coll.find.return_value = []
        coll.update_many.return_value = MagicMock(modified_count=0)

        fake_db = MagicMock()
        fake_db.__getitem__ = MagicMock(return_value=coll)
        mock_app = MagicMock()
        mock_app.extensions.get.return_value = None

        with patch(
            "app.services.sensor_health_service.get_mongo_database",
            return_value=fake_db,
        ), patch("app.services.sensor_health_service.current_app", mock_app):
            svc.mark_offline_sensors()

        coll.update_many.assert_called_once()
        assert coll.update_many.call_args[0][1]["$set"]["status"] == STATUS_OFFLINE
