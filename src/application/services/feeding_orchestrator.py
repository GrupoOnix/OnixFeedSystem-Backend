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
from domain.services.feeding_time_calculator import calculate_paused_visit_duration
from domain.value_objects import BlowerPowerPercentage
from domain.value_objects.identifiers import LineId, SiloId
from infrastructure.persistence.repositories.cage_feeding_repository import CageFeedingRepository
from infrastructure.persistence.repositories.feeding_event_repository import FeedingEventRepository
from infrastructure.persistence.repositories.feeding_line_repository import FeedingLineRepository
from infrastructure.persistence.repositories.feeding_session_repository import FeedingSessionRepository
from infrastructure.persistence.repositories.silo_repository import SiloRepository  # noqa: F401
from infrastructure.persistence.repositories.silo_inventory_repository import (
    SiloInventoryRepository,
)

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
        wait_after_visit_seconds: float = 0.0,
        hard_deadline_at: datetime | None = None,
        execute_pause_physically: bool = False,
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
        active_feeding_count = sum(1 for cf in cage_feedings if cf.mode != CageFeedingMode.FASTING)
        total_visit_executions = total_rounds * active_feeding_count
        completed_visit_executions = 0

        # El soplado pertenece a las visitas que accionan la máquina, no a PAUSE.
        # Usar IDs porque cada visita puede recargar instancias nuevas desde BD.
        first_machine_feeding_id = None
        last_machine_feeding_id = None
        for cf in cage_feedings:
            if cf.mode == CageFeedingMode.NORMAL:
                if first_machine_feeding_id is None:
                    first_machine_feeding_id = cf.id
                last_machine_feeding_id = cf.id

        for round_number in range(total_rounds):
            visit_number_in_round = round_number + 1

            for cage_feeding_index, cage_feeding in enumerate(cage_feedings):
                if hard_deadline_at and datetime.now(timezone.utc) >= hard_deadline_at.astimezone(timezone.utc):
                    await self._interrupt_for_deadline(session, line_id, cage_feedings)
                    return
                async with self._session_factory() as db:
                    refreshed_feeding = await CageFeedingRepository(db).find_by_id(cage_feeding.id)
                    if refreshed_feeding:
                        cage_feeding = refreshed_feeding
                        cage_feedings[cage_feeding_index] = cage_feeding

                # FASTING: programmed_visits=0 → saltar completamente
                if cage_feeding.mode == CageFeedingMode.FASTING:
                    continue

                transport_time = transport_time_map.get(cage_feeding.cage_id, 0.0)
                is_first_visit = round_number == 0 and cage_feeding.id == first_machine_feeding_id
                is_last_visit = round_number == total_rounds - 1 and cage_feeding.id == last_machine_feeding_id
                actual_blow_before = blow_before_seconds if is_first_visit else 0.0
                actual_blow_after = blow_after_seconds if is_last_visit else 0.0

                planned_quantities = cage_feeding.visit_quantities_kg
                planned_quantity = (
                    planned_quantities[round_number]
                    if planned_quantities is not None and round_number < len(planned_quantities)
                    else None
                )
                is_empty_visit = round_number >= cage_feeding.programmed_visits or planned_quantity == 0

                if hard_deadline_at and cage_feeding.mode == CageFeedingMode.NORMAL and not is_empty_visit:
                    minimum_visit_seconds = (
                        selector_positioning_seconds
                        + actual_blow_before
                        + transport_time
                        + actual_blow_after
                        + (planned_quantity or 0.0) / cage_feeding.rate_kg_per_min * 60.0
                    )
                    seconds_until_deadline = (
                        hard_deadline_at.astimezone(timezone.utc) - datetime.now(timezone.utc)
                    ).total_seconds()
                    if minimum_visit_seconds > seconds_until_deadline:
                        await self._interrupt_for_deadline(session, line_id, cage_feedings)
                        return

                if cage_feeding.mode == CageFeedingMode.PAUSE and execute_pause_physically:
                    slot_number = slot_map[cage_feeding.cage_id]
                    await self._execute_empty_visit(
                        session=session,
                        cage_feeding=cage_feeding,
                        line_id=line_id,
                        slot_number=slot_number,
                        blower_power_percentage=blower_power_percentage,
                        visit_number=visit_number_in_round,
                        transport_time_seconds=transport_time,
                        blow_before_seconds=actual_blow_before,
                        blow_after_seconds=actual_blow_after,
                        selector_positioning_seconds=selector_positioning_seconds,
                        count_completed_visit=round_number < cage_feeding.programmed_visits,
                    )
                elif cage_feeding.mode == CageFeedingMode.PAUSE:
                    await self._execute_pause(
                        session=session,
                        cage_feeding=cage_feeding,
                        visit_number=visit_number_in_round,
                        transport_time_seconds=transport_time,
                        selector_positioning_seconds=selector_positioning_seconds,
                        target_kg=planned_quantity or 0.0,
                        count_completed_visit=round_number < cage_feeding.programmed_visits,
                    )
                elif is_empty_visit:
                    slot_number = slot_map[cage_feeding.cage_id]
                    await self._execute_empty_visit(
                        session=session,
                        cage_feeding=cage_feeding,
                        line_id=line_id,
                        slot_number=slot_number,
                        blower_power_percentage=blower_power_percentage,
                        visit_number=visit_number_in_round,
                        transport_time_seconds=transport_time,
                        blow_before_seconds=actual_blow_before,
                        blow_after_seconds=actual_blow_after,
                        selector_positioning_seconds=selector_positioning_seconds,
                        count_completed_visit=round_number < cage_feeding.programmed_visits,
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
                        blow_before_seconds=actual_blow_before,
                        blow_after_seconds=actual_blow_after,
                        selector_positioning_seconds=selector_positioning_seconds,
                        target_kg=planned_quantity,
                        hard_deadline_at=hard_deadline_at,
                    )

                completed_visit_executions += 1

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
                    await self._release_feeding_line(line_id)
                    return

                if wait_after_visit_seconds > 0 and completed_visit_executions < total_visit_executions:
                    effective_wait = wait_after_visit_seconds
                    if hard_deadline_at:
                        effective_wait = await self._calculate_adaptive_wait(
                            session_id=session.id,
                            round_number=round_number,
                            cage_index=cage_feeding_index,
                            total_rounds=total_rounds,
                            transport_time_map=transport_time_map,
                            selector_positioning_seconds=selector_positioning_seconds,
                            blow_after_seconds=blow_after_seconds,
                            hard_deadline_at=hard_deadline_at,
                        )
                    logger.info(
                        f"[Orchestrator] Session {session.id}: waiting "
                        f"{effective_wait:.1f}s before next cyclic visit"
                    )
                    if effective_wait > 0:
                        await asyncio.sleep(effective_wait)

        # Verificar una última vez antes de marcar como completada
        async with self._session_factory() as db:
            refreshed_session = await FeedingSessionRepository(db).find_by_id(session.id)
            if refreshed_session and refreshed_session.status.value in ("INTERRUPTED", "CANCELLED"):
                logger.info(
                    f"[Orchestrator] Session {session.id}: externally stopped before completion "
                    f"(status={refreshed_session.status.value}), aborting"
                )
                await self._release_feeding_line(line_id)
                return
            if refreshed_session:
                session = refreshed_session

        session.complete()
        total_dispensed = sum(cf.dispensed_kg for cf in cage_feedings)
        duration = (datetime.now(timezone.utc) - session.actual_start).total_seconds() if session.actual_start else 0.0
        completed_event = FeedingEvent.session_completed(
            feeding_session_id=session.id,
            total_dispensed_kg=total_dispensed,
            duration_seconds=duration,
        )

        async def _persist_completion(db: AsyncSession):
            await FeedingSessionRepository(db).save(session)
            await FeedingEventRepository(db).save(completed_event)
            await SiloInventoryRepository(db).release(session.id)

        await self._save(_persist_completion)
        await self._machine.stop(line_id)
        await self._turn_off_persisted_blower(line_id)
        await self._release_feeding_line(line_id)
        logger.info(f"[Orchestrator] Session {session.id}: COMPLETED")

    async def _execute_pause(
        self,
        session: FeedingSession,
        cage_feeding: CageFeeding,
        visit_number: int,
        transport_time_seconds: float,
        selector_positioning_seconds: float,
        target_kg: float | None = None,
        count_completed_visit: bool = True,
    ) -> None:
        """
        Simula una visita en modo PAUSE: espera el tiempo equivalente sin enviar
        nada al PLC. No dispensa, no descuenta silo.
        """
        simulated_target_kg = target_kg if target_kg is not None else cage_feeding.programmed_kg
        estimated_seconds = calculate_paused_visit_duration(
            quantity_kg=simulated_target_kg,
            rate_kg_per_min=cage_feeding.rate_kg_per_min,
            transport_time_seconds=transport_time_seconds,
            selector_positioning_seconds=selector_positioning_seconds,
        )

        logger.info(
            f"[Orchestrator] Session {session.id}: cage {cage_feeding.cage_id} "
            f"PAUSE — simulando visita por {estimated_seconds:.1f}s"
        )
        if not await self._wait_for_pause_or_stop(session.id, estimated_seconds):
            return
        if count_completed_visit:
            cage_feeding.increment_completed_visits()
        if cage_feeding.status.value == "PENDING":
            cage_feeding.start()
        if count_completed_visit and cage_feeding.completed_visits >= cage_feeding.programmed_visits:
            cage_feeding.complete()

        event = FeedingEvent.visit_simulated(
            feeding_session_id=session.id,
            cage_id=cage_feeding.cage_id,
            visit_number=visit_number,
            cycle_number=1,
            simulated_duration_seconds=estimated_seconds,
        )

        async def _persist_pause(db: AsyncSession):
            await CageFeedingRepository(db).record_visit_progress(
                cage_feeding.id,
                dispensed_kg=0.0,
                completed_visit=count_completed_visit,
            )
            await FeedingEventRepository(db).save(event)

        await self._save(_persist_pause)

    async def _wait_for_pause_or_stop(self, session_id: str, duration_seconds: float) -> bool:
        remaining_seconds = duration_seconds
        poll_interval = max(0.1, min(self._poll_interval, 1.0))
        while remaining_seconds > 0:
            async with self._session_factory() as db:
                session = await FeedingSessionRepository(db).find_by_id(session_id)
                if session and session.status.value in ("CANCELLED", "INTERRUPTED"):
                    return False
            wait_seconds = min(poll_interval, remaining_seconds)
            await asyncio.sleep(wait_seconds)
            remaining_seconds -= wait_seconds
        return True

    async def _execute_empty_visit(
        self,
        session: FeedingSession,
        cage_feeding: CageFeeding,
        line_id: LineId,
        slot_number: int,
        blower_power_percentage: float,
        visit_number: int,
        transport_time_seconds: float = 0.0,
        blow_before_seconds: float = 0.0,
        blow_after_seconds: float = 0.0,
        selector_positioning_seconds: float = 5.0,
        count_completed_visit: bool = False,
    ) -> None:
        await self._execute_visit(
            session=session,
            cage_feeding=cage_feeding,
            line_id=line_id,
            slot_number=slot_number,
            silo_id=SiloId.from_string(cage_feeding.silo_id),
            blower_power_percentage=blower_power_percentage,
            visit_number=visit_number,
            transport_time_seconds=transport_time_seconds,
            blow_before_seconds=blow_before_seconds,
            blow_after_seconds=blow_after_seconds,
            selector_positioning_seconds=selector_positioning_seconds,
            target_kg=0.0,
            doser_rate_kg_per_min=0.0,
            count_completed_visit=count_completed_visit,
            is_empty_visit=True,
        )

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
        target_kg: float | None = None,
        doser_rate_kg_per_min: float | None = None,
        count_completed_visit: bool = True,
        is_empty_visit: bool = False,
        hard_deadline_at: datetime | None = None,
    ) -> None:
        visit_start = datetime.now(timezone.utc)

        # Recargar desde DB para obtener ajustes live de apetito (cantidad/tasa).
        async with self._session_factory() as db:
            refreshed = await CageFeedingRepository(db).find_by_id(cage_feeding.id)
            current_rate = refreshed.rate_kg_per_min if refreshed else cage_feeding.rate_kg_per_min
            current_programmed_kg = refreshed.programmed_kg if refreshed else cage_feeding.programmed_kg
        command_target_kg = current_programmed_kg if target_kg is None else target_kg
        command_rate = current_rate if doser_rate_kg_per_min is None else doser_rate_kg_per_min

        command = MachineCommand(
            slot_number=slot_number,
            target_kg=command_target_kg,
            doser_rate_kg_per_min=command_rate,
            blower_power_percentage=blower_power_percentage,
            transport_time_seconds=transport_time_seconds,
            blow_before_seconds=blow_before_seconds,
            blow_after_seconds=blow_after_seconds,
            selector_positioning_seconds=selector_positioning_seconds,
            cage_id=cage_feeding.cage_id,
            cage_feeding_id=cage_feeding.id,
            visit_number=visit_number,
            is_empty_visit=is_empty_visit,
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
            is_empty_visit=is_empty_visit,
        )

        async def _persist_visit_start(db: AsyncSession):
            await CageFeedingRepository(db).mark_visit_started(cage_feeding.id)
            await FeedingEventRepository(db).save(visit_started_event)

        await self._save(_persist_visit_start)

        logger.info(
            f"[Orchestrator] Session {session.id}: visit {visit_number} started "
            f"slot={slot_number} target={command_target_kg}kg"
        )

        while True:
            await asyncio.sleep(self._poll_interval)
            status = await self._machine.get_status(line_id)

            if hard_deadline_at and datetime.now(timezone.utc) >= hard_deadline_at.astimezone(timezone.utc):
                if status.dispensed_kg > 0:
                    async def _persist_deadline_partial(db: AsyncSession):
                        await CageFeedingRepository(db).record_visit_progress(
                            cage_feeding.id,
                            dispensed_kg=status.dispensed_kg,
                            completed_visit=False,
                        )
                        await SiloInventoryRepository(db).consume(
                            session.id,
                            cage_feeding.id,
                            status.dispensed_kg,
                            getattr(session, "operator_id", "system:feeding"),
                        )
                    await self._save(_persist_deadline_partial)
                await self._interrupt_for_deadline(session, line_id, [cage_feeding])
                return

            # Verificar si la sesión fue cancelada o interrumpida externamente
            async with self._session_factory() as db:
                refreshed_session = await FeedingSessionRepository(db).find_by_id(session.id)
                if refreshed_session and refreshed_session.status.value in ("COMPLETED", "CANCELLED", "INTERRUPTED"):
                    logger.info(
                        f"[Orchestrator] Session {session.id}: externally stopped "
                        f"(status={refreshed_session.status.value}), exiting visit poll loop"
                    )
                    # Guardar la cantidad dispensada parcial antes de salir
                    if status.dispensed_kg > 0:
                        cage_feeding.add_dispensed_amount(status.dispensed_kg)
                        _captured_status = status

                        async def _persist_partial(db: AsyncSession):
                            inventory = SiloInventoryRepository(db)
                            try:
                                await inventory.consume(
                                    session.id,
                                    cage_feeding.id,
                                    _captured_status.dispensed_kg,
                                    getattr(session, "operator_id", "system:feeding"),
                                )
                            except ValueError as exc:
                                if "No existen reservas activas" not in str(exc):
                                    raise
                            else:
                                await CageFeedingRepository(db).record_visit_progress(
                                    cage_feeding.id,
                                    dispensed_kg=_captured_status.dispensed_kg,
                                    completed_visit=False,
                                )
                            await inventory.release(session.id)

                        await self._save(_persist_partial)
                        logger.info(
                            f"[Orchestrator] Session {session.id}: saved partial dispensed "
                            f"{status.dispensed_kg}kg for cage {cage_feeding.cage_id} on external stop"
                        )
                    return

            logger.info(
                f"[Orchestrator] Session {session.id}: poll — "
                f"dispensed={status.dispensed_kg:.3f}/{command_target_kg}kg "
                f"running={status.is_running} paused={status.is_paused}"
            )

            if status.has_error:
                logger.error(f"[Orchestrator] Session {session.id}: error code={status.error_code}")
                session.interrupt()
                interrupted_event = FeedingEvent.session_interrupted(
                    feeding_session_id=session.id,
                    reason=f"Machine error code={status.error_code}",
                    pending_visits=cage_feeding.programmed_visits - cage_feeding.completed_visits,
                )

                async def _persist_interrupt(db: AsyncSession):
                    if status.dispensed_kg > 0:
                        cage_feeding.add_dispensed_amount(status.dispensed_kg)
                        await CageFeedingRepository(db).record_visit_progress(
                            cage_feeding.id,
                            dispensed_kg=status.dispensed_kg,
                            completed_visit=False,
                        )
                        await SiloInventoryRepository(db).consume(
                            session.id,
                            cage_feeding.id,
                            status.dispensed_kg,
                            getattr(session, "operator_id", "system:feeding"),
                        )
                    await FeedingSessionRepository(db).save(session)
                    await FeedingEventRepository(db).save(interrupted_event)
                    await SiloInventoryRepository(db).release(session.id)

                await self._save(_persist_interrupt)
                await self._machine.stop(line_id)
                await self._turn_off_persisted_blower(line_id)
                await self._mark_feeding_line_fault(
                    line_id,
                    reason=f"Machine error code={status.error_code}",
                )
                return

            if status.current_stage == VisitStage.COMPLETED:
                duration_seconds = (datetime.now(timezone.utc) - visit_start).total_seconds()

                if count_completed_visit:
                    cage_feeding.add_dispensed_amount(status.dispensed_kg)
                    cage_feeding.increment_completed_visits()
                # Marcar COMPLETED solo cuando se terminaron todas las visitas programadas
                if count_completed_visit and cage_feeding.completed_visits >= cage_feeding.programmed_visits:
                    cage_feeding.complete()

                visit_completed_event = FeedingEvent.visit_completed(
                    feeding_session_id=session.id,
                    cage_id=cage_feeding.cage_id,
                    visit_number=visit_number,
                    cycle_number=1,
                    dispensed_grams=status.dispensed_kg * 1000,
                    duration_seconds=duration_seconds,
                    is_empty_visit=is_empty_visit,
                )

                async def _persist_visit_end(db: AsyncSession):
                    if count_completed_visit:
                        await CageFeedingRepository(db).record_visit_progress(
                            cage_feeding.id,
                            dispensed_kg=status.dispensed_kg,
                            completed_visit=True,
                        )
                    if count_completed_visit:
                        await SiloInventoryRepository(db).consume(
                            session.id,
                            cage_feeding.id,
                            status.dispensed_kg,
                            getattr(session, "operator_id", "system:feeding"),
                        )
                    await FeedingEventRepository(db).save(visit_completed_event)

                try:
                    await self._save(_persist_visit_end)
                except ValueError as exc:
                    session.interrupt()
                    discrepancy_event = FeedingEvent.alarm_triggered(
                        feeding_session_id=session.id,
                        alarm_type="SILO_INVENTORY_DISCREPANCY",
                        sensor_value=status.dispensed_kg,
                        threshold=command_target_kg,
                    )

                    async def _persist_discrepancy(db: AsyncSession):
                        await FeedingSessionRepository(db).save(session)
                        await FeedingEventRepository(db).save(discrepancy_event)
                        await SiloInventoryRepository(db).release(session.id)

                    await self._save(_persist_discrepancy)
                    await self._machine.stop(line_id)
                    await self._turn_off_persisted_blower(line_id)
                    await self._mark_feeding_line_fault(
                        line_id,
                        reason=f"Inventory reconciliation failed: {exc}",
                    )
                    logger.error(f"[Orchestrator] Session {session.id}: inventory discrepancy: {exc}")
                    return

                logger.info(
                    f"[Orchestrator] Session {session.id}: visit {visit_number} completed "
                    f"dispensed={status.dispensed_kg}kg in {duration_seconds:.1f}s"
                )
                return

    async def _interrupt_for_deadline(
        self,
        session: FeedingSession,
        line_id: LineId,
        cage_feedings: List[CageFeeding],
    ) -> None:
        session.interrupt()
        pending_visits = sum(max(0, item.programmed_visits - item.completed_visits) for item in cage_feedings)
        event = FeedingEvent.session_interrupted(
            feeding_session_id=session.id,
            reason="Hora límite ambiental alcanzada",
            pending_visits=pending_visits,
        )

        async def _persist(db: AsyncSession):
            await FeedingSessionRepository(db).save(session)
            await FeedingEventRepository(db).save(event)
            await SiloInventoryRepository(db).release(session.id)

        await self._machine.stop(line_id)
        await self._save(_persist)
        await self._turn_off_persisted_blower(line_id)
        await self._release_feeding_line(line_id)

    async def _calculate_adaptive_wait(
        self,
        *,
        session_id: str,
        round_number: int,
        cage_index: int,
        total_rounds: int,
        transport_time_map: Dict[str, float],
        selector_positioning_seconds: float,
        blow_after_seconds: float,
        hard_deadline_at: datetime,
    ) -> float:
        async with self._session_factory() as db:
            feedings = await CageFeedingRepository(db).find_by_session(session_id)
        feedings.sort(key=lambda item: item.execution_order)
        minimum_remaining = 0.0
        remaining_visits = 0
        for future_round in range(round_number, total_rounds):
            start_index = cage_index + 1 if future_round == round_number else 0
            for feeding in feedings[start_index:]:
                if feeding.mode == CageFeedingMode.FASTING:
                    continue
                remaining_visits += 1
                minimum_remaining += selector_positioning_seconds + transport_time_map.get(feeding.cage_id, 0.0)
                quantities = feeding.visit_quantities_kg or []
                quantity = quantities[future_round] if future_round < len(quantities) else 0.0
                if feeding.mode == CageFeedingMode.NORMAL and quantity > 0 and feeding.rate_kg_per_min > 0:
                    minimum_remaining += quantity / feeding.rate_kg_per_min * 60.0
        if remaining_visits == 0:
            return 0.0
        minimum_remaining += blow_after_seconds
        seconds_left = (hard_deadline_at.astimezone(timezone.utc) - datetime.now(timezone.utc)).total_seconds()
        return max(0.0, (seconds_left - minimum_remaining) / remaining_visits)

    async def _turn_off_persisted_blower(self, line_id: LineId) -> None:
        async def _persist_blower_off(db: AsyncSession):
            line = await FeedingLineRepository(db).find_by_id(line_id)
            if not line:
                return

            line.blower.current_power = BlowerPowerPercentage(0.0)
            await FeedingLineRepository(db).save(line)

        await self._save(_persist_blower_off)

    async def _release_feeding_line(self, line_id: LineId) -> None:
        async def _persist_release(db: AsyncSession):
            line = await FeedingLineRepository(db).find_by_id(line_id)
            if not line:
                return

            line.release_from_feeding()
            await FeedingLineRepository(db).save(line)

        await self._save(_persist_release)

    async def _mark_feeding_line_fault(self, line_id: LineId, reason: str) -> None:
        async def _persist_fault(db: AsyncSession):
            line = await FeedingLineRepository(db).find_by_id(line_id)
            if not line:
                return

            line.mark_fault(reason=reason)
            await FeedingLineRepository(db).save(line)

        await self._save(_persist_fault)
