from typing import Any, List, Optional, cast

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import col

from domain.aggregates.feeding_line.feeding_line import FeedingLine
from domain.enums import FeedingLineStatus
from domain.exceptions import FeedingLineUnavailableException
from domain.repositories import IFeedingLineRepository
from domain.value_objects import LineId, LineName
from infrastructure.persistence.models.doser_model import DoserModel
from infrastructure.persistence.models.doser_silo_model import DoserSiloModel
from infrastructure.persistence.models.feeding_line_model import FeedingLineModel


_blower_rel = cast(Any, FeedingLineModel.blower)
_cooler_rel = cast(Any, FeedingLineModel.cooler)
_dosers_rel = cast(Any, FeedingLineModel.dosers)
_selector_rel = cast(Any, FeedingLineModel.selector)
_sensors_rel = cast(Any, FeedingLineModel.sensors)
_silos_rel = cast(Any, DoserModel.silos)


class FeedingLineRepository(IFeedingLineRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, feeding_line: FeedingLine) -> None:
        line_model = FeedingLineModel.from_domain(feeding_line)
        await self.session.merge(line_model)
        await self.session.flush()
        await self._save_doser_silo_links(feeding_line)

    async def save_available_status_transition(self, feeding_line: FeedingLine) -> None:
        stmt = (
            update(FeedingLineModel)
            .where(
                col(FeedingLineModel.id) == feeding_line.id.value,
                col(FeedingLineModel.status) == FeedingLineStatus.AVAILABLE.value,
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
        rowcount = cast(Any, result).rowcount
        if rowcount != 1:
            current_status = await self._get_current_status(feeding_line.id)
            status_detail = current_status or "desconocido"
            raise FeedingLineUnavailableException(
                f"No se puede reservar la línea {feeding_line.name.value}: estado actual {status_detail}"
            )

        await self.session.flush()

    async def find_by_id(self, line_id: LineId) -> Optional[FeedingLine]:
        stmt = (
            select(FeedingLineModel)
            .where(col(FeedingLineModel.id) == line_id.value)
            .options(
                selectinload(_blower_rel),
                selectinload(_cooler_rel),
                selectinload(_dosers_rel).selectinload(_silos_rel),
                selectinload(_selector_rel),
                selectinload(_sensors_rel),
            )
        )

        result = await self.session.execute(stmt)
        line_model = result.scalar_one_or_none()
        return line_model.to_domain() if line_model else None

    async def find_by_name(self, name: LineName) -> Optional[FeedingLine]:
        stmt = (
            select(FeedingLineModel)
            .where(col(FeedingLineModel.name) == str(name))
            .options(
                selectinload(_blower_rel),
                selectinload(_cooler_rel),
                selectinload(_dosers_rel).selectinload(_silos_rel),
                selectinload(_selector_rel),
                selectinload(_sensors_rel),
            )
        )

        result = await self.session.execute(stmt)
        line_model = result.scalar_one_or_none()
        return line_model.to_domain() if line_model else None

    async def get_all(self) -> List[FeedingLine]:
        stmt = (
            select(FeedingLineModel)
            .order_by(col(FeedingLineModel.name))
            .options(
                selectinload(_blower_rel),
                selectinload(_cooler_rel),
                selectinload(_dosers_rel).selectinload(_silos_rel),
                selectinload(_selector_rel),
                selectinload(_sensors_rel),
            )
        )

        result = await self.session.execute(stmt)
        line_models = result.scalars().all()
        return [model.to_domain() for model in line_models]

    async def _get_current_status(self, line_id: LineId) -> Optional[str]:
        stmt = select(col(FeedingLineModel.status)).where(col(FeedingLineModel.id) == line_id.value)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, line_id: LineId) -> None:
        line_model = await self.session.get(FeedingLineModel, line_id.value)
        if line_model:
            await self.session.delete(line_model)
            await self.session.flush()

    async def _save_doser_silo_links(self, feeding_line: FeedingLine) -> None:
        doser_ids = [doser.id.value for doser in feeding_line.dosers]
        if not doser_ids:
            return

        await self.session.execute(delete(DoserSiloModel).where(col(DoserSiloModel.doser_id).in_(doser_ids)))

        for doser in feeding_line.dosers:
            for silo_id in doser.assigned_silo_ids:
                self.session.add(
                    DoserSiloModel(
                        doser_id=doser.id.value,
                        silo_id=silo_id.value,
                    )
                )

        await self.session.flush()
