"""Router para el módulo de jaulas."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from api.models.cage_models import (
    AdjustPopulationRequestModel,
    CageResponseModel,
    CreateCageRequestModel,
    HarvestRequestModel,
    ListCagesResponseModel,
    PopulationHistoryResponseModel,
    RegisterMortalityRequestModel,
    SetPopulationRequestModel,
    UpdateBiometryRequestModel,
    UpdateCageConfigRequestModel,
    UpdateCageRequestModel,
)

from api.dependencies import (
    AdjustPopulationUseCaseDep,
    CreateCageUseCaseDep,
    DeleteCageUseCaseDep,
    GetCageUseCaseDep,
    GetPopulationHistoryUseCaseDep,
    HarvestUseCaseDep,
    ListCagesUseCaseDep,
    RegisterMortalityUseCaseDep,
    SetPopulationUseCaseDep,
    UpdateBiometryUseCaseDep,
    UpdateCageConfigUseCaseDep,
    UpdateCageUseCaseDep,
)
from application.dtos.cage_dtos import (
    AdjustPopulationRequest,
    CreateCageRequest,
    HarvestRequest,
    RegisterMortalityRequest,
    SetPopulationRequest,
    UpdateBiometryRequest,
    UpdateCageConfigRequest,
    UpdateCageRequest,
)

router = APIRouter(prefix="/cages", tags=["Cages"])


# =============================================================================
# CRUD ENDPOINTS
# =============================================================================


@router.post("", response_model=CageResponseModel, status_code=201)
async def create_cage(
    request: CreateCageRequestModel,
    use_case: CreateCageUseCaseDep,
) -> CageResponseModel:
    """
    Crea una nueva jaula.

    - **name**: Nombre único de la jaula
    - **fcr**: Feed Conversion Ratio (opcional, 0.5-3.0)
    - **volume_m3**: Volumen en metros cúbicos (opcional)
    - **max_density_kg_m3**: Densidad máxima en kg/m³ (opcional)
    - **transport_time_seconds**: Tiempo de transporte en segundos (opcional)
    - **blower_power**: Potencia del blower para alcanzar la jaula (opcional, 30-100)
    """
    try:
        dto = CreateCageRequest(
            name=request.name,
            fcr=request.fcr,
            volume_m3=request.volume_m3,
            max_density_kg_m3=request.max_density_kg_m3,
            transport_time_seconds=request.transport_time_seconds,
            blower_power=request.blower_power,
        )
        result = await use_case.execute(dto)
        return CageResponseModel.from_dto(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=ListCagesResponseModel)
async def list_cages(
    use_case: ListCagesUseCaseDep,
) -> ListCagesResponseModel:
    """Lista todas las jaulas."""
    result = await use_case.execute()
    return ListCagesResponseModel.from_dto(result)


@router.get("/{cage_id}", response_model=CageResponseModel)
async def get_cage(
    cage_id: str,
    use_case: GetCageUseCaseDep,
) -> CageResponseModel:
    """Obtiene una jaula por su ID."""
    try:
        result = await use_case.execute(cage_id)
        return CageResponseModel.from_dto(result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{cage_id}", response_model=CageResponseModel)
async def update_cage(
    cage_id: str,
    request: UpdateCageRequestModel,
    use_case: UpdateCageUseCaseDep,
) -> CageResponseModel:
    """
    Actualiza nombre y/o estado de una jaula.

    - **name**: Nuevo nombre (opcional)
    - **status**: Nuevo estado: AVAILABLE, IN_USE, MAINTENANCE (opcional)
    """
    try:
        dto = UpdateCageRequest(
            name=request.name,
            status=request.status,
        )
        result = await use_case.execute(cage_id, dto)
        return CageResponseModel.from_dto(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{cage_id}", status_code=204)
async def delete_cage(
    cage_id: str,
    use_case: DeleteCageUseCaseDep,
) -> None:
    """Elimina una jaula."""
    try:
        await use_case.execute(cage_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# CONFIGURATION ENDPOINTS
# =============================================================================


@router.patch("/{cage_id}/config", response_model=CageResponseModel)
async def update_cage_config(
    cage_id: str,
    request: UpdateCageConfigRequestModel,
    use_case: UpdateCageConfigUseCaseDep,
) -> CageResponseModel:
    """
    Actualiza la configuración de una jaula.

    Solo actualiza los campos proporcionados, manteniendo los demás.

    - **fcr**: Feed Conversion Ratio (0.5-3.0)
    - **volume_m3**: Volumen en metros cúbicos
    - **max_density_kg_m3**: Densidad máxima en kg/m³
    - **transport_time_seconds**: Tiempo de transporte en segundos
    - **blower_power**: Potencia del blower para alcanzar la jaula (30-100)
    - **daily_feeding_target_kg**: Meta de alimentación diaria en kg
    """
    try:
        dto = UpdateCageConfigRequest(
            fcr=request.fcr,
            volume_m3=request.volume_m3,
            max_density_kg_m3=request.max_density_kg_m3,
            transport_time_seconds=request.transport_time_seconds,
            blower_power=request.blower_power,
            daily_feeding_target_kg=request.daily_feeding_target_kg,
        )
        result = await use_case.execute(cage_id, dto)
        return CageResponseModel.from_dto(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# POPULATION ENDPOINTS
# =============================================================================


@router.put("/{cage_id}/population", response_model=CageResponseModel)
async def set_population(
    cage_id: str,
    request: SetPopulationRequestModel,
    use_case: SetPopulationUseCaseDep,
) -> CageResponseModel:
    """
    Establece la población inicial de una jaula (siembra).

    - **fish_count**: Cantidad de peces
    - **avg_weight_grams**: Peso promedio en gramos
    - **event_date**: Fecha del evento
    - **note**: Nota opcional
    """
    try:
        dto = SetPopulationRequest(
            fish_count=request.fish_count,
            avg_weight_grams=request.avg_weight_grams,
            event_date=request.event_date,
            note=request.note,
        )
        result = await use_case.execute(cage_id, dto)
        return CageResponseModel.from_dto(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{cage_id}/mortality", response_model=CageResponseModel)
async def register_mortality(
    cage_id: str,
    request: RegisterMortalityRequestModel,
    use_case: RegisterMortalityUseCaseDep,
) -> CageResponseModel:
    """
    Registra mortalidad y resta los peces del total.

    - **dead_count**: Cantidad de peces muertos
    - **event_date**: Fecha del evento
    - **note**: Nota opcional
    """
    try:
        dto = RegisterMortalityRequest(
            dead_count=request.dead_count,
            event_date=request.event_date,
            note=request.note,
        )
        result = await use_case.execute(cage_id, dto)
        return CageResponseModel.from_dto(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{cage_id}/biometry", response_model=CageResponseModel)
async def update_biometry(
    cage_id: str,
    request: UpdateBiometryRequestModel,
    use_case: UpdateBiometryUseCaseDep,
) -> CageResponseModel:
    """
    Actualiza el peso promedio de los peces (biometría).

    - **avg_weight_grams**: Nuevo peso promedio en gramos
    - **event_date**: Fecha del muestreo
    - **note**: Nota opcional
    """
    try:
        dto = UpdateBiometryRequest(
            avg_weight_grams=request.avg_weight_grams,
            event_date=request.event_date,
            note=request.note,
        )
        result = await use_case.execute(cage_id, dto)
        return CageResponseModel.from_dto(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{cage_id}/harvest", response_model=CageResponseModel)
async def harvest(
    cage_id: str,
    request: HarvestRequestModel,
    use_case: HarvestUseCaseDep,
) -> CageResponseModel:
    """
    Registra una cosecha (extracción de peces).

    - **count**: Cantidad de peces cosechados
    - **event_date**: Fecha de la cosecha
    - **note**: Nota opcional
    """
    try:
        dto = HarvestRequest(
            count=request.count,
            event_date=request.event_date,
            note=request.note,
        )
        result = await use_case.execute(cage_id, dto)
        return CageResponseModel.from_dto(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{cage_id}/adjust", response_model=CageResponseModel)
async def adjust_population(
    cage_id: str,
    request: AdjustPopulationRequestModel,
    use_case: AdjustPopulationUseCaseDep,
) -> CageResponseModel:
    """
    Ajusta manualmente la población (corrección de inventario).

    Útil para reconciliar diferencias entre el sistema y conteos físicos.

    - **new_fish_count**: Nueva cantidad total de peces
    - **event_date**: Fecha del ajuste
    - **note**: Nota explicativa (recomendado)
    """
    try:
        dto = AdjustPopulationRequest(
            new_fish_count=request.new_fish_count,
            event_date=request.event_date,
            note=request.note,
        )
        result = await use_case.execute(cage_id, dto)
        return CageResponseModel.from_dto(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# HISTORY ENDPOINTS
# =============================================================================


@router.get("/{cage_id}/history", response_model=PopulationHistoryResponseModel)
async def get_population_history(
    cage_id: str,
    use_case: GetPopulationHistoryUseCaseDep,
    event_types: Optional[List[str]] = Query(None, description="Filtrar por tipos de evento"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> PopulationHistoryResponseModel:
    """
    Obtiene el historial de eventos de población.

    Tipos de evento disponibles:
    - INITIAL_STOCK: Siembra inicial
    - RESTOCK: Resiembra
    - MORTALITY: Mortalidad
    - HARVEST: Cosecha
    - TRANSFER_IN: Transferencia entrante
    - TRANSFER_OUT: Transferencia saliente
    - BIOMETRY: Actualización de peso
    - ADJUSTMENT: Ajuste de inventario
    """
    try:
        result = await use_case.execute(
            cage_id=cage_id,
            event_types=event_types,
            limit=limit,
            offset=offset,
        )
        return PopulationHistoryResponseModel.from_dto(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
