from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.aggregates.feeding_line.feeding_line import FeedingLine
from domain.enums import FeedingLineStatus
from domain.exceptions import FeedingLineUnavailableException
from domain.repositories import IFeedingLineRepository
from domain.value_objects import LineId, LineName
from infrastructure.persistence.models.feeding_line_model import FeedingLineModel


class FeedingLineRepository(IFeedingLineRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, feeding_line: FeedingLine) -> None:
        line_model = FeedingLineModel.from_domain(feeding_line)
        await self.session.merge(line_model)
        await self.session.flush()

    async def save_available_status_transition(self, feeding_line: FeedingLine) -> None:
        stmt = (
            update(FeedingLineModel)
            .where(
                FeedingLineModel.id == feeding_line.id.value,
                FeedingLineModel.status == FeedingLineStatus.AVAILABLE.value,
            )
            .values(
                status=feeding_line.status.value,
                locked_by=feeding_line.locked_by,
                locked_reason=feeding_line.locked_reason,
                locked_at=feeding_line.locked_at,
            )
            .execution_options(synchronize_session=False)
        )

        result = await self.session.execute(stmt)
        if result.rowcount != 1:
            current_status = await self._get_current_status(feeding_line.id)
            status_detail = current_status or "desconocido"
            raise FeedingLineUnavailableException(
                f"No se puede reservar la línea {feeding_line.name.value}: "
                f"estado actual {status_detail}"
            )

        await self.session.flush()

    async def find_by_id(self, line_id: LineId) -> Optional[FeedingLine]:
        stmt = (
            select(FeedingLineModel)
            .where(FeedingLineModel.id == line_id.value)
            .options(
                selectinload(FeedingLineModel.blower),
                selectinload(FeedingLineModel.cooler),
                selectinload(FeedingLineModel.dosers),
                selectinload(FeedingLineModel.selector),
                selectinload(FeedingLineModel.sensors),
            )
        )

        result = await self.session.execute(stmt)
        line_model = result.scalar_one_or_none()
        return line_model.to_domain() if line_model else None

    async def find_by_name(self, name: LineName) -> Optional[FeedingLine]:
        stmt = (
            select(FeedingLineModel)
            .where(FeedingLineModel.name == str(name))
            .options(
                selectinload(FeedingLineModel.blower),
                selectinload(FeedingLineModel.cooler),
                selectinload(FeedingLineModel.dosers),
                selectinload(FeedingLineModel.selector),
                selectinload(FeedingLineModel.sensors),
            )
        )

        result = await self.session.execute(stmt)
        line_model = result.scalar_one_or_none()
        return line_model.to_domain() if line_model else None

    async def get_all(self) -> List[FeedingLine]:
        stmt = select(FeedingLineModel).options(
            selectinload(FeedingLineModel.blower),
            selectinload(FeedingLineModel.cooler),
            selectinload(FeedingLineModel.dosers),
            selectinload(FeedingLineModel.selector),
            selectinload(FeedingLineModel.sensors),
        )

        result = await self.session.execute(stmt)
        line_models = result.scalars().all()
        return [model.to_domain() for model in line_models]

    async def _get_current_status(self, line_id: LineId) -> Optional[str]:
        stmt = select(FeedingLineModel.status).where(FeedingLineModel.id == line_id.value)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, line_id: LineId) -> None:
        line_model = await self.session.get(FeedingLineModel, line_id.value)
        if line_model:
            await self.session.delete(line_model)
            await self.session.flush()
