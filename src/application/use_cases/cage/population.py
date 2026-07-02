"""Use cases para gestión de población de jaulas."""

from application.dtos.cage_dtos import (
    AdjustPopulationRequest,
    CageConfigResponse,
    CageResponse,
    HarvestRequest,
    RegisterMortalityRequest,
    SetPopulationRequest,
    UpdateBiometryRequest,
)
from domain.aggregates.cage import Cage
from domain.enums import ActivityLogCategory, ActivityLogEventType
from domain.repositories import (
    IBiometryLogRepository,
    ICageActivityLogRepository,
    ICageRepository,
    IMortalityLogRepository,
    IPopulationEventRepository,
)
from domain.value_objects.activity_log_entry import ActivityLogEntry
from domain.value_objects.biometry_log_entry import BiometryLogEntry
from domain.value_objects.identifiers import CageId
from domain.value_objects.mortality_log_entry import MortalityLogEntry


class SetPopulationUseCase:
    """Caso de uso para establecer la población inicial de una jaula."""

    def __init__(
        self,
        cage_repository: ICageRepository,
        event_repository: IPopulationEventRepository,
        activity_log_repository: ICageActivityLogRepository,
    ):
        self.cage_repository = cage_repository
        self.event_repository = event_repository
        self.activity_log_repository = activity_log_repository

    async def execute(self, cage_id: str, request: SetPopulationRequest, actor: str) -> CageResponse:
        """
        Establece la población inicial de una jaula.

        Args:
            cage_id: ID de la jaula
            request: Datos de población
            actor: Usuario que realiza la acción

        Returns:
            CageResponse con los datos actualizados

        Raises:
            ValueError: Si la jaula no existe o ya tiene población
        """
        cage = await self.cage_repository.find_by_id(CageId.from_string(cage_id))
        if not cage:
            raise ValueError(f"No existe una jaula con ID '{cage_id}'")

        # Crear evento y actualizar población
        event = cage.set_initial_population(
            fish_count=request.fish_count,
            avg_weight_grams=request.avg_weight_grams,
            event_date=request.event_date,
            note=request.note,
        )

        # Persistir cambios
        await self.cage_repository.save(cage)
        await self.event_repository.save(event)

        await self.activity_log_repository.save(
            ActivityLogEntry.create(
                cage_id=cage.id,
                event_type=ActivityLogEventType.INFO,
                category=ActivityLogCategory.POPULATION,
                message="Siembra inicial registrada",
                details=f"{request.fish_count} peces, {request.avg_weight_grams}g promedio",
                actor=actor,
            )
        )

        return _to_response(cage)


class RegisterMortalityUseCase:
    """Caso de uso para registrar mortalidad."""

    def __init__(
        self,
        cage_repository: ICageRepository,
        event_repository: IPopulationEventRepository,
        mortality_log_repository: IMortalityLogRepository,
        activity_log_repository: ICageActivityLogRepository,
    ):
        self.cage_repository = cage_repository
        self.event_repository = event_repository
        self.mortality_log_repository = mortality_log_repository
        self.activity_log_repository = activity_log_repository

    async def execute(self, cage_id: str, request: RegisterMortalityRequest, actor: str) -> CageResponse:
        """
        Registra mortalidad y resta los peces del total.

        Args:
            cage_id: ID de la jaula
            request: Datos de mortalidad
            actor: Usuario que realiza la acción

        Returns:
            CageResponse con los datos actualizados

        Raises:
            ValueError: Si la jaula no existe o no hay suficientes peces
        """
        cage = await self.cage_repository.find_by_id(CageId.from_string(cage_id))
        if not cage:
            raise ValueError(f"No existe una jaula con ID '{cage_id}'")

        # Crear evento y actualizar población
        event = cage.register_mortality(
            dead_count=request.dead_count,
            event_date=request.event_date,
            note=request.note,
        )

        # Persistir cambios
        await self.cage_repository.save(cage)
        await self.event_repository.save(event)

        # Persistir en tabla de log dedicada
        log_entry = MortalityLogEntry.create(
            cage_id=cage.id,
            dead_fish_count=request.dead_count,
            mortality_date=request.event_date,
            note=request.note,
        )
        await self.mortality_log_repository.save(log_entry)

        await self.activity_log_repository.save(
            ActivityLogEntry.create(
                cage_id=cage.id,
                event_type=ActivityLogEventType.INFO,
                category=ActivityLogCategory.MORTALITY,
                message="Registro de mortalidad",
                details=f"{request.dead_count} peces muertos",
                actor=actor,
            )
        )

        return _to_response(cage)


class UpdateBiometryUseCase:
    """Caso de uso para actualizar biometría (peso promedio)."""

    def __init__(
        self,
        cage_repository: ICageRepository,
        event_repository: IPopulationEventRepository,
        biometry_log_repository: IBiometryLogRepository,
        activity_log_repository: ICageActivityLogRepository,
    ):
        self.cage_repository = cage_repository
        self.event_repository = event_repository
        self.biometry_log_repository = biometry_log_repository
        self.activity_log_repository = activity_log_repository

    async def execute(self, cage_id: str, request: UpdateBiometryRequest, actor: str) -> CageResponse:
        """
        Actualiza el peso promedio de los peces.

        Args:
            cage_id: ID de la jaula
            request: Datos de biometría
            actor: Usuario que realiza la acción

        Returns:
            CageResponse con los datos actualizados

        Raises:
            ValueError: Si la jaula no existe
        """
        cage = await self.cage_repository.find_by_id(CageId.from_string(cage_id))
        if not cage:
            raise ValueError(f"No existe una jaula con ID '{cage_id}'")

        # Capturar valores previos antes de actualizar
        old_avg_weight = cage.avg_weight_grams
        old_fish_count = cage.fish_count

        # Crear evento y actualizar biometría
        event = cage.update_biometry(
            avg_weight_grams=request.avg_weight_grams,
            event_date=request.event_date,
            note=request.note,
        )

        # Persistir cambios
        await self.cage_repository.save(cage)
        await self.event_repository.save(event)

        # Persistir en tabla de log dedicada
        log_entry = BiometryLogEntry.create(
            cage_id=cage.id,
            old_fish_count=old_fish_count,
            new_fish_count=cage.fish_count,
            old_average_weight_g=old_avg_weight,
            new_average_weight_g=request.avg_weight_grams,
            sampling_date=request.event_date,
            note=request.note,
        )
        await self.biometry_log_repository.save(log_entry)

        await self.activity_log_repository.save(
            ActivityLogEntry.create(
                cage_id=cage.id,
                event_type=ActivityLogEventType.INFO,
                category=ActivityLogCategory.BIOMETRY,
                message="Registro de biometría completado",
                details=f"Peso promedio: {old_avg_weight}g → {request.avg_weight_grams}g",
                actor=actor,
            )
        )

        return _to_response(cage)


class HarvestUseCase:
    """Caso de uso para registrar cosecha."""

    def __init__(
        self,
        cage_repository: ICageRepository,
        event_repository: IPopulationEventRepository,
        activity_log_repository: ICageActivityLogRepository,
    ):
        self.cage_repository = cage_repository
        self.event_repository = event_repository
        self.activity_log_repository = activity_log_repository

    async def execute(self, cage_id: str, request: HarvestRequest, actor: str) -> CageResponse:
        """
        Registra una cosecha (extracción de peces).

        Args:
            cage_id: ID de la jaula
            request: Datos de cosecha
            actor: Usuario que realiza la acción

        Returns:
            CageResponse con los datos actualizados

        Raises:
            ValueError: Si la jaula no existe o no hay suficientes peces
        """
        cage = await self.cage_repository.find_by_id(CageId.from_string(cage_id))
        if not cage:
            raise ValueError(f"No existe una jaula con ID '{cage_id}'")

        # Crear evento y actualizar población
        event = cage.harvest(
            count=request.count,
            event_date=request.event_date,
            note=request.note,
        )

        # Persistir cambios
        await self.cage_repository.save(cage)
        await self.event_repository.save(event)

        await self.activity_log_repository.save(
            ActivityLogEntry.create(
                cage_id=cage.id,
                event_type=ActivityLogEventType.INFO,
                category=ActivityLogCategory.POPULATION,
                message="Cosecha registrada",
                details=f"{request.count} peces cosechados",
                actor=actor,
            )
        )

        return _to_response(cage)


class AdjustPopulationUseCase:
    """Caso de uso para ajustar manualmente la población."""

    def __init__(
        self,
        cage_repository: ICageRepository,
        event_repository: IPopulationEventRepository,
        activity_log_repository: ICageActivityLogRepository,
    ):
        self.cage_repository = cage_repository
        self.event_repository = event_repository
        self.activity_log_repository = activity_log_repository

    async def execute(self, cage_id: str, request: AdjustPopulationRequest, actor: str) -> CageResponse:
        """
        Ajusta manualmente la población (corrección de inventario).

        Args:
            cage_id: ID de la jaula
            request: Datos del ajuste
            actor: Usuario que realiza la acción

        Returns:
            CageResponse con los datos actualizados

        Raises:
            ValueError: Si la jaula no existe
        """
        cage = await self.cage_repository.find_by_id(CageId.from_string(cage_id))
        if not cage:
            raise ValueError(f"No existe una jaula con ID '{cage_id}'")

        old_fish_count = cage.fish_count

        # Crear evento y ajustar población
        event = cage.adjust_population(
            new_fish_count=request.new_fish_count,
            event_date=request.event_date,
            note=request.note,
        )

        # Persistir cambios
        await self.cage_repository.save(cage)
        await self.event_repository.save(event)

        await self.activity_log_repository.save(
            ActivityLogEntry.create(
                cage_id=cage.id,
                event_type=ActivityLogEventType.CONFIG,
                category=ActivityLogCategory.POPULATION,
                message="Ajuste de inventario registrado",
                details=f"{old_fish_count} → {request.new_fish_count} peces",
                actor=actor,
            )
        )

        return _to_response(cage)


# =============================================================================
# HELPER
# =============================================================================


def _to_response(cage: Cage) -> CageResponse:
    """Convierte la entidad a response DTO.

    Note: today_feeding_kg is set to 0.0 for population operations since
    these operations don't need real-time feeding data. The actual value
    is calculated in GetCageUseCase and ListCagesUseCase.
    """
    return CageResponse(
        id=str(cage.id.value),
        name=str(cage.name),
        status=cage.status.value,
        created_at=cage.created_at,
        fish_count=cage.fish_count,
        avg_weight_grams=cage.avg_weight_grams,
        biomass_kg=cage.biomass_kg,
        config=CageConfigResponse(
            fcr=cage.config.fcr,
            volume_m3=cage.config.volume_m3,
            max_density_kg_m3=cage.config.max_density_kg_m3,
            transport_time_seconds=cage.config.transport_time_seconds,
            blower_power=cage.config.blower_power,
            daily_feeding_target_kg=cage.config.daily_feeding_target_kg,
        ),
        current_density_kg_m3=cage.current_density_kg_m3,
        today_feeding_kg=0.0,
    )
