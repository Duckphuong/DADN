"""
Unit tests for prediction_validators.

These are pure unit tests for validator functions and don't depend on
external services or the deployed backend. They test data validation logic.

Covers:
  - validate_predict_request
  - validate_predict_request_with_time
  - parse_prediction_timestamp
  - _get_prediction_timestamp_value
"""

import pytest
from datetime import datetime, timezone

from app.presentation.http.validators.prediction_validators import (
    validate_predict_request,
    validate_predict_request_with_time,
    parse_prediction_timestamp,
    _get_prediction_timestamp_value,
    PREDICTION_TIMESTAMP_FIELD_ALIASES,
)
from app.application.common.exceptions import ValidationError

# ══════════════════════════════════════════════════════════════════════════
# validate_predict_request
# ══════════════════════════════════════════════════════════════════════════


class TestValidatePredictRequest:
    def test_none_raises(self):
        with pytest.raises(ValidationError, match="Invalid JSON payload"):
            validate_predict_request(None)

    def test_list_raises(self):
        with pytest.raises(ValidationError, match="Invalid JSON payload"):
            validate_predict_request([1, 2, 3])

    def test_string_raises(self):
        with pytest.raises(ValidationError, match="Invalid JSON payload"):
            validate_predict_request("hello")

    def test_int_raises(self):
        with pytest.raises(ValidationError, match="Invalid JSON payload"):
            validate_predict_request(42)

    def test_valid_dict_returns_same(self):
        payload = {"pH": 7.0, "sensorId": "abc"}
        assert validate_predict_request(payload) is payload

    def test_empty_dict_returns_empty(self):
        assert validate_predict_request({}) is not None

    def test_does_not_modify_payload(self):
        payload = {"key": [1, 2]}
        validate_predict_request(payload)
        assert payload == {"key": [1, 2]}


# ══════════════════════════════════════════════════════════════════════════
# parse_prediction_timestamp
# ══════════════════════════════════════════════════════════════════════════


class TestParsePredictionTimestamp:
    def test_datetime_input(self):
        dt = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = parse_prediction_timestamp(dt)
        assert result.tzinfo is not None

    def test_naive_datetime_made_utc(self):
        dt = datetime(2025, 1, 1, 12, 0, 0)
        result = parse_prediction_timestamp(dt)
        assert result.tzinfo is not None

    def test_valid_iso_string(self):
        result = parse_prediction_timestamp("2025-01-01T12:00:00+00:00")
        assert isinstance(result, datetime)

    def test_z_suffix_converted(self):
        result = parse_prediction_timestamp("2025-01-01T12:00:00Z")
        assert result.tzinfo is not None
        assert result.year == 2025

    def test_whitespace_stripped(self):
        result = parse_prediction_timestamp("  2025-01-01T12:00:00+00:00  ")
        assert isinstance(result, datetime)

    def test_empty_string_raises(self):
        with pytest.raises(ValidationError):
            parse_prediction_timestamp("")

    def test_non_datetime_non_string_raises(self):
        with pytest.raises(ValidationError):
            parse_prediction_timestamp(42)

    def test_invalid_string_raises(self):
        with pytest.raises(ValidationError):
            parse_prediction_timestamp("not-a-date")

    def test_list_raises(self):
        with pytest.raises(ValidationError):
            parse_prediction_timestamp(["2025-01-01"])
            parse_prediction_timestamp([1, 2, 3])


# ══════════════════════════════════════════════════════════════════════════
# _get_prediction_timestamp_value
# ══════════════════════════════════════════════════════════════════════════


class TestGetPredictionTimestampValue:
    def test_returns_value_for_created_at(self):
        payload = {"createdAt": "2025-01-01T00:00:00Z"}
        result = _get_prediction_timestamp_value(payload)
        assert result == "2025-01-01T00:00:00Z"

    def test_returns_value_for_created_at_underscore(self):
        payload = {"created_at": "2025-01-01T00:00:00Z"}
        result = _get_prediction_timestamp_value(payload)
        assert result == "2025-01-01T00:00:00Z"

    def test_returns_value_for_timestamp_field(self):
        payload = {"timestamp": "2025-01-01T00:00:00Z"}
        result = _get_prediction_timestamp_value(payload)
        assert result == "2025-01-01T00:00:00Z"

    def test_returns_value_for_time_field(self):
        payload = {"time": "2025-01-01T00:00:00Z"}
        result = _get_prediction_timestamp_value(payload)
        assert result == "2025-01-01T00:00:00Z"

    def test_returns_none_when_missing(self):
        payload = {"pH": 7.0}
        assert _get_prediction_timestamp_value(payload) is None

    def test_returns_none_for_empty_payload(self):
        assert _get_prediction_timestamp_value({}) is None

    def test_aliases_defined(self):
        assert "createdAt" in PREDICTION_TIMESTAMP_FIELD_ALIASES
        assert "created_at" in PREDICTION_TIMESTAMP_FIELD_ALIASES
        assert "timestamp" in PREDICTION_TIMESTAMP_FIELD_ALIASES
        assert "time" in PREDICTION_TIMESTAMP_FIELD_ALIASES


# ══════════════════════════════════════════════════════════════════════════
# validate_predict_request_with_time
# ══════════════════════════════════════════════════════════════════════════


class TestValidatePredictRequestWithTime:
    def test_valid_payload_returns_tuple(self):
        payload = {"createdAt": "2025-01-01T00:00:00Z", "pH": 7.0}
        result = validate_predict_request_with_time(payload)
        assert isinstance(result, tuple)
        assert len(result) == 2
        data, ts = result
        assert isinstance(data, dict)
        assert isinstance(ts, datetime)

    def test_none_payload_raises(self):
        with pytest.raises(ValidationError, match="Invalid JSON payload"):
            validate_predict_request_with_time(None)

    def test_missing_timestamp_raises(self):
        with pytest.raises(ValidationError, match="createdAt is required"):
            validate_predict_request_with_time({"pH": 7.0})

    def test_returns_parsed_datetime(self):
        payload = {"created_at": "2025-06-15T08:00:00+00:00"}
        _, ts = validate_predict_request_with_time(payload)
        assert ts.hour == 8
        assert ts.year == 2025

    def test_list_payload_raises(self):
        with pytest.raises(ValidationError, match="Invalid JSON payload"):
            validate_predict_request_with_time([])

    def test_empty_dict_raises(self):
        with pytest.raises(ValidationError, match="createdAt is required"):
            validate_predict_request_with_time({})
