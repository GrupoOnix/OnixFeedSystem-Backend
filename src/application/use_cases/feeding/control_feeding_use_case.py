from uuid import UUID

from domain.interfaces import IFeedingMachine
from domain.repositories import IFeedingSessionRepository
from domain.value_objects import LineId

class PauseFeedingSessionUseCase:
    def __init__(
        self,
        session_repository: IFeedingSessionRepository,
        machine_service: IFeedingMachine
    ):
        self.session_repository = session_repository
        self.machine_service = machine_service

    async def execute(self, line_id: UUID) -> None:
        session = await self.session_repository.find_active_by_line_id(LineId(line_id))
        if not session:
            return # Idempotente

        await session.pause(self.machine_service)
        await self.session_repository.save(session)


class ResumeFeedingSessionUseCase:
    def __init__(
        self,
        session_repository: IFeedingSessionRepository,
        machine_service: IFeedingMachine
    ):
        self.session_repository = session_repository
        self.machine_service = machine_service

    async def execute(self, line_id: UUID) -> None:
        session = await self.session_repository.find_active_by_line_id(LineId(line_id))
        if not session:
            raise ValueError("No active session to resume.")

        await session.resume(self.machine_service)
        await self.session_repository.save(session)
