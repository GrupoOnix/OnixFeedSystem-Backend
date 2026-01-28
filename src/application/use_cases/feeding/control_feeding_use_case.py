from uuid import UUID

from domain.interfaces import IFeedingMachine
from domain.repositories import IFeedingSessionRepository, IFeedingOperationRepository
from domain.value_objects import LineId

class PauseFeedingSessionUseCase:
    def __init__(
        self,
        session_repository: IFeedingSessionRepository,
        operation_repository: IFeedingOperationRepository,
        machine_service: IFeedingMachine
    ):
        self.session_repository = session_repository
        self.operation_repository = operation_repository
        self.machine_service = machine_service

    async def execute(self, line_id: UUID) -> None:
        session = await self.session_repository.find_active_by_line_id(LineId(line_id))
        if not session:
            return  # Idempotente

        # Cargar operación actual
        current_op = await self.operation_repository.find_current_by_session(session.id)
        if current_op:
            session._current_operation = current_op

        await session.pause_current_operation(self.machine_service)

        # Guardar operación (sesión no cambia)
        await self.operation_repository.save(session.current_operation)


class ResumeFeedingSessionUseCase:
    def __init__(
        self,
        session_repository: IFeedingSessionRepository,
        operation_repository: IFeedingOperationRepository,
        machine_service: IFeedingMachine
    ):
        self.session_repository = session_repository
        self.operation_repository = operation_repository
        self.machine_service = machine_service

    async def execute(self, line_id: UUID) -> None:
        session = await self.session_repository.find_active_by_line_id(LineId(line_id))
        if not session:
            raise ValueError("No active session to resume.")

        # Cargar operación actual
        current_op = await self.operation_repository.find_current_by_session(session.id)
        if current_op:
            session._current_operation = current_op

        await session.resume_current_operation(self.machine_service)

        # Guardar operación (sesión no cambia)
        await self.operation_repository.save(session.current_operation)
