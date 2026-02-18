from domain.entities.feeding_event import FeedingEvent
from domain.interfaces import IMachine
from domain.repositories import (
    ICageFeedingRepository,
    IFeedingEventRepository,
    IFeedingSessionRepository,
)
from domain.value_objects import LineId


class UpdateFeedingRateUseCase:

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


class PauseFeedingUseCase:

    def __init__(
        self,
        session_repo: IFeedingSessionRepository,
        event_repo: IFeedingEventRepository,
        machine: IMachine,
    ):
        self._session_repo = session_repo
        self._event_repo = event_repo
        self._machine = machine

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


class ResumeFeedingUseCase:

    def __init__(
        self,
        session_repo: IFeedingSessionRepository,
        event_repo: IFeedingEventRepository,
        machine: IMachine,
    ):
        self._session_repo = session_repo
        self._event_repo = event_repo
        self._machine = machine

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


class CancelFeedingUseCase:

    def __init__(
        self,
        session_repo: IFeedingSessionRepository,
        event_repo: IFeedingEventRepository,
        machine: IMachine,
    ):
        self._session_repo = session_repo
        self._event_repo = event_repo
        self._machine = machine

    async def execute(self, session_id: str, operator_id: str, reason: str) -> None:
        session = await self._session_repo.find_by_id(session_id)
        if not session:
            raise ValueError(f"Sesión {session_id} no encontrada")

        session.cancel()
        await self._machine.stop(LineId.from_string(session.line_id))
        await self._session_repo.save(session)

        event = FeedingEvent.session_cancelled(
            feeding_session_id=session_id,
            operator_id=operator_id,
            reason=reason,
        )
        await self._event_repo.save(event)


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
