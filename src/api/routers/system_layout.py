from fastapi import APIRouter, HTTPException, status

from api.models.system_layout import SystemLayoutModel
from api.mappers import ResponseMapper
from api.dependencies import SyncUseCaseDep, GetUseCaseDep
from domain.exceptions import (
    DuplicateLineNameException,
    DomainException
)

router = APIRouter(prefix="/system-layout")


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post(
    "",
    response_model=SystemLayoutModel,
    status_code=status.HTTP_200_OK,
    summary="Sincronizar layout del sistema",
    description="""
    Sincroniza la configuración completa del sistema de alimentación.
    
    Este endpoint implementa el algoritmo de sincronización UC-01 que:
    1. Calcula el delta entre el estado actual y el deseado
    2. Elimina agregados que no están en el request
    3. Crea nuevos agregados (mapea IDs temporales a reales)
    4. Actualiza agregados existentes
    
    **IDs Temporales vs Reales:**
    - IDs temporales (ej: "temp_silo_1") → Se crean nuevos agregados
    - IDs UUID reales → Se actualizan agregados existentes
    
    **Validaciones aplicadas:**
    - FA1: Composición mínima de líneas (blower + dosers + selector)
    - FA2: Nombres únicos por tipo de agregado
    - FA3: Jaulas disponibles para asignación
    - FA4: Slots y jaulas sin duplicados en una línea
    - FA5: Referencias a silos válidos
    - FA6: Referencias a jaulas válidas
    """,
    responses={
        200: {
            "description": "Sincronización completada exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "status": "Sincronización completada",
                        "lines_processed": 2,
                        "silos_processed": 3,
                        "cages_processed": 5
                    }
                }
            }
        },
        400: {
            "description": "Error de validación de negocio",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Ya existe una línea con el nombre 'Linea Principal'"
                    }
                }
            }
        },
        422: {
            "description": "Error de validación de datos (Pydantic)",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "silos", 0, "capacity"],
                                "msg": "Input should be greater than 0",
                                "type": "greater_than"
                            }
                        ]
                    }
                }
            }
        },
        500: {
            "description": "Error interno del servidor"
        }
    },
    tags=["System Layout"]
)
async def save_system_layout(
    request: SystemLayoutModel,
    use_case: SyncUseCaseDep
) -> SystemLayoutModel:
    """
    Endpoint principal para sincronizar el layout del sistema.
    
    Args:
        request: Configuración completa del sistema (validada por Pydantic)
        use_case: Caso de uso inyectado por FastAPI DI
        
    Returns:
        Respuesta con el resultado de la sincronización
        
    Raises:
        HTTPException 400: Si hay errores de validación de negocio
        HTTPException 500: Si hay errores internos
    """
    try:
        silos, cages, lines = await use_case.execute(request)
        return ResponseMapper.to_system_layout_model(silos, cages, lines)
        
    except DuplicateLineNameException as e:
        # Error de negocio: Nombre duplicado
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except ValueError as e:
        # Error de validación: Referencias inválidas, etc.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
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


@router.get(
    "/export",
    response_model=SystemLayoutModel,
    summary="Obtener layout del sistema",
    description="Obtiene el layout completo del sistema desde la base de datos",
    tags=["System Layout"]
)
async def export_system(use_case: GetUseCaseDep) -> SystemLayoutModel:
    """
    Endpoint para obtener el layout completo del sistema.
    
    Retorna todos los agregados (silos, jaulas, líneas) con sus IDs reales.
    """
    silos, cages, lines = await use_case.execute()
    return ResponseMapper.to_system_layout_model(silos, cages, lines)
