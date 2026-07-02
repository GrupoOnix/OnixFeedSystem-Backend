"""Router para endpoints de gestión de silos."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from api.dependencies import (
    CreateSiloBatchUseCaseDep,
    CreateSiloUseCaseDep,
    DeleteSiloUseCaseDep,
    GetSiloUseCaseDep,
    ListSiloBatchesUseCaseDep,
    ListSilosUseCaseDep,
    MoveSiloBatchUseCaseDep,
    TransferSiloStockUseCaseDep,
    UpdateSiloBatchUseCaseDep,
    UpdateSiloUseCaseDep,
    WithdrawSiloBatchUseCaseDep,
    CurrentUserDep,
)
from application.dtos.silo_dtos import (
    CreateSiloRequest,
    ListSilosRequest,
    ListSilosResponse,
    SiloDTO,
    UpdateSiloRequest,
)
from application.dtos.silo_inventory_dtos import (
    CreateSiloBatchRequest,
    ListSiloBatchesResponse,
    MoveSiloBatchRequest,
    TransferSiloStockRequest,
    TransferSiloStockResponse,
    UpdateSiloBatchRequest,
    WithdrawSiloBatchRequest,
)
from application.dtos.silo_dtos import SiloInventoryBatchDTO
from domain.exceptions import (
    DomainException,
    DuplicateSiloNameError,
    SiloInUseError,
    SiloNotFoundError,
)

router = APIRouter(prefix="/silos", tags=["Silos"])


@router.post(
    "/{silo_id}/batches",
    response_model=SiloInventoryBatchDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_silo_batch(
    current_user: CurrentUserDep,
    silo_id: str,
    request: CreateSiloBatchRequest,
    use_case: CreateSiloBatchUseCaseDep,
) -> SiloInventoryBatchDTO:
    try:
        return await use_case.execute(silo_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/{silo_id}/batches", response_model=ListSiloBatchesResponse)
async def list_silo_batches(
    current_user: CurrentUserDep,
    silo_id: str,
    use_case: ListSiloBatchesUseCaseDep,
    batch_status: Optional[str] = Query(None, alias="status"),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> ListSiloBatchesResponse:
    try:
        return await use_case.execute(silo_id, batch_status, offset, limit)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.patch("/{silo_id}/batches/{batch_id}", response_model=SiloInventoryBatchDTO)
async def update_silo_batch(
    current_user: CurrentUserDep,
    silo_id: str,
    batch_id: str,
    request: UpdateSiloBatchRequest,
    use_case: UpdateSiloBatchUseCaseDep,
) -> SiloInventoryBatchDTO:
    try:
        return await use_case.execute(silo_id, batch_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/{silo_id}/batches/{batch_id}/move", response_model=SiloInventoryBatchDTO)
async def move_silo_batch(
    current_user: CurrentUserDep,
    silo_id: str,
    batch_id: str,
    request: MoveSiloBatchRequest,
    use_case: MoveSiloBatchUseCaseDep,
) -> SiloInventoryBatchDTO:
    try:
        return await use_case.execute(silo_id, batch_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/{silo_id}/batches/{batch_id}/withdraw", response_model=SiloInventoryBatchDTO)
async def withdraw_silo_batch(
    current_user: CurrentUserDep,
    silo_id: str,
    batch_id: str,
    request: WithdrawSiloBatchRequest,
    use_case: WithdrawSiloBatchUseCaseDep,
) -> SiloInventoryBatchDTO:
    try:
        return await use_case.execute(silo_id, batch_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/{silo_id}/transfer", response_model=TransferSiloStockResponse)
async def transfer_silo_stock(
    current_user: CurrentUserDep,
    silo_id: str,
    request: TransferSiloStockRequest,
    use_case: TransferSiloStockUseCaseDep,
) -> TransferSiloStockResponse:
    """Trasvasija stock FIFO disponible desde un silo hacia otro."""
    try:
        return await use_case.execute(silo_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("", response_model=ListSilosResponse)
async def list_silos(
    current_user: CurrentUserDep,
    use_case: ListSilosUseCaseDep,
    is_assigned: Optional[bool] = Query(None, description="Filtrar por estado de asignación"),
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
async def get_silo(current_user: CurrentUserDep, silo_id: str, use_case: GetSiloUseCaseDep) -> SiloDTO:
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
    current_user: CurrentUserDep, request: CreateSiloRequest, use_case: CreateSiloUseCaseDep
) -> SiloDTO:
    """
    Crea un nuevo silo.

    - **name**: Nombre del silo (único)
    - **capacity_kg**: Capacidad en kilogramos
    El silo se crea vacío. El inventario se carga mediante partidas.
    """
    try:
        return await use_case.execute(request)

    except DuplicateSiloNameError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Datos inválidos: {str(e)}")

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.patch("/{silo_id}", response_model=SiloDTO)
async def update_silo(
    current_user: CurrentUserDep, silo_id: str, request: UpdateSiloRequest, use_case: UpdateSiloUseCaseDep
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Datos inválidos: {str(e)}")

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.delete("/{silo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_silo(current_user: CurrentUserDep, silo_id: str, use_case: DeleteSiloUseCaseDep) -> None:
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
