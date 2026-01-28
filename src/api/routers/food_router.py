"""Router para endpoints de gestión de alimentos."""

from fastapi import APIRouter, HTTPException, Query, status

from api.dependencies import (
    CreateFoodUseCaseDep,
    DeleteFoodUseCaseDep,
    GetFoodUseCaseDep,
    ListFoodsUseCaseDep,
    ToggleFoodActiveUseCaseDep,
    UpdateFoodUseCaseDep,
)
from application.dtos.food_dtos import (
    CreateFoodRequest,
    FoodDetailResponse,
    FoodDTO,
    ListFoodsResponse,
    ToggleFoodActiveRequest,
    UpdateFoodRequest,
)
from domain.exceptions import (
    DomainException,
    DuplicateFoodCodeError,
    DuplicateFoodNameError,
    FoodInUseError,
    FoodNotFoundError,
)

router = APIRouter(prefix="/foods", tags=["Foods"])


@router.get("", response_model=ListFoodsResponse)
async def list_foods(
    use_case: ListFoodsUseCaseDep,
    active_only: bool = Query(False, description="Filtrar solo alimentos activos"),
) -> ListFoodsResponse:
    """
    Lista todos los alimentos del sistema.

    - **active_only**: (Opcional) Si es true, solo retorna alimentos activos
    """
    try:
        return await use_case.execute(active_only=active_only)

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get("/{food_id}", response_model=FoodDetailResponse)
async def get_food(food_id: str, use_case: GetFoodUseCaseDep) -> FoodDetailResponse:
    """
    Obtiene los detalles de un alimento específico.

    - **food_id**: ID del alimento
    """
    try:
        return await use_case.execute(food_id)

    except FoodNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ID de alimento inválido: {str(e)}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post("", response_model=FoodDTO, status_code=status.HTTP_201_CREATED)
async def create_food(
    request: CreateFoodRequest, use_case: CreateFoodUseCaseDep
) -> FoodDTO:
    """
    Crea un nuevo alimento.

    - **name**: Nombre del alimento (único)
    - **provider**: Proveedor/fabricante
    - **code**: Código del producto (único)
    - **ppk**: Pellets por kilo (debe ser > 0)
    - **size_mm**: Tamaño del pellet en milímetros (debe ser > 0)
    - **energy**: Energía en kcal/kg (debe ser > 0)
    - **kg_per_liter**: Densidad en kg/L (debe ser > 0)
    - **active**: Si está activo (por defecto true)

    Validaciones:
    - El nombre debe ser único
    - El código debe ser único
    - Todos los valores numéricos deben ser positivos
    """
    try:
        return await use_case.execute(request)

    except DuplicateFoodNameError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    except DuplicateFoodCodeError as e:
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


@router.patch("/{food_id}", response_model=FoodDTO)
async def update_food(
    food_id: str, request: UpdateFoodRequest, use_case: UpdateFoodUseCaseDep
) -> FoodDTO:
    """
    Actualiza un alimento existente.

    - **food_id**: ID del alimento a actualizar
    - **name**: (Opcional) Nuevo nombre del alimento
    - **provider**: (Opcional) Nuevo proveedor
    - **code**: (Opcional) Nuevo código
    - **ppk**: (Opcional) Nuevos pellets por kilo
    - **size_mm**: (Opcional) Nuevo tamaño del pellet
    - **energy**: (Opcional) Nueva energía
    - **kg_per_liter**: (Opcional) Nueva densidad
    - **active**: (Opcional) Nuevo estado activo/inactivo

    Validaciones:
    - Si se cambia el nombre, debe ser único
    - Si se cambia el código, debe ser único
    - Todos los valores numéricos deben ser positivos
    """
    try:
        return await use_case.execute(food_id, request)

    except FoodNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except DuplicateFoodNameError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    except DuplicateFoodCodeError as e:
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


@router.patch("/{food_id}/toggle-active", response_model=FoodDTO)
async def toggle_food_active(
    food_id: str,
    request: ToggleFoodActiveRequest,
    use_case: ToggleFoodActiveUseCaseDep,
) -> FoodDTO:
    """
    Activa o desactiva un alimento.

    - **food_id**: ID del alimento
    - **active**: Nuevo estado (true para activar, false para desactivar)

    Los alimentos inactivos no se muestran en dropdowns de selección.
    """
    try:
        return await use_case.execute(food_id, request)

    except FoodNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error: {str(e)}"
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.delete("/{food_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_food(food_id: str, use_case: DeleteFoodUseCaseDep) -> None:
    """
    Elimina un alimento.

    - **food_id**: ID del alimento a eliminar

    Restricciones:
    - No se puede eliminar un alimento que esté asignado a algún silo
    """
    try:
        await use_case.execute(food_id)

    except FoodNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except FoodInUseError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ID de alimento inválido: {str(e)}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )
