from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from domain.aggregates.feeding_session import FeedingSession
from domain.dtos import MachineConfiguration
from domain.enums import SessionStatus
from domain.interfaces import IFeedingMachine
from domain.repositories import (
    IFeedingSessionRepository, 
    IFeedingLineRepository, 
    ICageRepository
)
from domain.strategies.manual import ManualFeedingStrategy
from domain.value_objects import LineId, CageId
from application.dtos.feeding_dtos import StartFeedingRequest

class StartFeedingSessionUseCase:
    def __init__(
        self,
        session_repository: IFeedingSessionRepository,
        line_repository: IFeedingLineRepository,
        cage_repository: ICageRepository,
        machine_service: IFeedingMachine
    ):
        self.session_repository = session_repository
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
        
        # Validar que la jaula pertenece a la línea solicitada
        if cage.line_id and cage.line_id.value != request.line_id:
             raise ValueError(f"Cage {request.cage_id} does not belong to Line {request.line_id}")

        # Resolver Slot Físico
        # physical_slot = cage.slot_number # DEPRECATED: Cage model doesn't store slot info directly
        physical_slot = await self.line_repository.get_slot_number(LineId(request.line_id), CageId(request.cage_id))
        
        if physical_slot is None:
             raise ValueError(f"Cage {request.cage_id} does not have a physical slot assigned.")

        # 3. Gestión de Sesión (Day Boundary)
        active_session = await self.session_repository.find_active_by_line_id(LineId(request.line_id))
        
        # Regla de Negocio: Corte de día (ej: 6 AM). 
        # Si la sesión activa es de "ayer" (operativamente), la cerramos.
        today = datetime.utcnow().date()
        
        if active_session:
            if active_session.date.date() < today:
                # Es una sesión vieja que quedó abierta.
                # TODO: Implementar lógica de cierre automático real.
                pass 
                
            if active_session.status in [SessionStatus.RUNNING, SessionStatus.PAUSED]:
                raise ValueError("There is already an active feeding session on this line.")

        # Crear nueva sesión si no hay válida
        session = FeedingSession(line_id=LineId(request.line_id))
        
        # 4. Estrategia
        # Por ahora solo soportamos MANUAL
        # NOTA: dosing_rate_kg_min viene del request, pero el PLC espera porcentaje (0-100).
        # Asumimos temporalmente que el valor ingresado ES el porcentaje o que hay una conversión 1:1.
        # En el futuro, usar tabla de calibración: percentage = calibration.get_speed_for_rate(rate)
        
        strategy = ManualFeedingStrategy(
            target_slot=physical_slot,
            blower_speed=request.blower_speed_percentage,
            doser_speed=request.dosing_rate_kg_min,
            target_amount_kg=request.target_amount_kg
        )
        
        # 5. Ejecución
        await session.start(strategy, self.machine_service)
        
        # 6. Persistencia
        await self.session_repository.save(session)
        
        return session.id.value
