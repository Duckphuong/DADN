from datetime import datetime

from app.application.common.exceptions import ValidationError
from app.domain.shared.time import ensure_utc_datetime


PREDICTION_TIMESTAMP_FIELD_ALIASES = (
    "createdAt",
    "created_at",
    "timestamp",
    "time",
)


def validate_predict_request(payload: dict | None) -> dict:
    if not isinstance(payload, dict):
        raise ValidationError("Invalid JSON payload")
    return payload


def validate_predict_request_with_time(payload: dict | None) -> tuple[dict, datetime]:
    validated_payload = validate_predict_request(payload)
    timestamp_value = _get_prediction_timestamp_value(validated_payload)
    if timestamp_value is None:
        raise ValidationError(
            "createdAt is required. Accepted aliases: createdAt, created_at, timestamp, time"
        )
    return validated_payload, parse_prediction_timestamp(timestamp_value)


def parse_prediction_timestamp(value) -> datetime:
    if isinstance(value, datetime):
        return ensure_utc_datetime(value)

    if not isinstance(value, str):
        raise ValidationError("createdAt must be an ISO 8601 datetime string")

    normalized_value = value.strip()
    if not normalized_value:
        raise ValidationError("createdAt must not be empty")

    if normalized_value.endswith("Z"):
        normalized_value = normalized_value[:-1] + "+00:00"

    try:
        parsed_value = datetime.fromisoformat(normalized_value)
    except ValueError as exc:
        raise ValidationError("createdAt must be a valid ISO 8601 datetime") from exc

    return ensure_utc_datetime(parsed_value)


def _get_prediction_timestamp_value(payload: dict):
    for field_name in PREDICTION_TIMESTAMP_FIELD_ALIASES:
        if field_name in payload:
            return payload.get(field_name)
    return None
