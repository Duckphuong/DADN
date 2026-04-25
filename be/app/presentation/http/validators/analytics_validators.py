from app.application.analytics.commands import GetAnalyticsTrendsQuery
from app.application.common.exceptions import ValidationError


def validate_get_analytics_trends_request(
    user_id: str | None,
) -> GetAnalyticsTrendsQuery:
    normalized_user_id = (user_id or "").strip()
    if not normalized_user_id:
        raise ValidationError("Authenticated user id is required")
    return GetAnalyticsTrendsQuery(user_id=normalized_user_id)
