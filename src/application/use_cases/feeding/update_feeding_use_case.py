
from domain.enums import OperationStatus
from domain.interfaces import IFeedingMachine
from domain.repositories import IFeedingSessionRepository, IFeedingOperationRepository
from domain.value_objects import LineId
from domain.strategies.manual import ManualFeedingStrategy
from application.dtos.feeding_dtos import UpdateParamsRequest

class UpdateFeedingParametersUseCase:
    def __init__(
        self,
        session_repository: IFeedingSessionRepository,
        operation_repository: IFeedingOperationRepository,
        machine_service: IFeedingMachine
    ):
        self.session_repository = session_repository
        self.operation_repository = operation_repository
        self.machine_service = machine_service

    async def execute(self, request: UpdateParamsRequest) -> None:
        # 1. Recuperar Sesión
        session = await self.session_repository.find_active_by_line_id(LineId(request.line_id))
        if not session:
            raise ValueError("No active feeding session found.")

        # 2. Cargar operación actual
        current_op = await self.operation_repository.find_current_by_session(session.id)
        if not current_op:
            raise ValueError("No active operation to update.")

        session._current_operation = current_op

        if session.current_operation.status != OperationStatus.RUNNING:
            raise ValueError("Operation must be RUNNING to update parameters.")

        # 3. Reconstruir estrategia desde la operación actual
        current_config = session.current_operation.applied_config

        # Extraer valores actuales
        current_slots = current_config.get("slot_numbers", [])
        if not current_slots:
            raise ValueError("Invalid configuration state: no slots.")

        current_slot = current_slots[0]
        current_blower = current_config.get("blower_speed_percentage", 0.0)
        current_doser = current_config.get("doser_speed_percentage", 0.0)
        current_target = current_config.get("target_amount_kg", 0.0)

        # 4. Aplicar Cambios (Merge)
        new_blower = request.blower_speed if request.blower_speed is not None else current_blower
        new_doser = request.dosing_rate if request.dosing_rate is not None else current_doser

        new_strategy = ManualFeedingStrategy(
            target_slot=current_slot,
            blower_speed=new_blower,
            doser_speed=new_doser,
            target_amount_kg=current_target
        )

        # 5. Ejecutar Actualización
        await session.update_current_operation_params(new_strategy, self.machine_service)

        # 6. Persistencia (solo operación)
        await self.operation_repository.save(session.current_operation)
