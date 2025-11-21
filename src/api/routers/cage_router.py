"""Router para endpoints de gestión de jaulas."""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.dependencies import get_list_cages_use_case
from application.use_cases.cage import ListCagesUseCase
from application.dtos.cage_dtos import ListCagesRequest, ListCagesResponse
from domain.exceptions import DomainException


router = APIRouter(prefix="/cages", tags=["Cages"])


@router.get("", response_model=ListCagesResponse)
async def list_cages(
    line_id: Optional[str] = Query(None, description="Filtrar por ID de línea de alimentación"),
    use_case: Annotated[ListCagesUseCase, Depends(get_list_cages_use_case)] = None
) -> ListCagesResponse:
    """
    Lista todas las jaulas del sistema con filtros opcionales.
    
    - **line_id**: (Opcional) Filtrar jaulas por línea de alimentación
    """
    try:
        request = ListCagesRequest(line_id=line_id)
        return await use_case.execute(request)
        
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )
