from uuid import UUID

from domain.enums import SessionStatus
from domain.interfaces import IFeedingMachine
from domain.repositories import IFeedingSessionRepository
from domain.value_objects import LineId
from domain.strategies.manual import ManualFeedingStrategy
from application.dtos.feeding_dtos import UpdateParamsRequest

class UpdateFeedingParametersUseCase:
    def __init__(
        self,
        session_repository: IFeedingSessionRepository,
        machine_service: IFeedingMachine
    ):
        self.session_repository = session_repository
        self.machine_service = machine_service

    async def execute(self, request: UpdateParamsRequest) -> None:
        # 1. Recuperar Sesión
        session = await self.session_repository.find_active_by_line_id(LineId(request.line_id))
        if not session:
            raise ValueError("No active feeding session found.")
            
        if session.status != SessionStatus.RUNNING:
            raise ValueError("Session must be RUNNING to update parameters.")

        # 2. Reconstruir Estrategia Actual
        # Asumimos que es MANUAL por ahora.
        # En el futuro, FeedingSession debería saber qué clase de estrategia usar o guardarla.
        # Por simplicidad y dado que el MVP es Manual, instanciamos ManualFeedingStrategy.
        # Necesitamos recuperar los valores actuales del snapshot para no perder lo que no cambia.
        
        current_config = session.applied_strategy_config
        if not current_config:
             raise ValueError("Session has no active configuration.")
             
        # Extraer valores actuales
        # Nota: MachineConfiguration tiene slot_numbers (lista), pero ManualStrategy usa target_slot (int).
        # Asumimos lista de 1 elemento.
        current_slots = current_config.get("slot_numbers", [])
        if not current_slots:
            raise ValueError("Invalid configuration state: no slots.")
            
        current_slot = current_slots[0]
        current_blower = current_config.get("blower_speed_percentage", 0.0)
        current_doser = current_config.get("doser_speed_percentage", 0.0)
        
        current_target = current_config.get("target_amount_kg", 0.0)
        
        # 3. Aplicar Cambios (Merge)
        new_blower = request.blower_speed if request.blower_speed is not None else current_blower
        new_doser = request.dosing_rate if request.dosing_rate is not None else current_doser
        
        new_strategy = ManualFeedingStrategy(
            target_slot=current_slot,
            blower_speed=new_blower,
            doser_speed=new_doser,
            target_amount_kg=current_target
        )
        
        # 4. Ejecutar Actualización
        await session.update_parameters(new_strategy, self.machine_service)
        
        # 5. Persistencia
        await self.session_repository.save(session)
