from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class FeedingRateTimelineVisit:
    session_id: str
    feeding_type: str
    line_id: str
    cage_id: str
    completed_at: datetime
    duration_seconds: float
    dispensed_kg: float
