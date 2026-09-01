from dataclasses import dataclass

from domain.entities.cage_feeding import CageFeeding, CageFeedingMode
from domain.entities.feeding_event import FeedingEvent
from domain.entities.feeding_session import FeedingSession
from domain.enums import ActivityLogCategory, ActivityLogEventType
from domain.interfaces import IMachine
from domain.repositories import (
    ICageActivityLogRepository,
    ICageFeedingRepository,
    IFeedingEventRepository,
    IFeedingLineRepository,
    IFeedingSessionRepository,
)
from domain.value_objects import BlowerPowerPercentage, CageId, LineId
from domain.value_objects.activity_log_entry import ActivityLogEntry
from domain.value_objects.identifiers import DoserId
from infrastructure.persistence.repositories.silo_inventory_repository import (
    SiloInventoryRepository,
)


LIVE_SESSION_STATUSES = {"IN_PROGRESS", "PAUSED"}
LIVE_VISIT_STAGES = {"POSITIONING_SELECTOR", "BLOWING_BEFORE", "FEEDING", "BLOWING_AFTER"}


@dataclass(frozen=True)
class CyclicCageAmountUpdate:
    total_amount_kg: float
    current_visit_target_kg: float | None
    remaining_visit_quantities_kg: list[float]
    applied_immediately: bool


def _is_live_cage_visit(session: FeedingSession, machine_status, cage_feeding: CageFeeding) -> bool:
    if session.status.value not in LIVE_SESSION_STATUSES:
        return False
    if getattr(machine_status.current_stage, "value", machine_status.current_stage) not in LIVE_VISIT_STAGES:
        return False
    status_cage_feeding_id = getattr(machine_status, "cage_feeding_id", None)
    if status_cage_feeding_id:
        return status_cage_feeding_id == cage_feeding.id
    status_cage_id = getattr(machine_status, "cage_id", None)
    return bool(status_cage_id and status_cage_id == cage_feeding.cage_id)


def _validate_cyclic_cage_feeding(
    session: FeedingSession,
    cage_feedings: list[CageFeeding],
    cage_id: str,
) -> CageFeeding:
    if session.type.value != "CYCLIC":
        raise ValueError("El ajuste por jaula solo aplica a sesiones cíclicas")
    if session.status.value not in LIVE_SESSION_STATUSES:
        raise ValueError(f"La sesión no está activa (estado: {session.status.value})")

    cage_feeding = next((cf for cf in cage_feedings if cf.cage_id == cage_id), None)
    if not cage_feeding:
        raise ValueError(f"La jaula {cage_id} no pertenece a la sesión {session.id}")
    if cage_feeding.mode == CageFeedingMode.FASTING:
        raise ValueError("No se puede ajustar una jaula en FASTING")
    if cage_feeding.status.value in ("COMPLETED", "CANCELLED"):
        raise ValueError(f"La jaula no se puede ajustar en estado {cage_feeding.status.value}")
    if cage_feeding.completed_visits >= cage_feeding.programmed_visits:
        raise ValueError("La jaula ya completó sus visitas programadas")
    return cage_feeding


class UpdateFeedingRateUseCase:
    def __init__(
        self,
        session_repo: IFeedingSessionRepository,
        cage_feeding_repo: ICageFeedingRepository,
        event_repo: IFeedingEventRepository,
        machine: IMachine,
        line_repo: IFeedingLineRepository,
    ):
        self._session_repo = session_repo
        self._cage_feeding_repo = cage_feeding_repo
        self._event_repo = event_repo
        self._machine = machine
        self._line_repo = line_repo

    async def execute(self, session_id: str, new_rate: float) -> float:
        session = await self._session_repo.find_by_id(session_id)
        if not session:
            raise ValueError(f"Sesión {session_id} no encontrada")
        if session.status.value not in ("IN_PROGRESS", "PAUSED"):
            raise ValueError(f"La sesión no está activa (estado: {session.status.value})")

        cage_feedings = await self._cage_feeding_repo.find_by_session(session_id)
        current = next((cf for cf in cage_feedings if cf.status.value == "IN_PROGRESS"), None)
        if not current:
            raise ValueError("No hay alimentación de jaula activa en esta sesión")

        if current.doser_id:
            line = await self._line_repo.find_by_id(LineId.from_string(session.line_id))
            if line:
                doser = line.get_doser_by_id(DoserId.from_string(current.doser_id))
                if doser and new_rate > doser.max_rate_kg_per_min:
                    raise ValueError(
                        f"La tasa solicitada ({new_rate} kg/min) supera la capacidad máxima "
                        f"del doser ({doser.max_rate_kg_per_min} kg/min)"
                    )

        previous_rate = current.rate_kg_per_min

        await self._machine.set_doser_rate(LineId.from_string(session.line_id), new_rate)
        await self._cage_feeding_repo.update_rate(current.id, new_rate)

        event = FeedingEvent.rate_changed(
            feeding_session_id=session_id,
            cage_id=current.cage_id,
            previous_rate=previous_rate,
            new_rate=new_rate,
            applied_immediately=session.status.value == "IN_PROGRESS",
        )
        await self._event_repo.save(event)

        return new_rate


class UpdateFeedingAmountUseCase:
    def __init__(
        self,
        session_repo: IFeedingSessionRepository,
        cage_feeding_repo: ICageFeedingRepository,
        event_repo: IFeedingEventRepository,
        machine: IMachine,
        inventory_repo: SiloInventoryRepository | None = None,
    ):
        self._session_repo = session_repo
        self._cage_feeding_repo = cage_feeding_repo
        self._event_repo = event_repo
        self._machine = machine
        self._inventory_repo = inventory_repo

    async def execute(self, session_id: str, new_amount_kg: float) -> float:
        session = await self._session_repo.find_by_id(session_id)
        if not session:
            raise ValueError(f"Sesión {session_id} no encontrada")
        if session.status.value not in ("IN_PROGRESS", "PAUSED"):
            raise ValueError(f"La sesión no está activa (estado: {session.status.value})")
        if new_amount_kg <= 0:
            raise ValueError("La cantidad debe ser mayor a 0")

        cage_feedings = await self._cage_feeding_repo.find_by_session(session_id)
        current = next((cf for cf in cage_feedings if cf.status.value == "IN_PROGRESS"), None)
        if not current:
            raise ValueError("No hay alimentación de jaula activa en esta sesión")

        line_id = LineId.from_string(session.line_id)
        machine_status = await self._machine.get_status(line_id)
        live_dispensed_kg = machine_status.dispensed_kg
        if new_amount_kg < live_dispensed_kg:
            raise ValueError(
                f"La nueva cantidad ({new_amount_kg} kg) no puede ser menor a lo ya "
                f"dispensado en la visita actual ({live_dispensed_kg} kg)"
            )

        previous_amount_kg = current.programmed_kg
        if self._inventory_repo:
            await self._inventory_repo.resize_reservation(session_id, new_amount_kg)

        await self._machine.set_target_amount(line_id, new_amount_kg)
        current = await self._cage_feeding_repo.update_programmed_kg(current.id, new_amount_kg)

        total_programmed_kg = sum(
            (current if cf.id == current.id else cf).programmed_kg
            * (current if cf.id == current.id else cf).programmed_visits
            for cf in cage_feedings
        )
        session.set_total_programmed_kg(total_programmed_kg)
        await self._session_repo.save(session)

        event = FeedingEvent.amount_changed(
            feeding_session_id=session_id,
            cage_id=current.cage_id,
            previous_amount_kg=previous_amount_kg,
            new_amount_kg=new_amount_kg,
            live_dispensed_kg=live_dispensed_kg,
            applied_immediately=session.status.value == "IN_PROGRESS",
        )
        await self._event_repo.save(event)

        return new_amount_kg


class UpdateCyclicCageRateUseCase:
    def __init__(
        self,
        session_repo: IFeedingSessionRepository,
        cage_feeding_repo: ICageFeedingRepository,
        event_repo: IFeedingEventRepository,
        machine: IMachine,
        line_repo: IFeedingLineRepository,
    ):
        self._session_repo = session_repo
        self._cage_feeding_repo = cage_feeding_repo
        self._event_repo = event_repo
        self._machine = machine
        self._line_repo = line_repo

    async def execute(self, session_id: str, cage_id: str, new_rate: float) -> float:
        session = await self._session_repo.find_by_id(session_id)
        if not session:
            raise ValueError(f"Sesión {session_id} no encontrada")
        if new_rate <= 0:
            raise ValueError("La tasa debe ser mayor a 0")

        cage_feedings = await self._cage_feeding_repo.find_by_session(session_id)
        cage_feeding = _validate_cyclic_cage_feeding(session, cage_feedings, cage_id)
        line_id = LineId.from_string(session.line_id)

        if cage_feeding.doser_id:
            line = await self._line_repo.find_by_id(line_id)
            if line:
                doser = line.get_doser_by_id(DoserId.from_string(cage_feeding.doser_id))
                if doser and new_rate > doser.max_rate_kg_per_min:
                    raise ValueError(
                        f"La tasa solicitada ({new_rate} kg/min) supera la capacidad máxima "
                        f"del doser ({doser.max_rate_kg_per_min} kg/min)"
                    )

        machine_status = await self._machine.get_status(line_id)
        applied_immediately = _is_live_cage_visit(session, machine_status, cage_feeding)
        previous_rate = cage_feeding.rate_kg_per_min

        if applied_immediately:
            await self._machine.set_doser_rate(line_id, new_rate)
        await self._cage_feeding_repo.update_rate(cage_feeding.id, new_rate)

        event = FeedingEvent.rate_changed(
            feeding_session_id=session_id,
            cage_id=cage_id,
            previous_rate=previous_rate,
            new_rate=new_rate,
            applied_immediately=applied_immediately,
        )
        await self._event_repo.save(event)

        return new_rate


class UpdateCyclicCageAmountUseCase:
    def __init__(
        self,
        session_repo: IFeedingSessionRepository,
        cage_feeding_repo: ICageFeedingRepository,
        event_repo: IFeedingEventRepository,
        machine: IMachine,
        inventory_repo: SiloInventoryRepository | None = None,
    ):
        self._session_repo = session_repo
        self._cage_feeding_repo = cage_feeding_repo
        self._event_repo = event_repo
        self._machine = machine
        self._inventory_repo = inventory_repo

    async def execute(
        self,
        session_id: str,
        cage_id: str,
        new_total_amount_kg: float,
    ) -> CyclicCageAmountUpdate:
        session = await self._session_repo.find_by_id(session_id)
        if not session:
            raise ValueError(f"Sesión {session_id} no encontrada")
        if new_total_amount_kg <= 0:
            raise ValueError("La cantidad debe ser mayor a 0")

        cage_feedings = await self._cage_feeding_repo.find_by_session(session_id)
        cage_feeding = _validate_cyclic_cage_feeding(session, cage_feedings, cage_id)
        line_id = LineId.from_string(session.line_id)
        machine_status = await self._machine.get_status(line_id)
        applied_immediately = _is_live_cage_visit(session, machine_status, cage_feeding)
        live_dispensed_kg = machine_status.dispensed_kg if applied_immediately else 0.0
        already_dispensed = cage_feeding.dispensed_kg + live_dispensed_kg
        if new_total_amount_kg < already_dispensed:
            raise ValueError(
                f"La nueva cantidad total ({new_total_amount_kg} kg) no puede ser menor a lo ya "
                f"dispensado para la jaula ({already_dispensed} kg)"
            )

        visit_quantities_kg, new_amount_per_visit, current_visit_target_kg = self._build_remaining_visit_plan(
            cage_feeding=cage_feeding,
            new_total_amount_kg=new_total_amount_kg,
            live_dispensed_kg=live_dispensed_kg,
            applied_immediately=applied_immediately,
        )

        previous_amount_kg = cage_feeding.programmed_kg
        new_session_total = self._recalculate_session_total(
            cage_feedings=cage_feedings,
            updated_cage_feeding=cage_feeding,
            updated_visit_quantities_kg=visit_quantities_kg,
        )
        if self._inventory_repo:
            await self._inventory_repo.resize_reservation(session_id, new_session_total)

        if applied_immediately and current_visit_target_kg is not None:
            await self._machine.set_target_amount(line_id, current_visit_target_kg)
        cage_feeding = await self._cage_feeding_repo.update_amount_plan(
            cage_feeding.id,
            new_amount_per_visit,
            visit_quantities_kg,
        )

        total_programmed_kg = self._recalculate_session_total(
            cage_feedings=cage_feedings,
            updated_cage_feeding=cage_feeding,
            updated_visit_quantities_kg=cage_feeding.visit_quantities_kg,
        )
        session.set_total_programmed_kg(total_programmed_kg)
        await self._session_repo.save(session)

        event = FeedingEvent.amount_changed(
            feeding_session_id=session_id,
            cage_id=cage_id,
            previous_amount_kg=previous_amount_kg,
            new_amount_kg=new_amount_per_visit,
            live_dispensed_kg=live_dispensed_kg,
            applied_immediately=applied_immediately,
        )
        await self._event_repo.save(event)

        return CyclicCageAmountUpdate(
            total_amount_kg=new_total_amount_kg,
            current_visit_target_kg=current_visit_target_kg,
            remaining_visit_quantities_kg=visit_quantities_kg[cage_feeding.completed_visits :],
            applied_immediately=applied_immediately,
        )

    def _build_remaining_visit_plan(
        self,
        cage_feeding: CageFeeding,
        new_total_amount_kg: float,
        live_dispensed_kg: float,
        applied_immediately: bool,
    ) -> tuple[list[float], float, float | None]:
        remaining_visits = cage_feeding.programmed_visits - cage_feeding.completed_visits
        if remaining_visits <= 0:
            raise ValueError("La jaula ya completó sus visitas programadas")

        existing_plan = cage_feeding.visit_quantities_kg
        if existing_plan is None:
            existing_plan = [cage_feeding.programmed_kg] * cage_feeding.programmed_visits
        if len(existing_plan) != cage_feeding.programmed_visits:
            raise ValueError("El plan por visita almacenado es inválido")

        remaining_amount = new_total_amount_kg - cage_feeding.dispensed_kg
        if applied_immediately:
            remaining_amount -= live_dispensed_kg
        if remaining_amount < -0.000001:
            raise ValueError("La nueva cantidad no puede ser menor a lo ya dispensado")
        remaining_amount = max(remaining_amount, 0.0)

        scheduled_remaining = self._split_amount(remaining_amount, remaining_visits)
        completed_plan = existing_plan[: cage_feeding.completed_visits]
        if applied_immediately:
            current_visit_target_kg = round(live_dispensed_kg + scheduled_remaining[0], 6)
            visit_quantities_kg = [
                *completed_plan,
                current_visit_target_kg,
                *scheduled_remaining[1:],
            ]
        else:
            current_visit_target_kg = None
            visit_quantities_kg = [*completed_plan, *scheduled_remaining]

        return visit_quantities_kg, scheduled_remaining[0], current_visit_target_kg

    @staticmethod
    def _split_amount(amount_kg: float, visits: int) -> list[float]:
        amount_per_visit = round(amount_kg / visits, 6)
        quantities = [amount_per_visit] * visits
        quantities[-1] = round(amount_kg - sum(quantities[:-1]), 6)
        return quantities

    def _recalculate_session_total(
        self,
        cage_feedings: list[CageFeeding],
        updated_cage_feeding: CageFeeding,
        updated_visit_quantities_kg: list[float] | None,
    ) -> float:
        total = 0.0
        for cf in cage_feedings:
            current = updated_cage_feeding if cf.id == updated_cage_feeding.id else cf
            if current.mode == CageFeedingMode.FASTING:
                continue
            visit_quantities_kg = (
                updated_visit_quantities_kg
                if current.id == updated_cage_feeding.id and updated_visit_quantities_kg is not None
                else current.visit_quantities_kg
            )
            if visit_quantities_kg is None:
                visit_quantities_kg = [current.programmed_kg] * current.programmed_visits
            total += current.dispensed_kg + sum(visit_quantities_kg[current.completed_visits :])
        return total


class UpdateCageModeUseCase:
    def __init__(
        self,
        session_repo: IFeedingSessionRepository,
        cage_feeding_repo: ICageFeedingRepository,
        event_repo: IFeedingEventRepository,
    ):
        self._session_repo = session_repo
        self._cage_feeding_repo = cage_feeding_repo
        self._event_repo = event_repo

    async def execute(
        self,
        session_id: str,
        cage_id: str,
        new_mode: str,
        operator_id: str,
    ) -> tuple[str, str]:
        session = await self._session_repo.find_by_id(session_id)
        if not session:
            raise ValueError(f"Sesión {session_id} no encontrada")
        if session.type.value != "CYCLIC":
            raise ValueError("El cambio de modo por jaula solo aplica a sesiones cíclicas")
        if session.status.value not in ("IN_PROGRESS", "PAUSED"):
            raise ValueError(f"La sesión no está activa (estado: {session.status.value})")

        try:
            mode = CageFeedingMode(new_mode)
        except ValueError:
            raise ValueError("mode debe ser 'NORMAL' o 'PAUSE'") from None
        if mode == CageFeedingMode.FASTING:
            raise ValueError("No se permite cambiar a FASTING durante una sesión activa")

        cage_feedings = await self._cage_feeding_repo.find_by_session(session_id)
        cage_feeding = next((cf for cf in cage_feedings if cf.cage_id == cage_id), None)
        if not cage_feeding:
            raise ValueError(f"La jaula {cage_id} no pertenece a la sesión {session_id}")
        if cage_feeding.mode == CageFeedingMode.FASTING:
            raise ValueError("No se puede cambiar el modo de una jaula en FASTING")
        if cage_feeding.completed_visits >= cage_feeding.programmed_visits:
            raise ValueError("La jaula ya completó sus visitas programadas")

        previous_mode = cage_feeding.mode.value
        if previous_mode == mode.value:
            return previous_mode, mode.value

        await self._cage_feeding_repo.update_mode(cage_feeding.id, mode)

        event = FeedingEvent.cage_mode_changed(
            feeding_session_id=session_id,
            cage_id=cage_id,
            previous_mode=previous_mode,
            new_mode=mode.value,
            operator_id=operator_id,
            applied_immediately=False,
        )
        await self._event_repo.save(event)

        return previous_mode, mode.value


class PauseFeedingUseCase:
    def __init__(
        self,
        session_repo: IFeedingSessionRepository,
        cage_feeding_repo: ICageFeedingRepository,
        event_repo: IFeedingEventRepository,
        machine: IMachine,
        activity_log_repository: ICageActivityLogRepository,
    ):
        self._session_repo = session_repo
        self._cage_feeding_repo = cage_feeding_repo
        self._event_repo = event_repo
        self._machine = machine
        self._activity_log_repo = activity_log_repository

    async def execute(self, session_id: str, operator_id: str, actor: str, reason: str) -> None:
        session = await self._session_repo.find_by_id(session_id)
        if not session:
            raise ValueError(f"Sesión {session_id} no encontrada")

        session.pause()
        await self._machine.pause(LineId.from_string(session.line_id))
        await self._session_repo.save(session)

        event = FeedingEvent.session_paused(
            feeding_session_id=session_id,
            operator_id=operator_id,
            reason=reason,
        )
        await self._event_repo.save(event)

        cage_feedings = await self._cage_feeding_repo.find_by_session(session_id)
        for cf in cage_feedings:
            await self._activity_log_repo.save(
                ActivityLogEntry.create(
                    cage_id=CageId.from_string(cf.cage_id),
                    event_type=ActivityLogEventType.INFO,
                    category=ActivityLogCategory.FEEDING,
                    message="Alimentación pausada",
                    details=reason if reason else None,
                    actor=actor,
                    source_entity_type="feeding_session",
                    source_entity_id=session_id,
                )
            )


class ResumeFeedingUseCase:
    def __init__(
        self,
        session_repo: IFeedingSessionRepository,
        cage_feeding_repo: ICageFeedingRepository,
        event_repo: IFeedingEventRepository,
        machine: IMachine,
        activity_log_repository: ICageActivityLogRepository,
    ):
        self._session_repo = session_repo
        self._cage_feeding_repo = cage_feeding_repo
        self._event_repo = event_repo
        self._machine = machine
        self._activity_log_repo = activity_log_repository

    async def execute(self, session_id: str, operator_id: str, actor: str) -> None:
        session = await self._session_repo.find_by_id(session_id)
        if not session:
            raise ValueError(f"Sesión {session_id} no encontrada")

        session.resume()
        await self._machine.resume(LineId.from_string(session.line_id))
        await self._session_repo.save(session)

        event = FeedingEvent.session_resumed(
            feeding_session_id=session_id,
            operator_id=operator_id,
        )
        await self._event_repo.save(event)

        cage_feedings = await self._cage_feeding_repo.find_by_session(session_id)
        for cf in cage_feedings:
            await self._activity_log_repo.save(
                ActivityLogEntry.create(
                    cage_id=CageId.from_string(cf.cage_id),
                    event_type=ActivityLogEventType.INFO,
                    category=ActivityLogCategory.FEEDING,
                    message="Alimentación reanudada",
                    actor=actor,
                    source_entity_type="feeding_session",
                    source_entity_id=session_id,
                )
            )


class CancelFeedingUseCase:
    def __init__(
        self,
        session_repo: IFeedingSessionRepository,
        cage_feeding_repo: ICageFeedingRepository,
        event_repo: IFeedingEventRepository,
        line_repo: IFeedingLineRepository,
        machine: IMachine,
        activity_log_repository: ICageActivityLogRepository,
        inventory_repo: SiloInventoryRepository | None = None,
    ):
        self._session_repo = session_repo
        self._cage_feeding_repo = cage_feeding_repo
        self._event_repo = event_repo
        self._line_repo = line_repo
        self._machine = machine
        self._activity_log_repo = activity_log_repository
        self._inventory_repo = inventory_repo

    async def execute(self, session_id: str, operator_id: str, actor: str, reason: str) -> None:
        session = await self._session_repo.find_by_id(session_id)
        if not session:
            raise ValueError(f"Sesión {session_id} no encontrada")

        line_id = LineId.from_string(session.line_id)
        cage_feedings = await self._cage_feeding_repo.find_by_session(session_id)
        current = next((cf for cf in cage_feedings if cf.status.value == "IN_PROGRESS"), None)
        machine_status = await self._machine.get_status(line_id)
        if self._inventory_repo and current and machine_status.dispensed_kg > 0:
            current.add_dispensed_amount(machine_status.dispensed_kg)
            await self._cage_feeding_repo.record_visit_progress(
                current.id,
                dispensed_kg=machine_status.dispensed_kg,
                completed_visit=False,
            )
            await self._inventory_repo.consume(
                session_id,
                current.id,
                machine_status.dispensed_kg,
                operator_id,
            )
        session.cancel()
        await self._machine.stop(line_id)
        await self._turn_off_persisted_blower(line_id)
        await self._release_feeding_line(line_id)
        await self._session_repo.save(session)
        if self._inventory_repo:
            await self._inventory_repo.release(session_id)

        event = FeedingEvent.session_cancelled(
            feeding_session_id=session_id,
            operator_id=operator_id,
            reason=reason,
        )
        await self._event_repo.save(event)

        cage_feedings = await self._cage_feeding_repo.find_by_session(session_id)
        for cf in cage_feedings:
            await self._activity_log_repo.save(
                ActivityLogEntry.create(
                    cage_id=CageId.from_string(cf.cage_id),
                    event_type=ActivityLogEventType.INFO,
                    category=ActivityLogCategory.FEEDING,
                    message="Alimentación cancelada",
                    details=reason if reason else None,
                    actor=actor,
                    source_entity_type="feeding_session",
                    source_entity_id=session_id,
                )
            )

    async def _turn_off_persisted_blower(self, line_id: LineId) -> None:
        line = await self._line_repo.find_by_id(line_id)
        if not line:
            return

        line.blower.current_power = BlowerPowerPercentage(0.0)
        await self._line_repo.save(line)

    async def _release_feeding_line(self, line_id: LineId) -> None:
        line = await self._line_repo.find_by_id(line_id)
        if not line:
            return

        line.release_from_feeding()
        await self._line_repo.save(line)


class UpdateBlowerPowerUseCase:
    def __init__(
        self,
        session_repo: IFeedingSessionRepository,
        machine: IMachine,
    ):
        self._session_repo = session_repo
        self._machine = machine

    async def execute(self, session_id: str, power_percentage: float) -> float:
        session = await self._session_repo.find_by_id(session_id)
        if not session:
            raise ValueError(f"Sesión {session_id} no encontrada")
        if session.status.value not in ("IN_PROGRESS", "PAUSED"):
            raise ValueError(f"La sesión no está activa (estado: {session.status.value})")

        await self._machine.set_blower_power(LineId.from_string(session.line_id), power_percentage)
        return power_percentage
