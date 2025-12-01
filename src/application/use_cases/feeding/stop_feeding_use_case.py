from uuid import UUID

from domain.enums import SessionStatus
from domain.interfaces import IFeedingMachine
from domain.repositories import IFeedingSessionRepository
from domain.value_objects import LineId, SessionId

class StopFeedingSessionUseCase:
    def __init__(
        self,
        session_repository: IFeedingSessionRepository,
        machine_service: IFeedingMachine
    ):
        self.session_repository = session_repository
        self.machine_service = machine_service

    async def execute(self, line_id: UUID) -> None:
        # 1. Recuperar Sesión Activa
        session = await self.session_repository.find_active_by_line_id(LineId(line_id))
        
        if not session:
            # Si no hay sesión activa, no hacemos nada o lanzamos error.
            # Idempotencia: Si ya paró, todo bien.
            return

        # 2. Ejecutar Parada
        await session.stop(self.machine_service)
        
        # 3. Persistencia
        await self.session_repository.save(session)
