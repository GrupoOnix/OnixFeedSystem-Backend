from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from domain.enums import ActivityLogCategory, ActivityLogEventType
from domain.value_objects.identifiers import CageId


@dataclass(frozen=True)
class ActivityLogEntry:
    """
    Value Object que representa un registro de actividad de una jaula.
    Inmutable, solo se crea y se consulta.
    """

    log_id: UUID
    cage_id: CageId
    event_type: ActivityLogEventType
    category: ActivityLogCategory
    message: str
    details: Optional[str]
    actor: Optional[str]
    source_entity_type: Optional[str]
    source_entity_id: Optional[str]
    event_at: datetime
    created_at: datetime

    @staticmethod
    def create(
        cage_id: CageId,
        event_type: ActivityLogEventType,
        category: ActivityLogCategory,
        message: str,
        details: Optional[str] = None,
        actor: Optional[str] = None,
        source_entity_type: Optional[str] = None,
        source_entity_id: Optional[str] = None,
    ) -> "ActivityLogEntry":
        """Factory method para crear un nuevo registro de actividad."""
        now = datetime.now(timezone.utc)
        return ActivityLogEntry(
            log_id=uuid4(),
            cage_id=cage_id,
            event_type=event_type,
            category=category,
            message=message,
            details=details,
            actor=actor,
            source_entity_type=source_entity_type,
            source_entity_id=source_entity_id,
            event_at=now,
            created_at=now,
        )
