"""
pytest configuration for the backend API tests.

All heavyweight dependencies are patched globally so tests never touch
a real MongoDB, the Groq LLM API, the Open-Meteo weather API, or any
background scheduler jobs.
"""

import os
import sys

import pytest
from unittest.mock import MagicMock, patch


# ══════════════════════════════════════════════════════════════════════════
# 0. Environment boot-strap (must run BEFORE any app imports)
# ══════════════════════════════════════════════════════════════════════════

# ai_model_service instantiates SolutionAIService() at import time → Groq().
# Set a dummy key so the constructor never raises; every Groq call is mocked below.
os.environ.setdefault("GROQ_API_KEY", "test-groq-key")
os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017/dungne")

# Make the `be/` directory importable when pytest is invoked from the repo root.
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
BE_DIR = os.path.join(TESTS_DIR, "..")
if BE_DIR not in sys.path:
    sys.path.insert(0, BE_DIR)


# ══════════════════════════════════════════════════════════════════════════
# 1. Global autouse fixture – patches every external / slow dependency
# ══════════════════════════════════════════════════════════════════════════


@pytest.fixture(autouse=True)
def patch_external_deps(monkeypatch):
    """Catch-all: mocks MongoDB, APScheduler, Open-Meteo, and Groq."""

    # ── APScheduler – never start real jobs ────────────────────────────────
    _sched_inst = MagicMock()
    _sched_inst.start.return_value = None
    _sched_inst.add_job.return_value = None
    monkeypatch.setattr(
        "apscheduler.schedulers.background.BackgroundScheduler",
        MagicMock(return_value=_sched_inst),
    )

    # ── init_mongo – no-op ─────────────────────────────────────────────────
    monkeypatch.setattr(
        "app.infrastructure.persistence.mongo.connection.init_mongo", lambda app: None
    )

    # ── Open-Meteo weather service ─────────────────────────────────────────
    monkeypatch.setattr(
        "app.infrastructure.external.weather_service.get_weather_data",
        MagicMock(
            return_value={
                "has_rain": False,
                "total_precipitation_mm": 0.0,
                "avg_temperature_c": 28.0,
                "avg_cloud_cover_pct": 50.0,
                "max_wind_speed_kmh": 10.0,
                "avg_humidity_pct": 70.0,
                "max_uv_index": 5.0,
            }
        ),
    )

    # ── Groq / LLM (ai_model_service module-level singleton) ───────────────
    _mock_llm = MagicMock()
    _mock_llm.generate_advanced_solution.return_value = "Test LLM response."
    monkeypatch.setattr(
        "app.services.ai_model_service.SolutionAIService",
        MagicMock(return_value=_mock_llm),
    )
    try:
        import app.services.ai_model_service as _ai_mod

        _ai_mod.solution_service = _mock_llm
    except Exception:
        pass

    # ── Container bootstrap ────────────────────────────────────────────────
    def _fake_build(cfg):
        _c = MagicMock()
        _c.authenticate_user_use_case.execute.return_value = MagicMock(
            id=DEFAULT_USER_ID,
            role="user",
            email="test@example.com",
            is_active=True,
        )
        return _c

    monkeypatch.setattr(
        "app.bootstrap.container.build_container", _fake_build, raising=False
    )

    yield


# ══════════════════════════════════════════════════════════════════════════
# 2. JWT helpers
# ══════════════════════════════════════════════════════════════════════════

JWT_SECRET = "test-jwt-secret-key"
DEFAULT_USER_ID = "507f1f77bcf86cd799439011"


def _encode_jwt(subject: str = DEFAULT_USER_ID, role: str = "user") -> str:
    import jwt as _jwt  # PyJWT

    payload = {"sub": subject, "role": role, "exp": 999_999_999_99}
    return _jwt.encode(payload, JWT_SECRET, algorithm="HS256")


@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {_encode_jwt()}"}


@pytest.fixture
def admin_headers():
    return {"Authorization": f"Bearer {_encode_jwt(role='admin')}"}


# ══════════════════════════════════════════════════════════════════════════
# 3. Flask test client
# ══════════════════════════════════════════════════════════════════════════


def _build_fake_db() -> MagicMock:
    """Return a shared fake MongoDB whose collections return empty/None by default."""
    _db = MagicMock()
    _coll = MagicMock()
    _coll.find.return_value = []
    _coll.find_one.return_value = None
    _coll.insert_one.return_value = MagicMock(inserted_id="fake")
    _coll.update_one.return_value = MagicMock(modified_count=0)
    _coll.update_many.return_value = MagicMock(modified_count=0)
    _db.__getitem__ = MagicMock(return_value=_coll)
    return _db


@pytest.fixture
def client(monkeypatch):
    """Yield a Flask test client with mocks for all route-level services."""

    # ── AlertService inside create_app ────────────────────────────────────
    _alert_svc = MagicMock()
    _alert_svc.enabled = True
    _alert_svc.check_and_send_alerts = MagicMock()
    _alert_svc.submit_sensor_error_alert = MagicMock(return_value=True)
    monkeypatch.setattr(
        "app.services.alert_service.AlertService",
        MagicMock(return_value=_alert_svc),
    )

    # ── Container bootstrap ───────────────────────────────────────────────
    def _fake_build(cfg):
        _c = MagicMock()
        _c.authenticate_user_use_case.execute.return_value = MagicMock(
            id=DEFAULT_USER_ID,
            role="user",
            email="test@example.com",
            is_active=True,
        )
        return _c

    monkeypatch.setattr(
        "app.bootstrap.container.build_container", _fake_build, raising=False
    )

    # ── Build the Flask app ────────────────────────────────────────────────
    from app import create_app

    flask_app = create_app()
    flask_app.config["TESTING"] = True

    # ── Replace module-level service singletons ────────────────────────────
    import app.routes.prediction_routes as pred_mod
    import app.services.sensor_health_service as sh_mod
    import app.routes.alert_routes as alert_mod

    _real_svc = sh_mod.SensorHealthService()

    # ai_service mock – must return JSON-serialisable dicts
    _ai_mock = MagicMock()
    _ai_mock.test_db.return_value = {
        "status": "ok",
        "task": "regression",
        "loaded_models": ["RandomForestRegressor"],
        "target_column": "WQI",
        "training_source": "dataset_DADN_Cleaned.xlsx",
    }
    _ai_mock.normalize_sensor_data.side_effect = lambda d: d
    _ai_mock.train_model_from_db.return_value = {"message": "Models trained from DB"}
    _ai_mock.train_model_from_file.return_value = {
        "message": "Models trained from file"
    }
    _ai_mock.predict.return_value = {
        "best_model": "RandomForestRegressor",
        "models": [{"wqi": {"score": 75.0, "label": "Good"}}],
        "ensemble": {
            "wqi": {"score": 75.0, "label": "Good"},
            "risk": {"status": "Medium Risk"},
            "confidence": 80.0,
            "forecast_24h": {"trend": "Stable", "predicted_wqi_range": [70.0, 80.0]},
        },
        "summary": {
            "wqi": {"score": 75.0, "label": "Good"},
            "risk": {"status": "Medium Risk"},
            "accuracy": 0.8,
            "metrics": {"r2": 0.8, "mae": 5.0, "rmse": 6.0},
            "forecast_24h": {
                "trend": "Stable",
                "predicted_wqi_range": [70.0, 80.0],
                "confidence_score": 80.0,
            },
            "solution": "Consider treatment.",
            "weather": None,
            "abnormal_parameters": [],
        },
    }
    pred_mod.ai_service = _ai_mock

    # sensor_health mock – delegate to real _detect_status
    _sh_mock = MagicMock()
    _sh_mock.check_and_update.side_effect = lambda sid, data: _real_svc._detect_status(
        data
    )[0]
    pred_mod.sensor_health = _sh_mock

    # ── Fake MongoDB – shared by prediction_routes AND alert_routes ────────
    _fake_db = _build_fake_db()

    # prediction_routes.get_mongo_database → fake DB
    _orig_pred_get_mongo = pred_mod.get_mongo_database
    pred_mod.get_mongo_database = MagicMock(return_value=_fake_db)

    # alert_routes.get_mongo_database → same fake DB
    _orig_alert_get_mongo = alert_mod.get_mongo_database
    alert_mod.get_mongo_database = MagicMock(return_value=_fake_db)

    try:
        with flask_app.test_client() as c:
            yield c
    finally:
        pred_mod.get_mongo_database = _orig_pred_get_mongo
        alert_mod.get_mongo_database = _orig_alert_get_mongo
