"""Router para el módulo de grupos de jaulas."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from api.models.cage_group_models import (
    CageGroupResponseModel,
    CreateCageGroupRequestModel,
    ListCageGroupsResponseModel,
    UpdateCageGroupRequestModel,
)
from application.dtos.cage_group_dtos import (
    CreateCageGroupRequest,
    UpdateCageGroupRequest,
)

from api.dependencies import (
    CreateCageGroupUseCaseDep,
    DeleteCageGroupUseCaseDep,
    GetCageGroupUseCaseDep,
    ListCageGroupsUseCaseDep,
    UpdateCageGroupUseCaseDep,
)

router = APIRouter(prefix="/cage-groups", tags=["Cage Groups"])


# =============================================================================
# CRUD ENDPOINTS
# =============================================================================


@router.post("", response_model=CageGroupResponseModel, status_code=201)
async def create_cage_group(
    request: CreateCageGroupRequestModel,
    use_case: CreateCageGroupUseCaseDep,
) -> CageGroupResponseModel:
    """
    Crea un nuevo grupo de jaulas.

    - **name**: Nombre único del grupo (1-255 caracteres)
    - **cage_ids**: Lista de IDs de jaulas (UUIDs), mínimo 1 jaula
    - **description**: Descripción opcional del grupo

    **Reglas de Negocio:**
    - El nombre debe ser único (case-insensitive)
    - Todas las jaulas deben existir en el sistema
    - Una jaula puede pertenecer a múltiples grupos
    """
    try:
        dto = CreateCageGroupRequest(
            name=request.name,
            cage_ids=request.cage_ids,
            description=request.description,
        )
        result = await use_case.execute(dto)
        return CageGroupResponseModel.from_dto(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=ListCageGroupsResponseModel)
async def list_cage_groups(
    use_case: ListCageGroupsUseCaseDep,
    search: Optional[str] = Query(
        None, description="Buscar en nombre, descripción o IDs de jaulas"
    ),
    limit: int = Query(50, ge=1, le=100, description="Cantidad máxima de resultados"),
    offset: int = Query(0, ge=0, description="Desplazamiento para paginación"),
) -> ListCageGroupsResponseModel:
    """
    Lista grupos de jaulas con filtros opcionales.

    **Filtros:**
    - **search**: Búsqueda parcial en nombre y descripción (case-insensitive),
      o búsqueda exacta en IDs de jaulas
    - **limit**: Cantidad máxima de resultados (default 50, max 100)
    - **offset**: Desplazamiento para paginación (default 0)

    **Respuesta:**
    - Lista de grupos con métricas calculadas en tiempo real
    - Total de grupos que coinciden con los filtros
    """
    result = await use_case.execute(search=search, limit=limit, offset=offset)
    return ListCageGroupsResponseModel.from_dto(result)


@router.get("/{group_id}", response_model=CageGroupResponseModel)
async def get_cage_group(
    group_id: str,
    use_case: GetCageGroupUseCaseDep,
) -> CageGroupResponseModel:
    """
    Obtiene un grupo de jaulas por su ID.

    **Parámetros:**
    - **group_id**: ID único del grupo (UUID)

    **Respuesta:**
    - Datos completos del grupo incluyendo métricas agregadas calculadas
    """
    try:
        result = await use_case.execute(group_id)
        return CageGroupResponseModel.from_dto(result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{group_id}", response_model=CageGroupResponseModel)
async def update_cage_group(
    group_id: str,
    request: UpdateCageGroupRequestModel,
    use_case: UpdateCageGroupUseCaseDep,
) -> CageGroupResponseModel:
    """
    Actualiza un grupo de jaulas.

    **Parámetros:**
    - **group_id**: ID del grupo a actualizar
    - **name**: Nuevo nombre (opcional)
    - **cage_ids**: Nueva lista de IDs de jaulas (opcional)
    - **description**: Nueva descripción (opcional, None para limpiar)

    **Reglas de Negocio:**
    - Solo se actualizan los campos proporcionados
    - El nombre debe ser único (excepto el actual)
    - Todas las jaulas deben existir
    - `updated_at` se actualiza automáticamente
    """
    try:
        dto = UpdateCageGroupRequest(
            name=request.name,
            cage_ids=request.cage_ids,
            description=request.description,
        )
        result = await use_case.execute(group_id, dto)
        return CageGroupResponseModel.from_dto(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{group_id}", status_code=204)
async def delete_cage_group(
    group_id: str,
    use_case: DeleteCageGroupUseCaseDep,
) -> None:
    """
    Elimina un grupo de jaulas.

    **Parámetros:**
    - **group_id**: ID del grupo a eliminar

    **Comportamiento:**
    - Eliminación física (hard delete)
    - Las jaulas NO se ven afectadas (solo se elimina la agrupación)
    - No retorna contenido (204 No Content)
    """
    try:
        await use_case.execute(group_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
