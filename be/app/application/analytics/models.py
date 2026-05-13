from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DateRange:
    start_time: datetime
    end_time: datetime


@dataclass(frozen=True)
class BucketWindow:
    label: str
    start_time: datetime
    end_time: datetime


@dataclass(frozen=True)
class TrendPoint:
    time: str
    value: float | None


@dataclass(frozen=True)
class TurbidityComparisonPoint:
    sensor_id: str
    sensor_name: str
    address: str | None
    value: float


@dataclass(frozen=True)
class AnalyticsTrendsResult:
    user_id: str
    date_range: DateRange
    ph_trend: list[TrendPoint]
    temperature_trend: list[TrendPoint]
    conductivity_trend: list[TrendPoint]
    dissolved_oxygen_trend: list[TrendPoint]
    turbidity_comparison: list[TurbidityComparisonPoint]

