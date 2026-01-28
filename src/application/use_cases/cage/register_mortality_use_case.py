from domain.repositories import ICageRepository, IMortalityLogRepository
from domain.value_objects import CageId, FishCount
from domain.value_objects.mortality_log_entry import MortalityLogEntry
from application.dtos.mortality_dtos import RegisterMortalityRequest


class RegisterMortalityUseCase:
    """
    Registra un evento de mortalidad en una jaula.
    
    IMPORTANTE: NO modifica current_fish_count de la jaula.
    Solo crea un registro en el log para auditoría y estadísticas.
    
    Patrón transaccional:
    - Si cualquier operación falla, toda la transacción se revierte
    - No hay commits explícitos, SQLAlchemy maneja la transacción
    """

    def __init__(
        self,
        cage_repository: ICageRepository,
        mortality_log_repository: IMortalityLogRepository
    ):
        self._cage_repo = cage_repository
        self._mortality_log_repo = mortality_log_repository

    async def execute(self, cage_id: str, request: RegisterMortalityRequest) -> None:
        """
        Ejecuta el registro de mortalidad.
        
        Args:
            cage_id: ID de la jaula
            request: Datos del registro de mortalidad
            
        Raises:
            ValueError: Si la jaula no existe o no tiene población
        """
        # Obtener jaula
        cage = await self._cage_repo.find_by_id(CageId.from_string(cage_id))
        if not cage:
            raise ValueError(f"La jaula con ID '{cage_id}' no existe")

        # Validar mortalidad (solo validación, NO modifica current_fish_count)
        cage.register_mortality(FishCount(request.dead_fish_count))

        # Crear registro en el log
        log_entry = MortalityLogEntry.create(
            cage_id=cage.id,
            dead_fish_count=request.dead_fish_count,
            mortality_date=request.mortality_date,
            note=request.note
        )

        # Persistir solo el log (NO se modifica la jaula)
        await self._mortality_log_repo.save(log_entry)
