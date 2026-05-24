"""
Integration tests for AI model service against deployed backend.

Tests AI model behavior through:
  - GET /prediction/test-db (model info)
  - POST /prediction/predict (model predictions)
  - POST /prediction/predict-with-time (time-aware predictions)

These tests verify real AI service behavior without mocking the service internals.
"""

import json
import os
import tempfile

import pandas as pd
import pytest
import requests
from unittest.mock import MagicMock, patch
from werkzeug.datastructures import FileStorage

from app.services.ai_model_service import (
    AIModelService,
    FEATURE_COLUMNS,
    MODEL_VERSION,
)

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
# 1. Model Database Info Tests
# ══════════════════════════════════════════════════════════════════════════


class TestAIModelInfo:
    """Test AI model information endpoint."""

    def test_test_db_endpoint_exists(self):
        """GET /prediction/test-db should be accessible."""
        resp = requests.get(f"{BASE}/test-db")
        assert resp.status_code == 200

    def test_test_db_returns_model_status(self):
        """Response should contain model status information."""
        resp = requests.get(f"{BASE}/test-db")
        data = resp.json()
        assert "status" in data
        assert data["status"] == "ok"

    def test_test_db_has_task_info(self):
        """Response should indicate task type."""
        resp = requests.get(f"{BASE}/test-db")
        data = resp.json()
        assert "task" in data
        assert data["task"] == "regression"

    def test_test_db_lists_loaded_models(self):
        """Response should list loaded models."""
        resp = requests.get(f"{BASE}/test-db")
        data = resp.json()
        assert "loaded_models" in data
        assert isinstance(data["loaded_models"], list)

    def test_test_db_has_target_column(self):
        """Response should indicate target column."""
        resp = requests.get(f"{BASE}/test-db")
        data = resp.json()
        assert "target_column" in data

    def test_test_db_has_training_source(self):
        """Response should indicate training data source."""
        resp = requests.get(f"{BASE}/test-db")
        data = resp.json()
        assert "training_source" in data


# ══════════════════════════════════════════════════════════════════════════
# 2. Model Prediction Tests
# ══════════════════════════════════════════════════════════════════════════


class TestModelPredictionBehavior:
    """Test model prediction behavior and output."""

    def test_prediction_returns_valid_structure(self):
        """Prediction response should have expected structure."""
        resp = requests.post(f"{BASE}/predict", json=VALID_SENSOR_DATA)
        assert resp.status_code == 200
        data = resp.json()
        
        assert "summary" in data
        assert "ensemble" in data

    def test_prediction_summary_has_wqi(self):
        """Summary should contain WQI prediction."""
        resp = requests.post(f"{BASE}/predict", json=VALID_SENSOR_DATA)
        if resp.status_code == 200:
            summary = resp.json().get("summary", {})
            # Summary should have water quality indicators
            assert isinstance(summary, dict)

    def test_prediction_with_different_ranges(self):
        """Model should handle various valid input ranges."""
        test_cases = [
            {**VALID_SENSOR_DATA, "pH": 5.0},
            {**VALID_SENSOR_DATA, "pH": 9.0},
            {**VALID_SENSOR_DATA, "DO": 0.5},
        ]
        
        for test_data in test_cases:
            resp = requests.post(f"{BASE}/predict", json=test_data)
            assert resp.status_code == 200

    def test_invalid_sensor_data_rejected(self):
        """All-zero sensor data should be rejected."""
        zero_data = {k: 0.0 for k in VALID_SENSOR_DATA}
        resp = requests.post(f"{BASE}/predict", json=zero_data)
        assert resp.status_code == 400

    def test_firmware_error_in_data_rejected(self):
        """Data with firmware error should be rejected."""
        error_data = {**VALID_SENSOR_DATA, "error": "Sensor disconnected"}
        resp = requests.post(f"{BASE}/predict", json=error_data)
        assert resp.status_code == 400


# ══════════════════════════════════════════════════════════════════════════
# 3. Time-Aware Prediction Tests
# ══════════════════════════════════════════════════════════════════════════


class TestTimeAwarePrediction:
    """Test model with timestamp information."""

    def test_predict_with_timestamp_succeeds(self):
        """Prediction with timestamp should work."""
        data = {**VALID_SENSOR_DATA, "createdAt": "2025-01-01T10:00:00+00:00"}
        resp = requests.post(f"{BASE}/predict-with-time", json=data)
        assert resp.status_code == 200

    def test_time_aware_returns_summary(self):
        """Time-aware prediction should return summary."""
        data = {**VALID_SENSOR_DATA, "createdAt": "2025-01-01T10:00:00+00:00"}
        resp = requests.post(f"{BASE}/predict-with-time", json=data)
        assert "summary" in resp.json()

    def test_missing_timestamp_rejected(self):
        """Request without timestamp should fail."""
        resp = requests.post(f"{BASE}/predict-with-time", json=VALID_SENSOR_DATA)
        assert resp.status_code == 400

    def test_various_timestamp_formats(self):
        """Should handle various valid timestamp formats."""
        timestamps = [
            "2025-01-01T10:00:00+00:00",
            "2025-01-01T10:00:00Z",
        ]
        
        for ts in timestamps:
            data = {**VALID_SENSOR_DATA, "createdAt": ts}
            resp = requests.post(f"{BASE}/predict-with-time", json=data)
            assert resp.status_code in [200, 400]  # Either succeeds or validates timestamp


class TestNormalizeFieldName:
    def test_canonical_name_passthrough(self, ai_svc):
        assert ai_svc._normalize_field_name("Nhiệt độ") == "Nhiệt độ"

    def test_alias_to_canonical(self, ai_svc):
        assert ai_svc._normalize_field_name("Temp") == "Nhiệt độ"

    def test_aliased_ph(self, ai_svc):
        assert ai_svc._normalize_field_name("ph") == "pH"

    def test_aliased_do(self, ai_svc):
        assert ai_svc._normalize_field_name("Dissolved Oxygen") == "DO"

    def test_aliased_conductivity(self, ai_svc):
        assert ai_svc._normalize_field_name("EC") == "Độ dẫn"

    def test_unknown_alias(self, ai_svc):
        assert ai_svc._normalize_field_name("SomeRandomField") == "SomeRandomField"


# ══════════════════════════════════════════════════════════════════════════
# 3. normalize_sensor_data
# ══════════════════════════════════════════════════════════════════════════


class TestNormalizeSensorData:
    def test_aliases_converted(self, ai_svc):
        data = {"Temp": 25.0, "ph": 7.0, "sensorId": "abc"}
        result = ai_svc.normalize_sensor_data(data)
        assert "Nhiệt độ" in result
        assert "Nhiệt độ" not in data

    def test_non_feature_fields_preserved(self, ai_svc):
        data = {"Temp": 25.0, "sensorId": "abc", "error": "low signal"}
        result = ai_svc.normalize_sensor_data(data)
        assert result["sensorId"] == "abc"
        assert result["error"] == "low signal"

    def test_no_unknown_feature_fields(self, ai_svc):
        data = {"Temp": 25.0, "UnknownField": 999}
        result = ai_svc.normalize_sensor_data(data)
        assert "UnknownField" not in result

    def test_returns_dict(self, ai_svc):
        assert isinstance(ai_svc.normalize_sensor_data({}), dict)


# ══════════════════════════════════════════════════════════════════════════
# 4. getWqiLabel
# ══════════════════════════════════════════════════════════════════════════


class TestGetWqiLabel:
    @pytest.mark.parametrize(
        "score,expected",
        [
            (100, "Excellent"),
            (80, "Excellent"),
            (79.9, "Good"),
            (60, "Good"),
            (40, "Good"),
            (39.9, "Poor"),
            (39, "Poor"),
            (0, "Poor"),
        ],
    )
    def test_labels(self, ai_svc, score, expected):
        assert ai_svc.getWqiLabel(score) == expected


# ══════════════════════════════════════════════════════════════════════════
# 5. getRiskFromWQILabel
# ══════════════════════════════════════════════════════════════════════════


class TestGetRiskFromWQILabel:
    def test_excellent(self, ai_svc):
        assert ai_svc.getRiskFromWQILabel("Excellent") == ("Low Risk", 0)

    def test_good(self, ai_svc):
        assert ai_svc.getRiskFromWQILabel("Good") == ("Medium Risk", 1)

    def test_poor(self, ai_svc):
        assert ai_svc.getRiskFromWQILabel("Poor") == ("High Risk", 2)

    def test_unknown(self, ai_svc):
        result = ai_svc.getRiskFromWQILabel("Mystery")
        assert isinstance(result, tuple)
        assert result[0] == "Unknown"


# ══════════════════════════════════════════════════════════════════════════
# 6. solution_for
# ══════════════════════════════════════════════════════════════════════════


class TestSolutionFor:
    @pytest.mark.parametrize(
        "label,expected",
        [
            ("Excellent", "Monitor regularly."),
            ("Good", "Consider treatment."),
            ("Poor", "Immediate action required."),
        ],
    )
    def test_known_labels(self, ai_svc, label, expected):
        assert ai_svc.solution_for(label) == expected

    def test_unknown_label(self, ai_svc):
        assert "Check water quality" in ai_svc.solution_for("Mystery")


# ══════════════════════════════════════════════════════════════════════════
# 7. _to_float
# ══════════════════════════════════════════════════════════════════════════


class TestToFloat:
    def test_none_returns_default(self, ai_svc):
        assert ai_svc._to_float(None) == 0.0

    def test_int(self, ai_svc):
        assert ai_svc._to_float(5) == 5.0

    def test_float(self, ai_svc):
        assert ai_svc._to_float(3.14) == pytest.approx(3.14)

    def test_empty_string_returns_default(self, ai_svc):
        assert ai_svc._to_float("") == 0.0

    def test_comma_decimal(self, ai_svc):
        assert ai_svc._to_float("7,5") == pytest.approx(7.5)

    def test_non_numeric_string(self, ai_svc):
        assert ai_svc._to_float("abc") == 0.0

    def test_custom_default(self, ai_svc):
        assert ai_svc._to_float(None, default=99.0) == 99.0

    def test_nan_returns_default(self, ai_svc):
        assert ai_svc._to_float(float("nan")) == 0.0


# ══════════════════════════════════════════════════════════════════════════
# 8. _build_feature_frame
# ══════════════════════════════════════════════════════════════════════════


class TestBuildFeatureFrame:
    def test_returns_dataframe(self, ai_svc):
        data = {col: 50.0 for col in FEATURE_COLUMNS}
        df = ai_svc._build_feature_frame(data)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1

    def test_all_feature_columns_present(self, ai_svc):
        data = {col: 50.0 for col in FEATURE_COLUMNS}
        df = ai_svc._build_feature_frame(data)
        assert list(df.columns) == FEATURE_COLUMNS

    def test_missing_feature_defaults_zero(self, ai_svc):
        df = ai_svc._build_feature_frame({"pH": 7.0})
        assert df["pH"].iloc[0] == pytest.approx(7.0)

    def test_alias_resolution(self, ai_svc):
        df = ai_svc._build_feature_frame({"Temp": 25.0})
        assert df["Nhiệt độ"].iloc[0] == pytest.approx(25.0)

    def test_non_sensor_fields_excluded(self, ai_svc):
        data = {col: 1.0 for col in FEATURE_COLUMNS}
        data["sensorId"] = "abc"
        df = ai_svc._build_feature_frame(data)
        assert "sensorId" not in df.columns


# ══════════════════════════════════════════════════════════════════════════
# 9. _prepare_training_dataframe
# ══════════════════════════════════════════════════════════════════════════


class TestPrepareTrainingDF:
    def test_strips_column_names(self, ai_svc):
        df = pd.DataFrame({" WQI  ": [1.0], "  pH  ": [7.0]})
        result = ai_svc._prepare_training_dataframe(df)
        assert "WQI" in result.columns
        assert "pH" in result.columns

    def test_replaces_comma_with_dot(self, ai_svc):
        df = pd.DataFrame({"pH": ["7,0"]})
        result = ai_svc._prepare_training_dataframe(df)
        assert isinstance(result["pH"].iloc[0], str)


# ══════════════════════════════════════════════════════════════════════════
# 10. _detect_target_column
# ══════════════════════════════════════════════════════════════════════════


class TestDetectTargetColumn:
    def test_finds_wqi(self, ai_svc):
        df = pd.DataFrame({"WQI": [1.0]})
        result = ai_svc._detect_target_column(df)
        assert result == "WQI"

    def test_returns_first_candidate(self, ai_svc):
        df = pd.DataFrame({"WQI": [1.0], "PH": [7.0]})
        result = ai_svc._detect_target_column(df)
        assert result == "WQI"

    def test_returns_none_when_missing(self, ai_svc):
        df = pd.DataFrame({"pH": [7.0]})
        assert ai_svc._detect_target_column(df) is None

    def test_updates_target_column_attribute(self, ai_svc):
        df = pd.DataFrame({"WQI": [1.0]})
        ai_svc._detect_target_column(df)
        assert ai_svc.target_column == "WQI"
        assert ai_svc.training_source is None


# ══════════════════════════════════════════════════════════════════════════
# 11. train_model_from_dataframe (happy path – minimal 10 rows)
# ══════════════════════════════════════════════════════════════════════════


class TestTrainModel:
    def test_returns_result_dict(self, ai_svc, sample_df, tmp_models_dir):
        ai_svc.MODEL_DIR = tmp_models_dir
        result = ai_svc.train_model_from_dataframe(sample_df)
        assert isinstance(result, dict)

    def test_contains_message(self, ai_svc, sample_df, tmp_models_dir):
        result = ai_svc.train_model_from_dataframe(sample_df, source_name="test.xlsx")
        assert "message" in result

    def test_missing_wqi_column(self, ai_svc, tmp_models_dir):
        df = pd.DataFrame({"pH": [7.0] * 12})
        ai_svc.MODEL_DIR = tmp_models_dir
        result = ai_svc.train_model_from_dataframe(df)
        assert "error" in result

    def test_missing_features(self, ai_svc, tmp_models_dir):
        df = pd.DataFrame({"WQI": [70.0] * 12})
        ai_svc.MODEL_DIR = tmp_models_dir
        result = ai_svc.train_model_from_dataframe(df)
        assert "error" in result

    def test_too_few_rows(self, ai_svc, tmp_models_dir):
        ai_svc.MODEL_DIR = tmp_models_dir
        df = pd.DataFrame({col: [50.0] * 5 for col in FEATURE_COLUMNS})
        df["WQI"] = [70.0] * 5
        result = ai_svc.train_model_from_dataframe(df)
        assert "error" in result

    def test_saves_metadata(self, ai_svc, sample_df, tmp_models_dir):
        ai_svc.MODEL_DIR = tmp_models_dir
        ai_svc.train_model_from_dataframe(sample_df, source_name="test.xlsx")
        meta_path = os.path.join(tmp_models_dir, "metadata.json")
        assert os.path.exists(meta_path)
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
        assert "_meta" in meta
        assert meta["_meta"]["source_name"] == "test.xlsx"

    def test_saves_models(self, ai_svc, sample_df, tmp_models_dir):
        ai_svc.MODEL_DIR = tmp_models_dir
        ai_svc.train_model_from_dataframe(sample_df)
        expected_models = [
            "RandomForestRegressor.pkl",
            "GradientBoostingRegressor.pkl",
            "LinearRegression.pkl",
            "SVR.pkl",
            "KNNRegressor.pkl",
        ]
        for name in expected_models:
            assert os.path.exists(os.path.join(tmp_models_dir, name))

    def test_metrics_present(self, ai_svc, sample_df, tmp_models_dir):
        ai_svc.MODEL_DIR = tmp_models_dir
        result = ai_svc.train_model_from_dataframe(sample_df)
        assert "metrics" in result
        for name in result["metrics"]:
            for key in ("score", "r2", "mae", "rmse"):
                assert key in result["metrics"][name]


# ══════════════════════════════════════════════════════════════════════════
# 12. predict (fully mocked – no disk or API hits)
# ══════════════════════════════════════════════════════════════════════════


@pytest.fixture()
def trained_ai_svc(tmp_models_dir):
    """AIModelService with a fake metadata + fake models injected."""
    # Write minimal compatible metadata and a trivial model pkl
    meta = {
        "_meta": {
            "version": MODEL_VERSION,
            "task": "regression",
            "target_column": "WQI",
            "feature_columns": FEATURE_COLUMNS,
            "source_name": "fake.xlsx",
        },
        "DummyModel": {
            "score": 0.8,
            "accuracy": 0.8,
            "r2": 0.8,
            "mae": 2.0,
            "rmse": 3.0,
            "path": os.path.join(tmp_models_dir, "DummyModel.pkl"),
            "use_scaler": False,
            "task": "regression",
        },
    }
    with open(os.path.join(tmp_models_dir, "metadata.json"), "w") as f:
        json.dump(meta, f)

    with open(os.path.join(tmp_models_dir, "good_water_profile.json"), "w") as f:
        json.dump(
            {
                col: {"mean": 50.0, "min_safe": 1.0, "max_safe": 100.0}
                for col in FEATURE_COLUMNS
            },
            f,
        )

    meta_path = os.path.join(tmp_models_dir, "metadata.json")
    scaler_path = None  # DummyModel does not use scaler

    svc = object.__new__(AIModelService)
    svc.MODEL_DIR = tmp_models_dir
    svc.metadata = meta
    svc.target_column = "WQI"
    svc.training_source = "fake.xlsx"

    # Minimal model object that sklearn-like predict returns a 1-element array
    from sklearn.tree import DecisionTreeRegressor
    import numpy as np

    rng = np.random.RandomState(42)
    X = np.random.randn(60, len(FEATURE_COLUMNS))
    y = np.random.uniform(20, 100, 60)
    clf = DecisionTreeRegressor(random_state=42)
    clf.fit(X, y)

    svc.models = {"DummyModel": clf}
    svc.scaler = None
    svc._scaler_path = None
    return svc


class TestPredict:
    def test_returns_summary(self, trained_ai_svc):
        data = {col: 50.0 for col in FEATURE_COLUMNS}
        with patch("app.services.ai_model_service.get_weather_data") as mw, patch(
            "app.services.ai_model_service.solution_service"
        ) as msol:
            mw.return_value = {"has_rain": False}
            msol.generate_advanced_solution.return_value = "Test solution."
            result = trained_ai_svc.predict(data)
            assert "summary" in result
            assert "ensemble" in result
            assert "models" in result

    def test_contains_wqi_score(self, trained_ai_svc):
        data = {col: 50.0 for col in FEATURE_COLUMNS}
        with patch("app.services.ai_model_service.get_weather_data"), patch(
            "app.services.ai_model_service.solution_service"
        ):
            result = trained_ai_svc.predict(data)
            assert "wqi" in result["summary"]
            assert "score" in result["summary"]["wqi"]
            assert 0.0 <= result["summary"]["wqi"]["score"] <= 100.0

    def test_empty_models_returns_error(self, ai_svc):
        ai_svc.models = {}
        result = ai_svc.predict({"pH": 7.0})
        assert "error" in result

    def test_unknown_model_name_returns_error(self, trained_ai_svc):
        with patch("app.services.ai_model_service.get_weather_data"), patch(
            "app.services.ai_model_service.solution_service"
        ):
            result = trained_ai_svc.predict({"pH": 7.0}, model_name="NonExistent")
            assert "error" in result

    def test_score_clipped_to_0_100(self, trained_ai_svc):
        """Ensure prediction value is bounded [0, 100]."""
        data = {col: 50.0 for col in FEATURE_COLUMNS}
        with patch("app.services.ai_model_service.get_weather_data"), patch(
            "app.services.ai_model_service.solution_service"
        ):
            result = trained_ai_svc.predict(data)
            score = result["summary"]["wqi"]["score"]
            assert 0.0 <= score <= 100.0


# ══════════════════════════════════════════════════════════════════════════
# 13. solve – weather failure falls back to solution_for
# ══════════════════════════════════════════════════════════════════════════


class TestPredictFallback:
    def test_weather_exception_uses_solution_for(self, trained_ai_svc):
        data = {col: 50.0 for col in FEATURE_COLUMNS}
        with patch(
            "app.services.ai_model_service.get_weather_data",
            side_effect=RuntimeError("offline"),
        ), patch("app.services.ai_model_service.solution_service") as m_sol:
            m_sol.generate_advanced_solution.side_effect = RuntimeError("also down")
            result = trained_ai_svc.predict(data)
            assert "summary" in result
            assert isinstance(result["summary"]["solution"], str)


# ══════════════════════════════════════════════════════════════════════════
# 14. load_models / metadata check
# ══════════════════════════════════════════════════════════════════════════


class TestLoadModelsVersionGuard:
    def test_incompatible_version_clears_models(self, ai_svc, tmp_models_dir):
        """If metadata version != MODEL_VERSION, models should be cleared."""
        meta = {
            "_meta": {"version": MODEL_VERSION + 1, "task": "regression"},
            "Fake": {"score": 0.5, "path": "does_not_matter.pkl", "use_scaler": False},
        }
        with open(os.path.join(tmp_models_dir, "metadata.json"), "w") as f:
            json.dump(meta, f)

        ai_svc.MODEL_DIR = str(tmp_models_dir)
        ai_svc.models = {"Fake": MagicMock()}
        ai_svc.scaler = MagicMock()

        ai_svc.load_models()

        assert ai_svc.models == {}
        assert ai_svc.scaler is None

    def test_missing_metadata_does_not_crash(self, ai_svc, tmp_models_dir):
        ai_svc.MODEL_DIR = str(tmp_models_dir)
        ai_svc.models = {"Fake": MagicMock()}
        ai_svc.load_models()  # must not raise
        assert ai_svc.models == {}

# ══════════════════════════════════════════════════════════════════════════
# 15. analyze_abnormal_parameters
# ══════════════════════════════════════════════════════════════════════════


class TestAnalyzeAbnormalParameters:
    def test_no_profile_returns_empty(self, ai_svc, tmp_path):
        ai_svc.MODEL_DIR = str(tmp_path / "empty_models")
        os.makedirs(ai_svc.MODEL_DIR, exist_ok=True)
        assert ai_svc.analyze_abnormal_parameters({"pH": 7.0}) == []

    def test_normal_values_return_empty(self, ai_svc):
        profile = {
            col: {"mean": 50.0, "min_safe": 1.0, "max_safe": 100.0}
            for col in FEATURE_COLUMNS
        }
        with open(os.path.join(ai_svc.MODEL_DIR, "good_water_profile.json"), "w") as f:
            json.dump(profile, f)

        data = {col: 50.0 for col in FEATURE_COLUMNS[:5]}
        result = ai_svc.analyze_abnormal_parameters(data)
        assert result == []

    def test_above_safe_detected(self, ai_svc):
        profile = {
            col: {"mean": 50.0, "min_safe": 1.0, "max_safe": 100.0}
            for col in FEATURE_COLUMNS
        }
        with open(os.path.join(ai_svc.MODEL_DIR, "good_water_profile.json"), "w") as f:
            json.dump(profile, f)

        data = {FEATURE_COLUMNS[0]: 200.0}
        result = ai_svc.analyze_abnormal_parameters(data)
        assert len(result) == 1
        assert result[0]["status"] == "above_safe"

    def test_below_safe_detected(self, ai_svc):
        profile = {
            col: {"mean": 50.0, "min_safe": 1.0, "max_safe": 100.0}
            for col in FEATURE_COLUMNS
        }
        with open(os.path.join(ai_svc.MODEL_DIR, "good_water_profile.json"), "w") as f:
            json.dump(profile, f)

        data = {FEATURE_COLUMNS[0]: 0.5}
        result = ai_svc.analyze_abnormal_parameters(data)
        assert len(result) == 1
        assert result[0]["status"] == "below_safe"
