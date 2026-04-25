from datetime import datetime, time, timedelta, tzinfo

from app.application.analytics.models import BucketWindow, DateRange, TrendPoint


BUCKET_LABELS = ("00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "23:00")
BUCKET_START_HOURS = (0, 4, 8, 12, 16, 20, 23)


def get_server_timezone() -> tzinfo:
    return datetime.now().astimezone().tzinfo


def get_yesterday_date_range(
    *,
    now: datetime | None = None,
    timezone: tzinfo | None = None,
) -> DateRange:
    active_timezone = timezone or get_server_timezone()
    localized_now = _ensure_timezone(
        now or datetime.now(active_timezone),
        active_timezone,
    )
    start_of_today = datetime.combine(
        localized_now.date(),
        time.min,
        tzinfo=active_timezone,
    )
    start_of_yesterday = start_of_today - timedelta(days=1)
    return DateRange(start_time=start_of_yesterday, end_time=start_of_today)


def build_dashboard_buckets(date_range: DateRange) -> list[BucketWindow]:
    return [
        BucketWindow(
            label=label,
            start_time=date_range.start_time + timedelta(hours=start_hour),
            end_time=_bucket_end_time(date_range, index),
        )
        for index, (label, start_hour) in enumerate(
            zip(BUCKET_LABELS, BUCKET_START_HOURS)
        )
    ]


def map_timestamp_to_bucket(
    timestamp: datetime,
    buckets: list[BucketWindow],
    *,
    timezone: tzinfo | None = None,
) -> str | None:
    if not buckets:
        return None

    active_timezone = (
        timezone
        or buckets[0].start_time.tzinfo
        or get_server_timezone()
    )
    localized_timestamp = _ensure_timezone(timestamp, active_timezone)
    for bucket in buckets:
        if bucket.start_time <= localized_timestamp < bucket.end_time:
            return bucket.label
    return None


def build_trend_output(bucket_averages: dict[str, float | None]) -> list[TrendPoint]:
    return [
        TrendPoint(time=label, value=_round_or_none(bucket_averages.get(label)))
        for label in BUCKET_LABELS
    ]


def _bucket_end_time(date_range: DateRange, bucket_index: int) -> datetime:
    if bucket_index + 1 >= len(BUCKET_START_HOURS):
        return date_range.end_time
    return date_range.start_time + timedelta(
        hours=BUCKET_START_HOURS[bucket_index + 1]
    )


def _ensure_timezone(value: datetime, timezone: tzinfo) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone)
    return value.astimezone(timezone)


def _round_or_none(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 2)
