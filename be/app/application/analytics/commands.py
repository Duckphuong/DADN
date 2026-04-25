from dataclasses import dataclass


@dataclass(frozen=True)
class GetAnalyticsTrendsQuery:
    user_id: str

