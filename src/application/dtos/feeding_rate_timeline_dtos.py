from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class RateTimelineSummaryDTO:
    total_dispensed_kg: float
    active_minutes: int
    avg_active_rate_kg_per_min: float
    peak_total_rate_kg_per_min: float
    peak_total_rate_at: datetime | None
    max_overlapping_sessions: int


@dataclass
class TotalRateTimelinePointDTO:
    timestamp: datetime
    rate_kg_per_min: float
    active_sessions: int


@dataclass
class RateTimelinePointDTO:
    timestamp: datetime
    rate_kg_per_min: float
    dispensed_kg: float
    active_sessions: int


@dataclass
class RateTimelineSeriesDTO:
    id: str
    name: str
    kind: str
    color_hint: str
    points: List[RateTimelinePointDTO]


@dataclass
class FeedingRateTimelineDTO:
    start_at: datetime
    end_at: datetime
    bucket_seconds: int
    timezone: str
    summary: RateTimelineSummaryDTO
    total_series: List[TotalRateTimelinePointDTO]
    series: List[RateTimelineSeriesDTO]
