from typing import Protocol

from app.application.analytics.models import DateRange, TurbidityComparisonPoint


class AnalyticsRepository(Protocol):
    def get_trend_bucket_averages(
        self,
        *,
        user_id: str,
        date_range: DateRange,
        timezone_name: str,
    ) -> dict[str, dict[str, float | None]]:
        raise NotImplementedError

    def get_random_turbidity_comparison(
        self,
        *,
        user_id: str,
        date_range: DateRange,
        sample_size: int,
    ) -> list[TurbidityComparisonPoint]:
        raise NotImplementedError

