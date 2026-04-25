from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.shared.time import ensure_utc_datetime, utc_now


@dataclass(slots=True)
class PredictModule:
    wqi_score: float
    contamination_risk: str
    forecast_24h: str
    predicted_wqi: str
    confidence: float
    message: str
    status: str
    time_ago: str
    input_sensor_id: str
    id_sensor: str
    is_email_processed: bool
    created_at: datetime
    updated_at: datetime
    id: Optional[str] = None

    @classmethod
    def create_new(
        cls,
        *,
        wqi_score: float,
        contamination_risk: str,
        forecast_24h: str,
        predicted_wqi: str,
        confidence: float,
        message: str,
        input_sensor_id: str,
        id_sensor: str,
        timestamp: datetime | None = None,
    ) -> "PredictModule":
        resolved_timestamp = ensure_utc_datetime(timestamp) if timestamp else utc_now()
        return cls(
            wqi_score=wqi_score,
            contamination_risk=contamination_risk,
            forecast_24h=forecast_24h,
            predicted_wqi=predicted_wqi,
            confidence=confidence,
            message=message,
            status="unread",
            time_ago="",
            input_sensor_id=input_sensor_id,
            id_sensor=id_sensor,
            is_email_processed=False,
            created_at=resolved_timestamp,
            updated_at=resolved_timestamp,
        )

    def mark_email_processed(self) -> None:
        self.is_email_processed = True
        self.updated_at = utc_now()
