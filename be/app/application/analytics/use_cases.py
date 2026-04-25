from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.application.analytics.commands import GetAnalyticsTrendsQuery
from app.application.analytics.interfaces import AnalyticsRepository
from app.application.analytics.models import AnalyticsTrendsResult
from app.application.analytics.time_buckets import (
    build_trend_output,
    get_server_timezone,
    get_yesterday_date_range,
)
from app.application.common.exceptions import ValidationError


class GetAnalyticsTrendsUseCase:
    def __init__(
        self,
        analytics_repository: AnalyticsRepository,
        *,
        timezone_name: str | None = None,
    ) -> None:
        self._analytics_repository = analytics_repository
        self._timezone_name = timezone_name

    def execute(self, query: GetAnalyticsTrendsQuery) -> AnalyticsTrendsResult:
        user_id = (query.user_id or "").strip()
        if not user_id:
            raise ValidationError("userId is required")

        app_timezone = _resolve_timezone(self._timezone_name)
        timezone_name = self._timezone_name or _timezone_to_mongo_name(app_timezone)
        date_range = get_yesterday_date_range(timezone=app_timezone)

        bucket_averages = self._analytics_repository.get_trend_bucket_averages(
            user_id=user_id,
            date_range=date_range,
            timezone_name=timezone_name,
        )
        turbidity_comparison = (
            self._analytics_repository.get_random_turbidity_comparison(
                user_id=user_id,
                date_range=date_range,
                sample_size=6,
            )
        )

        return AnalyticsTrendsResult(
            user_id=user_id,
            date_range=date_range,
            ph_trend=build_trend_output(bucket_averages.get("phTrend", {})),
            temperature_trend=build_trend_output(
                bucket_averages.get("temperatureTrend", {})
            ),
            conductivity_trend=build_trend_output(
                bucket_averages.get("conductivityTrend", {})
            ),
            dissolved_oxygen_trend=build_trend_output(
                bucket_averages.get("dissolvedOxygenTrend", {})
            ),
            turbidity_comparison=turbidity_comparison,
        )


def _timezone_to_mongo_name(timezone) -> str:
    zone_name = getattr(timezone, "key", None)
    if zone_name:
        return zone_name

    now = get_yesterday_date_range(timezone=timezone).end_time
    offset = now.strftime("%z")
    if len(offset) == 5:
        return f"{offset[:3]}:{offset[3:]}"
    return "UTC"


def _resolve_timezone(timezone_name: str | None):
    if not timezone_name:
        return get_server_timezone()
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValidationError("Invalid analytics timezone") from exc
