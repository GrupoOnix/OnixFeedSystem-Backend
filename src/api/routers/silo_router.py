"""Router para endpoints de gestión de silos."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from api.dependencies import (
    CreateSiloUseCaseDep,
    DeleteSiloUseCaseDep,
    GetSiloUseCaseDep,
    ListSilosUseCaseDep,
    UpdateSiloUseCaseDep,
)
from application.dtos.silo_dtos import (
    CreateSiloRequest,
    ListSilosRequest,
    ListSilosResponse,
    SiloDTO,
    UpdateSiloRequest,
)
from domain.exceptions import (
    DomainException,
    DuplicateSiloNameError,
    SiloInUseError,
    SiloNotFoundError,
)

router = APIRouter(prefix="/silos", tags=["Silos"])


@router.get("", response_model=ListSilosResponse)
async def list_silos(
    use_case: ListSilosUseCaseDep,
    is_assigned: Optional[bool] = Query(
        None, description="Filtrar por estado de asignación"
    ),
) -> ListSilosResponse:
    """
    Lista todos los silos del sistema con filtros opcionales.

    - **is_assigned**: (Opcional) Filtrar silos por estado de asignación
      - true: Solo silos asignados a dosificadores
      - false: Solo silos disponibles
      - null: Todos los silos
    """
    try:
        request = ListSilosRequest(is_assigned=is_assigned)
        return await use_case.execute(request)

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get("/{silo_id}", response_model=SiloDTO)
async def get_silo(silo_id: str, use_case: GetSiloUseCaseDep) -> SiloDTO:
    """
    Obtiene los detalles de un silo específico.

    - **silo_id**: ID del silo
    """
    try:
        return await use_case.execute(silo_id)

    except SiloNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ID de silo inválido: {str(e)}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post("", response_model=SiloDTO, status_code=status.HTTP_201_CREATED)
async def create_silo(
    request: CreateSiloRequest, use_case: CreateSiloUseCaseDep
) -> SiloDTO:
    """
    Crea un nuevo silo.

    - **name**: Nombre del silo (único)
    - **capacity_kg**: Capacidad en kilogramos
    - **stock_level_kg**: Nivel de stock inicial en kilogramos (por defecto 0)

    Validaciones:
    - El nombre debe ser único
    - El stock inicial no puede ser mayor que la capacidad
    """
    try:
        return await use_case.execute(request)

    except DuplicateSiloNameError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Datos inválidos: {str(e)}"
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.patch("/{silo_id}", response_model=SiloDTO)
async def update_silo(
    silo_id: str, request: UpdateSiloRequest, use_case: UpdateSiloUseCaseDep
) -> SiloDTO:
    """
    Actualiza un silo existente.

    - **silo_id**: ID del silo a actualizar
    - **name**: (Opcional) Nuevo nombre del silo
    - **capacity_kg**: (Opcional) Nueva capacidad en kilogramos

    Validaciones:
    - Si se cambia el nombre, debe ser único
    - Si se cambia la capacidad, no puede ser menor al stock actual
    """
    try:
        return await use_case.execute(silo_id, request)

    except SiloNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except DuplicateSiloNameError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Datos inválidos: {str(e)}"
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.delete("/{silo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_silo(silo_id: str, use_case: DeleteSiloUseCaseDep) -> None:
    """
    Elimina un silo.

    - **silo_id**: ID del silo a eliminar

    Restricciones:
    - No se puede eliminar un silo que esté asignado a un dosificador
    """
    try:
        await use_case.execute(silo_id)

    except SiloNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except SiloInUseError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ID de silo inválido: {str(e)}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )
