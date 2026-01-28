
from domain.repositories import ICageRepository, IBiometryLogRepository
from domain.value_objects import CageId, FishCount, Weight
from domain.value_objects.biometry_log_entry import BiometryLogEntry
from application.dtos.biometry_dtos import RegisterBiometryRequest


class RegisterBiometryUseCase:
    """
    Registra un muestreo de biometría y actualiza los datos de la jaula.
    
    Patrón transaccional:
    - Si cualquier operación falla, toda la transacción se revierte
    - No hay commits explícitos, SQLAlchemy maneja la transacción
    """

    def __init__(
        self,
        cage_repository: ICageRepository,
        biometry_log_repository: IBiometryLogRepository
    ):
        self._cage_repo = cage_repository
        self._biometry_log_repo = biometry_log_repository

    async def execute(self, cage_id: str, request: RegisterBiometryRequest) -> None:
        if not request.fish_count and not request.average_weight_g:
            raise ValueError(
                "Debe proporcionar al menos uno de los siguientes campos: "
                "fish_count o average_weight_g"
            )

        cage = await self._cage_repo.find_by_id(CageId.from_string(cage_id))
        if not cage:
            raise ValueError(f"La jaula con ID '{cage_id}' no existe")

        old_fish_count = None
        new_fish_count = None
        old_avg_weight = None
        new_avg_weight = None

        if request.fish_count is not None:
            old_fish_count = cage.current_fish_count.value if cage.current_fish_count else None
            new_fish_count = request.fish_count
            cage.update_fish_count(FishCount(request.fish_count))

        if request.average_weight_g is not None:
            old_avg_weight = cage.avg_fish_weight.as_grams if cage.avg_fish_weight else None
            new_avg_weight = request.average_weight_g
            cage.update_biometry(Weight.from_grams(request.average_weight_g))

        log_entry = BiometryLogEntry.create(
            cage_id=cage.id,
            old_fish_count=old_fish_count,
            new_fish_count=new_fish_count,
            old_average_weight_g=old_avg_weight,
            new_average_weight_g=new_avg_weight,
            sampling_date=request.sampling_date,
            note=request.note
        )

        await self._cage_repo.save(cage)
        await self._biometry_log_repo.save(log_entry)
