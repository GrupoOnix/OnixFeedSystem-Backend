"""Router para endpoints de gestión de jaulas."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from api.dependencies import (
    ListCagesUseCaseDep,
    RegisterBiometryUseCaseDep,
    ListBiometryUseCaseDep,
    RegisterMortalityUseCaseDep,
    ListMortalityUseCaseDep,
    UpdateCageConfigUseCaseDep,
    ListConfigChangesUseCaseDep
)
from application.dtos.cage_dtos import ListCagesRequest, ListCagesResponse
from application.dtos.biometry_dtos import RegisterBiometryRequest, PaginatedBiometryResponse
from application.dtos.mortality_dtos import RegisterMortalityRequest, PaginatedMortalityResponse
from application.dtos.config_dtos import UpdateCageConfigRequest, PaginatedConfigChangesResponse
from domain.exceptions import DomainException


router = APIRouter(prefix="/cages", tags=["Cages"])


@router.get("", response_model=ListCagesResponse)
async def list_cages(
    use_case: ListCagesUseCaseDep,
    line_id: Optional[str] = Query(None, description="Filtrar por ID de línea de alimentación")
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


@router.post("/{cage_id}/biometry", status_code=status.HTTP_200_OK)
async def register_biometry(
    cage_id: str,
    request: RegisterBiometryRequest,
    use_case: RegisterBiometryUseCaseDep
) -> dict:
    """
    Registra un muestreo de biometría y actualiza los datos de la jaula.
    
    - **cage_id**: ID de la jaula
    - **fish_count**: Cantidad actual de peces
    - **average_weight_g**: Peso promedio en gramos
    - **sampling_date**: Fecha del muestreo
    - **note**: (Opcional) Nota descriptiva
    """
    try:
        await use_case.execute(cage_id, request)
        return {"message": "Biometría registrada exitosamente"}
        
    except ValueError as e:
        # Error de validación: jaula no existe, datos inválidos, etc.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
        
    except DomainException as e:
        # Otros errores de dominio
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error de dominio: {str(e)}"
        )
        
    except Exception as e:
        # Error inesperado
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get("/{cage_id}/biometry", response_model=PaginatedBiometryResponse)
async def list_biometry(
    cage_id: str,
    use_case: ListBiometryUseCaseDep,
    limit: int = Query(50, ge=1, le=100, description="Cantidad máxima de registros"),
    offset: int = Query(0, ge=0, description="Cantidad de registros a saltar")
) -> PaginatedBiometryResponse:
    """
    Lista los registros de biometría de una jaula con paginación.
    
    - **cage_id**: ID de la jaula
    - **limit**: (Opcional) Cantidad máxima de registros (default: 50, max: 100)
    - **offset**: (Opcional) Cantidad de registros a saltar (default: 0)
    """
    try:
        return await use_case.execute(cage_id, limit, offset)
        
    except ValueError as e:
        # Error de validación: jaula no existe, etc.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
        
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


@router.post("/{cage_id}/mortality", status_code=status.HTTP_200_OK)
async def register_mortality(
    cage_id: str,
    request: RegisterMortalityRequest,
    use_case: RegisterMortalityUseCaseDep
) -> dict:
    """
    Registra un evento de mortalidad en una jaula.
    
    IMPORTANTE: Este endpoint NO modifica el current_fish_count de la jaula.
    Solo crea un registro en el log para auditoría y estadísticas.
    
    - **cage_id**: ID de la jaula
    - **dead_fish_count**: Cantidad de peces muertos
    - **mortality_date**: Fecha del evento de mortalidad
    - **note**: (Opcional) Nota descriptiva
    """
    try:
        await use_case.execute(cage_id, request)
        return {"message": "Mortalidad registrada exitosamente"}
        
    except ValueError as e:
        # Error de validación: jaula no existe, datos inválidos, etc.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
        
    except DomainException as e:
        # Otros errores de dominio
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error de dominio: {str(e)}"
        )
        
    except Exception as e:
        # Error inesperado
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get("/{cage_id}/mortality", response_model=PaginatedMortalityResponse)
async def list_mortality(
    cage_id: str,
    use_case: ListMortalityUseCaseDep,
    limit: int = Query(50, ge=1, le=100, description="Cantidad máxima de registros"),
    offset: int = Query(0, ge=0, description="Cantidad de registros a saltar")
) -> PaginatedMortalityResponse:
    """
    Lista los registros de mortalidad de una jaula con paginación.
    
    - **cage_id**: ID de la jaula
    - **limit**: (Opcional) Cantidad máxima de registros (default: 50, max: 100)
    - **offset**: (Opcional) Cantidad de registros a saltar (default: 0)
    """
    try:
        return await use_case.execute(cage_id, limit, offset)
        
    except ValueError as e:
        # Error de validación: jaula no existe, etc.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
        
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


@router.patch("/{cage_id}/config", status_code=status.HTTP_200_OK)
async def update_cage_config(
    cage_id: str,
    request: UpdateCageConfigRequest,
    use_case: UpdateCageConfigUseCaseDep
) -> dict:
    """
    Actualiza la configuración de una jaula y registra los cambios.
    
    Solo crea logs para campos que realmente cambian (OLD != NEW).
    Todos los campos son opcionales.
    
    - **cage_id**: ID de la jaula
    - **fcr**: (Opcional) Factor de conversión alimenticia
    - **volume_m3**: (Opcional) Volumen total en metros cúbicos
    - **max_density_kg_m3**: (Opcional) Densidad máxima en kg/m³
    - **feeding_table_id**: (Opcional) ID de la tabla de alimentación
    - **transport_time_seconds**: (Opcional) Tiempo de transporte en segundos
    - **change_reason**: (Opcional) Razón del cambio
    """
    try:
        await use_case.execute(cage_id, request)
        return {"message": "Configuración actualizada exitosamente"}
        
    except ValueError as e:
        # Error de validación: jaula no existe, datos inválidos, etc.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
        
    except DomainException as e:
        # Otros errores de dominio
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error de dominio: {str(e)}"
        )
        
    except Exception as e:
        # Error inesperado
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get("/{cage_id}/config-changes", response_model=PaginatedConfigChangesResponse)
async def list_config_changes(
    cage_id: str,
    use_case: ListConfigChangesUseCaseDep,
    limit: int = Query(50, ge=1, le=100, description="Cantidad máxima de registros"),
    offset: int = Query(0, ge=0, description="Cantidad de registros a saltar")
) -> PaginatedConfigChangesResponse:
    """
    Lista los cambios de configuración de una jaula con paginación.
    
    - **cage_id**: ID de la jaula
    - **limit**: (Opcional) Cantidad máxima de registros (default: 50, max: 100)
    - **offset**: (Opcional) Cantidad de registros a saltar (default: 0)
    """
    try:
        return await use_case.execute(cage_id, limit, offset)
        
    except ValueError as e:
        # Error de validación: jaula no existe, etc.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
        
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
