"""Router para endpoints de gestión de líneas de alimentación."""

from typing import Dict

from fastapi import APIRouter, HTTPException, status

from api.dependencies import (
    GetFeedingLineUseCaseDep,
    ListFeedingLinesUseCaseDep,
    MoveSelectorToSlotUseCaseDep,
    ResetSelectorPositionUseCaseDep,
    UpdateBlowerUseCaseDep,
    UpdateDoserUseCaseDep,
    UpdateSelectorUseCaseDep,
)
from application.dtos.feeding_line_dtos import (
    FeedingLineDTO,
    ListFeedingLinesResponse,
    UpdateBlowerRequest,
    UpdateDoserRequest,
    UpdateSelectorRequest,
)
from domain.exceptions import DomainException, FeedingLineNotFoundException

router = APIRouter(prefix="/feeding-lines", tags=["Feeding Lines"])


@router.get("", response_model=ListFeedingLinesResponse)
async def list_feeding_lines(
    use_case: ListFeedingLinesUseCaseDep,
) -> ListFeedingLinesResponse:
    """
    Lista todas las líneas de alimentación del sistema.

    Retorna información completa de cada línea incluyendo:
    - Blower (soplador)
    - Dosers (dosificadores) con sus silos asignados
    - Selector (selector de slot)
    - Sensors (sensores)
    - Conteo total de jaulas asignadas
    """
    try:
        return await use_case.execute()

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.patch("/{line_id}/selector", status_code=status.HTTP_200_OK)
async def update_selector(
    line_id: str, request: UpdateSelectorRequest, use_case: UpdateSelectorUseCaseDep
) -> Dict[str, str]:
    """
    Actualiza la configuración del selector de una línea de alimentación.

    - **line_id**: ID de la línea de alimentación
    - **name** (opcional): Nuevo nombre del selector
    - **fast_speed** (opcional): Nueva velocidad rápida (0-100%)
    - **slow_speed** (opcional): Nueva velocidad lenta (0-100%)

    Validaciones:
    - fast_speed y slow_speed deben estar entre 0 y 100
    - slow_speed no puede ser mayor que fast_speed

    Retorna un mensaje de éxito si la actualización se realizó correctamente.
    """
    try:
        await use_case.execute(line_id, request)
        return {"message": "Selector actualizado exitosamente"}

    except FeedingLineNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post(
    "/{line_id}/selector/move-to-slot/{slot_number}", status_code=status.HTTP_200_OK
)
async def move_selector_to_slot(
    line_id: str, slot_number: int, use_case: MoveSelectorToSlotUseCaseDep
) -> Dict[str, str]:
    """
    Mueve el selector de una línea a un slot específico.

    - **line_id**: ID de la línea de alimentación
    - **slot_number**: Número de slot destino (1 a capacity del selector)

    Esta operación:
    - Valida que el slot esté dentro del rango válido
    - Actualiza la posición del selector en la base de datos
    - Típicamente se usa antes o durante operaciones de alimentación

    Retorna un mensaje de éxito si el movimiento se realizó correctamente.
    """
    try:
        await use_case.execute(line_id, slot_number)
        return {"message": f"Selector movido a slot {slot_number} exitosamente"}

    except FeedingLineNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post("/{line_id}/selector/reset-position", status_code=status.HTTP_200_OK)
async def reset_selector_position(
    line_id: str, use_case: ResetSelectorPositionUseCaseDep
) -> Dict[str, str]:
    """
    Reinicia la posición del selector a neutral/home (None).

    - **line_id**: ID de la línea de alimentación

    Esta operación se usa típicamente:
    - Al finalizar una sesión de alimentación
    - En caso de error o emergencia
    - Al inicializar el sistema

    Retorna un mensaje de éxito si el reinicio se realizó correctamente.
    """
    try:
        await use_case.execute(line_id)
        return {"message": "Posición del selector reiniciada exitosamente"}

    except FeedingLineNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.patch("/{line_id}/blower", status_code=status.HTTP_200_OK)
async def update_blower(
    line_id: str, request: UpdateBlowerRequest, use_case: UpdateBlowerUseCaseDep
) -> Dict[str, str]:
    """
    Actualiza la configuración del blower de una línea de alimentación.

    - **line_id**: ID de la línea de alimentación
    - **name** (opcional): Nuevo nombre del blower
    - **non_feeding_power** (opcional): Potencia sin alimentación (0-100%)
    - **current_power** (opcional): Potencia actual del blower (0-100%)
    - **blow_before_feeding_time** (opcional): Tiempo de soplado antes (segundos)
    - **blow_after_feeding_time** (opcional): Tiempo de soplado después (segundos)

    Validaciones:
    - non_feeding_power y current_power deben estar entre 0 y 100
    - Los tiempos deben ser mayor o igual a 0

    Retorna un mensaje de éxito si la actualización se realizó correctamente.
    """
    try:
        await use_case.execute(line_id, request)
        return {"message": "Blower actualizado exitosamente"}

    except FeedingLineNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.patch("/{line_id}/dosers/{doser_id}", status_code=status.HTTP_200_OK)
async def update_doser(
    line_id: str,
    doser_id: str,
    request: UpdateDoserRequest,
    use_case: UpdateDoserUseCaseDep,
) -> Dict[str, str]:
    """
    Actualiza la configuración de un doser específico de una línea de alimentación.

    - **line_id**: ID de la línea de alimentación
    - **doser_id**: ID del doser a actualizar
    - **name** (opcional): Nuevo nombre del doser
    - **assigned_silo_id** (opcional): ID del silo asignado
    - **current_rate** (opcional): Tasa de dosificación actual
    - **dosing_range_min** (opcional): Rango mínimo de dosificación
    - **dosing_range_max** (opcional): Rango máximo de dosificación

    Validaciones:
    - Las tasas deben ser mayor o igual a 0
    - dosing_range_min no puede ser mayor que dosing_range_max
    - current_rate debe estar dentro del rango de dosificación

    Retorna un mensaje de éxito si la actualización se realizó correctamente.
    """
    try:
        await use_case.execute(line_id, doser_id, request)
        return {"message": "Doser actualizado exitosamente"}

    except FeedingLineNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get("/{line_id}", response_model=FeedingLineDTO)
async def get_feeding_line(
    line_id: str, use_case: GetFeedingLineUseCaseDep
) -> FeedingLineDTO:
    """
    Obtiene los detalles de una línea de alimentación específica.

    - **line_id**: ID de la línea de alimentación

    Retorna información completa de la línea incluyendo:
    - Blower (soplador)
    - Dosers (dosificadores) con sus silos asignados
    - Selector (selector de slot)
    - Sensors (sensores)
    - Conteo total de jaulas asignadas
    """
    try:
        return await use_case.execute(line_id)

    except FeedingLineNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ID de línea inválido: {str(e)}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )
