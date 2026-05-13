from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GetLatestSensorDataQuery:
    sensor_id: Optional[str] = None


@dataclass(frozen=True)
class GetSensorClassificationQuery:
    sensor_id: Optional[str] = None