from datetime import datetime

from app.domain.shared.time import ensure_utc_datetime


def serialize_utc_datetime(value: datetime) -> str:
    normalized_value = ensure_utc_datetime(value)
    return normalized_value.isoformat(timespec="milliseconds").replace("+00:00", "Z")
