import re
from datetime import date

from app.application.analytics.commands import GetAnalyticsTrendsQuery
from app.application.common.exceptions import ValidationError


def validate_get_analytics_trends_request(
    user_id: str | None,
    *,
    requested_date: str | None = None,
) -> GetAnalyticsTrendsQuery:
    normalized_user_id = (user_id or "").strip()
    if not normalized_user_id:
        raise ValidationError("Authenticated user id is required")
    return GetAnalyticsTrendsQuery(
        user_id=normalized_user_id,
        target_date=_parse_requested_date(requested_date),
    )


def _parse_requested_date(value: str | None) -> date | None:
    normalized_value = (value or "").strip()
    if not normalized_value:
        return None

    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", normalized_value) is None:
        raise ValidationError("date must be a valid date in YYYY-MM-DD format")

    try:
        return date.fromisoformat(normalized_value)
    except ValueError as exc:
        raise ValidationError(
            "date must be a valid date in YYYY-MM-DD format"
        ) from exc
