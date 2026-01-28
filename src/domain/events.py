from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

from domain.enums import FeedingEventType


@dataclass(frozen=True)
class FeedingEvent:
    timestamp: datetime
    type: FeedingEventType
    description: str
    details: Dict[str, Any]
