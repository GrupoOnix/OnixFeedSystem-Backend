"""Despacho distribuido de planes diarios de alimentación."""

import logging
import os
import socket
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from api.models.feeding_models import CageConfigInput, CyclicFeedingRequest
from application.services.feeding_orchestrator import FeedingOrchestrator
from application.use_cases.feeding.start_cyclic_feeding_use_case import StartCyclicFeedingUseCase
from domain.interfaces import IMachine
from infrastructure.persistence.models.scheduled_feeding_plan_model import ScheduledFeedingPlanModel
from infrastructure.persistence.repositories import (
    ActivityLogRepository,
    CageFeedingRepository,
    CageGroupRepository,
    CageRepository,
    FeedingEventRepository,
    FeedingLineRepository,
    FeedingSessionRepository,
    ScheduledFeedingPlanRepository,
    ScheduledFeedingRunRepository,
    SiloInventoryRepository,
    SiloRepository,
    SlotAssignmentRepository,
    SystemConfigRepository,
)
from infrastructure.services.scheduled_feeding_window import (
    ScheduledFeedingWindowStatus,
    evaluate_scheduled_feeding_window,
)

logger = logging.getLogger(__name__)


class ScheduledFeedingDispatcher:
    """Coordina los workers mediante una ejecución única por plan y fecha local."""

    def __init__(
        self,
        machine: IMachine,
        session_factory: Callable[[], AsyncSession],
        lease_seconds: float = 60.0,
        grace_period: timedelta = timedelta(minutes=15),
    ) -> None:
        if grace_period <= timedelta(0):
            raise ValueError("grace_period debe ser mayor que cero")
        self._machine = machine
        self._session_factory = session_factory
        self._lease_seconds = lease_seconds
        self._grace_period = grace_period
        self._worker_id = f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4()}"

    async def dispatch_due_plans(self) -> None:
        async with self._session_factory() as db:
            plans = await ScheduledFeedingPlanRepository(db).list()

        for plan in plans:
            if not plan.is_active:
                continue
            try:
                now = datetime.now(ZoneInfo(plan.timezone))
            except Exception:
                now = datetime.now(ZoneInfo("America/Santiago"))
            window = evaluate_scheduled_feeding_window(plan.start_time, now, self._grace_period)
            if window.status == ScheduledFeedingWindowStatus.DUE:
                await self._claim_and_dispatch(plan.id, now)
            elif window.status == ScheduledFeedingWindowStatus.EXPIRED:
                await self._mark_missed(plan.id, now, window.expires_at)

    async def _claim_and_dispatch(self, plan_id: UUID, now: datetime) -> None:
        run = None
        try:
            async with self._session_factory() as db:
                runs = ScheduledFeedingRunRepository(db)
                run = await runs.claim(plan_id, now.date(), self._worker_id, self._lease_seconds)
                await db.commit()
            if not run:
                return

            async with self._session_factory() as db:
                plans = ScheduledFeedingPlanRepository(db)
                plan = await plans.find_by_id(plan_id)
                if not plan or not plan.is_active:
                    raise ValueError("El plan ya no existe o está inactivo")
                use_case = self._build_start_use_case(db)
                result = await use_case.execute(
                    self._build_request(plan),
                    operator_id=str(plan.created_by_id or "00000000-0000-0000-0000-000000000000"),
                    operator_name=plan.created_by_name or "Programación diaria",
                    actor=plan.created_by_name or "scheduled-feeding",
                )
                await ScheduledFeedingRunRepository(db).mark_enqueued(run.id, result.session_id)
                plan.last_run_on = now.date().isoformat()
                plan.last_session_id = result.session_id
                plan.last_error = None
                await plans.save(plan)
                await db.commit()
            logger.info("Plan programado %s encoló sesión %s", plan_id, result.session_id)
        except Exception as exc:
            logger.error("No se pudo ejecutar plan programado %s: %s", plan_id, exc, exc_info=True)
            if run:
                await self._mark_failed(plan_id, run.id, now, str(exc))

    async def _mark_failed(self, plan_id: UUID, run_id: UUID, now: datetime, error: str) -> None:
        async with self._session_factory() as db:
            await ScheduledFeedingRunRepository(db).mark_failed(run_id, error)
            plans = ScheduledFeedingPlanRepository(db)
            plan = await plans.find_by_id(plan_id)
            if plan:
                plan.last_run_on = now.date().isoformat()
                plan.last_error = error[:500]
                await plans.save(plan)
            await db.commit()

    async def _mark_missed(self, plan_id: UUID, now: datetime, expires_at: datetime) -> None:
        error = f"Plan no ejecutado: la ventana venció a las {expires_at.isoformat()}"
        async with self._session_factory() as db:
            run = await ScheduledFeedingRunRepository(db).mark_missed(plan_id, now.date(), error)
            if run:
                plans = ScheduledFeedingPlanRepository(db)
                plan = await plans.find_by_id(plan_id)
                if plan:
                    plan.last_run_on = now.date().isoformat()
                    plan.last_error = error[:500]
                    await plans.save(plan)
            await db.commit()

    def _build_start_use_case(self, db: AsyncSession) -> StartCyclicFeedingUseCase:
        return StartCyclicFeedingUseCase(
            session_repository=FeedingSessionRepository(db),
            cage_feeding_repository=CageFeedingRepository(db),
            event_repository=FeedingEventRepository(db),
            line_repository=FeedingLineRepository(db),
            cage_repository=CageRepository(db),
            cage_group_repository=CageGroupRepository(db),
            silo_repository=SiloRepository(db),
            slot_assignment_repository=SlotAssignmentRepository(db),
            orchestrator=FeedingOrchestrator(self._machine, self._session_factory),
            system_config_repository=SystemConfigRepository(db),
            activity_log_repository=ActivityLogRepository(db),
            inventory_repository=SiloInventoryRepository(db),
        )

    @staticmethod
    def _build_request(plan: ScheduledFeedingPlanModel) -> CyclicFeedingRequest:
        return CyclicFeedingRequest(
            line_id=str(plan.line_id),
            group_id=str(plan.group_id),
            doser_id=str(plan.doser_id),
            silo_id=str(plan.silo_id),
            blower_power_percentage=plan.blower_power_percentage,
            wait_after_visit_seconds=plan.wait_after_visit_seconds,
            allow_overtime=True,
            cage_configs=[
                CageConfigInput(
                    cage_id=item["cage_id"],
                    quantity_kg=round(sum(item["quantity_schedule_kg"]), 6),
                    visits=len(item["quantity_schedule_kg"]),
                    visit_quantities_kg=item["quantity_schedule_kg"],
                    rate_kg_per_min=item["rate_kg_per_min"],
                    mode=item["mode"],
                )
                for item in plan.cage_plans
            ],
        )
