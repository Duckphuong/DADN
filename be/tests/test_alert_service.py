"""
Unit tests for AlertService.

Covers:
  - __init__
  - _sensor_alert_cache_key
  - _is_sensor_alert_rate_limited
  - _mark_sensor_alert_sent
  - _generate_email_body
  - _generate_sensor_error_email_body
  - _should_send_alert
  - check_and_send_alerts
  - send_sensor_error_alert
  - submit_sensor_error_alert
  - calculate_time_ago
"""

import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timezone

from app.services.alert_service import (
    AlertService,
)

SMTP = "smtp.gmail.com"
PORT = 587
EMAIL = "test@example.com"
PASSWORD = "testpass"


@pytest.fixture()
def service():
    svc = AlertService(
        smtp_server=SMTP,
        smtp_port=PORT,
        email=EMAIL,
        password=PASSWORD,
        enabled=True,
    )
    svc.last_email_time = {}
    svc.last_sensor_error_time = {}
    svc._pending_sensor_alerts = set()
    return svc


@pytest.fixture()
def disabled_service():
    return AlertService(
        smtp_server=SMTP,
        smtp_port=PORT,
        email=EMAIL,
        password=PASSWORD,
        enabled=False,
    )


# ══════════════════════════════════════════════════════════════════════════
# 1. Constructor
# ══════════════════════════════════════════════════════════════════════════


class TestConstructor:
    def test_attributes_saved(self, service):
        assert service.smtp_server == SMTP
        assert service.smtp_port == PORT
        assert service.email == EMAIL
        assert service.enabled is True

    def test_disabled_flag(self, disabled_service):
        assert disabled_service.enabled is False

    def test_tracking_dicts_initialized(self, service):
        assert isinstance(service.last_email_time, dict)
        assert isinstance(service.last_sensor_error_time, dict)
        assert isinstance(service._pending_sensor_alerts, set)

    def test_executor_created(self, service):
        assert service._sensor_alert_executor is not None


# ══════════════════════════════════════════════════════════════════════════
# 2. _sensor_alert_cache_key
# ══════════════════════════════════════════════════════════════════════════


class TestSensorAlertCacheKey:
    def test_basic(self, service):
        key = service._sensor_alert_cache_key("sensor-123", "ERROR")
        assert key == "sensor-123_ERROR"

    def test_offline(self, service):
        key = service._sensor_alert_cache_key("sensor-456", "OFFLINE")
        assert key == "sensor-456_OFFLINE"


# ══════════════════════════════════════════════════════════════════════════
# 3. _is_sensor_alert_rate_limited
# ══════════════════════════════════════════════════════════════════════════


class TestIsSensorAlertRateLimited:
    def test_not_limited_on_first_call(self, service):
        assert (
            service._is_sensor_alert_rate_limited(
                "k1", now=datetime.now(tz=timezone.utc)
            )
            is False
        )

    def test_limited_immediately_after_mark(self, service):
        now = datetime.now(tz=timezone.utc)
        service._mark_sensor_alert_sent("k1", sent_at=now)
        assert service._is_sensor_alert_rate_limited("k1", now=now) is True

    def test_not_limited_after_cooldown(self, service):
        past = datetime.now(tz=timezone.utc).replace(year=2025)
        service._mark_sensor_alert_sent("k1", sent_at=past)
        now = datetime.now(tz=timezone.utc)
        assert service._is_sensor_alert_rate_limited("k1", now=now) is False


# ══════════════════════════════════════════════════════════════════════════
# 4. _mark_sensor_alert_sent
# ══════════════════════════════════════════════════════════════════════════


class TestMarkSensorAlertSent:
    def test_sets_timestamp(self, service):
        now = datetime.now(tz=timezone.utc)
        service._mark_sensor_alert_sent("k1", sent_at=now)
        assert "k1" in service.last_sensor_error_time
        assert service.last_sensor_error_time["k1"] == now


# ══════════════════════════════════════════════════════════════════════════
# 5. _should_send_alert
# ══════════════════════════════════════════════════════════════════════════


class TestShouldSendAlert:
    def _make_doc(self, wqi=80, risk="Low Risk", sensor_id="s1"):
        return {"wqi_score": wqi, "contamination_risk": risk, "id_sensor": sensor_id}

    def test_no_cooldown_first_time_high_wqi(self, service):
        service.last_email_time = {}
        doc = self._make_doc(wqi=40)
        assert service._should_send_alert(doc) is True

    def test_low_risk_above_50_not_sent(self, service):
        service.last_email_time = {"s1": datetime.now(tz=timezone.utc)}
        doc = self._make_doc(wqi=80)
        assert service._should_send_alert(doc) is False

    def test_high_risk_sent(self, service):
        service.last_email_time = {}
        doc = self._make_doc(wqi=80, risk="High Risk")
        assert service._should_send_alert(doc) is True

    def test_critical_risk_sent(self, service):
        service.last_email_time = {}
        doc = self._make_doc(wqi=80, risk="Critical")
        assert service._should_send_alert(doc) is True

    def test_wqi_below_50_sent(self, service):
        service.last_email_time = {}
        doc = self._make_doc(wqi=49)
        assert service._should_send_alert(doc) is True

    def test_suppressed_after_cooldown(self, service):
        now = datetime.now(tz=timezone.utc)
        service.last_email_time = {"s1": now}
        doc = self._make_doc(wqi=40)
        assert service._should_send_alert(doc) is False


# ══════════════════════════════════════════════════════════════════════════
# 6. _generate_email_body
# ══════════════════════════════════════════════════════════════════════════


class TestGenerateEmailBody:
    def _make_doc(self):
        return {
            "wqi_score": 25.0,
            "contamination_risk": "Critical",
            "forecast_24h": "Deteriorating",
            "predicted_wqi": "15-25",
            "confidence": 78.0,
            "message": "WQI: 25.0, Risk: Critical",
            "id_sensor": "507f1f77bcf86cd799439011",
        }

    def _make_sensor(self):
        return {
            "sensorName": "Station Alpha",
            "location": {"latitude": 10.5, "longitude": 106.0},
        }

    def test_returns_string(self, service):
        body = service._generate_email_body(self._make_doc(), self._make_sensor())
        assert isinstance(body, str)

    def test_contains_sensor_name(self, service):
        body = service._generate_email_body(self._make_doc(), self._make_sensor())
        assert "Station Alpha" in body

    def test_contains_wqi_score(self, service):
        body = service._generate_email_body(self._make_doc(), self._make_sensor())
        assert "25.0" in body

    def test_contains_contamination_risk(self, service):
        body = service._generate_email_body(self._make_doc(), self._make_sensor())
        assert "Critical" in body

    def test_sensor_name_unknown_when_none(self, service):
        body = service._generate_email_body(self._make_doc(), None)
        assert "Unknown" in body

    def test_no_sensor_no_location_na(self, service):
        body = service._generate_email_body(self._make_doc(), None)
        assert "N/A" in body


# ══════════════════════════════════════════════════════════════════════════
# 7. _generate_sensor_error_email_body
# ══════════════════════════════════════════════════════════════════════════


class TestGenerateSensorErrorEmailBody:
    @pytest.mark.parametrize(
        "error_type,keyword",
        [
            ("ERROR", "issue"),
            ("OFFLINE", "stopped sending"),
        ],
    )
    def test_error_type_specific_message(self, service, error_type, keyword):
        body = service._generate_sensor_error_email_body(
            "s1", {"sensorName": "Node 1"}, error_type
        )
        assert keyword.lower() in body.lower()

    def test_contains_sensor_name(self, service):
        body = service._generate_sensor_error_email_body(
            "s1", {"sensorName": "Main Sensor"}, "ERROR"
        )
        assert "Main Sensor" in body

    def test_no_sensor_unknown_name(self, service):
        body = service._generate_sensor_error_email_body("s1", None, "ERROR")
        assert "Unknown" in body


# ══════════════════════════════════════════════════════════════════════════
# 8. check_and_send_alerts (disabled → no-op)
# ══════════════════════════════════════════════════════════════════════════


class TestCheckAndSendAlerts:
    def test_disabled_service_returns_immediately(self, disabled_service):
        disabled_service.check_and_send_alerts()  # must not raise

    def test_no_db_returns_immediately(self, service):
        with patch("app.services.alert_service.get_mongo_database", return_value=None):
            service.check_and_send_alerts()  # must not raise

    def test_alerts_candidates_skipped_when_score_ok(self, service):
        """Alerts with WQI >= 50 AND Low Risk must not trigger email."""
        fake_coll = MagicMock()
        fake_coll.find.return_value = [
            MagicMock(
                _id=MagicMock(string=lambda: "1"),
                wqi_score=80,
                contamination_risk="Low Risk",
                id_sensor="s1",
                input_sensor_id=None,
            )
        ]
        fake_db = MagicMock()
        fake_db.__getitem__ = MagicMock(return_value=fake_coll)

        def _users_collection_find_one(q):
            return None  # no linked user

        fake_user_coll = MagicMock()
        fake_user_coll.find_one.side_effect = _users_collection_find_one
        fake_db.__getitem__.side_effect = lambda n: (
            fake_coll if n == "predict_module" else fake_user_coll
        )

        with patch(
            "app.services.alert_service.get_mongo_database", return_value=fake_db
        ):
            service.check_and_send_alerts()
        fake_coll.update_one.assert_not_called()


# ══════════════════════════════════════════════════════════════════════════
# 9. send_sensor_error_alert (disabled → False)
# ══════════════════════════════════════════════════════════════════════════


class TestSendSensorErrorAlert:
    def test_disabled_returns_false(self, disabled_service):
        result = disabled_service.send_sensor_error_alert("s1", "ERROR")
        assert result is False

    def test_no_db_returns_false(self, service):
        with patch("app.services.alert_service.get_mongo_database", return_value=None):
            result = service.send_sensor_error_alert("s1", "ERROR")
            assert result is False

    def test_no_target_email_returns_false(self, service):
        """When sensor has no linked user → Cannot send."""
        fake_sensor_coll = MagicMock()
        fake_sensor_coll.find_one.return_value = {"sensorName": "Node"}  # no userId
        fake_db = MagicMock()
        fake_db.__getitem__ = MagicMock(return_value=fake_sensor_coll)

        with patch(
            "app.services.alert_service.get_mongo_database", return_value=fake_db
        ):
            result = service.send_sensor_error_alert("s1", "ERROR")
            assert result is False

    def test_rate_limited_returns_false(self, service):
        now = datetime.now(tz=timezone.utc)
        with service._sensor_alert_lock:
            service.last_sensor_error_time["s1_ERROR"] = now
        with patch(
            "app.services.alert_service.get_mongo_database", return_value=MagicMock()
        ):
            assert service.send_sensor_error_alert("s1", "ERROR") is False

    def test_success_sends_email(self, service):
        sensor_id = "507f1f77bcf86cd799439011"  # 24-char hex for ObjectId conversion
        sensor_obj_id = "507f1f77bcf86cd799439011"
        user_obj_id = "507f1f77bcf86cd799439012"
        fake_sensor_coll = MagicMock()
        fake_sensor_coll.find_one.return_value = {
            "_id": sensor_obj_id,
            "sensorName": "My Sensor",
            "userId": user_obj_id,
        }
        fake_user_coll = MagicMock()
        fake_user_coll.find_one.return_value = {
            "_id": user_obj_id,
            "email": "owner@example.com",
            "email_notifications_enabled": True,
        }
        fake_db = MagicMock()

        def _getitem(name):
            return {
                "sensor_informations": fake_sensor_coll,
                "users": fake_user_coll,
            }[name]

        fake_db.__getitem__ = _getitem
        fake_db.get_collection = _getitem

        with patch(
            "app.services.alert_service.get_mongo_database", return_value=fake_db
        ), patch("smtplib.SMTP") as MockSMTP:
            mock_server = MockSMTP.return_value
            result = service.send_sensor_error_alert(sensor_id, "ERROR")
            assert result is True
            MockSMTP.return_value.sendmail.assert_called_once()


# ══════════════════════════════════════════════════════════════════════════
# 10. submit_sensor_error_alert
# ══════════════════════════════════════════════════════════════════════════


class TestSubmitSensorErrorAlert:
    def test_disabled_returns_false(self, disabled_service):
        result = disabled_service.submit_sensor_error_alert(MagicMock(), "s1", "ERROR")
        assert result is False

    def test_rate_limited_returns_false(self, service):
        now = datetime.now(tz=timezone.utc)
        with service._sensor_alert_lock:
            service.last_sensor_error_time["s1_ERROR"] = now
        result = service.submit_sensor_error_alert(MagicMock(), "s1", "ERROR")
        assert result is False

    def test_submits_to_executor(self, service):
        fake_app = MagicMock()
        original_executor = service._sensor_alert_executor
        try:
            service._sensor_alert_executor = MagicMock()
            service.submit_sensor_error_alert(fake_app, "s1", "ERROR")
            service._sensor_alert_executor.submit.assert_called_once()
            assert service._sensor_alert_executor.submit.call_count >= 1
        finally:
            service._sensor_alert_executor = original_executor


# ══════════════════════════════════════════════════════════════════════════
# 11. calculate_time_ago
# ══════════════════════════════════════════════════════════════════════════


class TestCalculateTimeAgo:
    def test_just_now(self):
        from app.routes.alert_routes import calculate_time_ago

        now = datetime.now(tz=timezone.utc)
        assert calculate_time_ago(now) == "Just now"

    def test_minutes_ago(self):
        from app.routes.alert_routes import calculate_time_ago

        past = datetime.now(tz=timezone.utc).replace(
            second=0, microsecond=0
        ) - __import__("datetime").timedelta(minutes=5)
        result = calculate_time_ago(past)
        assert "minute(s) ago" in result

    def test_hours_ago(self):
        from app.routes.alert_routes import calculate_time_ago

        past = datetime.now(tz=timezone.utc) - __import__("datetime").timedelta(hours=3)
        result = calculate_time_ago(past)
        assert "hour(s) ago" in result

    def test_days_ago(self):
        from app.routes.alert_routes import calculate_time_ago

        past = datetime.now(tz=timezone.utc) - __import__("datetime").timedelta(days=2)
        result = calculate_time_ago(past)
        assert "day(s) ago" in result

    def test_naive_datetime_assumes_utc(self):
        from app.routes.alert_routes import calculate_time_ago

        past = datetime(2025, 1, 1, 0, 0, 0)
        result = calculate_time_ago(past)
        assert isinstance(result, str)

    def test_iso_string_input(self):
        from app.routes.alert_routes import calculate_time_ago

        past = datetime.now(tz=timezone.utc) - __import__("datetime").timedelta(hours=1)
        result = calculate_time_ago(past.isoformat())
        assert isinstance(result, str)
