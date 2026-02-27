from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from application.dtos.feeding_history_dtos import (
    CageFeedingHistoryDTO,
    FeedingHistoryItemDTO,
    FeedingHistoryPaginationDTO,
)
from infrastructure.persistence.models.cage_feeding_model import CageFeedingModel
from infrastructure.persistence.models.feeding_line_model import FeedingLineModel
from infrastructure.persistence.models.feeding_session_model import FeedingSessionModel


class GetCageFeedingHistoryUseCase:
    """
    Retorna el historial paginado de alimentaciones de una jaula.

    Hace join de cage_feedings → feeding_sessions → feeding_lines.
    El dispensed_kg es el específico de esa CageFeeding (por jaula).
    El tipo y estado provienen de la FeedingSession.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def execute(
        self,
        cage_id: str,
        limit: int = 10,
        offset: int = 0,
    ) -> CageFeedingHistoryDTO:
        cage_uuid = UUID(cage_id)

        # cage_feedings.feeding_session_id (str) == feeding_sessions.id (str)
        # No se requiere cast — ambos son VARCHAR.
        join_condition = CageFeedingModel.feeding_session_id == FeedingSessionModel.id

        stmt = (
            select(
                CageFeedingModel.feeding_session_id,
                FeedingSessionModel.type,
                FeedingSessionModel.status,
                FeedingLineModel.name.label("line_name"),
                FeedingSessionModel.actual_start,
                FeedingSessionModel.actual_end,
                CageFeedingModel.dispensed_kg,
            )
            .join(FeedingSessionModel, join_condition)
            .join(FeedingLineModel, FeedingSessionModel.line_id == FeedingLineModel.id)
            .where(CageFeedingModel.cage_id == cage_uuid)
            .order_by(desc(FeedingSessionModel.actual_start))
        )

        count_stmt = (
            select(func.count())
            .select_from(CageFeedingModel)
            .join(FeedingSessionModel, join_condition)
            .where(CageFeedingModel.cage_id == cage_uuid)
        )

        total = (await self._session.execute(count_stmt)).scalar_one()
        rows = (await self._session.execute(stmt.limit(limit).offset(offset))).all()

        items = []
        for row in rows:
            started_at = row.actual_start
            ended_at = row.actual_end
            duration_seconds = None
            if started_at and ended_at:
                duration_seconds = int((ended_at - started_at).total_seconds())

            items.append(
                FeedingHistoryItemDTO(
                    session_id=str(row.feeding_session_id),
                    type=row.type,
                    status=row.status,
                    line_name=row.line_name,
                    started_at=started_at,
                    ended_at=ended_at,
                    duration_seconds=duration_seconds,
                    dispensed_kg=row.dispensed_kg,
                )
            )

        return CageFeedingHistoryDTO(
            items=items,
            pagination=FeedingHistoryPaginationDTO(
                total=total,
                limit=limit,
                offset=offset,
                has_next=(offset + limit) < total,
                has_previous=offset > 0,
            ),
        )
