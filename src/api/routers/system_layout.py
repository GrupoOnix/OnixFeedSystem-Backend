from fastapi import APIRouter, HTTPException, status

from api.dependencies import GetUseCaseDep, SyncUseCaseDep, CurrentUserDep
from api.mappers import ResponseMapper
from api.models.system_layout import FeedingLineConfigModel, SystemLayoutModel
from domain.exceptions import DomainException, DuplicateLineNameException

router = APIRouter(prefix="/system-layout", tags=["System Layout"])


@router.post("", response_model=SystemLayoutModel)
async def save_system_layout(
    current_user: CurrentUserDep, request: SystemLayoutModel, use_case: SyncUseCaseDep
) -> SystemLayoutModel:
    try:
        silos, cages, lines, slot_assignments_by_line = await use_case.execute(request)
        return ResponseMapper.to_system_layout_model(silos, cages, lines, slot_assignments_by_line)

    except (DuplicateLineNameException, ValueError, DomainException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.patch("/lines/{line_id}", response_model=SystemLayoutModel)
async def update_feeding_line(
    line_id: str,
    request: FeedingLineConfigModel,
    current_user: CurrentUserDep,
    get_use_case: GetUseCaseDep,
    sync_use_case: SyncUseCaseDep,
) -> SystemLayoutModel:
    """Actualiza una sola línea sin que el cliente deba reenviar el layout completo."""
    if request.id != line_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El ID de la línea no coincide con la URL")

    try:
        current_layout = await _export_system_layout(get_use_case)
        replacement_index = next(
            (index for index, line in enumerate(current_layout.feeding_lines) if line.id == line_id),
            None,
        )
        if replacement_index is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Línea no encontrada")

        feeding_lines = list(current_layout.feeding_lines)
        feeding_lines[replacement_index] = request
        merged_layout = current_layout.model_copy(update={"feeding_lines": feeding_lines})
        silos, cages, lines, assignments = await sync_use_case.execute(merged_layout)
        return ResponseMapper.to_system_layout_model(silos, cages, lines, assignments)
    except HTTPException:
        raise
    except (DuplicateLineNameException, ValueError, DomainException) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


async def _export_system_layout(use_case: GetUseCaseDep) -> SystemLayoutModel:
    silos, cages, lines, slot_assignments_by_line = await use_case.execute()
    return ResponseMapper.to_system_layout_model(silos, cages, lines, slot_assignments_by_line)


@router.get("", response_model=SystemLayoutModel)
async def get_system_layout(current_user: CurrentUserDep, use_case: GetUseCaseDep) -> SystemLayoutModel:
    return await _export_system_layout(use_case)


@router.get("/export", response_model=SystemLayoutModel)
async def export_system(current_user: CurrentUserDep, use_case: GetUseCaseDep) -> SystemLayoutModel:
    return await _export_system_layout(use_case)
