from datetime import datetime
from typing import List, Optional

from application.dtos.activity_log_dtos import ActivityLogItemResponse, PaginatedActivityLogResponse
from application.dtos.cage_dtos import PaginationInfo
from domain.enums import ActivityLogCategory, ActivityLogEventType
from domain.repositories import ICageActivityLogRepository
from domain.value_objects import CageId


class ListActivityLogUseCase:
    """Lista los registros de actividad de una jaula con filtros y paginación."""

    def __init__(self, activity_log_repository: ICageActivityLogRepository):
        self._repo = activity_log_repository

    async def execute(
        self,
        cage_id: str,
        event_type: Optional[List[str]] = None,
        category: Optional[List[str]] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> PaginatedActivityLogResponse:
        cage_id_vo = CageId.from_string(cage_id)

        event_type_enums = [ActivityLogEventType(e) for e in event_type] if event_type else None
        category_enums = [ActivityLogCategory(c) for c in category] if category else None

        entries = await self._repo.list_by_cage(
            cage_id_vo,
            event_type=event_type_enums,
            category=category_enums,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset,
        )
        total = await self._repo.count_by_cage(
            cage_id_vo,
            event_type=event_type_enums,
            category=category_enums,
            from_date=from_date,
            to_date=to_date,
        )

        logs = [
            ActivityLogItemResponse(
                log_id=str(entry.log_id),
                cage_id=str(entry.cage_id.value),
                event_type=entry.event_type.value,
                category=entry.category.value,
                message=entry.message,
                details=entry.details,
                actor=entry.actor,
                source_entity_type=entry.source_entity_type,
                source_entity_id=entry.source_entity_id,
                event_at=entry.event_at,
                created_at=entry.created_at,
            )
            for entry in entries
        ]

        pagination = PaginationInfo(
            total=total,
            limit=limit,
            offset=offset,
            has_next=(offset + limit) < total,
            has_previous=offset > 0,
        )

        return PaginatedActivityLogResponse(logs=logs, pagination=pagination)
