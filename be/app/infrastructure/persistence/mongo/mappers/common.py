from datetime import datetime

from app.domain.shared.time import ensure_utc_datetime


def parse_document_datetime(value: datetime | str | None) -> datetime:
    if isinstance(value, datetime):
        return ensure_utc_datetime(value)

    if isinstance(value, str):
        normalized_value = value.replace("Z", "+00:00")
        return ensure_utc_datetime(datetime.fromisoformat(normalized_value))

    return ensure_utc_datetime(datetime.min.replace(year=1970, month=1, day=1))


def to_document_datetime(value: datetime) -> datetime:
    return ensure_utc_datetime(value)
