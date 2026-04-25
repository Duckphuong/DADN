from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class GetAnalyticsTrendsQuery:
    user_id: str
    target_date: date | None = None
