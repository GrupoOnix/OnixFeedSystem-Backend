from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from infrastructure.persistence.models.last_selected_feeding_mode_model import (
    LastSelectedFeedingModeModel,
)


class LastSelectedFeedingModeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self) -> List[LastSelectedFeedingModeModel]:
        result = await self.session.execute(select(LastSelectedFeedingModeModel))
        return list(result.scalars().all())

    async def find_by_line_id(self, line_id: UUID) -> Optional[LastSelectedFeedingModeModel]:
        result = await self.session.execute(
            select(LastSelectedFeedingModeModel).where(
                col(LastSelectedFeedingModeModel.line_id) == line_id
            )
        )
        return result.scalar_one_or_none()

    async def upsert_by_line_id(
        self,
        *,
        line_id: UUID,
        selected_mode: str,
        updated_by: Optional[str] = None,
    ) -> LastSelectedFeedingModeModel:
        existing = await self.find_by_line_id(line_id)

        if existing:
            if existing.selected_mode == selected_mode and existing.updated_by == updated_by:
                return existing

            existing.selected_mode = selected_mode
            existing.updated_by = updated_by
            existing.updated_at = datetime.now(timezone.utc)
            await self.session.flush()
            return existing

        model = LastSelectedFeedingModeModel(
            line_id=line_id,
            selected_mode=selected_mode,
            updated_by=updated_by,
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model
