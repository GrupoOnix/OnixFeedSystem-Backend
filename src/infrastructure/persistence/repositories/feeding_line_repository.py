from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.aggregates.feeding_line.feeding_line import FeedingLine
from domain.repositories import IFeedingLineRepository
from domain.value_objects import LineId, LineName, CageId
from infrastructure.persistence.models.feeding_line_model import FeedingLineModel


class FeedingLineRepository(IFeedingLineRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, feeding_line: FeedingLine) -> None:
        line_model = FeedingLineModel.from_domain(feeding_line)
        await self.session.merge(line_model)
        await self.session.flush()

    async def find_by_id(self, line_id: LineId) -> Optional[FeedingLine]:
        stmt = (
            select(FeedingLineModel)
            .where(FeedingLineModel.id == line_id.value)
            .options(
                selectinload(FeedingLineModel.blower),
                selectinload(FeedingLineModel.dosers),
                selectinload(FeedingLineModel.selector),
                selectinload(FeedingLineModel.sensors),
                selectinload(FeedingLineModel.slot_assignments),
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
                selectinload(FeedingLineModel.dosers),
                selectinload(FeedingLineModel.selector),
                selectinload(FeedingLineModel.sensors),
                selectinload(FeedingLineModel.slot_assignments),
            )
        )

        result = await self.session.execute(stmt)
        line_model = result.scalar_one_or_none()
        return line_model.to_domain() if line_model else None

    async def get_all(self) -> List[FeedingLine]:
        stmt = select(FeedingLineModel).options(
            selectinload(FeedingLineModel.blower),
            selectinload(FeedingLineModel.dosers),
            selectinload(FeedingLineModel.selector),
            selectinload(FeedingLineModel.sensors),
            selectinload(FeedingLineModel.slot_assignments),
        )

        result = await self.session.execute(stmt)
        line_models = result.scalars().all()
        return [model.to_domain() for model in line_models]

    async def delete(self, line_id: LineId) -> None:
        line_model = await self.session.get(FeedingLineModel, line_id.value)
        if line_model:
            await self.session.delete(line_model)
            await self.session.flush()

    async def get_slot_number(self, line_id: LineId, cage_id: CageId) -> Optional[int]:
        from infrastructure.persistence.models.slot_assignment_model import SlotAssignmentModel
        
        stmt = select(SlotAssignmentModel.slot_number).where(
            SlotAssignmentModel.line_id == line_id.value,
            SlotAssignmentModel.cage_id == cage_id.value
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
