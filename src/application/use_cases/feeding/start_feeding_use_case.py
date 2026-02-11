from datetime import datetime
from uuid import UUID

from domain.aggregates.feeding_session import FeedingSession
from domain.interfaces import IFeedingMachine
from domain.repositories import (
    IFeedingSessionRepository,
    IFeedingLineRepository,
    ICageRepository,
    IFeedingOperationRepository
)
from domain.strategies.manual import ManualFeedingStrategy
from domain.value_objects import LineId, CageId
from application.dtos.feeding_dtos import StartFeedingRequest

class StartFeedingSessionUseCase:
    def __init__(
        self,
        session_repository: IFeedingSessionRepository,
        operation_repository: IFeedingOperationRepository,
        line_repository: IFeedingLineRepository,
        cage_repository: ICageRepository,
        machine_service: IFeedingMachine
    ):
        self.session_repository = session_repository
        self.operation_repository = operation_repository
        self.line_repository = line_repository
        self.cage_repository = cage_repository
        self.machine_service = machine_service

    async def execute(self, request: StartFeedingRequest) -> UUID:
        # 1. Validar Línea
        line = await self.line_repository.find_by_id(LineId(request.line_id))
        if not line:
            raise ValueError(f"Line {request.line_id} not found")

        # 2. Validar Jaula y obtener Slot Físico
        cage = await self.cage_repository.find_by_id(CageId(request.cage_id))
        if not cage:
            raise ValueError(f"Cage {request.cage_id} not found")

        # Resolver Slot Físico
        physical_slot = await self.line_repository.get_slot_number(LineId(request.line_id), CageId(request.cage_id))

        if physical_slot is None:
             raise ValueError(f"Cage {request.cage_id} does not have a physical slot assigned.")

        # 3. Gestión de Sesión (Day Boundary)
        session = await self.session_repository.find_active_by_line_id(LineId(request.line_id))

        today = datetime.utcnow().date()

        if session:
            # Si la sesión es de ayer, cerrarla y crear nueva
            if session.date.date() < today:
                session.close_session()
                await self.session_repository.save(session)
                session = None

        # Crear nueva sesión si no existe (siempre en ACTIVE)
        if not session:
            session = FeedingSession(line_id=LineId(request.line_id))
            await self.session_repository.save(session)  # Guardar sesión nueva

        # 4. Cargar operación actual si existe
        current_op = await self.operation_repository.find_current_by_session(session.id)
        if current_op:
            session._current_operation = current_op

        # 5. Estrategia
        strategy = ManualFeedingStrategy(
            target_slot=physical_slot,
            blower_speed=request.blower_speed_percentage,
            doser_speed=request.dosing_rate_kg_min,
            target_amount_kg=request.target_amount_kg
        )

        # 6. Iniciar Operación
        operation_id = await session.start_operation(
            cage_id=CageId(request.cage_id),
            target_slot=physical_slot,
            strategy=strategy,
            machine=self.machine_service
        )

        # 7. Persistencia (sesión + operación)
        await self.session_repository.save(session)
        await self.operation_repository.save(session.current_operation)

        return operation_id.value
