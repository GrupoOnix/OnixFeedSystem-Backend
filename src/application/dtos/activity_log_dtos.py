from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from application.dtos.cage_dtos import PaginationInfo


@dataclass
class ActivityLogItemResponse:
    """DTO de respuesta para un registro de actividad de jaula."""

    log_id: str
    cage_id: str
    event_type: str
    category: str
    message: str
    details: Optional[str]
    actor: Optional[str]
    source_entity_type: Optional[str]
    source_entity_id: Optional[str]
    event_at: datetime
    created_at: datetime


@dataclass
class PaginatedActivityLogResponse:
    """DTO de respuesta paginado para registros de actividad de jaula."""

    logs: List[ActivityLogItemResponse]
    pagination: PaginationInfo
