"""Reclamo distribuido y auditabilidad de disparos programados."""

from datetime import date, datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from infrastructure.persistence.models.scheduled_feeding_run_model import ScheduledFeedingRunModel


class ScheduledFeedingRunRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def claim(
        self, plan_id: UUID, run_date: date, worker_id: str, lease_seconds: float
    ) -> Optional[ScheduledFeedingRunModel]:
        now = datetime.now(timezone.utc)
        statement = (
            insert(ScheduledFeedingRunModel)
            .values(
                plan_id=plan_id,
                run_date=run_date,
                worker_id=worker_id,
                lease_expires_at=now + timedelta(seconds=lease_seconds),
            )
            .on_conflict_do_nothing(index_elements=["plan_id", "run_date"])
            .returning(ScheduledFeedingRunModel)
        )
        inserted = (await self.session.execute(statement)).scalars().first()
        if inserted:
            return inserted

        result = await self.session.execute(
            select(ScheduledFeedingRunModel)
            .where(
                col(ScheduledFeedingRunModel.plan_id) == plan_id,
                col(ScheduledFeedingRunModel.run_date) == run_date,
            )
            .with_for_update(skip_locked=True)
        )
        existing = result.scalars().first()
        if (
            not existing
            or existing.status != "CLAIMED"
            or not existing.lease_expires_at
            or existing.lease_expires_at >= now
        ):
            return None
        existing.worker_id = worker_id
        existing.attempts += 1
        existing.lease_expires_at = now + timedelta(seconds=lease_seconds)
        existing.updated_at = now
        await self.session.flush()
        return existing

    async def mark_enqueued(self, run_id: UUID, session_id: str) -> ScheduledFeedingRunModel:
        run = await self._find_for_update(run_id)
        run.status = "ENQUEUED"
        run.session_id = session_id
        run.error = None
        run.lease_expires_at = None
        run.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return run

    async def mark_failed(self, run_id: UUID, error: str) -> ScheduledFeedingRunModel:
        run = await self._find_for_update(run_id)
        run.status = "FAILED"
        run.error = error[:500]
        run.lease_expires_at = None
        run.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return run

    async def mark_missed(self, plan_id: UUID, run_date: date, error: str) -> Optional[ScheduledFeedingRunModel]:
        now = datetime.now(timezone.utc)
        statement = (
            insert(ScheduledFeedingRunModel)
            .values(
                plan_id=plan_id,
                run_date=run_date,
                status="MISSED",
                attempts=0,
                error=error[:500],
                created_at=now,
                updated_at=now,
            )
            .on_conflict_do_nothing(index_elements=["plan_id", "run_date"])
            .returning(ScheduledFeedingRunModel)
        )
        inserted = (await self.session.execute(statement)).scalars().first()
        if inserted:
            return inserted

        result = await self.session.execute(
            select(ScheduledFeedingRunModel)
            .where(
                col(ScheduledFeedingRunModel.plan_id) == plan_id,
                col(ScheduledFeedingRunModel.run_date) == run_date,
            )
            .with_for_update(skip_locked=True)
        )
        existing = result.scalars().first()
        if (
            not existing
            or existing.status != "CLAIMED"
            or (existing.lease_expires_at is not None and existing.lease_expires_at > now)
        ):
            return None
        existing.status = "MISSED"
        existing.error = error[:500]
        existing.lease_expires_at = None
        existing.updated_at = now
        await self.session.flush()
        return existing

    async def _find_for_update(self, run_id: UUID) -> ScheduledFeedingRunModel:
        result = await self.session.execute(
            select(ScheduledFeedingRunModel).where(col(ScheduledFeedingRunModel.id) == run_id).with_for_update()
        )
        run = result.scalars().first()
        if not run:
            raise ValueError(f"Ejecución programada {run_id} no encontrada")
        return run
