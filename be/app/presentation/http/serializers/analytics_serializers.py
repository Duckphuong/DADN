from datetime import datetime

from app.application.analytics.models import AnalyticsTrendsResult


def serialize_analytics_trends(result: AnalyticsTrendsResult) -> dict:
    return {
        "userId": result.user_id,
        "dateRange": {
            "startTime": _serialize_datetime(result.date_range.start_time),
            "endTime": _serialize_datetime(result.date_range.end_time),
        },
        "phTrend": [_serialize_trend_point(point) for point in result.ph_trend],
        "temperatureTrend": [
            _serialize_trend_point(point) for point in result.temperature_trend
        ],
        "conductivityTrend": [
            _serialize_trend_point(point) for point in result.conductivity_trend
        ],
        "dissolvedOxygenTrend": [
            _serialize_trend_point(point) for point in result.dissolved_oxygen_trend
        ],
        "turbidityComparison": [
            {
                "sensorId": point.sensor_id,
                "sensorName": point.sensor_name,
                "address": point.address,
                "value": point.value,
            }
            for point in result.turbidity_comparison
        ],
    }


def _serialize_trend_point(point) -> dict:
    return {"time": point.time, "value": point.value}


def _serialize_datetime(value: datetime) -> str:
    return value.isoformat()

