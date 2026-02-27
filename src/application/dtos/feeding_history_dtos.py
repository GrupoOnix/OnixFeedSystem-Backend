from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class FeedingHistoryItemDTO:
    session_id: str
    type: str
    status: str
    line_name: str
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    duration_seconds: Optional[int]
    dispensed_kg: float


@dataclass
class FeedingHistoryPaginationDTO:
    total: int
    limit: int
    offset: int
    has_next: bool
    has_previous: bool


@dataclass
class CageFeedingHistoryDTO:
    items: List[FeedingHistoryItemDTO]
    pagination: FeedingHistoryPaginationDTO
