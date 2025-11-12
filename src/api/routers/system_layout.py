from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from api.models.system_layout import SystemLayoutModel
from api.mappers import SystemLayoutMapper
from application.use_cases import SyncSystemLayoutUseCase, GetSystemLayoutUseCase
from infrastructure.persistence.mock_repositories import (
    MockFeedingLineRepository,
    MockSiloRepository,
    MockCageRepository
)
from domain.exceptions import (
    DuplicateLineNameException,
    DomainException
)


# Crear router con prefijo
router = APIRouter(prefix="/system-layout")


# ============================================================================
# DEPENDENCY INJECTION (Temporal - Mock Repositories)
# ============================================================================
# TODO: Reemplazar con repositorios reales cuando se implemente la BD

# Repositorios singleton para mantener estado en memoria durante la sesión
_line_repo = MockFeedingLineRepository()
_silo_repo = MockSiloRepository()
_cage_repo = MockCageRepository()


def get_sync_system_layout_use_case() -> SyncSystemLayoutUseCase:
    """
    Factory que crea una instancia del caso de uso con dependencias inyectadas.
    
    Returns:
        Instancia configurada de SyncSystemLayoutUseCase
    """
    return SyncSystemLayoutUseCase(
        line_repo=_line_repo,
        silo_repo=_silo_repo,
        cage_repo=_cage_repo
    )


def get_get_system_layout_use_case() -> GetSystemLayoutUseCase:
    """
    Factory que crea una instancia del caso de uso con dependencias inyectadas.
    
    Returns:
        Instancia configurada de GetSystemLayoutUseCase
    """
    return GetSystemLayoutUseCase(
        line_repo=_line_repo,
        silo_repo=_silo_repo,
        cage_repo=_cage_repo
    )


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
    request: SystemLayoutModel
) -> SystemLayoutModel:
    """
    Endpoint principal para sincronizar el layout del sistema.
    
    Args:
        request: Configuración completa del sistema (validada por Pydantic)
        
    Returns:
        Respuesta con el resultado de la sincronización
        
    Raises:
        HTTPException 400: Si hay errores de validación de negocio
        HTTPException 500: Si hay errores internos
    """
    try:
        # 1. Convertir modelo Pydantic a DTO de aplicación
        app_dto = SystemLayoutMapper.to_app_dto(request)
        
        # 2. Obtener instancia del caso de uso
        use_case = get_sync_system_layout_use_case()
        
        # 3. Ejecutar el caso de uso (retorna layout con IDs reales)
        result_dto = await use_case.execute(app_dto)
        
        # 4. Convertir DTO de aplicación a modelo Pydantic
        api_response = SystemLayoutMapper.to_api_model(result_dto)
        
        return api_response
        
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


# ============================================================================
# ENDPOINTS AUXILIARES (Opcional - Para debugging/testing)
# ============================================================================

@router.get(
    "/status",
    summary="Estado del sistema",
    description="Obtiene el estado actual del sistema (número de agregados en memoria)",
    tags=["System Layout"]
)
async def get_system_status():
    """
    Endpoint auxiliar para verificar el estado del sistema.
    
    Útil para debugging y testing.
    """
    lines = await _line_repo.get_all()
    silos = await _silo_repo.get_all()
    cages = await _cage_repo.get_all()
    
    return {
        "status": "ok",
        "aggregates": {
            "feeding_lines": len(lines),
            "silos": len(silos),
            "cages": len(cages)
        },
        "details": {
            "lines": [{"id": str(line.id), "name": str(line.name)} for line in lines],
            "silos": [{"id": str(silo.id), "name": str(silo.name)} for silo in silos],
            "cages": [{"id": str(cage.id), "name": str(cage.name)} for cage in cages]
        }
    }


@router.delete(
    "/reset",
    summary="Resetear sistema",
    description="Elimina todos los agregados del sistema (solo para testing)",
    tags=["System Layout"]
)
async def reset_system():
    """
    Endpoint auxiliar para limpiar el sistema.
    
    ⚠️ SOLO PARA DESARROLLO/TESTING - Eliminar en producción.
    """
    global _line_repo, _silo_repo, _cage_repo
    
    # Recrear repositorios vacíos
    _line_repo = MockFeedingLineRepository()
    _silo_repo = MockSiloRepository()
    _cage_repo = MockCageRepository()
    
    return {
        "status": "Sistema reseteado",
        "message": "Todos los agregados han sido eliminados"
    }


@router.get(
    "/export",
    response_model=SystemLayoutModel,
    summary="Obtener layout del sistema",
    description="Obtiene el layout completo del sistema desde la base de datos",
    tags=["System Layout"]
)
async def export_system() -> SystemLayoutModel:
    """
    Endpoint para obtener el layout completo del sistema.
    
    Retorna todos los agregados (silos, jaulas, líneas) con sus IDs reales.
    """
    use_case = get_get_system_layout_use_case()
    result_dto = await use_case.execute()
    api_response = SystemLayoutMapper.to_api_model(result_dto)
    return api_response
