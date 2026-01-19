"""Router para endpoints del sistema de alertas."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from api.dependencies import (
    CreateScheduledAlertUseCaseDep,
    DeleteScheduledAlertUseCaseDep,
    GetUnreadCountUseCaseDep,
    ListAlertsUseCaseDep,
    ListScheduledAlertsUseCaseDep,
    MarkAlertReadUseCaseDep,
    MarkAllAlertsReadUseCaseDep,
    ToggleScheduledAlertUseCaseDep,
    UpdateAlertUseCaseDep,
    UpdateScheduledAlertUseCaseDep,
)
from application.dtos.alert_dtos import (
    AlertDTO,
    CreateScheduledAlertRequest,
    ListAlertsRequest,
    ListAlertsResponse,
    ListScheduledAlertsResponse,
    MarkAllReadResponse,
    ScheduledAlertDTO,
    ToggleScheduledAlertResponse,
    UnreadCountResponse,
    UpdateAlertRequest,
    UpdateScheduledAlertRequest,
)

router = APIRouter(prefix="/alerts", tags=["Alerts"])


# ============================================================================
# Endpoints de Alertas
# ============================================================================


@router.get("", response_model=ListAlertsResponse)
async def list_alerts(
    use_case: ListAlertsUseCaseDep,
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Filtrar por status (separados por coma: UNREAD,READ)",
    ),
    type_filter: Optional[str] = Query(
        None,
        alias="type",
        description="Filtrar por tipo (separados por coma: CRITICAL,WARNING)",
    ),
    category_filter: Optional[str] = Query(
        None,
        alias="category",
        description="Filtrar por categoría (separados por coma: DEVICE,INVENTORY)",
    ),
    search: Optional[str] = Query(
        None, description="Buscar en título, mensaje y origen"
    ),
    limit: int = Query(50, ge=1, le=100, description="Cantidad máxima de resultados"),
    offset: int = Query(0, ge=0, description="Desplazamiento para paginación"),
) -> ListAlertsResponse:
    """
    Lista alertas con filtros opcionales.

    - **status**: Filtrar por estado (UNREAD, READ, RESOLVED, ARCHIVED)
    - **type**: Filtrar por tipo (CRITICAL, WARNING, INFO, SUCCESS)
    - **category**: Filtrar por categoría (SYSTEM, DEVICE, FEEDING, INVENTORY, MAINTENANCE, CONNECTION)
    - **search**: Buscar en título, mensaje y origen
    - **limit**: Cantidad máxima de resultados (default: 50)
    - **offset**: Desplazamiento para paginación
    """
    try:
        request = ListAlertsRequest(
            status=status_filter.split(",") if status_filter else None,
            type=type_filter.split(",") if type_filter else None,
            category=category_filter.split(",") if category_filter else None,
            search=search,
            limit=limit,
            offset=offset,
        )
        return await use_case.execute(request)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Filtro inválido: {str(e)}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get("/unread/count", response_model=UnreadCountResponse)
async def get_unread_count(use_case: GetUnreadCountUseCaseDep) -> UnreadCountResponse:
    """
    Obtiene el contador de alertas no leídas.

    Usado principalmente para mostrar el badge en el navbar del frontend.
    Recomendado: polling cada 15 segundos.
    """
    try:
        return await use_case.execute()

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.patch("/{alert_id}", response_model=AlertDTO)
async def update_alert(
    alert_id: str, request: UpdateAlertRequest, use_case: UpdateAlertUseCaseDep
) -> AlertDTO:
    """
    Actualiza una alerta.

    - **alert_id**: ID de la alerta
    - **status**: Nuevo estado (READ, RESOLVED, ARCHIVED)
    - **resolved_by**: Usuario que resuelve (opcional)
    """
    try:
        return await use_case.execute(alert_id, request)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post("/{alert_id}/read", status_code=status.HTTP_200_OK)
async def mark_alert_read(alert_id: str, use_case: MarkAlertReadUseCaseDep) -> dict:
    """
    Marca una alerta como leída.

    - **alert_id**: ID de la alerta a marcar como leída
    """
    try:
        await use_case.execute(alert_id)
        return {"message": "Alerta marcada como leída"}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.patch("/read-all", response_model=MarkAllReadResponse)
async def mark_all_read(use_case: MarkAllAlertsReadUseCaseDep) -> MarkAllReadResponse:
    """
    Marca todas las alertas no leídas como leídas.

    Retorna la cantidad de alertas actualizadas.
    """
    try:
        return await use_case.execute()

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


# ============================================================================
# Endpoints de Alertas Programadas
# ============================================================================


@router.get("/scheduled", response_model=ListScheduledAlertsResponse)
async def list_scheduled_alerts(
    use_case: ListScheduledAlertsUseCaseDep,
) -> ListScheduledAlertsResponse:
    """
    Lista todas las alertas programadas.

    Ordenadas por próxima fecha de disparo.
    """
    try:
        return await use_case.execute()

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post(
    "/scheduled", response_model=ScheduledAlertDTO, status_code=status.HTTP_201_CREATED
)
async def create_scheduled_alert(
    request: CreateScheduledAlertRequest, use_case: CreateScheduledAlertUseCaseDep
) -> ScheduledAlertDTO:
    """
    Crea una nueva alerta programada.

    - **title**: Título de la alerta
    - **message**: Mensaje de la alerta
    - **type**: Tipo de alerta (CRITICAL, WARNING, INFO, SUCCESS)
    - **category**: Categoría (MAINTENANCE para alertas programadas)
    - **frequency**: Frecuencia (DAILY, WEEKLY, MONTHLY, CUSTOM_DAYS)
    - **next_trigger_date**: Próxima fecha de disparo
    - **days_before_warning**: Días de anticipación (default: 0)
    - **device_id**: ID del dispositivo relacionado (opcional)
    - **device_name**: Nombre del dispositivo (opcional)
    - **custom_days_interval**: Intervalo en días para CUSTOM_DAYS (requerido si frequency=CUSTOM_DAYS)
    - **metadata**: Datos adicionales (opcional)
    """
    try:
        return await use_case.execute(request)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Datos inválidos: {str(e)}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.patch("/scheduled/{alert_id}", response_model=ScheduledAlertDTO)
async def update_scheduled_alert(
    alert_id: str,
    request: UpdateScheduledAlertRequest,
    use_case: UpdateScheduledAlertUseCaseDep,
) -> ScheduledAlertDTO:
    """
    Actualiza una alerta programada.

    - **alert_id**: ID de la alerta programada
    - Campos opcionales a actualizar (solo se actualizan los enviados)
    """
    try:
        return await use_case.execute(alert_id, request)

    except ValueError as e:
        if "no encontrada" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Datos inválidos: {str(e)}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.delete("/scheduled/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scheduled_alert(
    alert_id: str, use_case: DeleteScheduledAlertUseCaseDep
) -> None:
    """
    Elimina una alerta programada.

    - **alert_id**: ID de la alerta programada a eliminar
    """
    try:
        await use_case.execute(alert_id)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.patch(
    "/scheduled/{alert_id}/toggle", response_model=ToggleScheduledAlertResponse
)
async def toggle_scheduled_alert(
    alert_id: str, use_case: ToggleScheduledAlertUseCaseDep
) -> ToggleScheduledAlertResponse:
    """
    Activa/desactiva una alerta programada.

    - **alert_id**: ID de la alerta programada

    Retorna el nuevo estado de is_active.
    """
    try:
        return await use_case.execute(alert_id)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )
