"""Worker durable y recuperación segura de ejecuciones de alimentación."""

import asyncio
import logging
import os
import socket
import uuid
from collections.abc import Callable
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from application.services.feeding_orchestrator import FeedingOrchestrator
from domain.entities.feeding_event import FeedingEvent
from domain.entities.feeding_session import SessionStatus
from domain.interfaces import IMachine
from domain.value_objects import LineId
from domain.value_objects.identifiers import SiloId
from infrastructure.persistence.models.feeding_execution_job_model import FeedingExecutionJobModel
from infrastructure.persistence.repositories.cage_feeding_repository import CageFeedingRepository
from infrastructure.persistence.repositories.feeding_event_repository import FeedingEventRepository
from infrastructure.persistence.repositories.feeding_execution_job_repository import FeedingExecutionJobRepository
from infrastructure.persistence.repositories.feeding_line_repository import FeedingLineRepository
from infrastructure.persistence.repositories.feeding_session_repository import FeedingSessionRepository
from infrastructure.persistence.repositories.silo_inventory_repository import SiloInventoryRepository

logger = logging.getLogger(__name__)


class FeedingExecutionWorker:
    """Consume trabajos persistidos; nunca reanuda una operación física abandonada."""

    def __init__(
        self,
        machine: IMachine,
        session_factory: Callable[[], AsyncSession],
        poll_interval_seconds: float = 1.0,
        lease_seconds: float = 15.0,
    ) -> None:
        self._machine = machine
        self._session_factory = session_factory
        self._poll_interval = poll_interval_seconds
        self._lease_seconds = lease_seconds
        self._worker_id = f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4()}"
        self._orchestrator = FeedingOrchestrator(machine=machine, session_factory=session_factory)

    async def run(self) -> None:
        logger.info("Iniciando worker durable de alimentación %s", self._worker_id)
        while True:
            did_work = await self.poll_once()
            if not did_work:
                await asyncio.sleep(self._poll_interval)

    async def poll_once(self) -> bool:
        recovered = await self._recover_one_expired_job()
        job = await self._claim_next_job()
        if job:
            await self._execute(job)
        return recovered or job is not None

    async def _claim_next_job(self) -> FeedingExecutionJobModel | None:
        async with self._session_factory() as db:
            repository = FeedingExecutionJobRepository(db)
            job = await repository.claim_next(self._worker_id, self._lease_seconds)
            await db.commit()
            return job

    async def _recover_one_expired_job(self) -> bool:
        async with self._session_factory() as db:
            repository = FeedingExecutionJobRepository(db)
            job = await repository.claim_expired(self._worker_id, self._lease_seconds)
            await db.commit()
        if not job:
            return False
        return await self._interrupt_job(job, "Worker perdido o proceso reiniciado")

    async def _execute(self, job: FeedingExecutionJobModel) -> None:
        heartbeat_task = asyncio.create_task(self._heartbeat(job.id))
        try:
            async with self._session_factory() as db:
                session = await FeedingSessionRepository(db).find_by_id(job.feeding_session_id)
                cage_feedings = await CageFeedingRepository(db).find_by_session(job.feeding_session_id)

            if not session:
                await self._mark_interrupted(job.id, "La sesión asociada ya no existe")
                return
            if session.status in (SessionStatus.CANCELLED, SessionStatus.INTERRUPTED):
                await self._mark_interrupted(job.id, f"La sesión ya está {session.status.value}")
                return
            if session.status == SessionStatus.COMPLETED:
                await self._mark_completed(job.id)
                return

            payload = job.payload
            await self._orchestrator.run(
                session=session,
                cage_feedings=cage_feedings,
                line_id=LineId.from_string(payload["line_id"]),
                slot_map={str(key): int(value) for key, value in payload["slot_map"].items()},
                silo_id=SiloId.from_string(payload["silo_id"]),
                blower_power_percentage=float(payload["blower_power_percentage"]),
                transport_time_map={str(key): float(value) for key, value in payload["transport_time_map"].items()},
                blow_before_seconds=float(payload.get("blow_before_seconds", 0.0)),
                blow_after_seconds=float(payload.get("blow_after_seconds", 0.0)),
                selector_positioning_seconds=float(payload.get("selector_positioning_seconds", 5.0)),
                wait_after_visit_seconds=float(payload.get("wait_after_visit_seconds", 0.0)),
            )
            await self._finish_job(job.id, job.feeding_session_id)
        except asyncio.CancelledError:
            await self._interrupt_job(job, "Worker detenido durante la ejecución")
            raise
        except Exception as exc:
            logger.exception("Falló el job durable de alimentación %s", job.id)
            await self._interrupt_job(job, f"Error no controlado del orquestador: {exc}")
        finally:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass

    async def _heartbeat(self, job_id: str) -> None:
        interval = max(1.0, self._lease_seconds / 3)
        while True:
            await asyncio.sleep(interval)
            async with self._session_factory() as db:
                updated = await FeedingExecutionJobRepository(db).heartbeat(
                    job_id,
                    self._worker_id,
                    self._lease_seconds,
                )
                await db.commit()
            if not updated:
                return

    async def _finish_job(self, job_id: str, feeding_session_id: str) -> None:
        async with self._session_factory() as db:
            session = await FeedingSessionRepository(db).find_by_id(feeding_session_id)
            jobs = FeedingExecutionJobRepository(db)
            if session and session.status == SessionStatus.COMPLETED:
                await jobs.mark_completed(job_id)
            else:
                status = session.status.value if session else "NO_ENCONTRADA"
                await jobs.mark_interrupted(job_id, f"La sesión terminó en estado {status}")
            await db.commit()

    async def _mark_completed(self, job_id: str) -> None:
        async with self._session_factory() as db:
            await FeedingExecutionJobRepository(db).mark_completed(job_id)
            await db.commit()

    async def _mark_interrupted(self, job_id: str, reason: str) -> None:
        async with self._session_factory() as db:
            await FeedingExecutionJobRepository(db).mark_interrupted(job_id, reason)
            await db.commit()

    async def _interrupt_job(self, job: FeedingExecutionJobModel, reason: str) -> bool:
        """Detiene primero la máquina; solo entonces libera los recursos persistidos."""
        payload: dict[str, Any] = job.payload
        line_id = LineId.from_string(payload["line_id"])
        try:
            machine_status = await self._machine.get_status(line_id)
            await self._machine.stop(line_id)
        except Exception as exc:
            logger.exception("No fue posible detener la línea %s durante recuperación", line_id)
            async with self._session_factory() as db:
                await FeedingExecutionJobRepository(db).defer_recovery(job.id, f"{reason}. Stop falló: {exc}")
                await db.commit()
            return False

        async with self._session_factory() as db:
            sessions = FeedingSessionRepository(db)
            cage_feedings = CageFeedingRepository(db)
            events = FeedingEventRepository(db)
            inventory = SiloInventoryRepository(db)
            lines = FeedingLineRepository(db)
            jobs = FeedingExecutionJobRepository(db)
            session = await sessions.find_by_id(job.feeding_session_id)

            if session and session.status in (SessionStatus.IN_PROGRESS, SessionStatus.PAUSED):
                # Solo se concilia una visita aún activa. Una visita ya terminada se
                # persiste en una transacción antes de que el orquestador continúe.
                if machine_status.is_running and machine_status.dispensed_kg > 0 and machine_status.cage_feeding_id:
                    current = await cage_feedings.find_by_id(machine_status.cage_feeding_id)
                    if current and current.feeding_session_id == session.id and current.status.value != "COMPLETED":
                        await cage_feedings.record_visit_progress(
                            current.id,
                            dispensed_kg=machine_status.dispensed_kg,
                            completed_visit=False,
                        )
                        await inventory.consume(
                            session.id,
                            current.id,
                            machine_status.dispensed_kg,
                            session.operator_id,
                        )

                pending_visits = sum(
                    max(0, feeding.programmed_visits - feeding.completed_visits)
                    for feeding in await cage_feedings.find_by_session(session.id)
                )
                session.interrupt()
                await sessions.save(session)
                await events.save(
                    FeedingEvent.session_interrupted(
                        feeding_session_id=session.id,
                        reason=reason,
                        pending_visits=pending_visits,
                    )
                )
                await inventory.release(session.id)

            line = await lines.find_by_id(line_id)
            if line:
                line.release_from_feeding()
                await lines.save(line)
            await jobs.mark_interrupted(job.id, reason)
            await db.commit()
        return True
