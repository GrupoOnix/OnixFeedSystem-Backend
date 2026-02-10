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
from domain.repositories import ICageRepository, IPopulationEventRepository
from domain.value_objects.identifiers import CageId


class SetPopulationUseCase:
    """Caso de uso para establecer la población inicial de una jaula."""

    def __init__(
        self,
        cage_repository: ICageRepository,
        event_repository: IPopulationEventRepository,
    ):
        self.cage_repository = cage_repository
        self.event_repository = event_repository

    async def execute(self, cage_id: str, request: SetPopulationRequest) -> CageResponse:
        """
        Establece la población inicial de una jaula.

        Args:
            cage_id: ID de la jaula
            request: Datos de población

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

        return _to_response(cage)


class RegisterMortalityUseCase:
    """Caso de uso para registrar mortalidad."""

    def __init__(
        self,
        cage_repository: ICageRepository,
        event_repository: IPopulationEventRepository,
    ):
        self.cage_repository = cage_repository
        self.event_repository = event_repository

    async def execute(self, cage_id: str, request: RegisterMortalityRequest) -> CageResponse:
        """
        Registra mortalidad y resta los peces del total.

        Args:
            cage_id: ID de la jaula
            request: Datos de mortalidad

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

        return _to_response(cage)


class UpdateBiometryUseCase:
    """Caso de uso para actualizar biometría (peso promedio)."""

    def __init__(
        self,
        cage_repository: ICageRepository,
        event_repository: IPopulationEventRepository,
    ):
        self.cage_repository = cage_repository
        self.event_repository = event_repository

    async def execute(self, cage_id: str, request: UpdateBiometryRequest) -> CageResponse:
        """
        Actualiza el peso promedio de los peces.

        Args:
            cage_id: ID de la jaula
            request: Datos de biometría

        Returns:
            CageResponse con los datos actualizados

        Raises:
            ValueError: Si la jaula no existe
        """
        cage = await self.cage_repository.find_by_id(CageId.from_string(cage_id))
        if not cage:
            raise ValueError(f"No existe una jaula con ID '{cage_id}'")

        # Crear evento y actualizar biometría
        event = cage.update_biometry(
            avg_weight_grams=request.avg_weight_grams,
            event_date=request.event_date,
            note=request.note,
        )

        # Persistir cambios
        await self.cage_repository.save(cage)
        await self.event_repository.save(event)

        return _to_response(cage)


class HarvestUseCase:
    """Caso de uso para registrar cosecha."""

    def __init__(
        self,
        cage_repository: ICageRepository,
        event_repository: IPopulationEventRepository,
    ):
        self.cage_repository = cage_repository
        self.event_repository = event_repository

    async def execute(self, cage_id: str, request: HarvestRequest) -> CageResponse:
        """
        Registra una cosecha (extracción de peces).

        Args:
            cage_id: ID de la jaula
            request: Datos de cosecha

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

        return _to_response(cage)


class AdjustPopulationUseCase:
    """Caso de uso para ajustar manualmente la población."""

    def __init__(
        self,
        cage_repository: ICageRepository,
        event_repository: IPopulationEventRepository,
    ):
        self.cage_repository = cage_repository
        self.event_repository = event_repository

    async def execute(self, cage_id: str, request: AdjustPopulationRequest) -> CageResponse:
        """
        Ajusta manualmente la población (corrección de inventario).

        Args:
            cage_id: ID de la jaula
            request: Datos del ajuste

        Returns:
            CageResponse con los datos actualizados

        Raises:
            ValueError: Si la jaula no existe
        """
        cage = await self.cage_repository.find_by_id(CageId.from_string(cage_id))
        if not cage:
            raise ValueError(f"No existe una jaula con ID '{cage_id}'")

        # Crear evento y ajustar población
        event = cage.adjust_population(
            new_fish_count=request.new_fish_count,
            event_date=request.event_date,
            note=request.note,
        )

        # Persistir cambios
        await self.cage_repository.save(cage)
        await self.event_repository.save(event)

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
