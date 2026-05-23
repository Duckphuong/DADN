"""
Tests for alert API routes:
  GET    /api/v1/alerts
  PUT    /api/v1/alerts/<alert_id>/read
  GET    /api/v1/alerts/settings/email
  PUT    /api/v1/alerts/settings/email
"""

import contextlib
import jwt
from unittest.mock import MagicMock, patch, call

import pytest
from datetime import datetime, timezone

ALERT_BASE = "/api/v1/alerts"
DEFAULT_USER_ID = "507f1f77bcf86cd799439011"
DEFAULT_SENSOR_ID = "507f1f77bcf86cd799439011"
DEFAULT_ALERT_ID = "507f1f77bcf86cd799439012"


# ══════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════


def _jwt_token(user_id=None, role="user"):
    uid = user_id or DEFAULT_USER_ID
    return jwt.encode(
        {"sub": uid, "role": role, "exp": 999_999_999_99},
        "test-jwt-secret-key",
        algorithm="HS256",
    )


def _auth_headers(user_id=None, role="user"):
    return {"Authorization": f"Bearer {_jwt_token(user_id, role)}"}


def _ok(resp_or_code):
    if hasattr(resp_or_code, "status_code"):
        return resp_or_code.status_code == 200
    return resp_or_code == 200


def _mock_modified_count(n: int):
    """Create a MagicMock whose .modified_count is a real `int`."""
    m = MagicMock()
    # MagicMock() does not treat keyword args as mock attributes – so the
    # positional check above is incorrect.  We set the attribute manually
    # AFTER construction using __setattr__ on the *instance* dict to avoid
    # MagicMock's normal attribute-interception.
    m.__dict__["modified_count"] = n
    return m


def _fake_db_for_settings(
    users_findone=None,
    coll_name_for_collections: str = "predict_module",
):
    """Build a DB mock where collection names map to configured collections."""
    users_coll = MagicMock()
    users_coll.find_one.return_value = users_findone
    db = MagicMock()

    def _get_collection(name):
        if name == "users":
            return users_coll
        return MagicMock()

    db.get_collection = _get_collection
    return db


@contextlib.contextmanager
def _make_fresh_app():
    """Context-manager: create a fresh Flask app with all heavy deps mocked."""
    with patch(
        "app.services.alert_service.AlertService", return_value=MagicMock(enabled=True)
    ), patch(
        "app.infrastructure.external.weather_service.get_weather_data",
        return_value={"has_rain": False},
    ), patch(
        "app.infrastructure.persistence.mongo.connection.init_mongo"
    ), patch(
        "apscheduler.schedulers.background.BackgroundScheduler",
        return_value=MagicMock(),
    ), patch(
        "app.routes.alert_routes.ObjectId", side_effect=lambda x: x
    ), patch(
        "app.bootstrap.container.build_container"
    ) as _bc:

        def _fake_build(cfg):
            _c = MagicMock()

            # Decode JWT token to get the actual user_id
            def authenticate_user(token):
                try:
                    decoded = jwt.decode(
                        token, "test-jwt-secret-key", algorithms=["HS256"]
                    )
                    uid = decoded.get("sub", DEFAULT_USER_ID)
                except Exception:
                    uid = DEFAULT_USER_ID
                return MagicMock(
                    id=uid,
                    role=(
                        decoded.get("role", "user") if "decoded" in locals() else "user"
                    ),
                    email="test@example.com",
                    is_active=True,
                )

            _c.authenticate_user_use_case.execute.side_effect = authenticate_user
            return _c

        _bc.side_effect = _fake_build
        with patch(
            "app.infrastructure.persistence.mongo.connection.get_mongo_database",
            return_value=None,
        ):
            from app import create_app

            yield create_app()


def _patch_get_mongo(**kwargs):
    return patch("app.routes.alert_routes.get_mongo_database", **kwargs)


def _call_put_read(db, alert_id=DEFAULT_ALERT_ID, user_id=None):
    """PUT /api/v1/alerts/<id>/read – return status code."""
    with _make_fresh_app() as app:
        with app.test_client() as c:
            with _patch_get_mongo(return_value=db):
                resp = c.put(
                    f"{ALERT_BASE}/{alert_id}/read",
                    headers=_auth_headers(user_id=user_id),
                )
                return resp.status_code


def _call_put_read_body(db, alert_id=DEFAULT_ALERT_ID):
    """PUT /api/v1/alerts/<id>/read – return Flask Response object."""
    with _make_fresh_app() as app:
        with app.test_client() as c:
            with _patch_get_mongo(return_value=db):
                return c.put(
                    f"{ALERT_BASE}/{alert_id}/read",
                    headers=_auth_headers(),
                )


def _call_get_email_settings(db):
    """GET /api/v1/alerts/settings/email – return Flask Response object."""
    with _make_fresh_app() as app:
        with app.test_client() as c:
            with _patch_get_mongo(return_value=db):
                return c.get(
                    f"{ALERT_BASE}/settings/email",
                    headers=_auth_headers(),
                )


def _call_toggle_email(db, enabled: bool):
    """PUT /api/v1/alerts/settings/email – return status code."""
    with _make_fresh_app() as app:
        with app.test_client() as c:
            with _patch_get_mongo(return_value=db):
                resp = c.put(
                    f"{ALERT_BASE}/settings/email",
                    json={"enabled": enabled},
                    headers=_auth_headers(),
                )
                return resp.status_code


# ══════════════════════════════════════════════════════════════════════════
# GET /api/v1/alerts
# ══════════════════════════════════════════════════════════════════════════


class TestGetAlerts:
    def test_no_auth_returns_401(self, client):
        resp = client.get(ALERT_BASE)
        assert resp.status_code == 401

    def test_with_token_returns_200(self, client, auth_headers):
        resp = client.get(ALERT_BASE, headers=auth_headers)
        assert resp.status_code == 200

    def test_response_is_list(self, client, auth_headers):
        resp = client.get(ALERT_BASE, headers=auth_headers)
        assert isinstance(resp.get_json(), list)

    def test_no_sensors_returns_empty_list(self, client, auth_headers):
        resp = client.get(ALERT_BASE, headers=auth_headers)
        body = resp.get_json()
        assert isinstance(body, list)
        assert body == []

    def test_status_query_unread(self, client, auth_headers):
        resp = client.get(f"{ALERT_BASE}?status=unread", headers=auth_headers)
        assert resp.status_code == 200

    def test_status_query_all(self, client, auth_headers):
        resp = client.get(f"{ALERT_BASE}?status=all", headers=auth_headers)
        assert resp.status_code == 200

    def test_db_raises_returns_500(self):
        """An unhandled exception in the route → 500."""
        with _make_fresh_app() as app:
            with app.test_client() as c:
                with _patch_get_mongo(side_effect=Exception("DB down")):
                    resp = c.get(ALERT_BASE, headers=_auth_headers())
                    assert resp.status_code == 500


# ══════════════════════════════════════════════════════════════════════════
# PUT /api/v1/alerts/<alert_id>/read
# ══════════════════════════════════════════════════════════════════════════


class TestMarkRead:
    def _read_db(
        self, alert_has_sensor_doc: bool = True, sensor_owner: str = DEFAULT_USER_ID
    ):
        """Return (db, coll_pm) pair set up for the mark_read happy path."""
        alert_doc = {"_id": DEFAULT_ALERT_ID}
        if alert_has_sensor_doc:
            alert_doc["id_sensor"] = DEFAULT_SENSOR_ID

        coll_pm = MagicMock()
        coll_pm.find_one.return_value = alert_doc
        coll_pm.update_one.return_value = _mock_modified_count(1)

        coll_si = MagicMock()
        coll_si.find_one.return_value = {
            "_id": DEFAULT_SENSOR_ID,
            "userId": sensor_owner,
        }

        db = MagicMock()

        def _get_collection(name):
            if name == "predict_module":
                return coll_pm
            if name == "sensor_informations":
                return coll_si
            return MagicMock()

        db.get_collection = _get_collection
        return db, coll_pm

    # ── Auth ──────────────────────────────────────────────────────────────

    def test_no_auth(self, client):
        resp = client.put(f"{ALERT_BASE}/{DEFAULT_ALERT_ID}/read")
        assert resp.status_code == 401

    # ── Status codes ──────────────────────────────────────────────────────

    def test_alert_not_found_404(self):
        """predict_module find_one returns None → 404."""
        coll_pm = MagicMock()
        coll_pm.find_one.return_value = None
        db = MagicMock()
        db.get_collection = MagicMock(return_value=coll_pm)
        assert _call_put_read(db) == 404

    def test_happy_path_200(self):
        """Both alert and sensor found, owner matches → 200."""
        db, _ = self._read_db()
        assert _call_put_read(db) == 200

    def test_200_message_body(self):
        """Response body contains 'Alert marked as read'."""
        resp = _call_put_read_body(*self._read_db())
        body = resp.get_json()
        assert "Alert marked as read" in body.get("message", "")

    def test_already_read_200(self):
        """modified_count=0 → 'already read' → 200."""
        db, coll_pm = self._read_db()
        coll_pm.update_one.return_value = _mock_modified_count(0)
        assert _call_put_read(db) == 200

    def test_missing_sensor_400(self):
        """Alert doc has no id_sensor field → 400."""
        coll_pm = MagicMock()
        coll_pm.find_one.return_value = {"_id": DEFAULT_ALERT_ID}
        db = MagicMock()
        db.get_collection = MagicMock(return_value=coll_pm)
        assert _call_put_read(db) == 400

    def test_sensor_not_owned_403(self):
        """sensor_informations returns None (not owned) → 403."""
        coll_pm = MagicMock()
        coll_pm.find_one.return_value = {
            "_id": DEFAULT_ALERT_ID,
            "id_sensor": DEFAULT_SENSOR_ID,
        }
        coll_si = MagicMock()
        coll_si.find_one.return_value = None  # not found in ownership check
        db = MagicMock()

        def _get_collection(name):
            return coll_pm if name == "predict_module" else coll_si

        db.get_collection = _get_collection
        assert _call_put_read(db) == 403

    def test_wrong_user_403(self):
        """sensor found but userId belongs to someone else → 403."""
        # Authenticate as a different user
        DIFFERENT_USER_ID = "999999999999999999999999"

        coll_pm = MagicMock()
        coll_pm.find_one.return_value = {
            "_id": DEFAULT_ALERT_ID,
            "id_sensor": DEFAULT_SENSOR_ID,
        }
        # Mock update_one even though it shouldn't be called due to 403
        coll_pm.update_one.return_value = _mock_modified_count(1)

        coll_si = MagicMock()

        # The sensor belongs to DEFAULT_USER_ID, not DIFFERENT_USER_ID
        def find_one_impl(query):
            # Only return sensor if userId matches DEFAULT_USER_ID (the sensor's actual owner)
            if query.get("userId") == DEFAULT_USER_ID:
                return {"_id": DEFAULT_SENSOR_ID, "userId": DEFAULT_USER_ID}
            return None  # Different user → not found

        coll_si.find_one.side_effect = find_one_impl
        db = MagicMock()

        def _get_collection(name):
            return coll_pm if name == "predict_module" else coll_si

        db.get_collection = _get_collection

        # Authenticate as DIFFERENT_USER_ID, but the sensor belongs to DEFAULT_USER_ID
        assert (
            _call_put_read(db, alert_id=DEFAULT_ALERT_ID, user_id=DIFFERENT_USER_ID)
            == 403
        )

    def test_update_one_called(self):
        """update_one is called exactly once when alert is owned."""
        db, coll_pm = self._read_db()
        with _make_fresh_app() as app:
            with app.test_client() as c:
                with _patch_get_mongo(return_value=db):
                    c.put(
                        f"{ALERT_BASE}/{DEFAULT_ALERT_ID}/read", headers=_auth_headers()
                    )
        coll_pm.update_one.assert_called_once()


# ══════════════════════════════════════════════════════════════════════════
# GET /api/v1/alerts/settings/email
# ══════════════════════════════════════════════════════════════════════════


class TestGetEmailAlertSettings:
    ENDPOINT = f"{ALERT_BASE}/settings/email"

    def test_no_auth_returns_401(self, client):
        assert client.get(self.ENDPOINT).status_code == 401

    def test_with_auth_returns_200(self):
        db = _fake_db_for_settings(
            users_findone={"_id": DEFAULT_USER_ID, "email_notifications_enabled": True},
        )
        assert _call_get_email_settings(db).status_code == 200

    def test_response_has_enabled_field(self):
        db = _fake_db_for_settings(
            users_findone={"_id": DEFAULT_USER_ID, "email_notifications_enabled": True},
        )
        body = _call_get_email_settings(db).get_json()
        assert "enabled" in body

    @pytest.mark.parametrize(
        "val,expected",
        [
            (True, True),
            (False, False),
            (None, True),  # missing field → default True
        ],
    )
    def test_enabled_value(self, val, expected):
        user_doc = {"_id": DEFAULT_USER_ID}
        if val is not None:
            user_doc["email_notifications_enabled"] = val
        db = _fake_db_for_settings(users_findone=user_doc)
        resp = _call_get_email_settings(db)
        assert resp.get_json().get("enabled") is expected

    def test_user_not_found_404(self):
        db = _fake_db_for_settings(users_findone=None)
        assert _call_get_email_settings(db).status_code == 404

    def test_mongo_none_500(self):
        with _make_fresh_app() as app:
            with app.test_client() as c:
                with _patch_get_mongo(return_value=None):
                    resp = c.get(self.ENDPOINT, headers=_auth_headers())
                    assert resp.status_code == 500


# ══════════════════════════════════════════════════════════════════════════
# PUT /api/v1/alerts/settings/email
# ══════════════════════════════════════════════════════════════════════════


class TestToggleEmailAlertsSettings:
    ENDPOINT = f"{ALERT_BASE}/settings/email"

    def test_no_auth_returns_401(self, client):
        assert client.put(self.ENDPOINT, json={"enabled": False}).status_code == 401

    def test_missing_enabled_field_400(self, client):
        assert (
            client.put(self.ENDPOINT, json={}, headers=_auth_headers()).status_code
            == 400
        )

    def test_toggle_false_200(self, client):
        resp = client.put(
            self.ENDPOINT, json={"enabled": False}, headers=_auth_headers()
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body.get("enabled") is False
        assert "message" in body

    def test_toggle_true_200(self, client):
        resp = client.put(
            self.ENDPOINT, json={"enabled": True}, headers=_auth_headers()
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body.get("enabled") is True

    def test_update_one_called(self):
        coll = MagicMock()
        coll.update_one.return_value = _mock_modified_count(1)
        db = MagicMock()
        db.get_collection = MagicMock(return_value=coll)
        _call_toggle_email(db, enabled=False)
        coll.update_one.assert_called_once()

    def test_update_one_query_filter(self):
        """The $set collection updated is the 'users' collection."""
        coll = MagicMock()
        coll.update_one.return_value = _mock_modified_count(1)
        db = MagicMock()
        db.get_collection = MagicMock(return_value=coll)
        _call_toggle_email(db, enabled=False)
        db.get_collection.assert_called_with("users")

    def test_update_one_payload_false(self):
        coll = MagicMock()
        coll.update_one.return_value = _mock_modified_count(1)
        db = MagicMock()
        db.get_collection = MagicMock(return_value=coll)
        _call_toggle_email(db, enabled=False)
        _filter, _update = coll.update_one.call_args[0]
        assert _update == {"$set": {"email_notifications_enabled": False}}

    def test_update_one_payload_true(self):
        coll = MagicMock()
        coll.update_one.return_value = _mock_modified_count(1)
        db = MagicMock()
        db.get_collection = MagicMock(return_value=coll)
        _call_toggle_email(db, enabled=True)
        _filter, _update = coll.update_one.call_args[0]
        assert _update == {"$set": {"email_notifications_enabled": True}}

    def test_db_raises_returns_500(self):
        """update_one propagates via except → 500."""
        coll = MagicMock()
        coll.update_one.side_effect = Exception("DB error")
        db = MagicMock()
        db.get_collection = MagicMock(return_value=coll)
        assert _call_toggle_email(db, enabled=False) == 500
