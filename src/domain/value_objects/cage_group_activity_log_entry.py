from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from domain.enums import ActivityLogCategory, ActivityLogEventType
from domain.value_objects.identifiers import CageGroupId


@dataclass(frozen=True)
class CageGroupActivityLogEntry:
    """
    Value Object que representa un registro de actividad de un grupo de jaulas.
    Inmutable, solo se crea y se consulta.
    """

    log_id: UUID
    cage_group_id: CageGroupId
    event_type: ActivityLogEventType
    category: ActivityLogCategory
    message: str
    details: Optional[str]
    actor: Optional[str]
    event_at: datetime
    created_at: datetime

    @staticmethod
    def create(
        cage_group_id: CageGroupId,
        event_type: ActivityLogEventType,
        category: ActivityLogCategory,
        message: str,
        details: Optional[str] = None,
        actor: Optional[str] = None,
    ) -> "CageGroupActivityLogEntry":
        """Factory method para crear un nuevo registro de actividad."""
        now = datetime.now(timezone.utc)
        return CageGroupActivityLogEntry(
            log_id=uuid4(),
            cage_group_id=cage_group_id,
            event_type=event_type,
            category=category,
            message=message,
            details=details,
            actor=actor,
            event_at=now,
            created_at=now,
        )
