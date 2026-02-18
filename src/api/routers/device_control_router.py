"""Router para control directo de devices (blower, doser, selector)."""

from typing import Dict

from fastapi import APIRouter, HTTPException, status

from api.dependencies import (
    GetBlowerStatusUseCaseDep,
    GetDoserStatusUseCaseDep,
    GetSelectorStatusUseCaseDep,
    MoveSelectorDirectUseCaseDep,
    ResetSelectorDirectUseCaseDep,
    SetBlowerPowerUseCaseDep,
    SetCoolerPowerUseCaseDep,
    SetDoserRateUseCaseDep,
    SetDoserSpeedUseCaseDep,
    TurnBlowerOffUseCaseDep,
    TurnBlowerOnUseCaseDep,
    TurnCoolerOffUseCaseDep,
    TurnCoolerOnUseCaseDep,
    TurnDoserOffUseCaseDep,
    TurnDoserOnUseCaseDep,
)
from application.dtos.device_control_dtos import (
    BlowerStatusResponse,
    DoserStatusResponse,
    MoveSelectorRequest,
    SelectorStatusResponse,
    SetBlowerPowerRequest,
    SetCoolerPowerRequest,
    SetDoserRateRequest,
    SetDoserSpeedRequest,
)
from domain.exceptions import DomainException

router = APIRouter(prefix="/device-control", tags=["Device Control"])


@router.post("/blowers/{blower_id}/on", status_code=status.HTTP_200_OK)
async def turn_blower_on(
    blower_id: str,
    use_case: TurnBlowerOnUseCaseDep,
) -> Dict[str, str]:
    """
    Enciende un blower específico.

    El blower se enciende a su potencia non_feeding_power configurada.

    - **blower_id**: ID del blower (UUID)
    """
    try:
        await use_case.execute(blower_id)
        return {"message": "Blower turned on successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post("/blowers/{blower_id}/off", status_code=status.HTTP_200_OK)
async def turn_blower_off(
    blower_id: str,
    use_case: TurnBlowerOffUseCaseDep,
) -> Dict[str, str]:
    """
    Apaga un blower específico.

    El blower se apaga (potencia a 0%).

    - **blower_id**: ID del blower (UUID)
    """
    try:
        await use_case.execute(blower_id)
        return {"message": "Blower turned off successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post("/blowers/{blower_id}/set-power", status_code=status.HTTP_200_OK)
async def set_blower_power(
    blower_id: str,
    request: SetBlowerPowerRequest,
    use_case: SetBlowerPowerUseCaseDep,
) -> Dict[str, str]:
    """
    Establece la potencia de un blower específico.

    Control manual del blower sin sesión de alimentación activa.
    Útil para pruebas y mantenimiento.

    - **blower_id**: ID del blower (UUID)
    - **power_percentage**: Potencia del blower (0-100%)
    """
    try:
        await use_case.execute(blower_id, request.power_percentage)
        return {
            "message": f"Blower power set to {request.power_percentage}% successfully"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post("/dosers/{doser_id}/on", status_code=status.HTTP_200_OK)
async def turn_doser_on(
    doser_id: str,
    use_case: TurnDoserOnUseCaseDep,
) -> Dict[str, str]:
    """
    Enciende un doser específico.

    El doser se enciende a su tasa mínima del rango configurado.

    - **doser_id**: ID del doser (UUID)
    """
    try:
        await use_case.execute(doser_id)
        return {"message": "Doser turned on successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post("/dosers/{doser_id}/off", status_code=status.HTTP_200_OK)
async def turn_doser_off(
    doser_id: str,
    use_case: TurnDoserOffUseCaseDep,
) -> Dict[str, str]:
    """
    Apaga un doser específico.

    El doser se apaga (tasa a 0).

    - **doser_id**: ID del doser (UUID)
    """
    try:
        await use_case.execute(doser_id)
        return {"message": "Doser turned off successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post("/dosers/{doser_id}/set-rate", status_code=status.HTTP_200_OK)
async def set_doser_rate(
    doser_id: str,
    request: SetDoserRateRequest,
    use_case: SetDoserRateUseCaseDep,
) -> Dict[str, str]:
    """
    Establece la tasa de dosificación de un doser específico.

    Control manual del doser sin sesión de alimentación activa.
    Útil para pruebas y mantenimiento.

    - **doser_id**: ID del doser (UUID)
    - **rate_kg_min**: Tasa de dosificación en kg/min
    """
    try:
        await use_case.execute(doser_id, request.rate_kg_min)
        return {
            "message": f"Doser rate set to {request.rate_kg_min} kg/min successfully"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post("/dosers/{doser_id}/set-speed", status_code=status.HTTP_200_OK)
async def set_doser_speed(
    doser_id: str,
    request: SetDoserSpeedRequest,
    use_case: SetDoserSpeedUseCaseDep,
) -> Dict[str, str]:
    """
    Establece la velocidad del motor de un doser específico.

    Envía el porcentaje de velocidad directamente al PLC.
    Útil para calibración de dosificadores.

    - **doser_id**: ID del doser (UUID)
    - **speed_percentage**: Velocidad del motor (1-100%)
    """
    try:
        await use_case.execute(doser_id, request.speed_percentage)
        return {"message": f"Doser speed set to {request.speed_percentage}%"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post("/selectors/{selector_id}/move", status_code=status.HTTP_200_OK)
async def move_selector(
    selector_id: str,
    request: MoveSelectorRequest,
    use_case: MoveSelectorDirectUseCaseDep,
) -> Dict[str, str]:
    """
    Mueve un selector específico a un slot.

    Control manual del selector sin sesión de alimentación activa.
    Útil para pruebas y mantenimiento.

    - **selector_id**: ID del selector (UUID)
    - **slot_number**: Número de slot destino (1 a capacity)
    """
    try:
        await use_case.execute(selector_id, request.slot_number)
        return {"message": f"Selector moved to slot {request.slot_number} successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post("/selectors/{selector_id}/reset", status_code=status.HTTP_200_OK)
async def reset_selector(
    selector_id: str,
    use_case: ResetSelectorDirectUseCaseDep,
) -> Dict[str, str]:
    """
    Resetea la posición de un selector específico a neutral.

    Control manual del selector sin sesión de alimentación activa.
    Útil para pruebas y mantenimiento.

    - **selector_id**: ID del selector (UUID)
    """
    try:
        await use_case.execute(selector_id)
        return {"message": "Selector position reset successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get("/blowers/{blower_id}/status", status_code=status.HTTP_200_OK)
async def get_blower_status(
    blower_id: str,
    use_case: GetBlowerStatusUseCaseDep,
) -> BlowerStatusResponse:
    """
    Obtiene el estado actual de un blower específico.

    - **blower_id**: ID del blower (UUID)
    """
    try:
        return await use_case.execute(blower_id)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get("/dosers/{doser_id}/status", status_code=status.HTTP_200_OK)
async def get_doser_status(
    doser_id: str,
    use_case: GetDoserStatusUseCaseDep,
) -> DoserStatusResponse:
    """
    Obtiene el estado actual de un doser específico.

    - **doser_id**: ID del doser (UUID)
    """
    try:
        return await use_case.execute(doser_id)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get("/selectors/{selector_id}/status", status_code=status.HTTP_200_OK)
async def get_selector_status(
    selector_id: str,
    use_case: GetSelectorStatusUseCaseDep,
) -> SelectorStatusResponse:
    """
    Obtiene el estado actual de un selector específico.

    - **selector_id**: ID del selector (UUID)
    """
    try:
        return await use_case.execute(selector_id)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


# =========================================================================
# Cooler Control
# =========================================================================


@router.post("/coolers/{cooler_id}/on", status_code=status.HTTP_200_OK)
async def turn_cooler_on(
    cooler_id: str,
    use_case: TurnCoolerOnUseCaseDep,
) -> Dict[str, str]:
    """
    Enciende un cooler específico.

    El cooler se enciende a su potencia cooling_power_percentage configurada.

    - **cooler_id**: ID del cooler (UUID)
    """
    try:
        await use_case.execute(cooler_id)
        return {"message": "Cooler turned on successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post("/coolers/{cooler_id}/off", status_code=status.HTTP_200_OK)
async def turn_cooler_off(
    cooler_id: str,
    use_case: TurnCoolerOffUseCaseDep,
) -> Dict[str, str]:
    """
    Apaga un cooler específico.

    El cooler se apaga (potencia a 0%).

    - **cooler_id**: ID del cooler (UUID)
    """
    try:
        await use_case.execute(cooler_id)
        return {"message": "Cooler turned off successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post("/coolers/{cooler_id}/set-power", status_code=status.HTTP_200_OK)
async def set_cooler_power(
    cooler_id: str,
    request: SetCoolerPowerRequest,
    use_case: SetCoolerPowerUseCaseDep,
) -> Dict[str, str]:
    """
    Establece la potencia de un cooler específico.

    Control manual del cooler sin sesión de alimentación activa.
    Útil para pruebas y mantenimiento.

    - **cooler_id**: ID del cooler (UUID)
    - **power_percentage**: Potencia del cooler (0-100%)
    """
    try:
        await use_case.execute(cooler_id, request.power_percentage)
        return {
            "message": f"Cooler power set to {request.power_percentage}% successfully"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )
