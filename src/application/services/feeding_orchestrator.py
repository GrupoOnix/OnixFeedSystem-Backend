import asyncio
import logging
from datetime import datetime, timezone
from typing import Callable, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from domain.dtos.machine_io import MachineCommand, VisitStage
from domain.entities.cage_feeding import CageFeeding, CageFeedingMode
from domain.entities.feeding_event import FeedingEvent
from domain.entities.feeding_session import FeedingSession
from domain.interfaces import IMachine
from domain.value_objects.identifiers import LineId, SiloId
from domain.value_objects.measurements import Weight
from infrastructure.persistence.repositories.cage_feeding_repository import CageFeedingRepository
from infrastructure.persistence.repositories.feeding_event_repository import FeedingEventRepository
from infrastructure.persistence.repositories.feeding_session_repository import FeedingSessionRepository
from infrastructure.persistence.repositories.silo_repository import SiloRepository

logger = logging.getLogger(__name__)


class FeedingOrchestrator:

    def __init__(
        self,
        machine: IMachine,
        session_factory: Callable[[], AsyncSession],
        poll_interval_seconds: float = 2.0,
    ):
        self._machine = machine
        self._session_factory = session_factory
        self._poll_interval = poll_interval_seconds

    async def _save(self, operation):
        async with self._session_factory() as db:
            try:
                await operation(db)
                await db.commit()
            except Exception:
                await db.rollback()
                raise

    async def run(
        self,
        session: FeedingSession,
        cage_feedings: List[CageFeeding],
        line_id: LineId,
        slot_map: Dict[str, int],
        silo_id: SiloId,
        blower_power_percentage: float,
        transport_time_map: Dict[str, float],
        blow_before_seconds: float = 0.0,
        blow_after_seconds: float = 0.0,
        selector_positioning_seconds: float = 5.0,
    ) -> None:
        """
        Ejecuta una sesión de alimentación (manual o cíclica).

        Args:
            slot_map: Mapa de cage_id → slot_number para cada jaula.
            transport_time_map: Mapa de cage_id → transport_time_seconds para cada jaula.
        """
        logger.info(f"[Orchestrator] Session {session.id}: starting")

        # Determinar número de rondas: el máximo de programmed_visits entre todos los
        # cage_feedings (FASTING tiene programmed_visits=0 y no contribuye).
        total_rounds = max(
            (cf.programmed_visits for cf in cage_feedings),
            default=0,
        )

        for round_number in range(total_rounds):
            visit_number_in_round = round_number + 1

            for cage_feeding in cage_feedings:
                # FASTING: programmed_visits=0 → saltar completamente
                if cage_feeding.mode == CageFeedingMode.FASTING:
                    continue

                # Solo ejecutar si esta jaula aún tiene visitas en esta ronda
                if round_number >= cage_feeding.programmed_visits:
                    continue

                transport_time = transport_time_map.get(cage_feeding.cage_id, 0.0)

                if cage_feeding.mode == CageFeedingMode.PAUSE:
                    await self._execute_pause(
                        session=session,
                        cage_feeding=cage_feeding,
                        blow_before_seconds=blow_before_seconds,
                        blow_after_seconds=blow_after_seconds,
                        transport_time_seconds=transport_time,
                        selector_positioning_seconds=selector_positioning_seconds,
                    )
                else:
                    slot_number = slot_map[cage_feeding.cage_id]
                    await self._execute_visit(
                        session=session,
                        cage_feeding=cage_feeding,
                        line_id=line_id,
                        slot_number=slot_number,
                        silo_id=silo_id,
                        blower_power_percentage=blower_power_percentage,
                        visit_number=visit_number_in_round,
                        transport_time_seconds=transport_time,
                        blow_before_seconds=blow_before_seconds,
                        blow_after_seconds=blow_after_seconds,
                        selector_positioning_seconds=selector_positioning_seconds,
                    )

                # Recargar sesión desde BD para sincronizar cambios externos
                async with self._session_factory() as db:
                    refreshed_session = await FeedingSessionRepository(db).find_by_id(session.id)
                    if refreshed_session:
                        session = refreshed_session

                if session.status.value in ("INTERRUPTED", "CANCELLED"):
                    logger.info(
                        f"[Orchestrator] Session {session.id}: detected external stop "
                        f"(status={session.status.value}), skipping completion"
                    )
                    return

        # Verificar una última vez antes de marcar como completada
        async with self._session_factory() as db:
            refreshed_session = await FeedingSessionRepository(db).find_by_id(session.id)
            if refreshed_session and refreshed_session.status.value in ("INTERRUPTED", "CANCELLED"):
                logger.info(
                    f"[Orchestrator] Session {session.id}: externally stopped before completion "
                    f"(status={refreshed_session.status.value}), aborting"
                )
                return
            if refreshed_session:
                session = refreshed_session

        session.complete()
        total_dispensed = sum(cf.dispensed_kg for cf in cage_feedings)
        duration = (
            datetime.now(timezone.utc) - session.actual_start
        ).total_seconds() if session.actual_start else 0.0
        completed_event = FeedingEvent.session_completed(
            feeding_session_id=session.id,
            total_dispensed_kg=total_dispensed,
            duration_seconds=duration,
        )

        async def _persist_completion(db: AsyncSession):
            await FeedingSessionRepository(db).save(session)
            await FeedingEventRepository(db).save(completed_event)

        await self._save(_persist_completion)
        await self._machine.stop(line_id)
        logger.info(f"[Orchestrator] Session {session.id}: COMPLETED")

    async def _execute_pause(
        self,
        session: FeedingSession,
        cage_feeding: CageFeeding,
        blow_before_seconds: float,
        blow_after_seconds: float,
        transport_time_seconds: float,
        selector_positioning_seconds: float,
    ) -> None:
        """
        Simula una visita en modo PAUSE: espera el tiempo equivalente sin enviar
        nada al PLC. No dispensa, no descuenta silo.
        """
        # Calcular duración equivalente usando los mismos parámetros de tiempo
        # que una visita real, pero con los kg/tasa de esta jaula.
        estimated_seconds = (
            selector_positioning_seconds
            + blow_before_seconds
            + (cage_feeding.programmed_kg / cage_feeding.rate_kg_per_min) * 60
            + transport_time_seconds
            + blow_after_seconds
        )

        logger.info(
            f"[Orchestrator] Session {session.id}: cage {cage_feeding.cage_id} "
            f"PAUSE — simulando visita por {estimated_seconds:.1f}s"
        )
        await asyncio.sleep(estimated_seconds)

    async def _execute_visit(
        self,
        session: FeedingSession,
        cage_feeding: CageFeeding,
        line_id: LineId,
        slot_number: int,
        silo_id: SiloId,
        blower_power_percentage: float,
        visit_number: int,
        transport_time_seconds: float = 0.0,
        blow_before_seconds: float = 0.0,
        blow_after_seconds: float = 0.0,
        selector_positioning_seconds: float = 5.0,
    ) -> None:
        visit_start = datetime.now(timezone.utc)

        # Recargar desde DB para obtener la tasa actualizada (puede haber cambiado en caliente)
        async with self._session_factory() as db:
            refreshed = await CageFeedingRepository(db).find_by_id(cage_feeding.id)
            current_rate = refreshed.rate_kg_per_min if refreshed else cage_feeding.rate_kg_per_min

        command = MachineCommand(
            slot_number=slot_number,
            target_kg=cage_feeding.programmed_kg,
            doser_rate_kg_per_min=current_rate,
            blower_power_percentage=blower_power_percentage,
            transport_time_seconds=transport_time_seconds,
            blow_before_seconds=blow_before_seconds,
            blow_after_seconds=blow_after_seconds,
            selector_positioning_seconds=selector_positioning_seconds,
        )
        await self._machine.start_visit(line_id, command)

        # Marcar IN_PROGRESS solo en la primera visita
        if cage_feeding.status.value == "PENDING":
            cage_feeding.start()

        visit_started_event = FeedingEvent.visit_started(
            feeding_session_id=session.id,
            cage_id=cage_feeding.cage_id,
            visit_number=visit_number,
            cycle_number=1,
        )

        async def _persist_visit_start(db: AsyncSession):
            await CageFeedingRepository(db).save(cage_feeding)
            await FeedingEventRepository(db).save(visit_started_event)

        await self._save(_persist_visit_start)

        logger.info(
            f"[Orchestrator] Session {session.id}: visit {visit_number} started "
            f"slot={slot_number} target={cage_feeding.programmed_kg}kg"
        )

        while True:
            await asyncio.sleep(self._poll_interval)
            status = await self._machine.get_status(line_id)

            # Verificar si la sesión fue cancelada o interrumpida externamente
            async with self._session_factory() as db:
                refreshed_session = await FeedingSessionRepository(db).find_by_id(session.id)
                if refreshed_session and refreshed_session.status.value in ("COMPLETED", "CANCELLED", "INTERRUPTED"):
                    logger.info(
                        f"[Orchestrator] Session {session.id}: externally stopped "
                        f"(status={refreshed_session.status.value}), exiting visit poll loop"
                    )
                    return

            logger.info(
                f"[Orchestrator] Session {session.id}: poll — "
                f"dispensed={status.dispensed_kg:.3f}/{cage_feeding.programmed_kg}kg "
                f"running={status.is_running} paused={status.is_paused}"
            )

            if status.has_error:
                logger.error(
                    f"[Orchestrator] Session {session.id}: error code={status.error_code}"
                )
                session.interrupt()
                interrupted_event = FeedingEvent.session_interrupted(
                    feeding_session_id=session.id,
                    reason=f"Machine error code={status.error_code}",
                    pending_visits=cage_feeding.programmed_visits - cage_feeding.completed_visits,
                )

                async def _persist_interrupt(db: AsyncSession):
                    await FeedingSessionRepository(db).save(session)
                    await FeedingEventRepository(db).save(interrupted_event)

                await self._save(_persist_interrupt)
                await self._machine.stop(line_id)
                return

            if status.current_stage == VisitStage.COMPLETED:
                duration_seconds = (
                    datetime.now(timezone.utc) - visit_start
                ).total_seconds()

                cage_feeding.add_dispensed_amount(status.dispensed_kg)
                cage_feeding.increment_completed_visits()
                # Marcar COMPLETED solo cuando se terminaron todas las visitas programadas
                if cage_feeding.completed_visits >= cage_feeding.programmed_visits:
                    cage_feeding.complete()

                visit_completed_event = FeedingEvent.visit_completed(
                    feeding_session_id=session.id,
                    cage_id=cage_feeding.cage_id,
                    visit_number=visit_number,
                    cycle_number=1,
                    dispensed_grams=status.dispensed_kg * 1000,
                    duration_seconds=duration_seconds,
                )

                async def _persist_visit_end(db: AsyncSession):
                    await CageFeedingRepository(db).save(cage_feeding)
                    silo = await SiloRepository(db).find_by_id(silo_id)
                    if silo:
                        silo.stock_level = silo.stock_level - Weight.from_kg(status.dispensed_kg)
                        await SiloRepository(db).save(silo)
                    await FeedingEventRepository(db).save(visit_completed_event)

                await self._save(_persist_visit_end)

                logger.info(
                    f"[Orchestrator] Session {session.id}: visit {visit_number} completed "
                    f"dispensed={status.dispensed_kg}kg in {duration_seconds:.1f}s"
                )
                return
