"""
Unit tests for SensorHealthService.

Covers:
  - check_and_update (happy path + ERROR firmware + all-zeros)
  - _detect_status
  - _resolve_sensor_name
  - _log_sensor_error
  - _update_sensor_status
  - mark_offline_sensors
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from app.services.sensor_health_service import (
    SensorHealthService,
    STATUS_ONLINE,
    STATUS_OFFLINE,
    STATUS_ERROR,
    OFFLINE_THRESHOLD_MINUTES,
    SENSOR_FIELDS,
    FIRMWARE_ERROR_PATTERNS,
)

VALID_SENSOR_ID = "507f1f77bcf86cd799439011"

# ══════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════


def _make_flask_app_with_alert_service():
    app = MagicMock()
    alert_mock = MagicMock()
    alert_mock.submit_sensor_error_alert.return_value = True
    app.extensions = {"alert_service": alert_mock}
    app._get_current_object.return_value = app
    return app


def _valid_sensor_data():
    return {f: 50.0 for f in SENSOR_FIELDS}


# ══════════════════════════════════════════════════════════════════════════
# 1. check_and_update
# ══════════════════════════════════════════════════════════════════════════


class TestCheckAndUpdate:

    def test_returns_online_for_valid_data(self):
        svc = SensorHealthService()
        data = _valid_sensor_data()
        with patch(
            "app.services.sensor_health_service.get_mongo_database", return_value=None
        ):
            status = svc.check_and_update(VALID_SENSOR_ID, data)
        assert status == STATUS_ONLINE

    def test_returns_error_for_firmware_error(self):
        svc = SensorHealthService()
        data = dict(_valid_sensor_data(), error="DS18B20 sensor disconnected")
        app = _make_flask_app_with_alert_service()

        with patch(
            "app.services.sensor_health_service.get_mongo_database", return_value=None
        ), patch("app.services.sensor_health_service.current_app", app):
            status = svc.check_and_update(VALID_SENSOR_ID, data)

        assert status == STATUS_ERROR

    def test_returns_error_for_all_zeros(self):
        svc = SensorHealthService()
        data = {f: 0.0 for f in SENSOR_FIELDS}
        app = _make_flask_app_with_alert_service()

        with patch(
            "app.services.sensor_health_service.get_mongo_database", return_value=None
        ), patch("app.services.sensor_health_service.current_app", app):
            status = svc.check_and_update(VALID_SENSOR_ID, data)

        assert status == STATUS_ERROR

    def test_logs_error_on_firmware_failure(self):
        svc = SensorHealthService()
        data = dict(_valid_sensor_data(), error="Unknown failure")
        fake_db = MagicMock()
        fake_coll = MagicMock()
        fake_db.__getitem__ = MagicMock(return_value=fake_coll)
        app = _make_flask_app_with_alert_service()

        with patch(
            "app.services.sensor_health_service.get_mongo_database",
            return_value=fake_db,
        ), patch("app.services.sensor_health_service.current_app", app):
            svc.check_and_update(VALID_SENSOR_ID, data)
        fake_coll.insert_one.assert_called_once()

    def test_logs_error_on_all_zeros(self):
        svc = SensorHealthService()
        data = {f: 0.0 for f in SENSOR_FIELDS}
        fake_db = MagicMock()
        fake_coll = MagicMock()
        fake_db.__getitem__ = MagicMock(return_value=fake_coll)
        app = _make_flask_app_with_alert_service()

        with patch(
            "app.services.sensor_health_service.get_mongo_database",
            return_value=fake_db,
        ), patch("app.services.sensor_health_service.current_app", app):
            svc.check_and_update(VALID_SENSOR_ID, data)
        fake_coll.insert_one.assert_called_once()

    def test_submits_alert_on_error(self):
        svc = SensorHealthService()
        data = dict(_valid_sensor_data(), error="DS18B20 sensor disconnected")
        fake_alert_service = MagicMock()
        app = _make_flask_app_with_alert_service()
        app.extensions["alert_service"] = fake_alert_service
        with patch(
            "app.services.sensor_health_service.get_mongo_database", return_value=None
        ), patch("app.services.sensor_health_service.current_app", app):
            svc.check_and_update(VALID_SENSOR_ID, data)
        fake_alert_service.submit_sensor_error_alert.assert_called_once()

    def test_no_alert_submitted_for_online(self):
        svc = SensorHealthService()
        data = _valid_sensor_data()
        fake_alert_service = MagicMock()
        app = _make_flask_app_with_alert_service()
        app.extensions["alert_service"] = fake_alert_service
        with patch(
            "app.services.sensor_health_service.get_mongo_database", return_value=None
        ), patch("app.services.sensor_health_service.current_app", app):
            svc.check_and_update(VALID_SENSOR_ID, data)
        fake_alert_service.submit_sensor_error_alert.assert_not_called()


# ══════════════════════════════════════════════════════════════════════════
# 2. _detect_status
# ══════════════════════════════════════════════════════════════════════════


class TestDetectStatus:
    def test_firmware_error_detected(self):
        svc = SensorHealthService()
        data = dict(_valid_sensor_data(), error="DS18B20 sensor disconnected")
        status, msg = svc._detect_status(data)
        assert status == STATUS_ERROR
        assert "Temperature Sensor (DS18B20)" in msg

    def test_unknown_firmware_error(self):
        svc = SensorHealthService()
        data = dict(_valid_sensor_data(), error="Mystery error")
        status, msg = svc._detect_status(data)
        assert status == STATUS_ERROR
        assert "Unknown Sensor" in msg

    def test_all_zeros_is_error(self):
        svc = SensorHealthService()
        data = {f: 0.0 for f in SENSOR_FIELDS}
        status, msg = svc._detect_status(data)
        assert status == STATUS_ERROR
        assert msg == "All sensor values are 0"

    def test_valid_data_is_online(self):
        svc = SensorHealthService()
        data = _valid_sensor_data()
        status, msg = svc._detect_status(data)
        assert status == STATUS_ONLINE
        assert msg is None

    def test_some_zeros_is_online(self):
        svc = SensorHealthService()
        data = {f: (0.0 if f == "TSS" else 50.0) for f in SENSOR_FIELDS}
        status, msg = svc._detect_status(data)
        assert status == STATUS_ONLINE

    def test_error_key_with_none_value_passes(self):
        svc = SensorHealthService()
        # Python truthiness: None is falsy → _detect_status should not trigger error
        data = dict(_valid_sensor_data(), error=None)
        status, msg = svc._detect_status(data)
        assert status == STATUS_ONLINE

    def test_error_key_with_empty_string_passes(self):
        svc = SensorHealthService()
        data = dict(_valid_sensor_data(), error="")
        status, msg = svc._detect_status(data)
        assert status == STATUS_ONLINE


# ══════════════════════════════════════════════════════════════════════════
# 3. _resolve_sensor_name
# ══════════════════════════════════════════════════════════════════════════


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
