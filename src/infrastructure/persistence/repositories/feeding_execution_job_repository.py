"""Repositorio de trabajos durables de ejecución de alimentación."""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from infrastructure.persistence.models.feeding_execution_job_model import FeedingExecutionJobModel


class FeedingExecutionJobRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def enqueue(self, feeding_session_id: str, payload: dict[str, Any]) -> FeedingExecutionJobModel:
        job = FeedingExecutionJobModel(feeding_session_id=feeding_session_id, payload=payload)
        self.session.add(job)
        await self.session.flush()
        return job

    async def claim_next(self, worker_id: str, lease_seconds: float) -> Optional[FeedingExecutionJobModel]:
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(FeedingExecutionJobModel)
            .where(col(FeedingExecutionJobModel.status) == "PENDING")
            .order_by(col(FeedingExecutionJobModel.created_at))
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        job = result.scalars().first()
        if not job:
            return None
        job.status = "RUNNING"
        job.worker_id = worker_id
        job.attempts += 1
        job.started_at = job.started_at or now
        job.heartbeat_at = now
        job.lease_expires_at = now + timedelta(seconds=lease_seconds)
        await self.session.flush()
        return job

    async def claim_expired(self, worker_id: str, lease_seconds: float) -> Optional[FeedingExecutionJobModel]:
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(FeedingExecutionJobModel)
            .where(
                col(FeedingExecutionJobModel.status) == "RUNNING",
                or_(
                    col(FeedingExecutionJobModel.lease_expires_at).is_(None),
                    col(FeedingExecutionJobModel.lease_expires_at) < now,
                ),
            )
            .order_by(col(FeedingExecutionJobModel.lease_expires_at))
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        job = result.scalars().first()
        if not job:
            return None
        job.worker_id = worker_id
        job.heartbeat_at = now
        job.lease_expires_at = now + timedelta(seconds=lease_seconds)
        await self.session.flush()
        return job

    async def heartbeat(self, job_id: str, worker_id: str, lease_seconds: float) -> bool:
        result = await self.session.execute(
            select(FeedingExecutionJobModel).where(col(FeedingExecutionJobModel.id) == job_id).with_for_update()
        )
        job = result.scalars().first()
        if not job or job.status != "RUNNING" or job.worker_id != worker_id:
            return False
        now = datetime.now(timezone.utc)
        job.heartbeat_at = now
        job.lease_expires_at = now + timedelta(seconds=lease_seconds)
        await self.session.flush()
        return True

    async def mark_completed(self, job_id: str) -> None:
        job = await self._find_for_update(job_id)
        job.status = "COMPLETED"
        job.completed_at = datetime.now(timezone.utc)
        job.lease_expires_at = None
        await self.session.flush()

    async def mark_interrupted(self, job_id: str, reason: str) -> None:
        job = await self._find_for_update(job_id)
        job.status = "INTERRUPTED"
        job.last_error = reason[:1000]
        job.completed_at = datetime.now(timezone.utc)
        job.lease_expires_at = None
        await self.session.flush()

    async def defer_recovery(self, job_id: str, reason: str) -> None:
        job = await self._find_for_update(job_id)
        job.last_error = reason[:1000]
        job.lease_expires_at = datetime.now(timezone.utc)
        await self.session.flush()

    async def _find_for_update(self, job_id: str) -> FeedingExecutionJobModel:
        result = await self.session.execute(
            select(FeedingExecutionJobModel).where(col(FeedingExecutionJobModel.id) == job_id).with_for_update()
        )
        job = result.scalars().first()
        if not job:
            raise ValueError(f"Job de ejecución {job_id} no encontrado")
        return job
