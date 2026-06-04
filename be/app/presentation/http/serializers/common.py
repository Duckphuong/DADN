# be/app/presentation/http/serializers/common.py
from datetime import datetime
from zoneinfo import ZoneInfo

from app.domain.shared.time import ensure_utc_datetime


def serialize_utc_datetime(value: datetime) -> str:
    """
    Trả về chuỗi ISO UTC (Z) với milliseconds:
    2026-06-04T11:30:00.123Z
    """
    normalized_value = ensure_utc_datetime(value)
    return normalized_value.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def serialize_local_datetime(
    value: datetime,
    tz_name: str = "Asia/Ho_Chi_Minh",
    fmt_iso: bool = True,
) -> str:
    """
    Chuyển datetime (được chuẩn hoá sang UTC) sang timezone chỉ định (mặc định VN)
    Nếu fmt_iso True: trả ISO string có offset (ví dụ "2026-06-04T18:30:00.123+07:00")
    Nếu fmt_iso False: trả chuỗi friendly (ví dụ "2026-06-04 18:30:00 +07:00")
    """
    if value is None:
        return ""
    normalized_value = ensure_utc_datetime(value)
    try:
        local_tz = ZoneInfo(tz_name)
    except Exception:
        local_tz = ZoneInfo("UTC")
    local_dt = normalized_value.astimezone(local_tz)
    if fmt_iso:
        return local_dt.isoformat(timespec="milliseconds")
    return local_dt.strftime("%Y-%m-%d %H:%M:%S %z")