"""Router para endpoints de operaciones de alimentación."""

from typing import Dict
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from api.dependencies import (
    StartFeedingUseCaseDep,
    StopFeedingUseCaseDep,
    PauseFeedingUseCaseDep,
    ResumeFeedingUseCaseDep,
    UpdateFeedingParamsUseCaseDep
)
from application.dtos.feeding_dtos import StartFeedingRequest, UpdateParamsRequest
from domain.exceptions import DomainException


router = APIRouter(prefix="/feeding", tags=["Feeding Operations"])


@router.post("/start", status_code=status.HTTP_201_CREATED)
async def start_feeding(
    request: StartFeedingRequest,
    use_case: StartFeedingUseCaseDep
) -> Dict[str, str]:
    """
    Inicia una nueva sesión de alimentación en una línea.
    
    - **line_id**: ID de la línea de alimentación
    - **cage_id**: ID de la jaula objetivo
    - **mode**: Modo de operación (MANUAL, CYCLIC)
    - **target_amount_kg**: Meta de alimentación en kg
    - **blower_speed_percentage**: Velocidad del soplador (0-100)
    - **dosing_rate_kg_min**: Tasa de dosificación en kg/min
    """
    try:
        session_id = await use_case.execute(request)
        return {
            "session_id": str(session_id),
            "message": "Feeding session started successfully"
        }

    except ValueError as e:
        # Error de validación: línea no existe, jaula no existe, etc.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    except DomainException as e:
        # Errores de dominio: sesión ya activa, etc.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        # Error inesperado
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.post("/lines/{line_id}/stop", status_code=status.HTTP_200_OK)
async def stop_feeding(
    line_id: UUID,
    use_case: StopFeedingUseCaseDep
) -> Dict[str, str]:
    """
    Detiene la alimentación activa en una línea.
    
    - **line_id**: ID de la línea de alimentación
    """
    try:
        await use_case.execute(line_id)
        return {"message": "Feeding session stopped successfully"}

    except ValueError as e:
        # Error de validación: línea no existe, sesión no existe, etc.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    except DomainException as e:
        # Errores de dominio
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        # Error inesperado
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.post("/lines/{line_id}/pause", status_code=status.HTTP_200_OK)
async def pause_feeding(
    line_id: UUID,
    use_case: PauseFeedingUseCaseDep
) -> Dict[str, str]:
    """
    Pausa temporalmente la alimentación en una línea.
    
    - **line_id**: ID de la línea de alimentación
    """
    try:
        await use_case.execute(line_id)
        return {"message": "Feeding session paused successfully"}

    except ValueError as e:
        # Error de validación: línea no existe, sesión no existe, etc.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    except DomainException as e:
        # Errores de dominio
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        # Error inesperado
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.post("/lines/{line_id}/resume", status_code=status.HTTP_200_OK)
async def resume_feeding(
    line_id: UUID,
    use_case: ResumeFeedingUseCaseDep
) -> Dict[str, str]:
    """
    Reanuda una alimentación pausada en una línea.
    
    - **line_id**: ID de la línea de alimentación
    """
    try:
        await use_case.execute(line_id)
        return {"message": "Feeding session resumed successfully"}

    except ValueError as e:
        # Error de validación: línea no existe, sesión no existe, etc.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    except DomainException as e:
        # Errores de dominio
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        # Error inesperado
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.patch("/lines/{line_id}/parameters", status_code=status.HTTP_200_OK)
async def update_feeding_parameters(
    line_id: UUID,
    request: UpdateParamsRequest,
    use_case: UpdateFeedingParamsUseCaseDep
) -> Dict[str, str]:
    """
    Actualiza parámetros de alimentación en caliente (sin detener).
    
    - **line_id**: ID de la línea de alimentación
    - **blower_speed**: (Opcional) Nueva velocidad del soplador (0-100)
    - **dosing_rate**: (Opcional) Nueva tasa de dosificación en kg/min
    """
    try:
        # Agregar line_id al request
        request.line_id = line_id
        await use_case.execute(request)
        return {"message": "Feeding parameters updated successfully"}

    except ValueError as e:
        # Error de validación: línea no existe, sesión no existe, etc.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    except DomainException as e:
        # Errores de dominio
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        # Error inesperado
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

