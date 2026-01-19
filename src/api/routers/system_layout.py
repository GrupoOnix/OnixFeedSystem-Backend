from fastapi import APIRouter, HTTPException, status

from api.dependencies import GetUseCaseDep, SyncUseCaseDep
from api.mappers import ResponseMapper
from api.models.system_layout import SystemLayoutModel
from domain.exceptions import DomainException, DuplicateLineNameException

router = APIRouter(prefix="/system-layout", tags=["System Layout"])


@router.post("", response_model=SystemLayoutModel)
async def save_system_layout(
    request: SystemLayoutModel, use_case: SyncUseCaseDep
) -> SystemLayoutModel:
    try:
        silos, cages, lines, slot_assignments_by_line = await use_case.execute(request)
        return ResponseMapper.to_system_layout_model(
            silos, cages, lines, slot_assignments_by_line
        )

    except (DuplicateLineNameException, ValueError, DomainException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get("/export", response_model=SystemLayoutModel)
async def export_system(use_case: GetUseCaseDep) -> SystemLayoutModel:
    silos, cages, lines, slot_assignments_by_line = await use_case.execute()
    return ResponseMapper.to_system_layout_model(
        silos, cages, lines, slot_assignments_by_line
    )
