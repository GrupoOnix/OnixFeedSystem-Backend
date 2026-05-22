from domain.entities.cage_feeding import CageFeedingMode
from domain.entities.feeding_event import FeedingEvent
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
        current.set_rate(new_rate)

        await self._machine.set_doser_rate(LineId.from_string(session.line_id), new_rate)
        await self._cage_feeding_repo.save(current)

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
    ):
        self._session_repo = session_repo
        self._cage_feeding_repo = cage_feeding_repo
        self._event_repo = event_repo
        self._machine = machine

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
        current.set_programmed_kg(new_amount_kg)

        await self._machine.set_target_amount(line_id, new_amount_kg)
        await self._cage_feeding_repo.save(current)

        total_programmed_kg = sum(
            cf.programmed_kg * cf.programmed_visits
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

        cage_feeding.set_mode(mode)
        await self._cage_feeding_repo.save(cage_feeding)

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

    async def execute(self, session_id: str, operator_id: str, reason: str) -> None:
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

    async def execute(self, session_id: str, operator_id: str) -> None:
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
    ):
        self._session_repo = session_repo
        self._cage_feeding_repo = cage_feeding_repo
        self._event_repo = event_repo
        self._line_repo = line_repo
        self._machine = machine
        self._activity_log_repo = activity_log_repository

    async def execute(self, session_id: str, operator_id: str, reason: str) -> None:
        session = await self._session_repo.find_by_id(session_id)
        if not session:
            raise ValueError(f"Sesión {session_id} no encontrada")

        line_id = LineId.from_string(session.line_id)
        session.cancel()
        await self._machine.stop(line_id)
        await self._turn_off_persisted_blower(line_id)
        await self._release_feeding_line(line_id)
        await self._session_repo.save(session)

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
